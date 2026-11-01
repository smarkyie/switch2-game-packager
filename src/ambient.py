"""Quiet, bounded-cost ambient light behind the native Tk interface."""
import math
import time
import weakref
import tkinter as tk
from PIL import Image, ImageOps, ImageTk

BASE = '#0e1726'


class AmbientBackground:
    """One low-resolution light field shared by the background surfaces.

    Controls keep their native windows, focus and input behavior. The light is
    sampled behind them, so rounded corners blend into the same background.
    Foreground motion runs independently at 60 Hz; this slow field needs 12 Hz.
    """
    def __init__(self, root, motion):
        self.root = root
        self.motion = motion
        self.targets = weakref.WeakSet()
        self.started = time.perf_counter()
        self.job = None
        self.closed = False
        self.frame = None
        self.photo = None
        self.frame_count = 0
        self.canvas = tk.Canvas(root, bg=BASE, bd=0, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.tk.call('lower', self.canvas._w)
        radial = ImageOps.invert(Image.radial_gradient('L'))
        self.mask = radial.point([round((x/255)**2 * 115) for x in range(256)])
        self.mask = self.mask.resize((200, 158), Image.Resampling.BILINEAR)
        self.colors = ('#204a79', '#303463')
        self.job = root.after(20, self.tick)

    def register(self, widget):
        self.targets.add(widget)
        widget.bind('<Configure>', lambda event: self.paint(widget), add='+')
        self.paint(widget)

    def paint(self, widget):
        if self.closed or self.frame is None or not widget.winfo_exists():
            return
        width, height = widget.winfo_width(), widget.winfo_height()
        if width < 2 or height < 2:
            return
        x = widget.winfo_rootx() - self.root.winfo_rootx()
        y = widget.winfo_rooty() - self.root.winfo_rooty()
        # Every canvas references ONE Tk image at a different offset. Native
        # clipping handles the viewport; never copy a full image per control.
        found = widget.find_withtag('ambient')
        geometry=(x,y,str(self.photo))
        if found and getattr(widget,'_ambient_geometry',None)==geometry:return
        if found:
            widget.itemconfigure(found[0], image=self.photo)
            widget.coords(found[0],-x,-y)
        else:
            widget.create_image(-x, -y, anchor='nw', image=self.photo, tags='ambient')
        widget._ambient_geometry=geometry
        widget.tag_lower('ambient')

    def tick(self):
        self.job = None
        if self.closed:
            return
        visible = self.root.state() not in ('iconic', 'withdrawn')
        width, height = self.root.winfo_width(), self.root.winfo_height()
        needs_size = self.frame is None or self.frame.size != (width, height)
        moving = self.motion.enabled and visible
        if visible and (moving or needs_size):
            t = (time.perf_counter()-self.started) / 24 if self.motion.enabled else 0
            field = Image.new('RGB', (160, 120), BASE)
            positions = ((-78+22*math.sin(t), -80+15*math.cos(t*.7)),
                         (45+22*math.cos(t*.8), 20+18*math.sin(t*.6)))
            for color, (x, y) in zip(self.colors, positions):
                layer = Image.new('RGB', self.mask.size, color)
                field.paste(layer, (round(x), round(y)), self.mask)
            self.frame = field.resize((max(1,width), max(1,height)), Image.Resampling.BILINEAR)
            if self.photo is None or self.photo.width()!=width or self.photo.height()!=height:
                self.photo=ImageTk.PhotoImage(self.frame,master=self.canvas)
            else:
                self.photo.paste(self.frame)
            self.frame_count += 1
            # The root-sized canvas and small exposed control backgrounds use
            # the same image; panels are opaque and never repainted by this loop.
            self.paint(self.canvas)
            for widget in tuple(self.targets):
                try:
                    if widget.winfo_ismapped():
                        self.paint(widget)
                except tk.TclError:
                    self.targets.discard(widget)
        slow = (getattr(self.root, 'busy', False) or getattr(self.root, 'scanning', False)
                or getattr(getattr(self.root, 'dlc_panel', None), 'busy', False))
        self.job = self.root.after(250 if slow or not visible or not self.motion.enabled else 83, self.tick)

    def stop(self):
        self.closed = True
        if self.job is not None:
            self.root.after_cancel(self.job)
            self.job = None
        self.targets.clear()


class AmbientFrame(tk.Canvas):
    """A frame-like geometry container whose background samples ambient light."""
    def __init__(self, parent, **kw):
        kw.setdefault('bg', BASE)
        kw.setdefault('width', 1)
        kw.setdefault('height', 1)
        kw.setdefault('bd', 0)
        kw.setdefault('highlightthickness', 0)
        super().__init__(parent, **kw)
        backdrop = getattr(self.winfo_toplevel(), '_ambient', None)
        if backdrop is not None:
            backdrop.register(self)


class AmbientLabel(AmbientFrame):
    """Canvas text keeps the light continuous behind header/footer captions."""
    def __init__(self, parent, text='', textvariable=None, fg='#edf4ff',
                 font=None, anchor='w', justify='left', wraplength=0, **kw):
        super().__init__(parent, **kw)
        self.variable = textvariable
        self.text = text or ''
        self.wraplength = wraplength
        self.text_item = self.create_text(0,0,anchor='nw',fill=fg,font=font,
                                         justify=justify,text=self.text,width=wraplength)
        self.trace = textvariable.trace_add('write', self.refresh) if textvariable is not None else None
        self.bind('<Destroy>', self.cleanup, add='+')
        self.refresh()

    def refresh(self, *args):
        if not self.winfo_exists():return
        text=self.variable.get() if self.variable is not None else self.text
        self.itemconfigure(self.text_item,text=text,width=self.wraplength)
        box=self.bbox(self.text_item)
        if box:
            super().configure(width=max(1,box[2]-box[0]+2),height=max(1,box[3]-box[1]))

    def configure(self, cnf=None, **kw):
        refresh=False
        if 'wraplength' in kw:self.wraplength=kw.pop('wraplength');refresh=True
        if 'text' in kw:self.text=kw.pop('text');refresh=True
        if 'fg' in kw:self.itemconfigure(self.text_item,fill=kw.pop('fg'))
        if cnf or kw:super().configure(cnf,**kw)
        if refresh and hasattr(self,'text_item'):self.refresh()
    config=configure

    def cleanup(self, event):
        if event.widget is self and self.trace is not None:
            self.variable.trace_remove('write',self.trace)
            self.trace=None
