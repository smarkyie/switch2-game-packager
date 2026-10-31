"""Smoke-test the final frozen entry point using original synthetic files."""
from pathlib import Path
import json,struct,subprocess,tempfile,sys
from PIL import Image
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root/'src'))
from engine import VERSION
scratch=root/'test-work';scratch.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='frozen-',dir=scratch) as tmp:
    base=Path(tmp);game=base/'Sample Game';(game/'exefs').mkdir(parents=True);(game/'romfs').mkdir()
    b=bytearray(0x100);b[:4]=b'META';struct.pack_into('<II',b,0x70,0x80,0x80);b[0x80:0x84]=b'ACI0'
    struct.pack_into('<Q',b,0x90,0x0400111122220000)
    (game/'exefs/main.npdm').write_bytes(b);(game/'exefs/main').write_bytes(b'NSO0'+bytes(256))
    (game/'romfs/example.bin').write_bytes(bytes(range(256))*512)
    exe=root/'dist/Switch2-XCI-Packager.exe'
    for extension,format_name,kind in [('png','PNG','xci'),('webp','WEBP','xci'),('ico','ICO','xci'),('avif','AVIF','xci'),
                                     ('png','PNG','nsp'),('webp','WEBP','nsp'),('ico','ICO','nsp'),('avif','AVIF','nsp')]:
        art=base/('artwork.'+extension);Image.new('RGB',(256,256),'#137eef').save(art,format=format_name)
        out=base/('Output-'+extension+'.'+kind)
        result=subprocess.run([str(exe),'--package',str(game),'--output',str(out),'--artwork',str(art),'--title','Smoke Test',
                               '--artwork-crop','.25','.25','.75','.75'],timeout=30)
        assert result.returncode==0
        report=json.loads(out.with_suffix('.'+kind+'.report.json').read_text())
        assert report['verified'] and report['version']==VERSION and report['source_file_count']==3
        assert report['output_format']==kind.upper()
        assert (out.parent/'main.npdm').read_bytes()==(game/'exefs/main.npdm').read_bytes()
        print(json.dumps({'frozen_smoke':'passed','format':kind,'artwork':extension,'app_version':report['version'],'verified':True}),flush=True)
