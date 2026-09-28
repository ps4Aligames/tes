import os, sys, time, threading, queue, subprocess, ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import messagebox

BASE = os.path.dirname(os.path.abspath(sys.argv[0]))
WETOOL = os.path.join(BASE, 'external', 'wetool.exe')
BWE = os.path.join(BASE, 'external', 'BwE_PS4_NOR_Validator.exe')

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
        self.root.title('SMART REPAIR EDITION BY ALI GAMES - WETOOL CONTROLLER TEST 8')
        self.root.geometry('1080x680')
        self.root.configure(bg='#0b0b0d')
        self.q = queue.Queue(); self.proc = None; self.hwnd = None; self.bwe_proc = None; self.running = False
        self.last_filtered = ''
        self.last_read_view = ''
        self.spinner_index = 0
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
        self.running = True; self.btn.config(state='disabled'); self.status.config(text='Controller aktif...'); self.log.delete('1.0','end'); self.last_filtered=''; self.last_read_view=''; self.spinner_index=0
        threading.Thread(target=self.worker, daemon=True).start()

    def worker(self):
        try:
            self.q.put('[SMART] TEST 8: READ FULL → F → RENAME → LOAD KE BwE.\n')
            self.q.put('[SMART] WETOOL asli tetap menjadi engine.\n')
            self.q.put('[SMART] Menjalankan WETOOL asli...\n')
            self.proc = subprocess.Popen([WETOOL], cwd=os.path.dirname(WETOOL))
            self.q.put(f'[SMART] PID WETOOL = {self.proc.pid}\n')
            hwnds = self.find_windows(self.proc.pid, timeout=20)
            if not hwnds:
                self.q.put('[ERROR] Tidak menemukan HWND WETOOL.\n'); return
            self.hwnd = self.choose_window(hwnds)
            self.q.put('[SMART] WETOOL ditemukan.\n')
            time.sleep(1)
            ok3=self.console_command('3')
            self.q.put('[SMART] NO. 3 → %s\n' % ('OK ✓' if ok3 else 'GAGAL'))
            # Capture chip information once only. Do not repeat it on every screen refresh.
            for _ in range(40):
                if self.proc.poll() is not None: break
                text=self.read_console_text(self.proc.pid)
                filtered=self.filter_version_to_flash(text)
                if filtered:
                    self.q.put(('__FILTER__', filtered))
                    break
                time.sleep(.25)
            ok1=self.console_command('1')
            self.q.put('[SMART] READ FULL / READ ALL → %s\n' % ('DIKIRIM ✓' if ok1 else 'GAGAL'))
            self.q.put('[SMART] Membaca NOR...\n')
            self.q.put(('__READ_START__', 'Membaca NOR asli dari WETOOL'))
            last=''
            read_done=False
            stable_complete=0
            for _ in range(2400):
                if self.proc.poll() is not None: break
                text=self.read_console_text(self.proc.pid)
                if text and text!=last:
                    last=text
                    filtered=self.filter_read_output(text)
                    if filtered:
                        # Show only the latest real WETOOL progress, not the same chip header for every block.
                        progress=self.extract_latest_progress(filtered)
                        if progress:
                            self.q.put(('__READ__', progress))
                    if self.is_read_complete(text):
                        stable_complete += 1
                        if stable_complete >= 2:
                            read_done=True
                            break
                    else:
                        stable_complete=0
                time.sleep(.25)
            if not read_done:
                self.q.put('[SMART] READ FULL belum terdeteksi selesai dari output WETOOL.\n')
                return
            self.q.put('[SMART] READ FULL SELESAI ✓\n')
            self.q.put(('__READ_DONE__', 'READ FULL selesai'))
            # User-requested sequence: after the real read completes, send F first, then R.
            time.sleep(.8)
            okf=self.console_command('f')
            self.q.put('[SMART] F → %s\n' % ('DIKIRIM ✓' if okf else 'GAGAL'))
            time.sleep(1.2)
            self.q.put('[SMART] Mengirim R: Rename File to Canonical Name...\n')
            okr=self.console_command('r')
            self.q.put('[SMART] R → %s\n' % ('DIKIRIM ✓' if okr else 'GAGAL'))
            time.sleep(2)
            # Show newest NOR/bin information found under the WETOOL directory tree.
            info=self.find_newest_nor()
            if info:
                self.q.put(('__FILEINFO__', info))
                self.q.put('[SMART] File NOR hasil READ ditemukan.\n')
            else:
                self.q.put('[SMART] File NOR hasil READ belum ditemukan otomatis.\n')
            # Launch the supplied original BwE executable.
            if not os.path.exists(BWE):
                self.q.put('[ERROR] BwE_PS4_NOR_Validator.exe tidak ditemukan.\n'); return
            self.bwe_proc=subprocess.Popen([BWE], cwd=os.path.dirname(BWE))
            self.q.put(f'[SMART] BwE Validator dijalankan. PID={self.bwe_proc.pid}\n')
            bwe_hwnds=self.find_windows(self.bwe_proc.pid, timeout=20)
            if bwe_hwnds:
                self.q.put('[SMART] Window BwE ditemukan.\n')
                self.bwe_hwnd=self.choose_window(bwe_hwnds)
                time.sleep(1)
                # The previous test only sent the character 7 and did not load the NOR.
                # For this test, try the normal Windows Open dialog and pass the actual NOR path.
                info=self.find_newest_nor()
                nor_path=self.last_nor_path if hasattr(self,'last_nor_path') else ''
                if not nor_path and info:
                    nor_path=self.extract_path_from_fileinfo(info)
                if nor_path:
                    sent=self.open_file_in_bwe(self.bwe_hwnd, nor_path)
                    self.q.put('[SMART] BwE LOAD NOR → %s\n' % ('PERINTAH DIKIRIM ✓' if sent else 'GAGAL'))
                else:
                    self.q.put('[SMART] Path NOR hasil READ tidak tersedia untuk BwE.\n')
            else:
                self.q.put('[SMART] Window BwE tidak ditemukan.\n')
        except Exception as e:
            self.q.put('[ERROR] %r\n' % (e,))
        finally:
            self.q.put('__DONE__')

    def filter_read_output(self,text):
        if not text: return ''
        lines=[x.rstrip() for x in text.replace('\\x00','').splitlines()]
        # Keep actual read-related lines only; remove internal menus.
        keep=[]
        for line in lines:
            low=line.lower().strip()
            if any(k in low for k in ('read','reading','progress','sector','block','dump','percent','bytes','mb','completed','complete','saved','save','error','success')):
                if 'make choice' not in low and not low.startswith(('1:','2:','3:','4:','5:','6:','7:','8:','9:')):
                    keep.append(line)
        return '\n'.join(keep[-40:])+'\n' if keep else ''

    def is_read_complete(self,text):
        low=text.lower()
        if '100%' in low and ('32768 kb / 32768 kb' in low or '32768 kb' in low):
            return True
        if 'block 511' in low and ('100%' in low or '32768 kb' in low):
            return True
        return ('read all' in low and ('complete' in low or 'completed' in low or 'success' in low)) or ('saved' in low and ('nor' in low or '.bin' in low))

    def find_newest_nor(self):
        roots=[os.path.dirname(WETOOL), os.path.expanduser('~/Desktop'), os.path.expanduser('~/Documents')]
        found=[]
        cutoff=time.time()-3600
        for root in roots:
            if not os.path.isdir(root): continue
            for base,dirs,files in os.walk(root):
                dirs[:]=[d for d in dirs if d not in ('.git','__pycache__')]
                for fn in files:
                    if fn.lower().endswith(('.bin','.nor')):
                        fp=os.path.join(base,fn)
                        try:
                            st=os.stat(fp)
                            if st.st_mtime>=cutoff and st.st_size>0:
                                found.append((st.st_mtime,fp,st.st_size))
                        except OSError: pass
        if not found: return ''
        _,fp,size=max(found)
        self.last_nor_path=fp
        return f'File name : {os.path.basename(fp)}\nSize      : {size:,} bytes\nLocation  : {fp}\n'

    def extract_latest_progress(self, filtered):
        lines=[x.strip() for x in filtered.splitlines() if x.strip()]
        # Keep only one latest real progress line. Prefer Block/KB/%/seconds lines.
        candidates=[]
        for line in lines:
            low=line.lower()
            if ('block ' in low and '%' in low) or ('kb /' in low and '%' in low) or ('reading' in low and ('block' in low or '%' in low)):
                candidates.append(line)
        if candidates:
            return candidates[-1] + '\n'
        # If WETOOL has a textual read status but no numeric progress, show that status once.
        for line in reversed(lines):
            if line.lower() in ('reading','read all','reading...'):
                return line + '\n'
        return ''

    def extract_path_from_fileinfo(self, info):
        for line in info.splitlines():
            if line.lower().startswith('location') and ':' in line:
                return line.split(':',1)[1].strip()
        return ''

    def open_file_in_bwe(self, hwnd, path):
        if not hwnd or not user32.IsWindow(hwnd): return False
        try:
            user32.ShowWindow(hwnd, SW_RESTORE); user32.SetForegroundWindow(hwnd)
            time.sleep(.7)
            self.hotkey_ctrl_o()
            time.sleep(1.0)
            self.type_text_foreground(path)
            self.key_event(VK_RETURN, True); self.key_event(VK_RETURN, False)
            return True
        except Exception:
            return False

    def hotkey_ctrl_o(self):
        VK_CONTROL=0x11; VK_O=0x4F
        self.key_event(VK_CONTROL, True); self.key_event(VK_O, True); self.key_event(VK_O, False); self.key_event(VK_CONTROL, False)

    def type_text_foreground(self,text):
        for ch in text:
            vk=user32.VkKeyScanW(ord(ch))
            if vk == -1: continue
            mods=(vk >> 8) & 0xff; base=vk & 0xff
            if mods & 1: self.key_event(0x10, True)
            self.key_event(base, True); self.key_event(base, False)
            if mods & 1: self.key_event(0x10, False)

    def send_foreground_keys(self,hwnd,text):
        if not hwnd or not user32.IsWindow(hwnd): return False
        try:
            user32.ShowWindow(hwnd, SW_RESTORE); user32.SetForegroundWindow(hwnd)
            time.sleep(.4)
            # simple keyboard injection for BwE GUI; no claim of completion, only command dispatch.
            for ch in text:
                vk=user32.VkKeyScanW(ord(ch)) & 0xff
                self.key_event(vk, True); self.key_event(vk, False)
            self.key_event(VK_RETURN, True); self.key_event(VK_RETURN, False)
            return True
        except Exception: return False

    def key_event(self,vk,down):
        class KEYBDINPUT(ctypes.Structure):
            _fields_=[('wVk',wintypes.WORD),('wScan',wintypes.WORD),('dwFlags',wintypes.DWORD),('time',wintypes.DWORD),('dwExtraInfo',ctypes.c_void_p)]
        class INPUT(ctypes.Structure):
            _fields_=[('type',wintypes.DWORD),('ki',KEYBDINPUT)]
        KEYEVENTF_KEYUP=0x0002
        inp=INPUT(); inp.type=1; inp.ki=KEYBDINPUT(vk,0,KEYEVENTF_KEYUP if not down else 0,0,None)
        user32.SendInput(1,ctypes.byref(inp),ctypes.sizeof(inp))

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

    def set_read_status(self, s):
        # Keep one live read-status line instead of appending every console refresh.
        self.log.tag_config('read_status', foreground='#e0c16b')
        ranges=self.log.tag_ranges('read_status')
        if ranges:
            self.log.delete(ranges[0], ranges[1])
        self.log.insert('end', '[READ FULL] ' + s + '\n', 'read_status')
        self.log.see('end')

    def start_spinner(self):
        self.spinner_index=0
        self.spinner_running=True
        self.animate_spinner()

    def stop_spinner(self):
        self.spinner_running=False

    def animate_spinner(self):
        if not getattr(self,'spinner_running',False): return
        frames='|/-\\'
        ch=frames[self.spinner_index % len(frames)]
        self.status.config(text='READ FULL berjalan ' + ch)
        self.spinner_index += 1
        self.root.after(180,self.animate_spinner)

    def append_read(self, s):
        self.log.insert('end', s if s.endswith('\n') else s+'\n'); self.log.see('end')

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
                elif isinstance(s, tuple) and s[0]=='__READ_START__':
                    self.set_read_status(s[1])
                    self.start_spinner()
                elif isinstance(s, tuple) and s[0]=='__READ__':
                    self.set_read_status(s[1].strip())
                elif isinstance(s, tuple) and s[0]=='__READ_DONE__':
                    self.set_read_status(s[1])
                    self.stop_spinner()
                elif isinstance(s, tuple) and s[0]=='__FILEINFO__':
                    self.append_read('\n[FILE INFORMATION]\n'+s[1])
                else:
                    self.w(s)
        except queue.Empty: pass
        self.root.after(100,self.pump)

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
