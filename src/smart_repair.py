import os, sys, time, subprocess, threading, queue, tkinter as tk
from tkinter import filedialog, messagebox

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT=os.path.join(ROOT,'external')
WETOOL=os.path.join(EXT,'wetool.exe')
BWE=os.path.join(EXT,'BwE_PS4_NOR_Validator.exe')

try:
    import serial.tools.list_ports
except Exception:
    serial=None

# Windows-only keyboard control. Smart Repair sends only the native single-key commands
# requested by the user; it does not implement/fake WETOOL's hardware protocol.
if os.name == 'nt':
    import ctypes
    user32=ctypes.windll.user32
    VK_F=0x46; VK_R=0x52; VK_7=0x37; VK_Y=0x59
    KEYEVENTF_KEYUP=0x0002
    def send_key(vk):
        user32.keybd_event(vk,0,0,0); user32.keybd_event(vk,0,KEYEVENTF_KEYUP,0)
else:
    def send_key(vk): raise OSError('Windows required')

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('SMART REPAIR EDITION BY ALI GAMES'); self.geometry('1100x680'); self.configure(bg='#101010')
        self.q=queue.Queue(); self.wproc=None; self.bproc=None
        self.build(); self.after(100,self.pump); self.detect_com()
    def build(self):
        top=tk.Frame(self,bg='#171717'); top.pack(fill='x',padx=10,pady=10)
        tk.Label(top,text='SMART REPAIR',fg='#d7b35a',bg='#171717',font=('Segoe UI',20,'bold')).pack(side='left',padx=15,pady=12)
        tk.Label(top,text='EDITION BY ALI GAMES',fg='#ddd',bg='#171717').pack(side='left')
        bar=tk.Frame(self,bg='#101010'); bar.pack(fill='x',padx=15,pady=4)
        self.btn(bar,'SMART READ FULL NOR',self.start,True).pack(side='left')
        self.btn(bar,'OPEN WETOOL',self.open_wetool).pack(side='left',padx=6)
        self.btn(bar,'F',lambda:self.command('F')).pack(side='left',padx=2)
        self.btn(bar,'R',lambda:self.command('R')).pack(side='left',padx=2)
        self.btn(bar,'OPEN BwE',self.open_bwe).pack(side='left',padx=6)
        self.btn(bar,'No.7',lambda:self.command('7')).pack(side='left',padx=2)
        self.btn(bar,'Y',lambda:self.command('Y')).pack(side='left',padx=2)
        self.com=tk.StringVar(value='COM: scanning...')
        tk.Label(bar,textvariable=self.com,bg='#101010',fg='#bbb').pack(side='right',padx=10)
        body=tk.Frame(self,bg='#101010'); body.pack(fill='both',expand=True,padx=15,pady=10)
        self.log=tk.Text(body,bg='#050505',fg='#ddd',font=('Consolas',10),relief='flat'); self.log.pack(side='left',fill='both',expand=True)
        info=tk.Frame(body,bg='#181818',width=280); info.pack(side='right',fill='y',padx=(10,0)); info.pack_propagate(False)
        self.status=tk.StringVar(value='READY'); self.step=tk.StringVar(value='—')
        for title,var in [('STATUS',self.status),('STEP',self.step)]:
            f=tk.Frame(info,bg='#222'); f.pack(fill='x',padx=10,pady=10)
            tk.Label(f,text=title,bg='#222',fg='#d7b35a',font=('Segoe UI',9,'bold')).pack(anchor='w',padx=10,pady=7)
            tk.Label(f,textvariable=var,bg='#222',fg='white',wraplength=240,justify='left').pack(anchor='w',padx=10,pady=(0,10))
        tk.Label(self,text='Original PS4WETOOLS PRO',bg='#0b0b0b',fg='#aaa',anchor='w',padx=15,pady=8).pack(fill='x')
    def btn(self,p,text,cmd,primary=False):
        return tk.Button(p,text=text,command=cmd,bg='#292929' if not primary else '#3a3020',fg='#eee' if not primary else '#f0d27a',relief='flat',padx=10,pady=8,font=('Segoe UI',9,'bold'))
    def logx(self,s): self.q.put(('log',s))
    def setv(self,v,s): self.q.put(('v',v,s))
    def detect_com(self):
        if serial:
            ports=list(serial.tools.list_ports.comports())
            names=[p.device for p in ports]
            self.com.set('COM: '+(', '.join(names) if names else 'not detected'))
        else: self.com.set('COM: install pyserial / GitHub build includes it')
        self.after(1500,self.detect_com)
    def open_wetool(self):
        if not os.path.exists(WETOOL): return messagebox.showerror('WETOOL','external/wetool.exe tidak ditemukan')
        self.wproc=subprocess.Popen([WETOOL],cwd=EXT); self.logx('WETOOL dibuka. Smart Repair tidak menggantikan fungsi WETOOL.')
    def open_bwe(self):
        if not os.path.exists(BWE): return messagebox.showerror('BwE','external/BwE_PS4_NOR_Validator.exe tidak ditemukan')
        self.bproc=subprocess.Popen([BWE],cwd=EXT); self.logx('BwE Validator dibuka.')
    def command(self,c):
        if os.name!='nt': return
        try:
            key={'F':VK_F,'R':VK_R,'7':VK_7,'Y':VK_Y}[c]
            send_key(key); self.logx('Perintah native dikirim: '+c)
        except Exception as e: messagebox.showerror('Command',str(e))
    def start(self):
        if not messagebox.askyesno('SMART READ FULL NOR','Buka WETOOL dan mulai alur perintah?\n\nSetelah No.3/READ ALL dijalankan di WETOOL, Smart Repair akan menunggu konfirmasi Read Full selesai sebelum F → R → BwE → 7 → Y.'):
            return
        threading.Thread(target=self.run,daemon=True).start()
    def run(self):
        self.setv(self.status,'RUNNING'); self.setv(self.step,'No.3')
        self.open_wetool(); self.logx('SMART READ FULL NOR → No.3 → Deteksi COM/Teensy → SPIway/Juegos → READ ALL')
        self.logx('Catatan: Smart tidak mengarang READ ALL. READ ALL tetap dijalankan oleh WETOOL.')
        if not messagebox.askyesno('Read Full selesai?','Klik YES setelah WETOOL benar-benar menampilkan Read Full selesai.\nLalu Smart akan mengirim F → R dan membuka BwE.'):
            self.setv(self.status,'READY'); return
        self.setv(self.step,'F otomatis'); self.command('F'); time.sleep(.4)
        self.setv(self.step,'R = Rename Non-Canonical'); self.command('R'); time.sleep(.8)
        self.setv(self.step,'BwE'); self.open_bwe(); time.sleep(1.0)
        self.setv(self.step,'No.7'); self.command('7'); time.sleep(.4)
        self.setv(self.step,'Y'); self.command('Y'); self.setv(self.step,'Selesai'); self.setv(self.status,'READY')
        self.logx('Tahap 1 selesai: READ ALL → Read Full selesai → F → R (Rename Non-Canonical) → BwE → No.7 → Y')
    def pump(self):
        try:
            while True:
                x=self.q.get_nowait()
                if x[0]=='log': self.log.insert('end',x[1]+'\n'); self.log.see('end')
                else: x[1].set(x[2])
        except queue.Empty: pass
        self.after(100,self.pump)

if __name__=='__main__': App().mainloop()
