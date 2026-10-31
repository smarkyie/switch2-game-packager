"""UI integration checks using synthetic content and the app's own widgets."""
from pathlib import Path
import ctypes, io, json, struct, sys, tempfile, time, unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'src'))
from app import App
from crop_dialog import CropDialog
from PIL import Image

class InterfaceTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).parent/'test-work';scratch.mkdir(exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(prefix='ui-',dir=scratch);self.root=Path(self.tmp.name)
        self.game=self.root/'Sample Game'
        for version in (65536,131072):
            p=self.game/'updates'/str(version);(p/'exefs').mkdir(parents=True);(p/'romfs').mkdir()
            npdm=bytearray(0x100);npdm[:4]=b'META';struct.pack_into('<II',npdm,0x70,0x80,0x80)
            npdm[0x80:0x84]=b'ACI0';struct.pack_into('<Q',npdm,0x90,0x0400111122220000)
            (p/'exefs/main.npdm').write_bytes(npdm);(p/'exefs/main').write_bytes(b'NSO0'+bytes(256))
            (p/'romfs/content.bin').write_bytes(bytes(range(256))*81)
        self.art=self.root/'cover.png';Image.new('RGB',(320,240),'#55aaff').save(self.art)
        self.app=App();self.errors=[]
        self.app.report_callback_exception=lambda *args:self.errors.append(args)
        self.pump(.5)
    def tearDown(self):
        self.app.close();self.tmp.cleanup()
    def pump(self,seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:self.app.update();time.sleep(.008)
    def until(self,condition,timeout=8):
        end=time.monotonic()+timeout
        while not condition() and time.monotonic()<end:self.pump(.03)
        self.assertTrue(condition(),'UI did not finish within the timeout')
    def shell_drop(self,path):
        if sys.platform!='win32':self.app.receive_drop([str(path)]);return
        from ctypes import wintypes as w
        self.assertIsNotNone(self.app._drops,'Native drop registration failed')
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GlobalAlloc.argtypes=[w.UINT,ctypes.c_size_t];kernel.GlobalAlloc.restype=w.HGLOBAL
        kernel.GlobalLock.argtypes=[w.HGLOBAL];kernel.GlobalLock.restype=ctypes.c_void_p
        kernel.GlobalUnlock.argtypes=[w.HGLOBAL]
        payload=struct.pack('<IiiII',20,0,0,0,1)+(str(path)+'\0\0').encode('utf-16le')
        handle=kernel.GlobalAlloc(0x42,len(payload));pointer=kernel.GlobalLock(handle)
        ctypes.memmove(pointer,payload,len(payload));kernel.GlobalUnlock(handle)
        user=ctypes.WinDLL('user32');user.SendMessageW.argtypes=[w.HWND,w.UINT,w.WPARAM,w.LPARAM]
        user.SendMessageW.restype=ctypes.c_ssize_t
        user.SendMessageW(self.app._drops.hwnd,0x233,handle,0)
    def test_drop_build_artwork_and_controls(self):
        app=self.app;self.shell_drop(self.game);self.until(lambda:len(app.snapshots)==2 and not app.scanning)
        self.assertEqual(app.title_id_text.get(),'0400111122220000')
        self.assertEqual(app.version_text.get(),'dump-131072')
        app.combo.current(1);app.select_snapshot();self.assertEqual(app.version_text.get(),'dump-65536')
        self.shell_drop(self.art);self.pump(.35);self.assertEqual(app.art_path,self.art)
        app.clear_art_btn.invoke();self.assertIsNone(app.art_path)
        app.set_art(self.art);app.title_text.set('Sample Custom Title');app.version_text.set('1.2')
        app.verify_check.invoke();self.assertFalse(app.verify.get())
        app.verify_check.invoke();self.assertTrue(app.verify.get())
        out=self.root/'Built.xci';app.output.set(str(out));app.build_btn.invoke()
        self.assertTrue(app.busy);self.assertFalse(app.browse.enabled);self.assertTrue(app.cancel_btn.enabled)
        self.until(lambda:not app.busy,timeout=10)
        self.assertTrue(out.is_file());self.assertTrue(app.open_btn.enabled)
        report=json.loads(out.with_suffix('.xci.report.json').read_text())
        self.assertTrue(report['verified']);self.assertEqual(report['title'],'Sample Custom Title')
        app.notes();self.pump(.06)
        self.assertTrue(any(w.winfo_class()=='Toplevel' for w in app.winfo_children()))
        self.assertFalse(self.errors)
    def test_motion_and_minimum_layout(self):
        app=self.app;app.motion.enabled=True
        values=[];app.motion.to('test',0,1,.18,values.append);self.pump(.08)
        self.assertTrue(any(0<v<1 for v in values));self.pump(.18);self.assertAlmostEqual(values[-1],1)
        app.geometry('1010x780');self.pump(.1)
        for widget in (app.verify_check,app.folder_entry,app.combo,app.format_combo,app.version_entry,app.clear_art_btn,app.crop_art_btn,app.paste_art_btn,app.build_btn,app.help_btn):
            self.assertTrue(widget.winfo_ismapped(),str(widget))
            self.assertLessEqual(widget.winfo_rooty()+widget.winfo_height(),app.winfo_rooty()+app.winfo_height())
            self.assertLessEqual(widget.winfo_rooty()+widget.winfo_height(),app.content_area.winfo_rooty()+app.content_area.winfo_height()) if widget not in (app.build_btn,app.help_btn) else None
        app.motion.enabled=False;values=[]
        app.motion.to('static',0,1,.3,values.append);self.assertEqual(values,[1])
        self.assertFalse(self.errors)

    def test_format_selection_path_and_nsp_build(self):
        app=self.app;app.output_format.set('NSP')
        self.shell_drop(self.game);self.until(lambda:len(app.snapshots)==2 and not app.scanning)
        self.assertTrue(app.output.get().endswith('.nsp'))
        out=self.root/'Custom destination.nsp';app.output.set(str(out))
        app.format_combo.current(0);app.format_combo.entry.event_generate('<<ComboboxSelected>>');self.pump(.04)
        self.assertEqual(app.output.get(),str(out.with_suffix('.xci')))
        app.format_combo.current(1);app.format_combo.entry.event_generate('<<ComboboxSelected>>');self.pump(.04)
        self.assertEqual(app.output.get(),str(out));self.assertEqual(app.build_btn.text,'Build NSP')
        app.set_art(self.art);app.build_btn.invoke()
        self.assertEqual(str(app.format_combo.entry.cget('state')),'disabled')
        self.until(lambda:not app.busy,timeout=10)
        self.assertTrue(out.is_file());self.assertEqual(app.status.get(),'NSP ready')
        self.assertEqual(str(app.format_combo.entry.cget('state')),'readonly')
        report=json.loads(out.with_suffix('.nsp.report.json').read_text())
        self.assertEqual(report['output_format'],'NSP');self.assertTrue(report['verified'])
        self.assertFalse(self.errors)

    def test_crop_dialog_and_clipboard(self):
        app=self.app
        with patch('app.ImageGrab.grabclipboard',return_value=Image.new('RGB',(600,300),'#ffaa55')):
            self.assertTrue(app.paste_art())
        self.assertTrue(app.crop_art_btn.enabled);clipboard_path=app.art_path
        self.assertTrue(clipboard_path.is_file())
        dialog=CropDialog(app,app.art_selection);self.pump(.13)
        dialog.model.set_zoom(2);dialog.model.pan(80,0);dialog.schedule_render();self.pump(.08)
        selected=dialog.current_selection();dialog.apply();self.pump(.05)
        self.assertEqual(dialog.result,selected)
        with patch('app.CropDialog') as factory:
            factory.return_value.show.return_value=selected;app.crop_art()
        self.assertEqual(app.art_selection,selected)
        with patch('app.CropDialog') as factory:
            factory.return_value.show.return_value=None;app.crop_art()
        self.assertEqual(app.art_selection,selected)
        with patch('app.ImageGrab.grabclipboard',return_value=[str(self.art)]):
            self.assertTrue(app.paste_art());self.assertEqual(app.art_path,self.art)
        app.folder_entry.entry.focus_force();self.pump(.02)
        with patch('app.ImageGrab.grabclipboard',return_value=None):
            self.assertIsNone(app.paste_art_shortcut())
        self.assertFalse(self.errors)

    def test_explicit_emulator_setup_from_notes(self):
        import compatibility
        app=self.app;app.notes();self.pump(.05)
        notes=next(w for w in app.winfo_children() if w.winfo_class()=='Toplevel')
        setup=next(w for w in notes.winfo_children() if w.winfo_class()=='TButton' and w.cget('text')=='Set up emulator keys folder…')
        folder=self.root/'emulator-keys'
        with patch('app.filedialog.askdirectory',return_value=str(folder)),patch('app.messagebox.showinfo') as info:
            setup.invoke()
        self.assertTrue(compatibility.inspect(folder)['ready']);self.assertTrue(info.called)
        before=(folder/'prod.keys_autogenerated').read_bytes()
        with patch('app.filedialog.askdirectory',return_value=''),patch('app.messagebox.showinfo') as info:
            setup.invoke()
        self.assertFalse(info.called);self.assertEqual((folder/'prod.keys_autogenerated').read_bytes(),before)
        self.assertFalse(self.errors)

if __name__=='__main__':unittest.main(verbosity=2)
