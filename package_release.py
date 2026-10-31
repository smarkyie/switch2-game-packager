"""Assemble an allowlisted portable release for GitHub, without game content."""
from pathlib import Path
from importlib.metadata import version
import argparse,datetime,hashlib,json,os,platform,re,shutil,ssl,sys,zipfile
import tkinter

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
import engine

DOCS=('README.md','BUILD.md','TECHNICAL_NOTES.md','PERFORMANCE_NOTES.md','CHANGELOG.md',
      'LICENSE.txt','THIRD_PARTY_NOTICES.md','RELEASE_VALIDATION.md','GITHUB_RELEASES.md','DISCLAIMER.md')
SOURCE=('Packager.spec','app.ico','requirements-build.txt','package_release.py','frozen_smoke.py',
        'test_engine.py','test_ui.py','test_artwork.py','test_performance_safety.py','test_nsp.py','test_compatibility.py','.gitignore')

def source_files():
    paths=[ROOT/p for p in DOCS+SOURCE]
    paths+=sorted((ROOT/'src').glob('*.py'))
    paths+=sorted(p for p in (ROOT/'licenses').rglob('*') if p.is_file())
    paths+=sorted((ROOT/'.github/workflows').glob('*.yml'))
    for path in paths:
        if not path.is_file():raise FileNotFoundError(path.name)
        if path.is_symlink():raise ValueError('Linked release input: '+path.name)
    return paths

def notes():
    text=(ROOT/'CHANGELOG.md').read_text(encoding='utf-8')
    match=re.search(r'^## '+re.escape(engine.VERSION)+r'[^\n]*\n(.*?)(?=^## |\Z)',text,re.M|re.S)
    if not match:raise ValueError('Add changelog notes for '+engine.VERSION)
    return ('# Switch 2 Game Packager '+engine.VERSION+'\n\n'+match.group(1).strip()+
            '\n\nPortable Windows x64 build. Extract the complete Windows ZIP and run '
            '`Switch2-XCI-Packager.exe`. Source, licenses and build notes are included. '
            'No game data, artwork, firmware or retail keys are included.\n\n'
            '**Caution — experimental:** set emulator memory to **12 GiB** before testing Switch 2 packages. '
            'Booting without an external companion was reported in PokeDinner 2.0.0 with this setting; '
            'other games/builds may differ. The app does not change emulator memory settings. '
            'Verification does not guarantee booting or gameplay.\n\n'
            '**Performance caution:** considerably lower performance was reported without the external '
            '`main.npdm`, even with 12 GiB selected. Keep **Create package folder** enabled and retain '
            'its companion beside the game for the recommended setup. This is not a controlled benchmark.\n\n'
            '**Piracy is not supported.** Use only lawfully obtained content you are authorized '
            'to use. Nintendo names and related marks belong to Nintendo; game content belongs '
            'to its respective rights holders. This independent project is not affiliated with '
            'or endorsed by Nintendo. See `DISCLAIMER.md` in the downloads for full notices.\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'release')
    parser.add_argument('--executable',type=Path,default=ROOT/'dist/Switch2-XCI-Packager.exe')
    args=parser.parse_args()
    if not re.fullmatch(r'\d+\.\d+\.\d+',engine.VERSION):raise ValueError('Invalid release version')
    tag='v'+engine.VERSION
    if os.environ.get('GITHUB_REF_TYPE')=='tag' and os.environ.get('GITHUB_REF_NAME')!=tag:
        raise ValueError('Git tag must match engine.VERSION: '+tag)
    files=source_files();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    name='Switch2-XCI-Packager-'+tag+'-Windows-x64';release=out/name
    release.mkdir()  # Refuse to overwrite an existing assembled release.
    shutil.copy2(args.executable,release/'Switch2-XCI-Packager.exe')
    for path in files:
        relative=path.relative_to(ROOT)
        dest=release/relative if relative.parts[0]=='licenses' or relative.as_posix() in DOCS else release/'source'/relative
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    shutil.copy2(ROOT/'BUILD.md',release/'source/BUILD.md')
    (release/'compatibility').mkdir()
    (release/'compatibility/plaintext-repack.keys').write_text(engine.placeholder_keys(),encoding='utf-8')
    info={'app_version':engine.VERSION,'build_date':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'platform':'Windows x64','python':platform.python_version(),'pillow':version('Pillow'),
          'pyinstaller':version('PyInstaller'),'pyinstaller_hooks':version('pyinstaller-hooks-contrib'),
          'tcl':tkinter.Tcl().eval('info patchlevel'),'openssl':ssl.OPENSSL_VERSION,
          'source_commit':os.environ.get('GITHUB_SHA'),'code_license':'MIT','ai_assisted':True,'signed':False,
          'executable_sha256':hashlib.sha256((release/'Switch2-XCI-Packager.exe').read_bytes()).hexdigest()}
    (release/'BUILD_INFO.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    manifest=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(release).as_posix()+'\n'
                     for p in sorted(release.rglob('*')) if p.is_file())
    (release/'SHA256SUMS.txt').write_text(manifest,encoding='utf-8')
    portable=out/(name+'.zip');source=out/('Switch2-XCI-Packager-'+tag+'-source.zip')
    with zipfile.ZipFile(portable,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for p in sorted(release.rglob('*')):
            if p.is_file():archive.write(p,Path(name)/p.relative_to(release))
    with zipfile.ZipFile(source,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for p in files:archive.write(p,Path('switch2-game-packager-'+tag)/p.relative_to(ROOT))
    for p in (portable,source):
        with zipfile.ZipFile(p) as archive:
            if archive.testzip() is not None:raise ValueError('Archive integrity failed: '+p.name)
    sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in (portable,source))
    (out/'SHA256SUMS.txt').write_text(sums,encoding='utf-8')
    (out/'RELEASE_NOTES.md').write_text(notes(),encoding='utf-8')
    print(json.dumps({'version':engine.VERSION,'portable':portable.name,'source':source.name}))

if __name__=='__main__':main()
