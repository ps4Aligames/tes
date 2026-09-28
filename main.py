import os, sys, subprocess, threading, queue, time, tkinter as tk
from tkinter import ttk, filedialog, messagebox

BASE = os.path.dirname(os.path.abspath(sys.argv[0]))
WETOOL = os.path.join(BASE, 'wetool.exe')

class App:
    def __init__(self, root):
        self.root=root
        self.root.title('SMART REPAIR EDITION BY ALI GAMES')
        self.root.geometry('1050x650')
        self.root.configure(bg='#0b0b0d')
        self.proc=None
        self.q=queue.Queue()
        self.running=False
        self.stage_started=False
        self.build_ui()
        self.root.after(100,self.pump)

    def build_ui(self):
        top=tk.Frame(self.root,bg='#0b0b0d'); top.pack(fill='x',padx=14,pady=(12,6))
        tk.Label(top,text='SMART REPAIR EDITION BY ALI GAMES',fg='#d9b45a',bg='#0b0b0d',font=('Segoe UI',18,'bold')).pack(side='left')
        self.status=tk.Label(top,text='WETOOL: belum dijalankan',fg='#aaa',bg='#0b0b0d',font=('Segoe UI',10))
        self.status.pack(side='right')

        bar=tk.Frame(self.root,bg='#111216'); bar.pack(fill='x',padx=14,pady=6)
        self.btn=tk.Button(bar,text='SMART READ FULL NOR',command=self.start_read,bg='#18191e',fg='#e0c16b',activebackground='#262329',activeforeground='white',font=('Segoe UI',11,'bold'),relief='flat',padx=18,pady=10)
        self.btn.pack(side='left',padx=6,pady=8)
        tk.Button(bar,text='STOP',command=self.stop,bg='#2a1717',fg='#ffb0b0',activebackground='#3a2020',relief='flat',padx=16,pady=10).pack(side='left',padx=6,pady=8)
        tk.Button(bar,text='PILIH FOLDER HASIL',command=self.choose_folder,bg='#18191e',fg='#ddd',activebackground='#262329',relief='flat',padx=16,pady=10).pack(side='left',padx=6,pady=8)
        self.folder=tk.StringVar(value='(belum dipilih)')
        tk.Label(bar,textvariable=self.folder,fg='#aaa',bg='#111216',font=('Segoe UI',9)).pack(side='left',padx=10)

        body=tk.Frame(self.root,bg='#0b0b0d'); body.pack(fill='both',expand=True,padx=14,pady=8)
        left=tk.Frame(body,bg='#090a0c'); left.pack(side='left',fill='both',expand=True)
        tk.Label(left,text='LIVE WETOOL OUTPUT — proses asli, tanpa simulasi',fg='#c9a957',bg='#090a0c',anchor='w',font=('Consolas',10,'bold')).pack(fill='x',padx=8,pady=6)
        self.log=tk.Text(left,bg='#050607',fg='#d6d6d6',insertbackground='white',font=('Consolas',10),wrap='none',state='disabled')
        self.log.pack(fill='both',expand=True,padx=8,pady=(0,8))
        self.log.tag_config('ok',foreground='#8fd18f'); self.log.tag_config('warn',foreground='#e6c36a'); self.log.tag_config('err',foreground='#ff8d8d')

        right=tk.Frame(body,bg='#111216',width=260); right.pack(side='right',fill='y',padx=(10,0)); right.pack_propagate(False)
        self.info=tk.StringVar(value='Menunggu proses...')
        tk.Label(right,text='STATUS',fg='#c9a957',bg='#111216',font=('Segoe UI',10,'bold')).pack(anchor='w',padx=12,pady=(12,5))
        tk.Label(right,textvariable=self.info,justify='left',anchor='nw',fg='#ddd',bg='#111216',font=('Segoe UI',9),wraplength=230).pack(fill='x',padx=12)
        tk.Label(right,text='CATATAN',fg='#c9a957',bg='#111216',font=('Segoe UI',10,'bold')).pack(anchor='w',padx=12,pady=(22,5))
        tk.Label(right,text='Smart Repair tidak membuat READ sendiri. Output yang tampil berasal dari WETOOL asli yang dijalankan tanpa jendela.',justify='left',anchor='nw',fg='#aaa',bg='#111216',font=('Segoe UI',9),wraplength=230).pack(fill='x',padx=12)

        tk.Label(self.root,text='Original PS4WETOOLS PRO',fg='#777',bg='#0b0b0d',font=('Segoe UI',8)).pack(side='bottom',pady=6)

    def write(self,s,tag=None):
        self.log.configure(state='normal'); self.log.insert('end',s,tag or ''); self.log.see('end'); self.log.configure(state='disabled')

    def choose_folder(self):
        p=filedialog.askdirectory(title='Pilih folder hasil READ FULL')
        if p: self.folder.set(p)

    def start_read(self):
        if self.running: return
        if not os.path.exists(WETOOL):
            messagebox.showerror('WETOOL tidak ditemukan',f'Taruh wetool.exe di folder yang sama dengan Smart Repair.\n\n{WETOOL}')
            return
        self.running=True; self.btn.configure(state='disabled'); self.info.set('Menjalankan WETOOL asli di background...')
        self.write('\n===== SMART READ FULL NOR =====\n','warn')
        self.write('[SMART] Menjalankan WETOOL asli tanpa menampilkan jendelanya...\n')
        threading.Thread(target=self.worker,daemon=True).start()

    def worker(self):
        try:
            flags=getattr(subprocess,'CREATE_NO_WINDOW',0x08000000)
            self.proc=subprocess.Popen([WETOOL],cwd=BASE,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,creationflags=flags)
            self.q.put(('status','WETOOL berjalan di background.'))
            self.q.put(('log','[SMART] WETOOL PID %s aktif.\n' % self.proc.pid))
            # Give native startup a moment, then issue the requested top-level No. 3.
            time.sleep(1.0)
            self.send('3')
            self.q.put(('log','[SMART] Mengirim perintah native: 3\n'))
            self.q.put(('status','Perintah No. 3 dikirim. Menunggu output native WETOOL...'))
            # From this point onward, do not invent progress. Native output is streamed verbatim.
            while True:
                chunk=self.proc.stdout.read(1)
                if not chunk: break
                try: text=chunk.decode('utf-8','replace')
                except: text=str(chunk)
                self.q.put(('log',text))
            rc=self.proc.wait()
            self.q.put(('log','\n[SMART] WETOOL selesai, exit code=%s\n' % rc))
            self.q.put(('status','WETOOL selesai. Periksa output native di log.'))
        except Exception as e:
            self.q.put(('err','[SMART] ERROR: %s\n' % e))
            self.q.put(('status','Gagal menjalankan WETOOL.'))
        finally:
            self.q.put(('done',None))

    def send(self,s):
        if self.proc and self.proc.stdin:
            self.proc.stdin.write((s+'\n').encode()); self.proc.stdin.flush()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try: self.proc.terminate()
            except: pass
        self.running=False; self.btn.configure(state='normal'); self.info.set('Dihentikan.')
        self.write('\n[SMART] Proses dihentikan.\n','err')

    def pump(self):
        try:
            while True:
                typ,val=self.q.get_nowait()
                if typ=='log': self.write(val)
                elif typ=='err': self.write(val,'err')
                elif typ=='status': self.info.set(val)
                elif typ=='done': self.running=False; self.btn.configure(state='normal')
        except queue.Empty: pass
        self.root.after(100,self.pump)

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
