import os, sys, time, threading, queue, subprocess, tkinter as tk
from tkinter import messagebox

try:
    from pywinauto import Desktop
except Exception:
    Desktop = None

BASE = os.path.dirname(os.path.abspath(sys.argv[0]))
WETOOL = os.path.join(BASE, 'external', 'wetool.exe')

class App:
    def __init__(self, root):
        self.root = root
        self.root.title('SMART REPAIR EDITION BY ALI GAMES - WETOOL CONTROLLER TEST 2')
        self.root.geometry('1080x680')
        self.root.configure(bg='#0b0b0d')
        self.q = queue.Queue(); self.proc = None; self.win = None; self.running = False
        self.ui(); self.root.after(100, self.pump)

    def ui(self):
        top = tk.Frame(self.root, bg='#0b0b0d'); top.pack(fill='x', padx=14, pady=12)
        tk.Label(top, text='SMART REPAIR EDITION BY ALI GAMES', fg='#d9b45a', bg='#0b0b0d', font=('Segoe UI',18,'bold')).pack(side='left')
        self.status = tk.Label(top, text='Siap', fg='#aaa', bg='#0b0b0d'); self.status.pack(side='right')
        bar = tk.Frame(self.root, bg='#111216'); bar.pack(fill='x', padx=14, pady=6)
        self.btn = tk.Button(bar, text='SMART READ FULL NOR', command=self.start, bg='#18191e', fg='#e0c16b', font=('Segoe UI',11,'bold'), relief='flat', padx=18, pady=10)
        self.btn.pack(side='left', padx=6, pady=8)
        tk.Button(bar, text='STOP', command=self.stop, bg='#2a1717', fg='#ffb0b0', relief='flat', padx=16, pady=10).pack(side='left', padx=6, pady=8)
        body = tk.Frame(self.root, bg='#0b0b0d'); body.pack(fill='both', expand=True, padx=14, pady=8)
        self.log = tk.Text(body, bg='#050607', fg='#d6d6d6', insertbackground='white', font=('Consolas',10), wrap='none')
        self.log.pack(fill='both', expand=True)
        tk.Label(self.root, text='Original PS4WETOOLS PRO', fg='#777', bg='#0b0b0d', font=('Segoe UI',8)).pack(side='bottom', pady=6)

    def w(self, s):
        self.log.insert('end', s); self.log.see('end')

    def start(self):
        if self.running: return
        if not os.path.exists(WETOOL):
            messagebox.showerror('WETOOL tidak ditemukan', WETOOL); return
        if Desktop is None:
            messagebox.showerror('Dependency', 'pywinauto belum tersedia.'); return
        self.running = True; self.btn.config(state='disabled'); self.status.config(text='Mencari WETOOL...'); self.log.delete('1.0','end')
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        try:
            # IMPORTANT: do NOT start WETOOL hidden. UI Automation cannot reliably attach to a
            # window that was created hidden. We start normally, attach, then minimize it.
            self.q.put('[SMART] Menjalankan WETOOL asli untuk proses controller test...\n')
            self.q.put('[SMART] WETOOL sengaja tidak di-HIDE saat inisialisasi agar UI Automation dapat menemukan window.\n')
            self.proc = subprocess.Popen([WETOOL], cwd=os.path.dirname(WETOOL))
            pid = self.proc.pid
            self.q.put('[SMART] WETOOL PID=%s berjalan.\n' % pid)

            found = None
            found_backend = None
            # Try both UIA and Win32. WETOOL may expose a normal Tk/Win32 window rather than UIA.
            for attempt in range(60):
                for backend in ('uia', 'win32'):
                    try:
                        desk = Desktop(backend=backend)
                        wins = desk.windows(process=pid, top_level_only=True, visible_only=False)
                        for w in wins:
                            try:
                                if w.exists(timeout=0.15):
                                    found = w; found_backend = backend; break
                            except Exception:
                                pass
                        if found: break
                    except Exception as e:
                        if attempt in (0, 20, 40):
                            self.q.put('[DEBUG] backend %s: %s\n' % (backend, e))
                if found: break
                if self.proc.poll() is not None:
                    self.q.put('[ERROR] WETOOL berhenti sendiri. Exit code=%s\n' % self.proc.returncode)
                    self.q.put('__DONE__'); return
                time.sleep(0.25)

            if not found:
                self.q.put('[ERROR] Window WETOOL tidak ditemukan setelah 15 detik.\n')
                self.q.put('[ERROR] Jadi No.3/No.1 belum dijalankan. Tidak ada proses READ palsu.\n')
                self.q.put('__DONE__'); return

            self.win = found
            title = ''
            try: title = found.window_text()
            except Exception: pass
            self.q.put('[SMART] Window WETOOL ditemukan. Backend=%s | Title=%r\n' % (found_backend, title))
            self.dump_controls(found, '[SMART] Kontrol WETOOL sebelum aksi:')

            # Minimize only AFTER the handle/control is acquired. This keeps it out of the way
            # while preserving a window that automation can still address.
            try:
                found.minimize()
                self.q.put('[SMART] WETOOL diminimalkan setelah handle ditemukan.\n')
            except Exception as e:
                self.q.put('[WARN] Tidak bisa minimize WETOOL: %s\n' % e)

            # Controller test: send the requested No.3 then No.1 to the ORIGINAL WETOOL.
            self.q.put('[SMART] Menjalankan NO. 3 pada WETOOL asli...\n')
            ok3 = self.send_number(found, '3')
            self.q.put('[SMART] NO. 3 %s\n' % ('terkirim ✓' if ok3 else 'GAGAL'))
            time.sleep(1.5)
            self.dump_controls(found, '[SMART] Kondisi WETOOL setelah NO. 3:')

            self.q.put('[SMART] Menjalankan NO. 1 pada WETOOL asli...\n')
            ok1 = self.send_number(found, '1')
            self.q.put('[SMART] NO. 1 %s\n' % ('terkirim ✓' if ok1 else 'GAGAL'))
            time.sleep(2.0)
            self.dump_controls(found, '[SMART] Kondisi WETOOL setelah NO. 1:')

            self.q.put('[SMART] Tahap ini hanya menguji controller. READ FULL belum dipanggil paksa.\n')
            self.q.put('[SMART] Jika kontrol/menu dan respons No.3/No.1 terlihat di log, kita lanjutkan ke READ FULL asli.\n')
        except Exception as e:
            self.q.put('[ERROR] %r\n' % (e,))
        finally:
            self.q.put('__DONE__')

    def send_number(self, win, number):
        # First try pywinauto keyboard on the real window. If unavailable, try a direct
        # click/type sequence on a standard edit/console control.
        try:
            win.restore()
        except Exception:
            pass
        try:
            win.set_focus()
        except Exception:
            pass
        try:
            win.type_keys(number + '{ENTER}', set_foreground=False)
            return True
        except Exception as e:
            self.q.put('[DEBUG] type_keys %s gagal: %r\n' % (number, e))
        return False

    def dump_controls(self, win, head):
        self.q.put(head + '\n')
        try:
            controls = win.descendants(depth=4)
            count = 0
            for c in controls:
                try:
                    txt = c.window_text(); typ = c.element_info.control_type
                    if txt or typ:
                        self.q.put('  - %s | %r\n' % (typ, txt))
                        count += 1
                        if count >= 80: break
                except Exception:
                    pass
            if count == 0:
                self.q.put('  - (tidak ada child control yang terbaca)\n')
        except Exception as e:
            self.q.put('  [WARN] tidak bisa membaca controls: %r\n' % (e,))

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try: self.proc.terminate()
            except Exception: pass
        self.running = False; self.btn.config(state='normal'); self.status.config(text='Dihentikan'); self.w('\n[SMART] STOP.\n')

    def pump(self):
        try:
            while True:
                s = self.q.get_nowait()
                if s == '__DONE__':
                    self.running = False; self.btn.config(state='normal'); self.status.config(text='Tes selesai')
                else:
                    self.w(s)
        except queue.Empty:
            pass
        self.root.after(100, self.pump)

if __name__ == '__main__':
    root = tk.Tk(); App(root); root.mainloop()
