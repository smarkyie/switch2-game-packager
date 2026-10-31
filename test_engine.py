"""Format round trips and failure behavior; no game files required."""
from pathlib import Path
import sys,tempfile,struct,threading,unittest,json,mmap
sys.path.insert(0,str(Path(__file__).parent/'src'))
import engine,verify_format as verify
from PIL import Image

class PackagingTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).parent/'test-work';scratch.mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(prefix='case-',dir=scratch);self.root=Path(self.tmp.name)
        self.game=self.root/'Example Game [0400111122220000]'
        for version in (65536,131072):
            p=self.game/'updates'/str(version);(p/'exefs').mkdir(parents=True);(p/'romfs'/'日本語').mkdir(parents=True)
            npdm=bytearray(0x100);npdm[:4]=b'META';struct.pack_into('<II',npdm,0x70,0x80,0x80)
            npdm[0x80:0x84]=b'ACI0';struct.pack_into('<Q',npdm,0x90,0x0400111122220000)
            (p/'exefs/main.npdm').write_bytes(npdm);(p/'exefs/main').write_bytes(b'NSO0'+bytes(256))
            (p/'romfs'/'日本語'/'hello.bin').write_bytes(bytes(range(256))*271)
            (p/'romfs'/'empty').write_bytes(b'')
        self.art=self.root/'art.png';Image.new('RGBA',(500,300),(20,90,180,120)).save(self.art)

    def tearDown(self):self.tmp.cleanup()

    def test_round_trip_dynamic_title_and_version(self):
        snapshots,_=engine.find_snapshots(self.game);self.assertEqual([s.version for s in snapshots],[131072,65536])
        out=self.root/'Example.xci';result=engine.build(snapshots[0],out,'Example 日本語','2.0',self.art)
        self.assertTrue(result['verified']);self.assertEqual(result['source_file_count'],4)
        self.assertEqual(result['title_id'],'0400111122220000');self.assertTrue(out.is_file())
        self.assertFalse(out.with_suffix('.xci.report.json').exists());self.assertIsNone(result['switch2_companion'])
        with out.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
            buf=verify.Region(mm);top=verify.partition(buf,verify.u('Q',buf,0x130)[0])
            contents=verify.partition(top['secure'])
            control=next(verify.nca_sections(b) for b in contents.values() if b[0x205]==2)
            packed=verify.romfs_files(control[2][0][1])
            self.assertEqual(bytes(packed['icon_AmericanEnglish.dat']),engine.artwork_bytes(self.art))
            nacp=bytes(packed['control.nacp'])
            self.assertEqual(nacp[:0x200].split(b'\0')[0].decode(),'Example 日本語')
            self.assertEqual(nacp[0x3060:0x3070].split(b'\0')[0],b'2.0')

    def test_existing_output_unchanged(self):
        snapshots,_=engine.find_snapshots(self.game);out=self.root/'Existing.xci';out.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):engine.build(snapshots[0],out,'Example','1')
        self.assertEqual(out.read_bytes(),b'existing')

    def test_cancel_removes_partial(self):
        snapshots,_=engine.find_snapshots(self.game);out=self.root/'Cancelled.xci';cancel=threading.Event()
        def progress(stage,value):
            if stage=='Writing XCI':cancel.set()
        with self.assertRaises(InterruptedError):engine.build(snapshots[0],out,'Example','1',notify=progress,cancel=cancel)
        self.assertFalse(out.exists());self.assertEqual(list(self.root.glob('*.partial')),[])

    def test_invalid_npdm_rejected(self):
        for p in self.game.rglob('main.npdm'):p.write_bytes(b'broken')
        with self.assertRaises(ValueError):engine.find_snapshots(self.game)

    def test_empty_romfs_rejected(self):
        snapshots,_=engine.find_snapshots(self.game)
        for p in (snapshots[0].root/'romfs').rglob('*'):
            if p.is_file():p.unlink()
        with self.assertRaisesRegex(ValueError,'empty'):engine.build(snapshots[0],self.root/'Empty.xci','Example','1')

    def test_output_in_romfs_rejected(self):
        snapshots,_=engine.find_snapshots(self.game)
        with self.assertRaisesRegex(ValueError,'outside'):engine.build(snapshots[0],snapshots[0].root/'romfs'/'bad.xci','Example','1')

    def test_artwork_fit_and_alpha(self):
        import io
        data=engine.artwork_bytes(self.art)
        with Image.open(io.BytesIO(data)) as im:self.assertEqual(im.size,(256,256));self.assertEqual(im.format,'JPEG')

    def test_generated_control_uses_documented_platform_offsets(self):
        snapshot=engine.find_snapshots(self.game)[0][0]
        entries,preserved=engine.control_data(snapshot,'Example','1',None)
        nacp=dict(entries)['control.nacp']
        self.assertFalse(preserved);self.assertEqual(nacp[0x3214],3);self.assertEqual(nacp[0x3217],1)
        self.assertEqual(nacp[0x3215],0);self.assertEqual(nacp[0x3218:0x33b0],bytes(0x198))

    def test_compressed_title_data_is_preserved(self):
        snapshot=engine.find_snapshots(self.game)[0][0]
        original=bytearray(0x4000);original[:0x3000]=bytes(range(256))*48
        original[0x3215]=1;original[0x3217]=1
        snapshot.nacp=self.root/'control.nacp';snapshot.nacp.write_bytes(original)
        entries,preserved=engine.control_data(snapshot,'Replacement','2',None)
        nacp=dict(entries)['control.nacp']
        self.assertTrue(preserved);self.assertEqual(nacp[:0x3000],original[:0x3000])
        self.assertEqual(nacp[0x3215],1);self.assertEqual(nacp[0x3217],1)

if __name__=='__main__':unittest.main(verbosity=2)
