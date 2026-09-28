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
VK_RETURN = 0x0D

class COORD(ctypes.Structure):
    _fields_ = [('X', wintypes.SHORT), ('Y', wintypes.SHORT)]

class SMALL_RECT(ctypes.Structure):
    _fields_ = [('Left', wintypes.SHORT), ('Top', wintypes.SHORT), ('Right', wintypes.SHORT), ('Bottom', wintypes.SHORT)]

class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [
        ('dwSize', COORD),
        ('dwCursorPosition', COORD),
        ('wAttributes', wintypes.WORD),
        ('srWindow', SMALL_RECT),
        ('dwMaximumWindowSize', COORD),
    ]

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
STD_INPUT_HANDLE = -10
KEY_EVENT = 0x0001

kernel32.AttachConsole.argtypes = [wintypes.DWORD]
kernel32.AttachConsole.restype = wintypes.BOOL
kernel32.FreeConsole.argtypes = []
kernel32.FreeConsole.restype = wintypes.BOOL
kernel32.GetConsoleScreenBufferInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(CONSOLE_SCREEN_BUFFER_INFO)]
kernel32.GetConsoleScreenBufferInfo.restype = wintypes.BOOL
kernel32.ReadConsoleOutputCharacterW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, COORD, ctypes.POINTER(wintypes.DWORD)]
kernel32.ReadConsoleOutputCharacterW.restype = wintypes.BOOL
kernel32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.GetStdHandle.argtypes = [ctypes.c_int]
kernel32.GetStdHandle.restype = wintypes.HANDLE
kernel32.WriteConsoleInputW.restype = wintypes.BOOL

class App:
    def __init__(self, root):
        self.root = root
        self.root.title('SMART REPAIR EDITION BY ALI GAMES - WETOOL CONTROLLER TEST 5')
        self.root.geometry('1080x680')
        self.root.configure(bg='#0b0b0d')
        self.q = queue.Queue(); self.proc = None; self.hwnd = None; self.running = False
        self.last_filtered = ''
        self.ui(); self.root.after(100, self.pump)

    def ui(self):
        top = tk.Frame(self.root, bg='#0b0b0d'); top.pack(fill='x', padx=14, pady=12)
        tk.Label(top, text='SMART REPAIR EDITION BY ALI GAMES', fg='#d9b45a', bg='#0b0b0d', font=('Segoe UI',18,'bold')).pack(side='left')
        self.status = tk.Label(top, text='Siap', fg='#aaa', bg='#0b0b0d'); self.status.pack(side='right')
        bar = tk.Frame(self.root, bg='#111216'); bar.pack(fill='x', padx=14, pady=6)
        self.btn = tk.Button(bar, text='SMART READ FULL NOR - TEST LOG', command=self.start, bg='#18191e', fg='#e0c16b', font=('Segoe UI',11,'bold'), relief='flat', padx=18, pady=10)
        self.btn.pack(side='left', padx=6, pady=8)
        tk.Button(bar, text='STOP', command=self.stop, bg='#2a1717', fg='#ffb0b0', relief='flat', padx=16, pady=10).pack(side='left', padx=6, pady=8)
        body = tk.Frame(self.root, bg='#0b0b0d'); body.pack(fill='both', expand=True, padx=14, pady=8)
        self.log = tk.Text(body, bg='#050607', fg='#d6d6d6', insertbackground='white', font=('Consolas',10), wrap='none')
        self.log.pack(fill='both', expand=True)
        tk.Label(self.root, text='Original PS4WETOOLS PRO', fg='#777', bg='#0b0b0d', font=('Segoe UI',8)).pack(side='bottom', pady=6)

    def w(self, s):
        self.log.insert('end', s); self.log.see('end')

    def replace_filtered(self, block):
        if block == self.last_filtered:
            return
        self.last_filtered = block
        # Keep controller status at the top; WETOOL's SPIway title, Actions and Make choice are hidden.
        self.log.delete('1.0', 'end')
        self.log.insert('end', '[SMART] WETOOL controller aktif.\n')
        self.log.insert('end', '[SMART] Output yang ditampilkan: Version sampai Flash config.\n\n')
        self.log.insert('end', block)
        self.log.see('end')

    def start(self):
        if self.running: return
        if not os.path.exists(WETOOL):
            messagebox.showerror('WETOOL tidak ditemukan', WETOOL); return
        self.running = True; self.btn.config(state='disabled'); self.status.config(text='Controller aktif...'); self.log.delete('1.0','end'); self.last_filtered=''
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        try:
            self.q.put('[SMART] TEST 5: controller WETOOL + filtered log.\n')
            self.q.put('[SMART] Bagian SPIway/Actions/Make choice disembunyikan.\n')
            self.q.put('[SMART] Menjalankan WETOOL asli...\n')
            self.proc = subprocess.Popen([WETOOL], cwd=os.path.dirname(WETOOL))
            self.q.put(f'[SMART] PID WETOOL = {self.proc.pid}\n')
            hwnds = self.find_windows(self.proc.pid, timeout=20)
            if not hwnds:
                self.q.put('[ERROR] Tidak menemukan HWND WETOOL.\n'); return
            self.hwnd = self.choose_window(hwnds)
            self.q.put('[SMART] WETOOL ditemukan: HWND=0x%X\n' % self.hwnd)
            time.sleep(1.0)
            ok3 = self.console_command('3')
            self.q.put('[SMART] NO. 3 → %s\n' % ('OK ✓' if ok3 else 'GAGAL'))
            # Give WETOOL time to enter SPIway and render its real chip information.
            for _ in range(12):
                if self.proc.poll() is not None: break
                text = self.read_console_text(self.proc.pid)
                filtered = self.filter_version_to_flash(text)
                if filtered:
                    self.q.put(('__FILTER__', filtered))
                time.sleep(0.25)
            self.q.put('[SMART] Mengirim NO. 1 melalui Console Input WETOOL...\n')
            ok1 = self.console_command('1')
            self.q.put('[SMART] NO. 1 → %s\n' % ('OK ✓' if ok1 else 'GAGAL'))
            # Keep capturing only the requested information block.
            for _ in range(20):
                if self.proc.poll() is not None: break
                text = self.read_console_text(self.proc.pid)
                filtered = self.filter_version_to_flash(text)
                if filtered:
                    self.q.put(('__FILTER__', filtered))
                time.sleep(0.25)
            self.q.put('[SMART] TEST 5 selesai.\n')
        except Exception as e:
            self.q.put('[ERROR] %r\n' % (e,))
        finally:
            self.q.put('__DONE__')

    def find_windows(self, pid, timeout=20):
        end = time.time() + timeout
        while time.time() < end:
            hs=[]
            @EnumWindowsProc
            def cb(hwnd, lparam):
                p=wintypes.DWORD(); user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
                if p.value == pid and user32.IsWindow(hwnd): hs.append(hwnd)
                return True
            user32.EnumWindows(cb, 0)
            if hs: return hs
            if self.proc and self.proc.poll() is not None: return []
            time.sleep(0.25)
        return []

    def choose_window(self, hs):
        titled=[h for h in hs if user32.IsWindowVisible(h) and user32.GetWindowTextLengthW(h)>0]
        return titled[0] if titled else hs[0]

    def read_console_text(self, pid):
        # Attach briefly to the WETOOL console and read the actual screen buffer.
        # This is read-only; WETOOL remains the engine.
        try:
            kernel32.FreeConsole()
            if not kernel32.AttachConsole(pid):
                return ''
            h = kernel32.CreateFileW('CONOUT$', GENERIC_READ | GENERIC_WRITE,
                                     FILE_SHARE_READ | FILE_SHARE_WRITE, None,
                                     OPEN_EXISTING, 0, None)
            if not h or h == INVALID_HANDLE_VALUE:
                return ''
            try:
                info = CONSOLE_SCREEN_BUFFER_INFO()
                if not kernel32.GetConsoleScreenBufferInfo(h, ctypes.byref(info)):
                    return ''
                width = max(1, info.dwSize.X)
                height = max(1, info.dwSize.Y)
                total = min(width * height, 30000)
                buf = ctypes.create_unicode_buffer(total + 1)
                read = wintypes.DWORD(0)
                if not kernel32.ReadConsoleOutputCharacterW(h, buf, total, COORD(0,0), ctypes.byref(read)):
                    return ''
                chars = buf[:read.value]
                rows = []
                for y in range(height):
                    start = y * width
                    row = chars[start:start+width]
                    if row:
                        rows.append(row.rstrip())
                return '\n'.join(rows)
            finally:
                kernel32.CloseHandle(h)
        finally:
            kernel32.FreeConsole()

    def filter_version_to_flash(self, text):
        if not text: return ''
        lines = [x.rstrip() for x in text.replace('\x00','').splitlines()]
        start = -1
        for i, line in enumerate(lines):
            if 'Version' in line and ':' in line:
                start = i; break
        if start < 0: return ''
        end = start
        for i in range(start, min(len(lines), start + 30)):
            if 'Flash config' in lines[i]:
                end = i; break
        else:
            return ''
        selected = lines[start:end+1]
        # Trim empty rows around the requested block but preserve internal spacing.
        while selected and not selected[0].strip(): selected.pop(0)
        while selected and not selected[-1].strip(): selected.pop()
        return '\n'.join(selected) + '\n'

    def console_command(self, text):
        if not self.proc or self.proc.poll() is not None: return False
        pid=self.proc.pid
        class CHAR_UNION(ctypes.Union): _fields_=[('UnicodeChar',wintypes.WCHAR),('AsciiChar',wintypes.CHAR)]
        class KEY_EVENT_RECORD(ctypes.Structure):
            _fields_=[('bKeyDown',wintypes.BOOL),('wRepeatCount',wintypes.WORD),('wVirtualKeyCode',wintypes.WORD),('wVirtualScanCode',wintypes.WORD),('uChar',CHAR_UNION),('dwControlKeyState',wintypes.DWORD)]
        class INPUT_RECORD_UNION(ctypes.Union): _fields_=[('KeyEvent',KEY_EVENT_RECORD)]
        class INPUT_RECORD(ctypes.Structure):
            _anonymous_=('Event',); _fields_=[('EventType',wintypes.WORD),('Event',INPUT_RECORD_UNION)]
        if not kernel32.AttachConsole(pid):
            if ctypes.get_last_error()!=5: return False
        try:
            hstdin=kernel32.GetStdHandle(STD_INPUT_HANDLE)
            if not hstdin or hstdin == wintypes.HANDLE(-1).value: return False
            records=[]
            for ch in text:
                vk=user32.VkKeyScanW(ord(ch)) & 0xFF
                for down in (True,False):
                    rec=INPUT_RECORD(); rec.EventType=KEY_EVENT; rec.KeyEvent.bKeyDown=down; rec.KeyEvent.wRepeatCount=1; rec.KeyEvent.wVirtualKeyCode=vk; rec.KeyEvent.wVirtualScanCode=user32.MapVirtualKeyW(vk,0); rec.KeyEvent.uChar.UnicodeChar=ch; records.append(rec)
            for down in (True,False):
                rec=INPUT_RECORD(); rec.EventType=KEY_EVENT; rec.KeyEvent.bKeyDown=down; rec.KeyEvent.wRepeatCount=1; rec.KeyEvent.wVirtualKeyCode=VK_RETURN; rec.KeyEvent.wVirtualScanCode=user32.MapVirtualKeyW(VK_RETURN,0); rec.KeyEvent.uChar.UnicodeChar='\r'; records.append(rec)
            arr=(INPUT_RECORD*len(records))(*records); written=wintypes.DWORD(0)
            return bool(kernel32.WriteConsoleInputW(hstdin,arr,len(records),ctypes.byref(written)) and written.value==len(records))
        finally:
            kernel32.FreeConsole()

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try: self.proc.terminate()
            except Exception: pass
        self.running=False; self.btn.config(state='normal'); self.status.config(text='Dihentikan'); self.w('\n[SMART] STOP.\n')

    def pump(self):
        try:
            while True:
                s=self.q.get_nowait()
                if s=='__DONE__':
                    self.running=False; self.btn.config(state='normal'); self.status.config(text='Tes selesai')
                elif isinstance(s, tuple) and s[0]=='__FILTER__':
                    self.replace_filtered(s[1])
                else:
                    self.w(s)
        except queue.Empty: pass
        self.root.after(100,self.pump)

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
