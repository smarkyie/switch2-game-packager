"""Smoke-test frozen single-file and optional-folder output with synthetic content."""
from pathlib import Path
import argparse,json,struct,subprocess,tempfile,sys
from PIL import Image
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'src'))
import engine
import dlc
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--executable',type=Path)
args=parser.parse_args()
scratch=root/'test-work';scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='frozen-',dir=scratch) as tmp:
    base=Path(tmp);game=base/'Sample Game';(game/'exefs').mkdir(parents=True);(game/'romfs').mkdir()
    b=bytearray(0x100);b[:4]=b'META';struct.pack_into('<II',b,0x70,0x80,0x80);b[0x80:0x84]=b'ACI0'
    struct.pack_into('<Q',b,0x90,0x0400111122220000)
    (game/'exefs/main.npdm').write_bytes(b);(game/'exefs/main').write_bytes(b'NSO0'+bytes(256))
    (game/'romfs/example.bin').write_bytes(bytes(range(256))*512)
    snapshot=engine.find_snapshots(game)[0][0];inventory=engine.source_inventory(snapshot.root)
    exe=(args.executable.resolve() if args.executable else root/('dist/NSP-Box.exe' if sys.platform=='win32' else 'dist/NSP-Box'))
    for folder_mode in (False,True):
        for kind in ('nsp',):
            for extension,format_name in [('png','PNG'),('webp','WEBP'),('ico','ICO'),('avif','AVIF')]:
                art=base/('artwork.'+extension);Image.new('RGB',(256,256),'#137eef').save(art,format=format_name)
                case=base/(str(folder_mode)+'-'+kind+'-'+extension);case.mkdir()
                requested=case/('Output.'+kind)
                args=[str(exe),'--package',str(game),'--output',str(requested),'--artwork',str(art),
                      '--title','Smoke Test','--artwork-crop','.25','.25','.75','.75']
                args.append('--package-folder' if folder_mode else '--no-package-folder')
                result=subprocess.run(args,timeout=30);assert result.returncode==0
                out=requested.parent/requested.stem/requested.name if folder_mode else requested
                assert out.is_file()
                if folder_mode:
                    report=json.loads(out.with_suffix('.'+kind+'.report.json').read_text(encoding='utf-8'))
                    assert report['verified'] and report['version']==engine.VERSION and report['source_file_count']==3
                    assert report['output_format']==kind.upper() and report['package_folder']
                    assert (out.parent/'main.npdm').read_bytes()==(game/'exefs/main.npdm').read_bytes()
                    assert len(list(out.parent.iterdir()))==3
                else:
                    assert list(case.iterdir())==[out]
                    assert len(engine.verify_image(out,snapshot,inventory,lambda *args:None,None))==3
                print(json.dumps({'frozen_smoke':'passed','format':kind,'artwork':extension,
                                  'package_folder':folder_mode,'app_version':engine.VERSION}),flush=True)
    content=base/'dlc'/'0400111122221001'/'0'/'romfs';content.mkdir(parents=True)
    (content/'dlc.bin').write_bytes(b'Synthetic DLC fixture'+bytes(range(256))*257)
    addon=dlc.find_snapshots(content)[0]
    for kind in ('nsp',):
        requested=base/('DLC.'+kind)
        result=subprocess.run([str(exe),'--dlc','--package',str(content),'--output',str(requested)],timeout=30)
        assert result.returncode==0 and requested.is_file()
        assert dlc.verify(requested,addon,dlc.inventory(addon))==1
        assert not requested.with_suffix('.'+kind+'.report.json').exists()
        print(json.dumps({'frozen_smoke':'passed','format':kind,'content':'DLC','app_version':engine.VERSION}),flush=True)

if sys.platform=="win32":
    from test_file_drops import frozen_check
    print(json.dumps(frozen_check(exe)),flush=True)
