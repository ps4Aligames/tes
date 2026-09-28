import os, sys, subprocess, hashlib, time, re
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path

APP_NAME = 'SMART REPAIR EDITION BY ALI GAMES'
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
LOGO = APP_DIR / 'assets' / 'ali_games_logo.png'

BG='#05080d'; PANEL='#0b1119'; GOLD='#f6c343'; TEXT='#e8eef7'; MUTED='#8fa1b5'
BLUE='#1488ff'; GREEN='#18c76a'; ORANGE='#ff9d19'; PURPLE='#9b38ff'; RED='#e52b35'

class App:
    def __init__(self, root):
        self.root=root
        root.title(APP_NAME); root.geometry('1500x900'); root.minsize(1200,720); root.configure(bg=BG)
        self.nor=None; self.syscon=None; self.active=0
        self.output_folder=None
        self.detected_com=None
        self.port_rows=[]
        self.scan_busy=False
        self.auto_scan_job=None
        self.busy_ops=0
        self.command_buttons=[]
        self.stop_requested=False
        self.stage1_ready=False
        self.build()
        self.log('SMART REPAIR EDITION BY ALI GAMES siap.','gold')
        self.log('Tahap 1 meniru alur WETOOL No. 3 secara internal — tidak membuka wetool.exe.','gold')
        self.log('Alur: Serial ports → pilih COM → SPIway/Juegos → READ ALL → hasil → BwE → Y lanjut.','gold')

    def build(self):
        header=tk.Frame(self.root,bg=BG); header.pack(fill='x',padx=14,pady=(10,5))
        left=tk.Frame(header,bg=BG); left.pack(side='left')
        if LOGO.exists():
            try:
                self.logo = tk.PhotoImage(file=str(LOGO))
                scale=max(1,(self.logo.width()+229)//230)
                if scale>1: self.logo=self.logo.subsample(scale,scale)
                tk.Label(left,image=self.logo,bg=BG).pack(side='left')
            except Exception: pass
        title=tk.Frame(header,bg=BG); title.pack(side='left',padx=20)
        tk.Label(title,text='SMART REPAIR EDITION',fg='#fff2b0',bg=BG,font=('Segoe UI',26,'bold')).pack(anchor='w')
        tk.Label(title,text='BY ALI GAMES',fg=GOLD,bg=BG,font=('Segoe UI',12,'bold')).pack(anchor='w')
        tk.Label(title,text='Original PS4WETOOLS PRO',fg='#dce5ee',bg=BG,font=('Segoe UI',10)).pack(anchor='w',pady=(3,0))
        status=tk.Frame(header,bg='#101821',highlightbackground=GOLD,highlightthickness=1); status.pack(side='right',padx=5)
        self.conn=tk.Label(status,text='● Device: Disconnected',fg='#ff5656',bg='#101821',font=('Segoe UI',10,'bold')); self.conn.pack(side='left',padx=15,pady=10)
        self.uart=tk.Label(status,text='● SPIway/Teensy: CHECK',fg='#ffcf42',bg='#101821',font=('Segoe UI',10,'bold')); self.uart.pack(side='left',padx=15,pady=10)

        self.stagebar=tk.Frame(self.root,bg=BG); self.stagebar.pack(fill='x',padx=14,pady=6)
        stages=[('1','SMART READ FULL NOR','No.3 → COM → READ ALL',BLUE,self.stage1),('2','WIRATE NOR FULL PS4','Load NOR → Verify',GREEN,self.stage2),('3','SMART PATCH WIRATE NOR','Load NOR → Patch → Wirate',ORANGE,self.stage3),('4','SMART SYSCON PATCH','Load & Patch Syscon',PURPLE,self.stage4),('5','SMART SYSCON REBUILD','Load → No.6 → No.4 → No.4',RED,self.stage5)]
        for num,name,sub,col,cmd in stages:
            b=tk.Button(self.stagebar,text=f'{num}\n{name}\n{sub}',command=cmd,bg='#111923',fg=TEXT,activebackground=col,activeforeground='white',font=('Segoe UI',10,'bold'),bd=0,relief='flat',height=3,highlightbackground=col,highlightthickness=2,cursor='hand2')
            b.pack(side='left',fill='x',expand=True,padx=4)
            self.command_buttons.append(b)

        loaders=tk.Frame(self.root,bg=BG); loaders.pack(fill='x',padx=14,pady=6)
        self.nor_btn=self.loader(loaders,'LOAD FILE NOR',self.load_nor); self.sys_btn=self.loader(loaders,'LOAD FILE SYSCON',self.load_syscon)

        output=tk.Frame(self.root,bg='#0b1119',highlightbackground=GOLD,highlightthickness=1); output.pack(fill='x',padx=14,pady=(0,6))
        tk.Label(output,text='OUTPUT HASIL NOR',fg=GOLD,bg='#0b1119',font=('Segoe UI',10,'bold')).pack(side='left',padx=(10,6),pady=7)
        self.output_var=tk.StringVar(value='Pilih folder hasil...')
        tk.Entry(output,textvariable=self.output_var,bg='#071019',fg='#cfe5ff',insertbackground='white',bd=0,font=('Consolas',9)).pack(side='left',fill='x',expand=True,padx=4,pady=6)
        tk.Button(output,text='PILIH FOLDER',command=self.choose_output_folder,bg='#151b22',fg='#ffe08a',activebackground='#272f38',font=('Segoe UI',9,'bold'),bd=0,highlightbackground=GOLD,highlightthickness=1).pack(side='left',padx=4,pady=4)
        tk.Button(output,text='CEK COM',command=lambda: self.scan_ports(auto_select=True, background=True),bg='#151b22',fg='#8fd8ff',activebackground='#272f38',font=('Segoe UI',9,'bold'),bd=0,highlightbackground=BLUE,highlightthickness=1).pack(side='left',padx=4,pady=4)
        tk.Button(output,text='BUKA FOLDER',command=self.open_output_folder,bg='#151b22',fg='#9ff3bd',activebackground='#272f38',font=('Segoe UI',9,'bold'),bd=0,highlightbackground=GREEN,highlightthickness=1).pack(side='left',padx=(4,8),pady=4)
        tk.Button(output,text='STOP PROSES',command=self.stop_all,bg='#151b22',fg='#ff8890',activebackground='#382025',font=('Segoe UI',9,'bold'),bd=0,highlightbackground=RED,highlightthickness=1).pack(side='left',padx=(0,8),pady=4)

        self.wetool3=tk.LabelFrame(self.root,text=' WETOOL No. 3  •  Serial ports → SPIway / Juegos ',fg=GOLD,bg=PANEL,font=('Segoe UI',10,'bold'),labelanchor='nw')
        self.wetool3.pack(fill='x',padx=14,pady=(0,6))
        row=tk.Frame(self.wetool3,bg=PANEL); row.pack(fill='x',padx=8,pady=6)
        self.w3_com=tk.Label(row,text='COM : --',fg=MUTED,bg=PANEL,font=('Consolas',10,'bold')); self.w3_com.pack(side='left',padx=6)
        self.w3_status=tk.Label(row,text='Serial ports : belum dicek',fg='#ffcf42',bg=PANEL,font=('Consolas',10,'bold')); self.w3_status.pack(side='left',padx=12)
        self.readall_btn=tk.Button(row,text='READ ALL',command=self.read_all_stage1,bg='#151b22',fg='#9ff3bd',activebackground='#24342b',font=('Segoe UI',10,'bold'),bd=0,highlightbackground=GREEN,highlightthickness=2,state='disabled',cursor='hand2'); self.readall_btn.pack(side='right',padx=4)
        tk.Button(row,text='PILIH COM',command=self.choose_com,bg='#151b22',fg='#8fd8ff',activebackground='#243342',font=('Segoe UI',10,'bold'),bd=0,highlightbackground=BLUE,highlightthickness=2).pack(side='right',padx=4)
        tk.Label(row,text='Output:',fg=MUTED,bg=PANEL,font=('Segoe UI',9)).pack(side='right',padx=(12,2))
        self.w3_out=tk.Label(row,text='Belum dipilih',fg='#cfe5ff',bg=PANEL,font=('Consolas',9)); self.w3_out.pack(side='right')

        self.portlist=tk.Text(self.wetool3,height=3,bg='#02060a',fg='#67d9ff',font=('Consolas',9),bd=0,padx=8,pady=5); self.portlist.pack(fill='x',padx=8,pady=(0,7)); self.portlist.insert('end','Serial ports\n  (Tekan CEK COM / PILIH COM)')
        self.portlist.config(state='disabled')

        body=tk.Frame(self.root,bg=BG); body.pack(fill='both',expand=True,padx=14,pady=5)
        main=tk.Frame(body,bg=BG); main.pack(side='left',fill='both',expand=True,padx=(0,6))
        side=tk.Frame(body,bg=BG,width=310); side.pack(side='right',fill='y')
        tk.Label(main,text='LOG AKTIVITAS',fg=GOLD,bg=PANEL,font=('Segoe UI',12,'bold'),anchor='w',padx=12).pack(fill='x')
        self.logbox=tk.Text(main,bg='#02060a',fg='#67d9ff',insertbackground='white',font=('Consolas',10),bd=0,padx=12,pady=10,wrap='none'); self.logbox.pack(fill='both',expand=True)
        self.logbox.tag_config('ok',foreground='#19e875'); self.logbox.tag_config('warn',foreground='#ffcf42'); self.logbox.tag_config('bad',foreground='#ff4c5b'); self.logbox.tag_config('gold',foreground=GOLD)
        cards={'nor_info':'INFORMASI NOR','sys_info':'INFORMASI SYSCON','bwe_info':'VALIDASI BwE','last_info':'AKTIVITAS TERAKHIR'}
        for attr,title in cards.items():
            f=tk.LabelFrame(side,text=' '+title+' ',fg=GOLD,bg=PANEL,font=('Segoe UI',10,'bold'),labelanchor='nw'); f.pack(fill='x',pady=4,ipady=8); setattr(self,attr,f)
        self.set_card(self.nor_info,'Belum ada NOR yang dimuat.'); self.set_card(self.sys_info,'Belum ada SYSCON yang dimuat.'); self.set_card(self.bwe_info,'Belum ada hasil validasi.'); self.set_card(self.last_info,'Belum ada aktivitas.')
        foot=tk.Frame(self.root,bg='#0b1016',highlightbackground=GOLD,highlightthickness=1); foot.pack(fill='x',padx=14,pady=(4,10))
        tk.Label(foot,text='SMART REPAIR EDITION  •  BY ALI GAMES',fg='#f7f0c4',bg='#0b1016',font=('Segoe UI',10,'bold')).pack(side='left',padx=15,pady=7)
        tk.Label(foot,text='Original PS4WETOOLS PRO',fg='#e1b94d',bg='#0b1016',font=('Segoe UI',9)).pack(side='right',padx=15)

    def loader(self,parent,label,cmd):
        f=tk.Frame(parent,bg='#111821',highlightbackground=GOLD,highlightthickness=1); f.pack(side='left',fill='x',expand=True,padx=4)
        tk.Button(f,text=label,command=cmd,bg='#111821',fg=TEXT,activebackground='#202a35',bd=0,font=('Segoe UI',10,'bold')).pack(side='left',padx=8,pady=8)
        var=tk.StringVar(value='Pilih file ...'); e=tk.Entry(f,textvariable=var,bg='#071019',fg='#cfe5ff',insertbackground='white',bd=0,font=('Consolas',9)); e.pack(side='left',fill='x',expand=True,padx=4,pady=6)
        return var
    def set_card(self,frame,text):
        for w in frame.winfo_children(): w.destroy()
        tk.Label(frame,text=text,fg='#cfe1f5',bg=PANEL,justify='left',anchor='w',font=('Consolas',9)).pack(fill='x',padx=8)
    def log(self,msg,tag=None):
        self.logbox.insert('end',f'[{time.strftime("%H:%M:%S")}] {msg}\n',tag); self.logbox.see('end')
    def last(self,s): self.set_card(self.last_info,s+'\n'+time.strftime('%Y-%m-%d %H:%M:%S'))

    def _set_commands_enabled(self, enabled):
        state = 'normal' if enabled else 'disabled'
        for b in self.command_buttons:
            try: b.config(state=state)
            except Exception: pass

    def _command(self, fn, label):
        if self.busy_ops:
            self.log(f'Perintah ditahan: {label} — proses lain masih berjalan.', 'warn')
            return
        self._bg(lambda: fn(), lambda r: self.log(f'{label} selesai.', 'ok'), f'{label} gagal', label)

    def _set_busy(self, busy, label=None):
        if busy:
            self.busy_ops += 1
            self.root.config(cursor='watch')
            self._set_commands_enabled(False)
            if label: self.last(label)
        else:
            self.busy_ops = max(0, self.busy_ops - 1)
            if self.busy_ops == 0:
                self.root.config(cursor='')
                self._set_commands_enabled(True)

    def _bg(self, work, done=None, error_title='Operation Error', label=None):
        import threading
        self.stop_requested=False
        self._set_busy(True, label)
        def worker():
            try:
                if self.stop_requested:
                    return
                result = work()
                if self.stop_requested:
                    return
                if done:
                    self.root.after(0, lambda: done(result))
            except Exception as exc:
                self.root.after(0, lambda e=exc: messagebox.showerror(error_title, str(e)))
            finally:
                self.root.after(0, lambda: self._set_busy(False))
        threading.Thread(target=worker, daemon=True).start()

    def stop_all(self):
        self.stop_requested=True
        self.log('STOP diminta. Operasi yang sedang berjalan akan berhenti pada titik aman berikutnya.', 'warn')
        self.last('STOP PROSES diminta')

    def load_nor(self):
        p=filedialog.askopenfilename(title='Pilih file NOR',filetypes=[('NOR files','*.*')])
        if not p:return
        def work():
            size=os.path.getsize(p)
            h=hashlib.md5()
            with open(p,'rb') as f:
                for chunk in iter(lambda:f.read(1024*1024),b''):
                    h.update(chunk)
            return size,h.hexdigest().upper()
        def done(result):
            size,md5=result; self.nor=p
            self.nor_btn.set(os.path.basename(p)); self.set_card(self.nor_info,f'Nama File : {os.path.basename(p)}\nUkuran    : {size:,} byte\nMD5       : {md5}\nStatus    : LOADED')
            self.log(f'NOR loaded: {p} | {size:,} byte','ok'); self.last('Load NOR selesai')
        self._bg(work,done,'Load NOR gagal','Load NOR sedang diproses...')

    def load_syscon(self):
        p=filedialog.askopenfilename(title='Pilih file SYSCON (512 KB)',filetypes=[('SYSCON files','*.*')])
        if not p:return
        def work():
            size=os.path.getsize(p); h=hashlib.md5()
            with open(p,'rb') as f:
                for chunk in iter(lambda:f.read(256*1024),b''):
                    h.update(chunk)
            return size,h.hexdigest().upper()
        def done(result):
            size,md5=result; self.syscon=p; self.sys_btn.set(os.path.basename(p)); good=size==512*1024
            self.log(f'SYSCON loaded: {p} | {size:,} byte','ok' if good else 'bad')
            self.set_card(self.sys_info,f'Nama File : {os.path.basename(p)}\nUkuran    : {size:,} byte\nMD5       : {md5}\nStatus    : {"VALID 512 KB" if good else "INVALID - HARUS 512 KB"}')
            self.last('Load SYSCON selesai')
        self._bg(work,done,'Load SYSCON gagal','Load SYSCON sedang diproses...')

    def need(self,kind):
        if kind=='nor' and not self.nor: messagebox.showwarning('NOR belum dipilih','Load file NOR terlebih dahulu.'); return False
        if kind=='sys' and not self.syscon: messagebox.showwarning('SYSCON belum dipilih','Load file SYSCON terlebih dahulu.'); return False
        return True

    def _scan_ports(self):
        ports=[]
        try:
            ps="Get-CimInstance Win32_SerialPort | Select-Object DeviceID,Caption | ConvertTo-Csv -NoTypeInformation"
            r=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True,timeout=6)
            lines=(r.stdout or '').splitlines()
            for line in lines[1:]:
                # CSV fields: DeviceID, Caption
                m=re.match(r'"?(COM\d+)"?,"?(.*?)"?$', line.strip())
                if m: ports.append((m.group(1),m.group(2).strip('"')))
        except Exception: pass
        # Fallback from mode command when WMI is unavailable.
        if not ports:
            try:
                r=subprocess.run(['cmd','/c','mode'],capture_output=True,text=True,timeout=5)
                for c in sorted(set(re.findall(r'COM\d+',r.stdout or '',re.I)),key=lambda x:int(re.search(r'\d+',x).group())):
                    ports.append((c,'Serial Port'))
            except Exception: pass
        ports=sorted({p[0].upper():p for p in ports}.values(), key=lambda x:int(re.search(r'\d+',x[0]).group()))
        return ports

    def _show_ports(self,ports):
        self.port_rows=ports
        self.portlist.config(state='normal'); self.portlist.delete('1.0','end')
        self.portlist.insert('end','Serial ports\n')
        if ports:
            for i,(com,caption) in enumerate(ports,1): self.portlist.insert('end',f'  {i}: {com} - {caption}\n')
        else: self.portlist.insert('end','  Tidak ada COM terdeteksi.\n')
        self.portlist.config(state='disabled')

    def _finish_scan(self, ports, auto_select=False):
        self.scan_busy=False
        self.port_rows=ports
        self._show_ports(ports)
        if ports:
            self.conn.config(text=f'● Serial: {len(ports)} port',fg=GREEN)
            self.uart.config(text='● SPIway/Teensy: AUTO-DETECT',fg='#ffcf42')
            self.w3_status.config(text=f'Serial ports : {len(ports)} terdeteksi',fg=GREEN)
            self.log('Serial ports terdeteksi otomatis:', 'ok')
            for i,(c,cap) in enumerate(ports,1): self.log(f'  {i}: {c} - {cap}', 'ok')
            # WETOOL-style behaviour: if exactly one port exists, select it automatically.
            if auto_select and len(ports)==1:
                self.set_com(ports[0][0], ports[0][1], auto=True)
            elif len(ports)>1:
                self.uart.config(text='● SPIway/Teensy: PILIH PORT',fg='#ffcf42')
                self.log('Lebih dari satu COM ditemukan — tidak mengunci COM tertentu.', 'warn')
            self.last('Serial ports terdeteksi')
            return ports
        self.conn.config(text='● Serial: Tidak ada',fg='#ff5656')
        self.uart.config(text='● SPIway/Teensy: NOT FOUND',fg='#ff5656')
        self.w3_status.config(text='Serial ports : TIDAK ADA',fg='#ff5656')
        self.log('Tidak ada COM terdeteksi.', 'bad')
        self.last('Tidak ada COM')
        return []

    def scan_ports(self, auto_select=False, background=False):
        if self.scan_busy:
            self.log('Pengecekan COM masih berjalan...', 'warn')
            return self.port_rows
        if not background:
            ports=self._scan_ports()
            return self._finish_scan(ports, auto_select=auto_select)
        import threading
        self.scan_busy=True
        self.conn.config(text='● Serial: SCANNING...',fg='#ffcf42')
        self.uart.config(text='● SPIway/Teensy: DETECTING...',fg='#ffcf42')
        self.w3_status.config(text='Serial ports : sedang dideteksi...',fg='#ffcf42')
        self.log('Mendeteksi COM otomatis — nomor COM tidak dipatok.', 'gold')
        def worker():
            ports=self._scan_ports()
            self.root.after(0, lambda: self._finish_scan(ports, auto_select=auto_select))
        threading.Thread(target=worker, daemon=True).start()
        return []

    def choose_com(self):
        ports=self.port_rows
        if not ports:
            self.log('Belum ada daftar COM — melakukan scan otomatis...', 'gold')
            self.scan_ports(auto_select=False, background=True)
            self.log('Setelah scan selesai, tekan PILIH COM lagi jika ditemukan beberapa port.', 'gold')
            return
        if len(ports)==1:
            self.set_com(ports[0][0],ports[0][1],auto=True); return
        win=tk.Toplevel(self.root); win.title('WETOOL No. 3 — Serial ports'); win.geometry('620x300'); win.configure(bg=PANEL); win.transient(self.root); win.grab_set()
        tk.Label(win,text='Serial ports',fg=GOLD,bg=PANEL,font=('Segoe UI',13,'bold')).pack(anchor='w',padx=18,pady=(15,6))
        lb=tk.Listbox(win,bg='#02060a',fg='#67d9ff',selectbackground='#1d5f8f',font=('Consolas',11),height=7,bd=0)
        lb.pack(fill='both',expand=True,padx=18,pady=6)
        for i,(com,caption) in enumerate(ports): lb.insert('end',f'{i+1}: {com} - {caption}')
        def select():
            sel=lb.curselection()
            if not sel:return
            self.set_com(ports[sel[0]][0],ports[sel[0]][1]); win.destroy()
        tk.Button(win,text='PILIH COM',command=select,bg='#151b22',fg='#9ff3bd',font=('Segoe UI',10,'bold'),bd=0,highlightbackground=GREEN,highlightthickness=2).pack(pady=12)
        lb.selection_set(0); lb.focus_set(); win.bind('<Return>',lambda e:select())

    def set_com(self,com,caption='',auto=False):
        self.detected_com=com.upper(); self.stage1_ready=True
        self.conn.config(text=f'● Serial: {self.detected_com}',fg=GREEN); self.uart.config(text=f'● SPIway/Teensy: {self.detected_com}',fg=GREEN)
        self.w3_com.config(text=f'COM : {self.detected_com}',fg=GREEN); self.w3_status.config(text='SPIway/Juegos : COM TERPILIH ✓',fg=GREEN); self.readall_btn.config(state='normal')
        mode='AUTO-DETECT' if auto else 'PILIH MANUAL'
        self.log(f'COM terdeteksi/dipilih: {self.detected_com} - {caption} [{mode}]','ok'); self.log('Masuk ke WETOOL No. 3 → SPIway / Juegos.','gold'); self.log('READ ALL berada di alur Smart Repair; wetool.exe tidak dibuka.','gold'); self.last(f'WETOOL No.3 — COM {self.detected_com}')

    def stage1(self):
        self.log('=== TAHAP 1: SMART READ FULL NOR ===','gold')
        self.log('Meniru alur WETOOL No. 3 secara internal. WETOOL EXE TIDAK dijalankan.','gold')
        self.stage1_ready=False; self.detected_com=None; self.readall_btn.config(state='disabled')
        self.scan_ports(auto_select=True, background=True)
        self.log('Jika hanya satu COM tersedia, COM tersebut dipilih otomatis. Jika beberapa COM tersedia, pilih yang sesuai.', 'gold')

    def choose_output_folder(self):
        d=filedialog.askdirectory(title='Pilih folder untuk menyimpan hasil NOR')
        if not d:return
        self.output_folder=Path(d); self.output_folder.mkdir(parents=True,exist_ok=True); self.output_var.set(str(self.output_folder)); self.w3_out.config(text=str(self.output_folder)); self.log(f'Folder output dipilih: {self.output_folder}','ok'); self.last('Pilih folder output NOR')
    def output_dir(self):
        if self.output_folder is None: self.choose_output_folder()
        if self.output_folder is None:return None
        self.output_folder.mkdir(parents=True,exist_ok=True); return self.output_folder
    def open_output_folder(self):
        d=self.output_dir()
        if d:
            try: os.startfile(str(d))
            except Exception as e: messagebox.showerror('Gagal membuka folder',str(e))

    def read_all_stage1(self):
        if not self.stage1_ready or not self.detected_com:
            self.log('READ ALL dibatalkan: pilih COM terlebih dahulu.','bad'); return
        out=self.output_dir()
        if out is None:return
        self.log('=== WETOOL No. 3 → SPIway / Juegos → READ ALL ===','gold')
        self.log(f'COM {self.detected_com} terpilih.','ok'); self.log(f'Output hasil: {out}','ok')
        self.log('SMART COMMAND → READ ALL (internal) dikirim ke tahap SPIway/Juegos.','gold')
        self.log('PERHATIAN: protokol SPIway READ ALL belum diketahui, jadi aplikasi tidak mengirim perintah tebakan dan tidak membuat NOR palsu.','warn')
        self.last('READ ALL — SIAP, PROTOKOL SPIWAY BELUM TERINTEGRASI')
        messagebox.showwarning('READ ALL belum dieksekusi','COM sudah dipilih dan alur No.3 → SPIway/Juegos → READ ALL sudah benar.\n\nPembacaan NOR nyata belum dijalankan karena protokol perintah SPIway/WETOOL belum tersedia. Tidak ada file NOR palsu yang dibuat.')

    def bwe_continue_prompt(self):
        ans=simpledialog.askstring('BwE selesai — lanjut?','Validasi BwE sudah selesai.\n\nKetik Y untuk melanjutkan proses Tahap 1, atau N untuk berhenti:',initialvalue='Y')
        if ans and ans.strip().upper()=='Y':
            self.log('BwE selesai → perintah Y diterima → lanjut.','ok'); self.last('BwE VALIDASI SELESAI — Y LANJUT')
            return True
        self.log('BwE selesai → proses dihentikan (bukan Y).','warn'); self.last('BwE VALIDASI SELESAI — STOP'); return False

    def stage2(self):
        if not self.need('nor'):return
        self.log('=== TAHAP 2: WIRATE NOR FULL PS4 ===','gold'); self.log(f'File siap diproses: {os.path.basename(self.nor)}','ok'); self.log('Write/Verify hardware belum dieksekusi pada build ini.','warn'); self.last('WIRATE NOR FULL')
    def stage3(self):
        if not self.need('nor'):return
        self.log('=== TAHAP 3: SMART PATCH WIRATE NOR ===','gold'); self.log(f'NOR siap diproses: {os.path.basename(self.nor)}','ok'); self.log('Menu native No.4 → Save → No.3 → No.5 belum dieksekusi otomatis.','warn'); self.last('SMART PATCH WIRATE NOR')
    def autosave_copy(self,src,prefix):
        srcp=Path(src); out=self.output_dir()
        if out is None:return None
        stamp=time.strftime('%Y%m%d_%H%M%S'); dst=out/f'{prefix}_{stamp}{srcp.suffix or ".bin"}'; data=srcp.read_bytes(); dst.write_bytes(data); md5=hashlib.md5(data).hexdigest().upper()
        self.log(f'SAVE OTOMATIS BERHASIL: {dst.name}','ok'); self.log(f'  Ukuran : {len(data):,} byte | MD5: {md5}','ok'); self.log(f'  Lokasi : {dst}','ok'); return dst
    def stage4(self):
        if not self.need('sys'):return
        if os.path.getsize(self.syscon)!=512*1024: messagebox.showwarning('SYSCON invalid','File SYSCON harus berukuran tepat 512 KB.'); return
        self.log('=== TAHAP 4: SMART SYSCON PATCH ===','gold'); self.log('LOAD SYSCON 512 KB → NO.1 → DEBUG ON → NO.2 → SNVS AUTO PATCHING','ok')
        choice=simpledialog.askstring('SNVS AUTO PATCHING','Masukkan nomor patch sesuai daftar yang tampil di WETOOL:')
        if not choice:return
        self.log(f'Patch nomor {choice} dipilih.','ok'); self.log('Fungsi patch native belum dieksekusi otomatis pada build ini.','warn'); dst=self.autosave_copy(self.syscon,f'SYSCON_STAGE4_PATCH_{choice}_INPUT'); self.last('SMART SYSCON PATCH — BACKUP')
    def stage5(self):
        if not self.need('sys'):return
        if os.path.getsize(self.syscon)!=512*1024: messagebox.showwarning('SYSCON invalid','File SYSCON harus berukuran tepat 512 KB.'); return
        self.log('=== TAHAP 5: SMART SYSCON REBUILD ===','gold')
        for x in ['LOAD SYSCON 512 KB','LOAD SYSCON KE WETOOL','NO. 6','NO. 4','NO. 4 LAGI','JALANKAN REBUILD']: self.log(x+' ... UI READY','ok')
        self.log('Fungsi native belum dieksekusi otomatis pada build ini.','warn'); self.autosave_copy(self.syscon,'SYSCON_STAGE5_REBUILD_INPUT'); self.last('SMART SYSCON REBUILD — BACKUP')

root=tk.Tk(); App(root); root.mainloop()
