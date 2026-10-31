"""Portable Windows GUI for rebuilding complete extracted game snapshots."""
from pathlib import Path
import argparse, ctypes, io, json, os, queue, re, sys, threading, time, traceback, tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageOps, ImageTk, ImageGrab
import engine
import compatibility
from artwork import ArtworkSelection, ARTWORK_FILETYPES, IMAGE_EXTENSIONS
from crop_dialog import CropDialog
from ui import Layout, BG, PANEL, FIELD, TEXT, MUTED, ACCENT, BORDER

class App(Layout,tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Switch 2 Game Packager');self.configure(bg=BG)
        self.geometry('1020x800');self.minsize(950,760)
        self.events=queue.Queue();self.cancel_event=threading.Event();self.busy=False;self.scanning=False
        self.snapshots=[];self.art_path=None;self.art_selection=None;self.last_output=None;self.last_progress=0
        self._clipboard_temp=None;self._art_editor=None
        self.folder=tk.StringVar();self.snapshot_label=tk.StringVar();self.title_text=tk.StringVar()
        self.version_text=tk.StringVar(value='Snapshot');self.output=tk.StringVar();self.id_text=tk.StringVar(value='Choose a game folder to detect the title ID.')
        self.output_format=tk.StringVar(value='XCI')
        self.verify=tk.BooleanVar(value=True);self.status=tk.StringVar(value='Ready')
        self.detail=tk.StringVar(value='Select a game folder to begin.')
        self.style();self.layout();self.protocol('WM_DELETE_WINDOW',self.close);self._poll_job=self.after(100,self.poll)
        self.output_format.trace_add('write',self.format_changed)
        self.bind_all('<Control-v>',self.paste_art_shortcut,add='+')
        self.bind_all('<Control-V>',self.paste_art_shortcut,add='+')

    def pick_folder(self):
        value=filedialog.askdirectory(title='Select main game dump folder',parent=self)
        if value:self.folder.set(value);self.scan()

    def scan(self):
        if self.busy or self.scanning:return
        self.scanning=True;self.folder_entry.configure(state='disabled')
        self.snapshots=[];self.combo['values']=();self.snapshot_label.set('');self.id_text.set('Scanning folder…');self.refresh_details()
        self.status.set('Finding complete snapshots');self.browse.configure(state='disabled');self.build_btn.configure(state='disabled')
        value=self.folder.get().strip()
        def worker():
            try:self.events.put(('scan',engine.find_snapshots(value)))
            except Exception as e:self.events.put(('scan_error',str(e)))
        threading.Thread(target=worker,daemon=True).start()

    def select_snapshot(self):
        i=self.combo.current()
        if not 0<=i<len(self.snapshots):return
        s=self.snapshots[i];self.title_text.set(s.title)
        self.id_text.set(f'Title ID  {s.title_id:016X}   ·   Snapshot version  {s.version}');self.refresh_details()
        if s.nacp:
            v=s.nacp.read_bytes()[0x3060:0x3070].split(b'\0')[0].decode('utf-8','replace')
        else:v='dump-'+str(s.version) if s.version else 'Snapshot'
        self.version_text.set(v)
        name=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',s.title).rstrip('. ')[:110]
        destination=s.root.parent/'Packed'/f'{name} [{s.title_id:016X}] [{s.version}]'
        self.output.set(str(destination/(f'{name} [{s.title_id:016X}].{self.output_format.get().lower()}')))

    def format_changed(self,*args):
        kind=self.output_format.get()
        if self.output.get().strip():
            self.output.set(str(Path(self.output.get()).with_suffix('.'+kind.lower())))
        self.build_btn.configure(text='Build '+kind)

    def pick_output(self):
        current=Path(self.output.get()) if self.output.get() else None
        kind=self.output_format.get();ext='.'+kind.lower()
        value=filedialog.asksaveasfilename(parent=self,title='Save rebuilt '+kind,defaultextension=ext,
            filetypes=[(kind+' package','*'+ext)],initialdir=str(current.parent) if current else None,
            initialfile=current.name if current else 'Game'+ext,confirmoverwrite=False)
        if value:self.output.set(value)

    def pick_art(self):
        if self.busy:return
        value=filedialog.askopenfilename(parent=self,title='Choose artwork',filetypes=ARTWORK_FILETYPES)
        if value:self.set_art(Path(value))

    def set_art(self,path):
        try:
            selection=ArtworkSelection(Path(path))
            data=engine.artwork_bytes(selection)
            with Image.open(io.BytesIO(data)) as image:self.preview.set_picture(image)
            self.art_path=Path(path);self.art_selection=selection;self.refresh_art_name()
            self.crop_art_btn.configure(state='normal')
        except Exception as e:messagebox.showerror('Cannot read artwork',str(e),parent=self)

    def refresh_art_name(self):
        name=self.art_path.name if self.art_path else '256 × 256 square icon'
        self.art_name.set(name if len(name)<=34 else name[:31]+'…')

    def crop_art(self):
        if self.busy or not self.art_selection:return
        try:
            self._art_editor=CropDialog(self,self.art_selection)
            selection=self._art_editor.show()
            if selection is not None:
                data=engine.artwork_bytes(selection)
                with Image.open(io.BytesIO(data)) as image:self.preview.set_picture(image)
                self.art_selection=selection
        except Exception as e:messagebox.showerror('Cannot crop artwork',str(e),parent=self)
        finally:self._art_editor=None

    def paste_art_shortcut(self,event=None):
        return 'break' if self.paste_art(quiet=True) else None

    def paste_art(self,quiet=False):
        if self.busy or self._art_editor is not None:return False
        try:
            value=ImageGrab.grabclipboard()
            if isinstance(value,Image.Image):
                if self._clipboard_temp is None:self._clipboard_temp=tempfile.TemporaryDirectory(prefix='xci-artwork-')
                path=Path(self._clipboard_temp.name)/('Clipboard-'+str(time.time_ns())+'.png')
                value.save(path,format='PNG');self.set_art(path);return True
            if isinstance(value,list):
                paths=[Path(p) for p in value if Path(p).suffix.lower() in IMAGE_EXTENSIONS and Path(p).is_file()]
                if paths:self.set_art(paths[0]);return True
            focus=self.focus_get()
            # Let native text editors receive ordinary text/path pastes.
            if quiet and isinstance(focus,(tk.Entry,ttk.Entry,ttk.Combobox)):return False
            try:text=self.clipboard_get().strip().strip('"')
            except tk.TclError:text=''
            if text and '\n' not in text:
                path=Path(text)
                if path.suffix.lower() in IMAGE_EXTENSIONS and path.is_file():self.set_art(path);return True
        except (OSError,ValueError,tk.TclError) as e:
            if not quiet:messagebox.showerror('Cannot paste artwork',str(e),parent=self)
            return False
        if not quiet:messagebox.showinfo('Paste artwork','Copy an image or artwork file, then click Paste or press Ctrl+V.',parent=self)
        return False

    def clear_art(self):
        self.art_path=None;self.art_selection=None;self.preview.set_picture(None)
        self.art_name.set('256 × 256 square icon');self.crop_art_btn.configure(state='disabled')

    def set_busy(self,value):
        self.busy=value
        for w in (self.browse,self.folder_entry,self.name_entry,self.version_entry,self.out_entry,self.save_btn,self.art_btn,self.paste_art_btn,self.clear_art_btn,self.verify_check,self.build_btn):
            w.configure(state='disabled' if value else 'normal')
        self.combo.configure(state='disabled' if value else 'readonly')
        self.format_combo.configure(state='disabled' if value else 'readonly')
        self.crop_art_btn.configure(state='normal' if self.art_selection and not value else 'disabled')
        self.cancel_btn.configure(state='normal' if value else 'disabled')

    def start(self):
        if self.busy:return
        i=self.combo.current()
        if not 0<=i<len(self.snapshots):messagebox.showinfo('Choose a game','Select a game folder first.',parent=self);return
        if not self.output.get().strip():self.pick_output();return
        options=(self.snapshots[i],Path(self.output.get()),self.title_text.get().strip(),self.version_text.get().strip(),self.art_selection or self.art_path,self.verify.get())
        output_format=self.output_format.get()
        self.set_busy(True);self.cancel_event.clear();self.last_progress=0;self.progressbar['value']=0
        self.status.set('Preparing build');self.detail.set('Your original dump stays untouched.');self.open_btn.configure(state='disabled')
        def worker():
            last=[0]
            def notify(stage,value):
                now=time.monotonic()
                if now-last[0]>.12 or value>=100:
                    self.events.put(('progress',(stage,value)));last[0]=now
            try:self.events.put(('done',engine.build(*options,notify=notify,cancel=self.cancel_event,output_format=output_format)))
            except InterruptedError:self.events.put(('cancelled',None))
            except Exception as e:self.events.put(('error',(str(e),traceback.format_exc())))
        threading.Thread(target=worker,daemon=True).start()

    def cancel(self):
        self.cancel_event.set();self.cancel_btn.configure(state='disabled');self.status.set('Cancelling…')
        self.detail.set('Finishing the current read and removing the unfinished image.')

    def poll(self):
        try:
            while True:
                kind,data=self.events.get_nowait()
                if kind=='scan':
                    self.scanning=False;self.folder_entry.configure(state='normal')
                    self.snapshots,skipped=data
                    self.combo['values']=[s.label for s in self.snapshots];self.combo.current(0);self.select_snapshot()
                    self.status.set('Ready');self.detail.set(f'{len(self.snapshots)} snapshot(s) found.'+(' Separate DLC folders will be left out.' if skipped else ''))
                    self.browse.configure(state='normal');self.build_btn.configure(state='normal')
                elif kind=='scan_error':
                    self.scanning=False;self.folder_entry.configure(state='normal')
                    self.browse.configure(state='normal');self.build_btn.configure(state='normal');self.id_text.set('No complete snapshot found.');self.refresh_details()
                    self.status.set('Choose a supported dump');self.detail.set(data)
                elif kind=='progress':
                    stage,value=data;self.last_progress=max(self.last_progress,value);self.progressbar['value']=self.last_progress
                    if not self.cancel_event.is_set():self.status.set(stage)
                    self.detail.set(f'{self.last_progress:.0f}% complete · originals untouched')
                elif kind=='done':
                    self.set_busy(False);self.progressbar['value']=100;self.status.set(data['output_format']+' ready')
                    self.last_output=Path(self.output.get());self.open_btn.configure(state='normal')
                    self.detail.set(f'{data["size"]/1e9:.2f} GB · '+('verification passed' if data['verified'] else 'verification skipped')+
                        (' · keep main.npdm beside it' if data.get('switch2_companion') else ''))
                elif kind=='cancelled':
                    self.set_busy(False);self.status.set('Build cancelled');self.detail.set('Unfinished image removed. Your originals are unchanged.')
                elif kind=='error':
                    self.set_busy(False);self.status.set('Build could not finish');self.detail.set(data[0])
                    messagebox.showerror('Packaging failed',data[0],parent=self)
        except queue.Empty:pass
        self._poll_job=self.after(100,self.poll)

    def open_output(self):
        if self.last_output:os.startfile(str(self.last_output.parent))

    def notes(self):
        w=tk.Toplevel(self);w.title('Notes & compatibility');w.geometry('650x650');w.configure(bg=BG)
        ttk.Label(w,text='Before sharing or packaging',style='Section.TLabel').pack(anchor='w',padx=24,pady=(22,12))
        text=('Select a complete decrypted game snapshot: sibling exefs and romfs folders. You may also select a main folder containing base and updates subfolders, then choose a snapshot.\n\n'
              'An update folder must contain a complete mounted filesystem, not only changed files. The app cannot determine completeness from file names. Separate updates, DLC and multi-program titles are not combined automatically.\n\n'
              'Choose XCI or NSP in Output. Both are unsigned plaintext emulator packages, written directly without an intermediate container. Packaging cannot add emulator support for a game. Original control metadata is preserved when present; otherwise basic metadata is generated.\n\n'
              'Keep the generated main.npdm beside the XCI/NSP in its own game folder. The checked PokeDinner loader needs it to select Switch 2 memory and clock settings.\n\n'
              'For missing-key errors, close the emulator and use Set up emulator keys folder below. It adds only missing local placeholders, preserves existing entries and prod.keys, and backs up an existing autogenerated file. These are not Nintendo keys and cannot decrypt retail content. Setup is never automatic.\n\n'
              'See the included README, TECHNICAL_NOTES and source folder for the format, tests, limitations and build instructions.')
        ttk.Label(w,text=text,wraplength=595,justify='left').pack(padx=24,anchor='w')
        ttk.Button(w,text='Export plaintext compatibility file…',command=lambda:self.export_keys(w)).pack(anchor='w',padx=24,pady=18)
        ttk.Button(w,text='Set up emulator keys folder…',command=lambda:self.setup_compatibility(w)).pack(anchor='w',padx=24)

    def setup_compatibility(self,parent):
        folder=filedialog.askdirectory(parent=parent,title='Choose the emulator keys folder',
            initialdir=str(Path(os.environ.get('APPDATA',Path.home()))/'eden'/'keys'))
        if not folder:return
        try:
            result=compatibility.install(folder)
            text=('Added missing plaintext compatibility entries. Restart the emulator before opening a repack.'
                  if result['added'] else 'Required compatibility entries are already present.')
            if result['backup']:text+='\n\nAn exact backup of the previous autogenerated file was saved beside it.'
            messagebox.showinfo('Emulator compatibility',text+'\n\nExisting entries and prod.keys were preserved.',parent=parent)
        except Exception as e:messagebox.showerror('Compatibility setup could not finish',str(e),parent=parent)

    def export_keys(self,parent):
        path=filedialog.asksaveasfilename(parent=parent,title='Export local placeholder keys',initialfile='plaintext-repack.keys',defaultextension='.keys',filetypes=[('Key configuration','*.keys')])
        if path:
            try:
                with Path(path).open('x',encoding='utf-8') as f:f.write(engine.placeholder_keys())
                messagebox.showinfo('Exported','Saved local placeholders. See README for Eglantine setup. Existing files were not changed.',parent=parent)
            except Exception as e:messagebox.showerror('Export failed',str(e),parent=parent)

    def close(self):
        if self.busy:
            self.cancel();self.detail.set('Cancelling the build. Close the app again after cleanup finishes.');return
        if self._drops:self._drops.close()
        if self._poll_job:self.after_cancel(self._poll_job)
        self.motion.stop()
        self.destroy()
        if self._clipboard_temp:self._clipboard_temp.cleanup()

def cli(argv):
    parser=argparse.ArgumentParser(description='Package a complete extracted ExeFS/RomFS snapshot into XCI or NSP.')
    parser.add_argument('--package',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--artwork',type=Path);parser.add_argument('--title');parser.add_argument('--snapshot',type=int,default=0)
    parser.add_argument('--display-version');parser.add_argument('--skip-verification',action='store_true')
    parser.add_argument('--format',choices=('xci','nsp'),help='Output format; inferred from --output extension when omitted.')
    art_options=parser.add_mutually_exclusive_group()
    art_options.add_argument('--artwork-fit',action='store_true')
    art_options.add_argument('--artwork-crop',nargs=4,type=float,metavar=('LEFT','TOP','RIGHT','BOTTOM'))
    args=parser.parse_args(argv);snapshots,_=engine.find_snapshots(args.package)
    if not 0<=args.snapshot<len(snapshots):raise ValueError('Snapshot index is out of range.')
    s=snapshots[args.snapshot]
    if (args.artwork_fit or args.artwork_crop) and not args.artwork:raise ValueError('Choose --artwork before specifying its crop mode.')
    artwork=ArtworkSelection(args.artwork,tuple(args.artwork_crop) if args.artwork_crop else None,args.artwork_fit) if args.artwork else None
    result=engine.build(s,args.output,args.title or s.title,args.display_version or ('dump-'+str(s.version) if s.version else 'Snapshot'),artwork,not args.skip_verification,output_format=args.format)
    return result

def main():
    if '--package' in sys.argv:
        try:result=cli(sys.argv[1:]);print(json.dumps(result,indent=2));return 0
        except Exception as e:
            if sys.stderr:print(str(e),file=sys.stderr)
            # Windowed EXEs have no console; retain a diagnostic next to the requested output.
            try:
                args=sys.argv;dest=Path(args[args.index('--output')+1]);dest.with_suffix('.error.txt').write_text(traceback.format_exc(),encoding='utf-8')
            except Exception:pass
            return 1
    try:ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:pass
    app=App()
    if '--folder' in sys.argv:
        app.folder.set(sys.argv[sys.argv.index('--folder')+1]);app.after(150,app.scan)
    if '--artwork' in sys.argv:app.after(200,lambda:app.set_art(Path(sys.argv[sys.argv.index('--artwork')+1])))
    app.mainloop();return 0

if __name__=='__main__':sys.exit(main())
