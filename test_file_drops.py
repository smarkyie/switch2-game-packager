"""Native WM_DROPFILES regression in real mainloop, not synchronous update().

Only addresses the window of a child process launched by this test. Uses tiny
synthetic images/game folders; never drives the user's other applications.
"""
from pathlib import Path
import ctypes, json, os, struct, subprocess, sys, tempfile, time, unittest
ROOT=Path(__file__).resolve().parent


def post_drop(hwnd, path):
    from ctypes import wintypes as w
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    user=ctypes.WinDLL('user32',use_last_error=True)
    kernel.GlobalAlloc.argtypes=[w.UINT,ctypes.c_size_t];kernel.GlobalAlloc.restype=w.HGLOBAL
    kernel.GlobalLock.argtypes=[w.HGLOBAL];kernel.GlobalLock.restype=ctypes.c_void_p
    kernel.GlobalUnlock.argtypes=[w.HGLOBAL];kernel.GlobalFree.argtypes=[w.HGLOBAL]
    user.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];user.PostMessageW.restype=w.BOOL
    payload=struct.pack('<IiiII',20,10,10,0,1)+(str(path)+'\0\0').encode('utf-16le')
    handle=kernel.GlobalAlloc(0x42,len(payload))
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    pointer=kernel.GlobalLock(handle)
    if not pointer:kernel.GlobalFree(handle);raise ctypes.WinError(ctypes.get_last_error())
    ctypes.memmove(pointer,payload,len(payload));kernel.GlobalUnlock(handle)
    if not user.PostMessageW(hwnd,0x233,handle,0):
        kernel.GlobalFree(handle);raise ctypes.WinError(ctypes.get_last_error())


def fixtures(root):
    from PIL import Image
    images=[]
    for name in ('art.png','日本語 art.webp','again.png'):
        p=root/name;Image.new('RGB',(320,180),'#55aaff').save(p);images.append(p)
    game=root/'Game';(game/'exefs').mkdir(parents=True);(game/'romfs').mkdir()
    n=bytearray(0x100);n[:4]=b'META';struct.pack_into('<II',n,0x70,0x80,0x80)
    n[0x80:0x84]=b'ACI0';struct.pack_into('<Q',n,0x90,0x0400111122220000)
    (game/'exefs/main.npdm').write_bytes(n);(game/'exefs/main').write_bytes(b'NSO0'+bytes(256))
    (game/'romfs/data.bin').write_bytes(b'Example')
    return images,game


def source_child(root):
    import faulthandler
    faulthandler.enable()
    sys.path.insert(0,str(ROOT/'src'))
    from app import App
    images,game=fixtures(root)
    app=App(show_startup=False,preferences_path=root/'preferences.json')
    errors=[];app.report_callback_exception=lambda *a:errors.append(str(a[1]))
    received=[]
    original_receive=app.receive_drop
    def observe(paths):
        received.append(paths)
        original_receive(paths)
    app.receive_drop=observe
    sequence=[images[0],game,images[1],game,images[2],images[0]]
    state={'index':0,'start':0,'sent':False}
    def step():
        i=state['index']
        if i==len(sequence):
            (root/'drop-result.json').write_text(json.dumps({'passed':not errors,'drops':i,'errors':errors}))
            app.close();return
        p=sequence[i]
        if not state['sent']:
            post_drop(app._drops.hwnd,p);state.update(sent=True,start=time.monotonic())
        ready=len(received)>i and ((not app.scanning and bool(app.snapshots)) if p==game else app.art_path==p)
        if ready and not errors:
            state.update(index=i+1,sent=False)
        elif errors or time.monotonic()-state['start']>6:
            (root/'drop-result.json').write_text(json.dumps({'passed':False,'drops':i,'errors':errors or ['drop timed out']}))
            app.close();return
        app.after(60,step)
    app.after(300,step);app.mainloop()


def frozen_check(executable):
    """Deliver native drops to the frozen EXE's own mainloop and close cleanly."""
    from ctypes import wintypes as w
    scratch=ROOT/'test-work';scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='frozen-drop-',dir=scratch) as temp:
        root=Path(temp);images,game=fixtures(root)
        env=os.environ.copy();env['LOCALAPPDATA']=str(root/'preferences')
        proc=subprocess.Popen([str(Path(executable).resolve())],cwd=ROOT,env=env)
        user=ctypes.WinDLL('user32',use_last_error=True)
        user.PostMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM];user.PostMessageW.restype=w.BOOL
        user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
        user.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
        user.IsWindowVisible.argtypes=[w.HWND];user.IsWindowVisible.restype=w.BOOL
        signature=ctypes.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
        user.EnumWindows.argtypes=[signature,w.LPARAM]
        windows=[]
        def owned_processes():
            # PyInstaller one-file executables have a bootloader parent and a
            # GUI child. Verify that ancestry rather than choosing by title.
            class Entry(ctypes.Structure):
                _fields_=[('size',w.DWORD),('usage',w.DWORD),('pid',w.DWORD),('heap',ctypes.c_size_t),
                          ('module',w.DWORD),('threads',w.DWORD),('parent',w.DWORD),('priority',w.LONG),
                          ('flags',w.DWORD),('name',w.WCHAR*260)]
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.CreateToolhelp32Snapshot.argtypes=[w.DWORD,w.DWORD];kernel.CreateToolhelp32Snapshot.restype=w.HANDLE
            kernel.Process32FirstW.argtypes=[w.HANDLE,ctypes.POINTER(Entry)];kernel.Process32NextW.argtypes=[w.HANDLE,ctypes.POINTER(Entry)]
            kernel.CloseHandle.argtypes=[w.HANDLE]
            handle=kernel.CreateToolhelp32Snapshot(2,0);pairs=[]
            try:
                entry=Entry();entry.size=ctypes.sizeof(entry)
                more=kernel.Process32FirstW(handle,ctypes.byref(entry))
                while more:
                    pairs.append((entry.pid,entry.parent))
                    more=kernel.Process32NextW(handle,ctypes.byref(entry))
            finally:kernel.CloseHandle(handle)
            family={proc.pid}
            while True:
                found=family|{pid for pid,parent in pairs if parent in family}
                if found==family:return family
                family=found
        family={proc.pid}
        @signature
        def visit(hwnd,lp):
            pid=w.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            if pid.value in family and user.IsWindowVisible(hwnd):
                text=ctypes.create_unicode_buffer(512);user.GetWindowTextW(hwnd,text,512)
                if text.value=='NSP Box':windows.append(hwnd)
            return True
        try:
            deadline=time.monotonic()+20
            while not windows and time.monotonic()<deadline:
                if proc.poll() is not None:raise AssertionError('Frozen app exited before its window opened')
                family=owned_processes();user.EnumWindows(visit,0);time.sleep(.08)
            assert len(windows)==1,'Frozen NSP Box window not uniquely identified'
            for path in [images[0],game,images[1],images[2]]:
                post_drop(windows[0],path)
                try:code=proc.wait(timeout=.7)
                except subprocess.TimeoutExpired:continue
                raise AssertionError(f'Frozen app crashed after {path.name}: {code:#x}')
            user.PostMessageW(windows[0],0x10,0,0)
            assert proc.wait(timeout=10)==0,'Frozen app did not close normally'
            return {'native_file_drops':'passed','drops':4,'frozen':True}
        finally:
            if proc.poll() is None:proc.terminate();proc.wait(timeout=5)


@unittest.skipUnless(sys.platform=='win32','Native Windows shell test')
class FileDropRegression(unittest.TestCase):
    def test_posted_images_folders_and_repeated_drops_in_mainloop(self):
        scratch=ROOT/'test-work';scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='drop-loop-',dir=scratch) as temp:
            result=subprocess.run([sys.executable,'-X','faulthandler',str(Path(__file__).resolve()),'--child',temp],
                                  cwd=ROOT,capture_output=True,text=True,timeout=25)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads((Path(temp)/'drop-result.json').read_text())
            self.assertTrue(report['passed'],report);self.assertEqual(report['drops'],6)


if __name__=='__main__':
    if '--child' in sys.argv:source_child(Path(sys.argv[-1]))
    else:unittest.main()
