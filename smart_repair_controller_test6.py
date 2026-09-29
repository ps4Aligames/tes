import ctypes
from ctypes import wintypes
import os
import sys
import time
import threading
from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import messagebox

# Test 6 workflow:
# START
#   -> WETOOL
#   -> HWND
#   -> "3"
#   -> read Version..Flash config
#   -> "1"
#   -> read Version..Flash config
#   -> "f"
#   -> "r"
#   -> detect newly-created NOR file
#   -> start BwE PS4 NOR Validator
#   -> type NOR path + ENTER
#   -> "7"
#   -> wait for validator activity to finish
#   -> "y"
#
# NOTE: The exact interactive prompt used by the supplied BwE build could not
# be verified on this non-Windows build environment. The load step therefore
# sends the NOR path as the first console input, followed by 7 and y.

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

CREATE_NEW_CONSOLE = 0x00000010
STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
KEY_EVENT = 0x0001
VK_RETURN = 0x0D

class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("bKeyDown", wintypes.BOOL),
        ("wRepeatCount", wintypes.WORD),
        ("wVirtualKeyCode", wintypes.WORD),
        ("wVirtualScanCode", wintypes.WORD),
        ("UnicodeChar", wintypes.WCHAR),
        ("dwControlKeyState", wintypes.DWORD),
    ]

class INPUT_RECORD(ctypes.Structure):
    _fields_ = [
        ("EventType", wintypes.WORD),
        ("KeyEvent", KEY_EVENT_RECORD),
    ]

class COORD(ctypes.Structure):
    _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

class SMALL_RECT(ctypes.Structure):
    _fields_ = [
        ("Left", wintypes.SHORT), ("Top", wintypes.SHORT),
        ("Right", wintypes.SHORT), ("Bottom", wintypes.SHORT)
    ]

class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", wintypes.WORD),
        ("srWindow", SMALL_RECT),
        ("dwMaximumWindowSize", COORD),
    ]

kernel32.AttachConsole.argtypes = [wintypes.DWORD]
kernel32.AttachConsole.restype = wintypes.BOOL
kernel32.FreeConsole.argtypes = []
kernel32.FreeConsole.restype = wintypes.BOOL
kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
kernel32.GetStdHandle.restype = wintypes.HANDLE
kernel32.WriteConsoleInputW.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(INPUT_RECORD), wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD)
]
kernel32.WriteConsoleInputW.restype = wintypes.BOOL
kernel32.GetConsoleScreenBufferInfo.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(CONSOLE_SCREEN_BUFFER_INFO)
]
kernel32.GetConsoleScreenBufferInfo.restype = wintypes.BOOL
kernel32.ReadConsoleOutputCharacterW.argtypes = [
    wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, COORD,
    ctypes.POINTER(wintypes.DWORD)
]
kernel32.ReadConsoleOutputCharacterW.restype = wintypes.BOOL

def app_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

ROOT = app_root()
EXTERNAL = ROOT / "external"
WETOOL = EXTERNAL / "wetool.exe"
BWE = EXTERNAL / "BwE_PS4_NOR_Validator.exe"

def find_windows_for_pid(pid):
    found = []
    @EnumWindowsProc
    def cb(hwnd, _):
        p = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True
    user32.EnumWindows(cb, 0)
    return found

def console_command(pid, text):
    """Inject text + ENTER into the target process's console input."""
    if not kernel32.AttachConsole(pid):
        return False

    try:
        h_in = kernel32.GetStdHandle(STD_INPUT_HANDLE)
        if not h_in or h_in == wintypes.HANDLE(-1).value:
            return False

        records = []
        for ch in str(text):
            vk = user32.VkKeyScanW(ord(ch))
            if vk == -1:
                continue
            vk_code = vk & 0xFF
            scan = user32.MapVirtualKeyW(vk_code, 0)
            for down in (True, False):
                rec = INPUT_RECORD()
                rec.EventType = KEY_EVENT
                rec.KeyEvent.bKeyDown = down
                rec.KeyEvent.wRepeatCount = 1
                rec.KeyEvent.wVirtualKeyCode = vk_code
                rec.KeyEvent.wVirtualScanCode = scan
                rec.KeyEvent.UnicodeChar = ch
                rec.KeyEvent.dwControlKeyState = 0
                records.append(rec)

        # ENTER
        for down in (True, False):
            rec = INPUT_RECORD()
            rec.EventType = KEY_EVENT
            rec.KeyEvent.bKeyDown = down
            rec.KeyEvent.wRepeatCount = 1
            rec.KeyEvent.wVirtualKeyCode = VK_RETURN
            rec.KeyEvent.wVirtualScanCode = user32.MapVirtualKeyW(VK_RETURN, 0)
            rec.KeyEvent.UnicodeChar = "\r"
            rec.KeyEvent.dwControlKeyState = 0
            records.append(rec)

        arr = (INPUT_RECORD * len(records))(*records)
        written = wintypes.DWORD()
        return bool(kernel32.WriteConsoleInputW(h_in, arr, len(records), ctypes.byref(written)))
    finally:
        kernel32.FreeConsole()

def read_console(pid):
    """Read visible console buffer text from a target process."""
    if not kernel32.AttachConsole(pid):
        return ""

    try:
        h_out = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        if not h_out or h_out == wintypes.HANDLE(-1).value:
            return ""
        info = CONSOLE_SCREEN_BUFFER_INFO()
        if not kernel32.GetConsoleScreenBufferInfo(h_out, ctypes.byref(info)):
            return ""

        width = max(1, info.dwSize.X)
        height = max(1, info.dwSize.Y)
        # Limit memory while still covering a normal console.
        height = min(height, 200)
        buf = ctypes.create_unicode_buffer(width * height)
        read = wintypes.DWORD()
        ok = kernel32.ReadConsoleOutputCharacterW(
            h_out, buf, width * height, COORD(0, 0), ctypes.byref(read)
        )
        if not ok:
            return ""
        raw = buf[:read.value]
        lines = [raw[i:i+width].rstrip() for i in range(0, len(raw), width)]
        return "\n".join(x for x in lines if x).strip()
    finally:
        kernel32.FreeConsole()

def filter_version_to_flash(text):
    lines = text.splitlines()
    start = next((i for i, x in enumerate(lines) if "Version" in x), None)
    if start is None:
        return text.strip()
    end = next((i for i in range(start, len(lines)) if "Flash config" in lines[i]), None)
    if end is None:
        return "\n".join(lines[start:]).strip()
    return "\n".join(lines[start:end+1]).strip()

def snapshot_nor_files():
    exts = {".bin", ".nor", ".dump", ".rom", ".img"}
    result = {}
    for base in (ROOT, EXTERNAL):
        if not base.exists():
            continue
        for p in base.iterdir():
            if p.is_file() and p.suffix.lower() in exts:
                try:
                    result[str(p.resolve())] = (p.stat().st_mtime_ns, p.stat().st_size)
                except OSError:
                    pass
    return result

def wait_for_new_nor(before, timeout=180):
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = snapshot_nor_files()
        candidates = []
        for path, meta in current.items():
            if path not in before or meta != before[path]:
                candidates.append((meta[0], Path(path)))
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            p = candidates[0][1]
            # Give the writer a moment to finish and size to settle.
            last = -1
            stable = 0
            while stable < 3 and time.time() < deadline:
                try:
                    size = p.stat().st_size
                except OSError:
                    size = -1
                if size == last and size > 0:
                    stable += 1
                else:
                    stable = 0
                    last = size
                time.sleep(0.5)
            if p.exists() and p.stat().st_size > 0:
                return p
        time.sleep(1.0)
    return None

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("SMART REPAIR EDITION BY ALI GAMES - TEST 6")
        self.root.geometry("760x560")
        self.root.configure(bg="#101010")

        self.running = False
        self.wetool_proc = None
        self.bwe_proc = None

        tk.Label(
            root, text="SMART REPAIR CONTROLLER TEST 6",
            font=("Segoe UI", 18, "bold"), fg="white", bg="#101010"
        ).pack(pady=(18, 6))

        self.status = tk.Label(
            root, text="READY", font=("Segoe UI", 11, "bold"),
            fg="#dddddd", bg="#101010"
        )
        self.status.pack(pady=4)

        self.log = tk.Text(
            root, height=23, bg="#080808", fg="#dddddd",
            insertbackground="white", relief="flat", font=("Consolas", 10)
        )
        self.log.pack(fill="both", expand=True, padx=18, pady=12)

        buttons = tk.Frame(root, bg="#101010")
        buttons.pack(pady=(0, 18))
        tk.Button(
            buttons, text="START", width=14, command=self.start,
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=6)
        tk.Button(
            buttons, text="STOP", width=14, command=self.stop,
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=6)

    def write(self, msg):
        self.root.after(0, self._write, msg)

    def _write(self, msg):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def set_status(self, msg):
        self.root.after(0, lambda: self.status.config(text=msg))

    def start(self):
        if self.running:
            return
        self.running = True
        self.log.delete("1.0", "end")
        threading.Thread(target=self.worker, daemon=True).start()

    def stop(self):
        self.running = False
        for proc in (self.bwe_proc, self.wetool_proc):
            try:
                if proc and proc.poll() is None:
                    proc.terminate()
            except Exception:
                pass
        self.write("[SMART] STOP requested.")
        self.set_status("STOPPED")

    def launch_console(self, exe, cwd):
        return subprocess.Popen(
            [str(exe)],
            cwd=str(cwd),
            creationflags=CREATE_NEW_CONSOLE
        )

    def wait_pid_window(self, proc, timeout=20):
        deadline = time.time() + timeout
        while time.time() < deadline and self.running:
            if proc.poll() is not None:
                return None
            wins = find_windows_for_pid(proc.pid)
            if wins:
                return wins[0]
            time.sleep(0.25)
        return None

    def command_and_log(self, pid, cmd, wait=1.0, filtered=True):
        self.write(f"[SMART] WETOOL <- {cmd}")
        ok = console_command(pid, cmd)
        if not ok:
            self.write(f"[SMART] GAGAL mengirim '{cmd}'.")
            return ""
        time.sleep(wait)
        text = read_console(pid)
        if filtered:
            shown = filter_version_to_flash(text)
        else:
            shown = text
        if shown:
            self.write(shown)
        return text

    def worker(self):
        try:
            if not WETOOL.exists():
                raise FileNotFoundError(f"WETOOL tidak ditemukan: {WETOOL}")
            if not BWE.exists():
                raise FileNotFoundError(f"BwE tidak ditemukan: {BWE}")

            self.set_status("RUNNING WETOOL")
            self.write("[SMART] START -> menjalankan WETOOL...")
            before_nor = snapshot_nor_files()

            self.wetool_proc = self.launch_console(WETOOL, EXTERNAL)
            hwnd = self.wait_pid_window(self.wetool_proc)
            if not hwnd:
                raise RuntimeError("HWND WETOOL tidak ditemukan.")
            self.write(f"[SMART] HWND WETOOL ditemukan: 0x{hwnd:X}")

            time.sleep(1.0)

            # Existing Test 5 path.
            self.set_status("TEST 5: COMMAND 3")
            self.command_and_log(self.wetool_proc.pid, "3", wait=1.0, filtered=True)

            self.set_status("TEST 5: COMMAND 1")
            self.command_and_log(self.wetool_proc.pid, "1", wait=1.0, filtered=True)

            self.write("[SMART] TEST 5 selesai.")

            # New requested path.
            self.set_status("WETOOL: F")
            self.command_and_log(self.wetool_proc.pid, "f", wait=1.0, filtered=False)

            self.set_status("WETOOL: READ NOR")
            self.write("[SMART] WETOOL <- r")
            if not console_command(self.wetool_proc.pid, "r"):
                raise RuntimeError("Gagal mengirim command r ke WETOOL.")

            # Read NOR can take considerably longer than the first commands.
            nor = wait_for_new_nor(before_nor, timeout=180)
            if nor is None:
                # One final console capture helps diagnose a prompt/error.
                txt = read_console(self.wetool_proc.pid)
                if txt:
                    self.write(txt)
                raise RuntimeError("NOR file baru/perubahan tidak terdeteksi dalam 180 detik.")

            self.write(f"[SMART] READ NOR selesai: {nor}")
            self.set_status("BWE: LOAD NOR")

            # Launch BwE as a console app.
            self.bwe_proc = self.launch_console(BWE, EXTERNAL)
            self.wait_pid_window(self.bwe_proc, timeout=10)
            time.sleep(1.5)

            # Interactive load: type the NOR path and press ENTER.
            nor_text = str(nor.resolve())
            self.write(f"[SMART] BwE <- load: {nor_text}")
            if not console_command(self.bwe_proc.pid, nor_text):
                raise RuntimeError("Gagal mengirim path NOR ke BwE.")

            time.sleep(2.0)

            self.set_status("BWE: COMMAND 7")
            self.write("[SMART] BwE <- 7")
            if not console_command(self.bwe_proc.pid, "7"):
                raise RuntimeError("Gagal mengirim command 7 ke BwE.")

            # Wait for console activity to settle, while allowing STOP.
            last = ""
            stable_since = time.time()
            deadline = time.time() + 180
            while self.running and time.time() < deadline:
                txt = read_console(self.bwe_proc.pid)
                if txt != last:
                    last = txt
                    stable_since = time.time()
                    if txt:
                        self.write(txt[-4000:])
                # Do not assume a specific English completion string.
                # "stable" is used only as a fallback for this protected build.
                if time.time() - stable_since >= 4.0:
                    break
                if self.bwe_proc.poll() is not None:
                    break
                time.sleep(1.0)

            self.set_status("BWE: Y")
            self.write("[SMART] BwE proses No. 7 selesai/stabil -> mengirim y")
            if not console_command(self.bwe_proc.pid, "y"):
                raise RuntimeError("Gagal mengirim y ke BwE.")

            time.sleep(1.0)
            final = read_console(self.bwe_proc.pid)
            if final:
                self.write(final[-6000:])

            self.set_status("TEST 6 SELESAI")
            self.write("[SMART] ===== TEST 6 SELESAI =====")

        except Exception as e:
            self.set_status("ERROR")
            self.write(f"[SMART] ERROR: {e}")
        finally:
            self.running = False

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
