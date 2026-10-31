"""Startup compatibility caution; preferences stay local to this application."""
from pathlib import Path
import json, os, tempfile
import tkinter as tk
from ui import BG, PANEL, TEXT, MUTED, Button, Check, Motion, Panel

NOTICE_ID = 'experimental-12gib-v1'
CAUTION = (
    'Set your emulator to 12 GiB RAM before testing Switch 2 packages. '
    'Some PokeDinner/Eglantine builds can exit on boot with the default 4 GiB setting.\n\n'
    'A PokeDinner 2.0.0 boot without an external main.npdm was reported with 12 GiB selected. '
    'Other games and emulator builds may behave differently. '
    'This app does not change emulator memory settings.\n\n'
    'Verification checks package integrity, not successful booting, gameplay or performance.'
)

def default_preferences_path():
    return Path(os.environ.get('LOCALAPPDATA') or Path.home())/'Switch2GamePackager'/'preferences.json'

def read_preferences(path):
    try:
        value=json.loads(Path(path).read_text(encoding='utf-8'))
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError):return {}

def should_show(path):
    return read_preferences(path).get('dismissed_startup_notice') != NOTICE_ID

def remember_dismissal(path):
    path=Path(path);data=read_preferences(path);data['dismissed_startup_notice']=NOTICE_ID
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',prefix='.preferences-',suffix='.tmp',dir=path.parent,delete=False) as f:
        temporary=Path(f.name);json.dump(data,f,indent=2)
    try:os.replace(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()

class StartupNotice(tk.Toplevel):
    def __init__(self,parent,preferences_path):
        super().__init__(parent);self.withdraw();self.title('Caution · experimental software')
        self.configure(bg=BG);self.transient(parent);self.resizable(False,False)
        self.preferences_path=Path(preferences_path);self.motion=Motion(self)
        self.dont_show=tk.BooleanVar(self,value=False)
        header=tk.Frame(self,bg=BG);header.pack(fill='x',padx=26,pady=(24,16))
        tk.Label(header,text='CAUTION',bg=BG,fg='#ffc36a',font=('Segoe UI Semibold',10)).pack(anchor='w')
        tk.Label(header,text='Experimental software',bg=BG,fg=TEXT,font=('Segoe UI Semibold',21)).pack(anchor='w',pady=(5,0))
        card=Panel(self,width=526,height=275);card.pack(fill='x',padx=22)
        tk.Label(card.inner,text='Emulator memory: 12 GiB',bg=PANEL,fg=TEXT,font=('Segoe UI Semibold',12)).pack(anchor='w',pady=(0,9))
        tk.Label(card.inner,text=CAUTION,bg=PANEL,fg=MUTED,font=('Segoe UI',10),wraplength=490,justify='left').pack(anchor='w')
        tk.Label(self,text='Use only content you are authorized to use. Piracy is not supported.\n'
                 'Nintendo and game content remain the property of their respective rights holders.\n'
                 'This independent project is not affiliated with or endorsed by Nintendo.',
                 bg=BG,fg=MUTED,font=('Segoe UI',9),wraplength=520,justify='left').pack(anchor='w',padx=26,pady=(14,10))
        footer=tk.Frame(self,bg=BG);footer.pack(fill='x',padx=24,pady=(8,22))
        self.dismiss_check=Check(footer,"Don't show this again",self.dont_show);self.dismiss_check.pack(side='left')
        self.continue_button=Button(footer,'Got it',self.close,self.motion,width=115,primary=True);self.continue_button.pack(side='right')
        self.protocol('WM_DELETE_WINDOW',self.close);self.bind('<Escape>',lambda event:self.close())
        self.bind('<Return>',lambda event:self.close())
        self.update_idletasks();card.configure(height=card.inner.winfo_reqheight()+28)
        self.update_idletasks();width=570;height=self.winfo_reqheight()
        x=max(0,parent.winfo_rootx()+(parent.winfo_width()-width)//2)
        y=max(0,parent.winfo_rooty()+(parent.winfo_height()-height)//2)
        self.geometry(f'{width}x{height}+{x}+{y}');self.deiconify();self.grab_set();self.continue_button.focus_set()

    def close(self):
        if self.dont_show.get():
            try:remember_dismissal(self.preferences_path)
            except OSError:pass  # Failure leaves the caution enabled next time.
        self.motion.stop()
        try:self.grab_release()
        except tk.TclError:pass
        self.destroy()
