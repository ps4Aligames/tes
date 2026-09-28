import os, sys, time, threading, queue, subprocess, tkinter as tk
from tkinter import messagebox

try:
    from pywinauto import Desktop
    from pywinauto.keyboard import send_keys
except Exception:
    Desktop = None
    send_keys = None

BASE = os.path.dirname(os.path.abspath(sys.argv[0]))
WETOOL = os.path.join(BASE, 'external', 'wetool.exe')

class App:
    def __init__(self, root):
        self.root=root; self.root.title('SMART REPAIR EDITION BY ALI GAMES - WETOOL CONTROLLER TEST')
        self.root.geometry('1050x650'); self.root.configure(bg='#0b0b0d')
        self.q=queue.Queue(); self.proc=None; self.win=None; self.running=False
        self.ui(); self.root.after(100,self.pump)
    def ui(self):
        top=tk.Frame(self.root,bg='#0b0b0d'); top.pack(fill='x',padx=14,pady=12)
        tk.Label(top,text='SMART REPAIR EDITION BY ALI GAMES',fg='#d9b45a',bg='#0b0b0d',font=('Segoe UI',18,'bold')).pack(side='left')
        self.status=tk.Label(top,text='Siap',fg='#aaa',bg='#0b0b0d'); self.status.pack(side='right')
        bar=tk.Frame(self.root,bg='#111216'); bar.pack(fill='x',padx=14,pady=6)
        self.btn=tk.Button(bar,text='SMART READ FULL NOR',command=self.start,bg='#18191e',fg='#e0c16b',font=('Segoe UI',11,'bold'),relief='flat',padx=18,pady=10); self.btn.pack(side='left',padx=6,pady=8)
        tk.Button(bar,text='STOP',command=self.stop,bg='#2a1717',fg='#ffb0b0',relief='flat',padx=16,pady=10).pack(side='left',padx=6,pady=8)
        body=tk.Frame(self.root,bg='#0b0b0d'); body.pack(fill='both',expand=True,padx=14,pady=8)
        self.log=tk.Text(body,bg='#050607',fg='#d6d6d6',insertbackground='white',font=('Consolas',10),wrap='none'); self.log.pack(fill='both',expand=True)
        tk.Label(self.root,text='Original PS4WETOOLS PRO',fg='#777',bg='#0b0b0d',font=('Segoe UI',8)).pack(side='bottom',pady=6)
    def w(self,s): self.log.insert('end',s); self.log.see('end')
    def start(self):
        if self.running:return
        if not os.path.exists(WETOOL): messagebox.showerror('WETOOL tidak ditemukan',WETOOL); return
        if Desktop is None: messagebox.showerror('Dependency','pywinauto belum tersedia.'); return
        self.running=True; self.btn.config(state='disabled'); self.status.config(text='Menjalankan WETOOL...'); self.log.delete('1.0','end')
        self.w('[SMART] Controller test dimulai.\n')
        self.w('[SMART] WETOOL asli akan dikendalikan otomatis; Smart Repair tidak membuat READ sendiri.\n\n')
        threading.Thread(target=self.worker,daemon=True).start()
    def worker(self):
        try:
            si=subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow=0
            self.proc=subprocess.Popen([WETOOL],cwd=os.path.dirname(WETOOL),startupinfo=si,creationflags=0)
            self.q.put('WETOOL process PID=%s berjalan hidden.\n' % self.proc.pid)
            desk=Desktop(backend='uia')
            win=None
            for _ in range(40):
                try:
                    win=desk.window(process=self.proc.pid)
                    if win.exists(timeout=0.2): break
                except Exception: pass
                time.sleep(.25)
            if not win:
                self.q.put('[ERROR] Jendela WETOOL tidak ditemukan oleh UI Automation.\n'); return
            self.win=win
            self.q.put('[SMART] Window WETOOL terdeteksi: %s\n' % (win.window_text() or '<tanpa title>'))
            self.dump_controls(win,'[SMART] Kontrol WETOOL saat awal:')
            # Keep WETOOL hidden, but try native keyboard input against its automation window.
            self.q.put('[SMART] Menjalankan NO. 3...\n')
            try: win.set_focus(); win.type_keys('3{ENTER}', set_foreground=False)
            except Exception as e: self.q.put('[WARN] No.3 via UIA gagal: %s\n' % e)
            time.sleep(1.5); self.dump_controls(win,'[SMART] Setelah NO. 3:')
            self.q.put('[SMART] Menjalankan NO. 1...\n')
            try: win.set_focus(); win.type_keys('1{ENTER}', set_foreground=False)
            except Exception as e: self.q.put('[WARN] No.1 via UIA gagal: %s\n' % e)
            time.sleep(2.0); self.dump_controls(win,'[SMART] Setelah NO. 1:')
            self.q.put('[SMART] Jika WETOOL menampilkan menu/COM pada kontrol yang terdeteksi, data tersebut akan terlihat di log ini.\n')
            self.q.put('[SMART] Belum menjalankan READ FULL secara paksa: kita hanya mengikuti kontrol nyata WETOOL pada tahap uji ini.\n')
        except Exception as e:
            self.q.put('[ERROR] %s\n' % e)
        finally:
            self.q.put('__DONE__')
    def dump_controls(self,win,head):
        self.q.put(head+'\n')
        try:
            for c in win.descendants(depth=3):
                try:
                    txt=c.window_text(); typ=c.element_info.control_type
                    if txt or typ: self.q.put('  - %s | %s\n' % (typ,txt))
                except Exception: pass
        except Exception as e:self.q.put('  [WARN] tidak bisa membaca controls: %s\n' % e)
    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:self.proc.terminate()
            except:pass
        self.running=False; self.btn.config(state='normal'); self.status.config(text='Dihentikan'); self.w('\n[SMART] STOP.\n')
    def pump(self):
        try:
            while True:
                s=self.q.get_nowait()
                if s=='__DONE__': self.running=False; self.btn.config(state='normal'); self.status.config(text='Tes selesai')
                else:self.w(s)
        except queue.Empty:pass
        self.root.after(100,self.pump)

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
