import os, sys, time, threading, queue, subprocess, ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import messagebox

BASE = os.path.dirname(os.path.abspath(sys.argv[0]))
WETOOL = os.path.join(BASE, 'external', 'wetool.exe')

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

SW_RESTORE = 9
SW_MINIMIZE = 6
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
VK_RETURN = 0x0D
VK_3 = 0x33
VK_1 = 0x31

class App:
    def __init__(self, root):
        self.root = root
        self.root.title('SMART REPAIR EDITION BY ALI GAMES - WETOOL CONTROLLER TEST 4')
        self.root.geometry('1080x680')
        self.root.configure(bg='#0b0b0d')
        self.q = queue.Queue(); self.proc = None; self.hwnd = None; self.running = False
        self.ui(); self.root.after(100, self.pump)

    def ui(self):
        top = tk.Frame(self.root, bg='#0b0b0d'); top.pack(fill='x', padx=14, pady=12)
        tk.Label(top, text='SMART REPAIR EDITION BY ALI GAMES', fg='#d9b45a', bg='#0b0b0d', font=('Segoe UI',18,'bold')).pack(side='left')
        self.status = tk.Label(top, text='Siap', fg='#aaa', bg='#0b0b0d'); self.status.pack(side='right')
        bar = tk.Frame(self.root, bg='#111216'); bar.pack(fill='x', padx=14, pady=6)
        self.btn = tk.Button(bar, text='SMART READ FULL NOR - TEST CONTROLLER', command=self.start, bg='#18191e', fg='#e0c16b', font=('Segoe UI',11,'bold'), relief='flat', padx=18, pady=10)
        self.btn.pack(side='left', padx=6, pady=8)
        tk.Button(bar, text='STOP', command=self.stop, bg='#2a1717', fg='#ffb0b0', relief='flat', padx=16, pady=10).pack(side='left', padx=6, pady=8)
        body = tk.Frame(self.root, bg='#0b0b0d'); body.pack(fill='both', expand=True, padx=14, pady=8)
        self.log = tk.Text(body, bg='#050607', fg='#d6d6d6', insertbackground='white', font=('Consolas',10), wrap='none')
        self.log.pack(fill='both', expand=True)
        tk.Label(self.root, text='Original PS4WETOOLS PRO', fg='#777', bg='#0b0b0d', font=('Segoe UI',8)).pack(side='bottom', pady=6)

    def w(self, s): self.log.insert('end', s); self.log.see('end')

    def start(self):
        if self.running: return
        if not os.path.exists(WETOOL):
            messagebox.showerror('WETOOL tidak ditemukan', WETOOL); return
        self.running = True; self.btn.config(state='disabled'); self.status.config(text='Controller test...'); self.log.delete('1.0','end')
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        try:
            self.q.put('[SMART] TEST 4: injeksi langsung ke Console Input WETOOL.\n')
            self.q.put('[SMART] Tidak membuat READ FULL sendiri.\n')
            self.q.put('[SMART] Menjalankan WETOOL...\n')
            self.proc = subprocess.Popen([WETOOL], cwd=os.path.dirname(WETOOL))
            self.q.put(f'[SMART] PID WETOOL = {self.proc.pid}\n')
            hwnds = self.find_windows(self.proc.pid, timeout=20)
            if not hwnds:
                self.q.put('[ERROR] Tidak menemukan HWND WETOOL.\n'); return
            self.q.put(f'[SMART] Ditemukan {len(hwnds)} window WETOOL.\n')
            for h in hwnds:
                self.q.put(self.window_info(h))
            self.hwnd = self.choose_window(hwnds)
            if not self.hwnd:
                self.q.put('[ERROR] Tidak ada window yang bisa dipakai.\n'); return
            self.q.put('[SMART] Target HWND = 0x%X\n' % self.hwnd)
            self.q.put('[SMART] Mengirim NO. 3 langsung ke Console Input WETOOL...\n')
            time.sleep(0.5)
            ok3 = self.console_command('3')
            self.q.put('[SMART] NO. 3 dimasukkan ke Console Input: %s\n' % ('OK ✓' if ok3 else 'GAGAL'))
            time.sleep(2.0)
            self.q.put('[SMART] Mengirim NO. 1 langsung ke Console Input WETOOL...\n')
            ok1 = self.console_command('1')
            self.q.put('[SMART] NO. 1 dimasukkan ke Console Input: %s\n' % ('OK ✓' if ok1 else 'GAGAL'))
            time.sleep(3.0)
            self.q.put('[SMART] TEST 4 selesai. Periksa apakah menu WETOOL benar-benar berpindah setelah NO.3 dan NO.1.\n')
            self.q.put('[SMART] Tahap READ FULL belum dijalankan otomatis pada test ini.\n')
        except Exception as e:
            self.q.put('[ERROR] %r\n' % (e,))
        finally:
            self.q.put('__DONE__')

    def find_windows(self, pid, timeout=20):
        end = time.time() + timeout
        while time.time() < end:
            hs = []
            @EnumWindowsProc
            def cb(hwnd, lparam):
                p = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
                if p.value == pid and user32.IsWindow(hwnd):
                    hs.append(hwnd)
                return True
            user32.EnumWindows(cb, 0)
            if hs: return hs
            if self.proc and self.proc.poll() is not None:
                return []
            time.sleep(0.25)
        return []

    def choose_window(self, hs):
        # Prefer visible top-level window with a title; otherwise first valid window.
        titled = [h for h in hs if user32.IsWindowVisible(h) and user32.GetWindowTextLengthW(h) > 0]
        return titled[0] if titled else hs[0]

    def window_info(self, h):
        title = ctypes.create_unicode_buffer(512); user32.GetWindowTextW(h, title, 512)
        cls = ctypes.create_unicode_buffer(256); user32.GetClassNameW(h, cls, 256)
        return '[WINDOW] HWND=0x%X | class=%r | title=%r | visible=%s\n' % (h, cls.value, title.value, bool(user32.IsWindowVisible(h)))

    def activate(self, h):
        user32.ShowWindow(h, SW_RESTORE)
        user32.SetForegroundWindow(h)
        return user32.GetForegroundWindow() == h

    def send_input_text(self, s):
        # SendInput is intentionally used only for this controller test. It targets the
        # currently foreground WETOOL window, which mirrors a real operator typing the choice.
        INPUT = ctypes.Structure
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD), ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))]
        class INPUTUNION(ctypes.Union):
            _fields_ = [('ki', KEYBDINPUT)]
        class INPUTT(ctypes.Structure):
            _anonymous_ = ('u',); _fields_ = [('type', wintypes.DWORD), ('u', INPUTUNION)]
        sent = 0
        for ch in s:
            vk = user32.VkKeyScanW(ord(ch)) & 0xFF
            arr = (INPUTT * 2)()
            arr[0].type = 1; arr[0].ki.wVk = vk
            arr[1].type = 1; arr[1].ki.wVk = vk; arr[1].ki.dwFlags = 2
            r = user32.SendInput(2, ctypes.byref(arr), ctypes.sizeof(INPUTT))
            if r == 2: sent += 1
        return sent == len(s)

    def send_input_key(self, vk):
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD), ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))]
        class U(ctypes.Union): _fields_=[('ki', KEYBDINPUT)]
        class IN(ctypes.Structure): _anonymous_=('u',); _fields_=[('type',wintypes.DWORD),('u',U)]
        arr=(IN*2)(); arr[0].type=1; arr[0].ki.wVk=vk; arr[1].type=1; arr[1].ki.wVk=vk; arr[1].ki.dwFlags=2
        return user32.SendInput(2, ctypes.byref(arr), ctypes.sizeof(IN)) == 2

    def console_command(self, text):
        """Inject characters into the target WETOOL console input buffer.
        This does not depend on foreground focus and is intended for a console app
        such as WETOOL (ConsoleWindowClass)."""
        if not self.proc or self.proc.poll() is not None:
            return False
        pid = self.proc.pid
        ATTACH_PARENT_PROCESS = 0xFFFFFFFF
        STD_INPUT_HANDLE = -10
        KEY_EVENT = 0x0001
        KEYEVENTF_KEYUP = 0x0002

        class CHAR_UNION(ctypes.Union):
            _fields_ = [('UnicodeChar', wintypes.WCHAR), ('AsciiChar', wintypes.CHAR)]
        class KEY_EVENT_RECORD(ctypes.Structure):
            _fields_ = [
                ('bKeyDown', wintypes.BOOL),
                ('wRepeatCount', wintypes.WORD),
                ('wVirtualKeyCode', wintypes.WORD),
                ('wVirtualScanCode', wintypes.WORD),
                ('uChar', CHAR_UNION),
                ('dwControlKeyState', wintypes.DWORD),
            ]
        class INPUT_RECORD_UNION(ctypes.Union):
            _fields_ = [('KeyEvent', KEY_EVENT_RECORD)]
        class INPUT_RECORD(ctypes.Structure):
            _anonymous_ = ('Event',)
            _fields_ = [('EventType', wintypes.WORD), ('Event', INPUT_RECORD_UNION)]

        if not kernel32.AttachConsole(pid):
            # ERROR_ACCESS_DENIED can mean the process is already attached to a console.
            err = ctypes.get_last_error()
            if err != 5:
                self.q.put('[WARN] AttachConsole gagal, error=%s\\n' % err)
                return False

        try:
            hstdin = kernel32.GetStdHandle(STD_INPUT_HANDLE)
            if not hstdin or hstdin == wintypes.HANDLE(-1).value:
                self.q.put('[WARN] Tidak mendapatkan Console Input Handle.\\n')
                return False
            records = []
            for ch in text:
                vk = user32.VkKeyScanW(ord(ch)) & 0xFF
                rec_down = INPUT_RECORD()
                rec_down.EventType = KEY_EVENT
                rec_down.KeyEvent.bKeyDown = True
                rec_down.KeyEvent.wRepeatCount = 1
                rec_down.KeyEvent.wVirtualKeyCode = vk
                rec_down.KeyEvent.wVirtualScanCode = user32.MapVirtualKeyW(vk, 0)
                rec_down.KeyEvent.uChar.UnicodeChar = ch
                records.append(rec_down)
                rec_up = INPUT_RECORD()
                rec_up.EventType = KEY_EVENT
                rec_up.KeyEvent.bKeyDown = False
                rec_up.KeyEvent.wRepeatCount = 1
                rec_up.KeyEvent.wVirtualKeyCode = vk
                rec_up.KeyEvent.wVirtualScanCode = user32.MapVirtualKeyW(vk, 0)
                rec_up.KeyEvent.uChar.UnicodeChar = ch
                records.append(rec_up)
            # Enter key
            for down in (True, False):
                rec = INPUT_RECORD()
                rec.EventType = KEY_EVENT
                rec.KeyEvent.bKeyDown = down
                rec.KeyEvent.wRepeatCount = 1
                rec.KeyEvent.wVirtualKeyCode = VK_RETURN
                rec.KeyEvent.wVirtualScanCode = user32.MapVirtualKeyW(VK_RETURN, 0)
                rec.KeyEvent.uChar.UnicodeChar = '\r'
                records.append(rec)
            arr = (INPUT_RECORD * len(records))(*records)
            written = wintypes.DWORD(0)
            ok = kernel32.WriteConsoleInputW(hstdin, arr, len(records), ctypes.byref(written))
            return bool(ok and written.value == len(records))
        finally:
            # Detach only if this controller attached to the target console.
            try:
                kernel32.FreeConsole()
            except Exception:
                pass

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try: self.proc.terminate()
            except Exception: pass
        self.running = False; self.btn.config(state='normal'); self.status.config(text='Dihentikan'); self.w('\n[SMART] STOP.\n')

    def pump(self):
        try:
            while True:
                s=self.q.get_nowait()
                if s=='__DONE__': self.running=False; self.btn.config(state='normal'); self.status.config(text='Tes selesai')
                else: self.w(s)
        except queue.Empty: pass
        self.root.after(100, self.pump)

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
