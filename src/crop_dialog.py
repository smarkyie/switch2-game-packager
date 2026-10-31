"""Interactive square crop, pan, zoom and full-image fitting."""
import io, tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
from artwork import ArtworkSelection, CropModel, encode_artwork, load_artwork
from ui import BG,PANEL,FIELD,TEXT,MUTED,ACCENT,Button,Motion

class ZoomSlider(tk.Canvas):
    def __init__(self,parent,variable,command):
        super().__init__(parent,bg=BG,height=30,width=240,highlightthickness=0,bd=0,takefocus=True,cursor='hand2')
        self.variable=variable;self.command=command
        variable.trace_add('write',lambda *a:self.draw())
        self.bind('<Configure>',lambda e:self.draw());self.bind('<Button-1>',self.position)
        self.bind('<B1-Motion>',self.position);self.bind('<Left>',lambda e:self.step(-.1));self.bind('<Right>',lambda e:self.step(.1))
    def position(self,event):
        self.focus_set();value=max(1,min(8,1+(event.x-10)/max(1,self.winfo_width()-20)*7))
        self.variable.set(value);self.command(value)
    def step(self,amount):
        value=max(1,min(8,self.variable.get()+amount));self.variable.set(value);self.command(value)
    def draw(self):
        w=max(21,self.winfo_width());h=30;s=3
        image=Image.new('RGBA',(w*s,h*s));d=ImageDraw.Draw(image)
        x=10+(w-20)*(self.variable.get()-1)/7
        d.rounded_rectangle((10*s,13*s,(w-10)*s,17*s),radius=2*s,fill='#344b68')
        d.rounded_rectangle((10*s,13*s,max(10.1,x)*s,17*s),radius=2*s,fill='#43aaff')
        d.ellipse(((x-8)*s,7*s,(x+8)*s,23*s),fill='#a8d7ff')
        self.photo=ImageTk.PhotoImage(image.resize((w,h),Image.Resampling.LANCZOS),master=self)
        self.delete('all');self.create_image(0,0,image=self.photo,anchor='nw')

class CropDialog(tk.Toplevel):
    def __init__(self,parent,selection):
        super().__init__(parent);self.withdraw();self.title('Crop artwork · 256 × 256')
        self.configure(bg=BG);self.geometry('800x610');self.minsize(740,560);self.transient(parent)
        self.selection=selection;self.image=load_artwork(selection.path);self.model=CropModel(*self.image.size,selection.box)
        self.preview_source=self.image.copy();self.preview_source.thumbnail((1600,1600),Image.Resampling.LANCZOS)
        self.fit=tk.BooleanVar(value=selection.fit);self.result=None;self.motion=Motion(self)
        self.zoom=tk.DoubleVar(value=self.model.zoom);self._drag=None;self._render_job=None
        header=tk.Frame(self,bg=BG);header.pack(fill='x',padx=23,pady=(20,13))
        tk.Label(header,text='Crop your icon',bg=BG,fg=TEXT,font=('Segoe UI Semibold',19)).pack(anchor='w')
        tk.Label(header,text='Drag to position · scroll to zoom · exported at 256 × 256',bg=BG,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',pady=(5,0))
        footer=tk.Frame(self,bg=BG);footer.pack(side='bottom',fill='x',padx=23,pady=(12,20))
        Button(footer,'Apply crop',self.apply,self.motion,width=140,primary=True).pack(side='right')
        Button(footer,'Cancel',self.close,self.motion,width=100).pack(side='right',padx=10)
        Button(footer,'Reset',self.reset,self.motion,width=95,quiet=True).pack(side='left')
        controls=tk.Frame(self,bg=BG);controls.pack(side='bottom',fill='x',padx=23,pady=8)
        tk.Label(controls,text='Zoom',bg=BG,fg=MUTED,font=('Segoe UI',10)).pack(side='left')
        ZoomSlider(controls,self.zoom,self.change_zoom).pack(side='left',fill='x',expand=True,padx=15)
        self.fit_control=ttk.Checkbutton(controls,text='Fit whole image',variable=self.fit,command=self.schedule_render);self.fit_control.pack(side='right')
        body=tk.Frame(self,bg=BG);body.pack(fill='both',expand=True,padx=23)
        aside=tk.Frame(body,bg=BG,width=190);aside.pack(side='right',fill='y',padx=(18,0));aside.pack_propagate(False)
        tk.Label(aside,text='ICON PREVIEW',bg=BG,fg=MUTED,font=('Segoe UI Semibold',9)).pack(anchor='w',pady=(10,13))
        self.thumbnail=tk.Label(aside,bg=FIELD,width=180,height=180);self.thumbnail.pack()
        tk.Label(aside,text='256 × 256 pixels\nJPEG icon inside the XCI',bg=BG,fg=MUTED,font=('Segoe UI',10),justify='left').pack(anchor='w',pady=15)
        self.canvas=tk.Canvas(body,bg=FIELD,bd=0,highlightthickness=0,cursor='fleur');self.canvas.pack(side='left',fill='both',expand=True)
        self.canvas.bind('<Configure>',lambda e:self.schedule_render());self.canvas.bind('<ButtonPress-1>',self.begin_drag)
        self.canvas.bind('<B1-Motion>',self.drag);self.canvas.bind('<ButtonRelease-1>',lambda e:setattr(self,'_drag',None))
        self.canvas.bind('<MouseWheel>',self.wheel)
        self.bind('<Escape>',lambda e:self.close());self.bind('<Return>',lambda e:self.apply())
        self.protocol('WM_DELETE_WINDOW',self.close);self.after(20,self.ready)
    def ready(self):self.deiconify();self.grab_set();self.focus_set();self.schedule_render()
    def show(self):self.wait_window();return self.result
    def current_selection(self):return ArtworkSelection(self.selection.path,self.model.box(),self.fit.get())
    def schedule_render(self):
        if self._render_job is None:self._render_job=self.after(16,self.render)
    def render(self):
        self._render_job=None;w=max(1,self.canvas.winfo_width());h=max(1,self.canvas.winfo_height())
        if w<10 or h<10:return
        square=max(50,min(w-42,h-42,360));self.display_scale=square/self.model.side
        if self.fit.get():
            scale=min(square/self.image.width,square/self.image.height)
            cx=self.image.width/2;cy=self.image.height/2
        else:scale=self.display_scale;cx=self.model.cx;cy=self.model.cy
        coeff=(1/scale,0,cx-w/(2*scale),0,1/scale,cy-h/(2*scale))
        canvas_image=self.image.transform((w,h),Image.Transform.AFFINE,coeff,resample=Image.Resampling.BICUBIC,fillcolor=(28,43,66,255))
        x=(w-square)/2;y=(h-square)/2
        shade=Image.new('RGBA',(w,h),(0,0,0,145));d=ImageDraw.Draw(shade);d.rectangle((x,y,x+square,y+square),fill=(0,0,0,0))
        canvas_image=Image.alpha_composite(canvas_image,shade)
        self.photo=ImageTk.PhotoImage(canvas_image,master=self);self.canvas.delete('all');self.canvas.create_image(0,0,anchor='nw',image=self.photo)
        self.canvas.create_rectangle(x,y,x+square,y+square,outline='#89c7ff',width=2)
        for fraction in (1/3,2/3):
            self.canvas.create_line(x+square*fraction,y,x+square*fraction,y+square,fill='#7290b3',dash=(3,5))
            self.canvas.create_line(x,y+square*fraction,x+square,y+square*fraction,fill='#7290b3',dash=(3,5))
        preview=encode_artwork(self.preview_source,self.current_selection())
        with Image.open(io.BytesIO(preview)) as image:self.preview_photo=ImageTk.PhotoImage(image.resize((180,180),Image.Resampling.LANCZOS),master=self)
        self.thumbnail.configure(image=self.preview_photo,width=180,height=180)
    def begin_drag(self,event):self._drag=(event.x,event.y)
    def drag(self,event):
        if self._drag is None or self.fit.get():return
        x,y=self._drag;self._drag=(event.x,event.y)
        self.model.pan(-(event.x-x)/self.display_scale,-(event.y-y)/self.display_scale);self.schedule_render()
    def change_zoom(self,value):
        self.fit.set(False);self.model.set_zoom(value);self.schedule_render()
    def wheel(self,event):
        self.fit.set(False);self.model.set_zoom(self.model.zoom*(1.12 if event.delta>0 else 1/1.12))
        self.zoom.set(self.model.zoom);self.schedule_render()
    def reset(self):
        self.model=CropModel(*self.image.size);self.zoom.set(1);self.fit.set(False);self.schedule_render()
    def apply(self):self.result=self.current_selection();self.close()
    def close(self):
        if self._render_job is not None:self.after_cancel(self._render_job)
        self.motion.stop()
        try:self.grab_release()
        except tk.TclError:pass
        self.destroy()
