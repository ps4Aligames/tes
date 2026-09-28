import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess

try:
    from serial.tools import list_ports
except ImportError:
    list_ports = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT = os.path.join(ROOT, "external")
WETOOL = os.path.join(EXT, "wetool.exe")
BWE = os.path.join(EXT, "BwE_PS4_NOR_Validator.exe")

class App:
    def __init__(self, root):
        self.root = root
        root.title("SMART REPAIR EDITION BY ALI GAMES")
        root.geometry("1050x650")
        root.configure(bg="#0b0b0b")

        tk.Label(root, text="SMART REPAIR", bg="#0b0b0b", fg="#d6b45a",
                 font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=18, pady=(14,0))
        tk.Label(root, text="SMART REPAIR EDITION BY ALI GAMES",
                 bg="#0b0b0b", fg="#999999").pack(anchor="w", padx=20)

        top = tk.Frame(root, bg="#151515")
        top.pack(fill="x", padx=15, pady=12)
        self.read_btn = tk.Button(top, text="SMART READ FULL NOR",
                                  command=self.prepare_read, bg="#222222",
                                  fg="white", relief="flat", padx=16, pady=10)
        self.read_btn.pack(side="left", padx=6, pady=7)
        tk.Button(top, text="REFRESH COM", command=self.scan_com,
                  bg="#222222", fg="white", relief="flat",
                  padx=16, pady=10).pack(side="left", padx=6, pady=7)
        tk.Button(top, text="OPEN ORIGINAL WETOOL",
                  command=self.open_wetool, bg="#222222", fg="white",
                  relief="flat", padx=16, pady=10).pack(side="left", padx=6, pady=7)

        body = tk.Frame(root, bg="#0b0b0b")
        body.pack(fill="both", expand=True, padx=15, pady=(0,15))

        left = tk.Frame(body, bg="#050505")
        left.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="ACTIVITY LOG", bg="#050505", fg="#d6b45a",
                 font=("Consolas", 10, "bold")).pack(anchor="w", padx=10, pady=8)
        self.log = tk.Text(left, bg="#030303", fg="#dddddd",
                           insertbackground="white", font=("Consolas", 10),
                           relief="flat")
        self.log.pack(fill="both", expand=True, padx=8, pady=(0,8))

        right = tk.Frame(body, bg="#151515", width=280)
        right.pack(side="right", fill="y", padx=(12,0))
        right.pack_propagate(False)

        tk.Label(right, text="COM / TEENSY", bg="#151515", fg="#d6b45a",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(16,6))
        self.com_label = tk.Label(right, text="Scanning...",
                                  bg="#151515", fg="#dddddd",
                                  justify="left", anchor="w", wraplength=245)
        self.com_label.pack(fill="x", padx=14)

        tk.Label(right, text="SAFETY MODE", bg="#151515", fg="#d6b45a",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(25,6))
        tk.Label(right, text="READ preparation only.\n\n"
                             "No automatic WRITE.\n"
                             "No PATCH.\n"
                             "No blind keyboard commands.\n\n"
                             "Original WETOOL remains the worker.",
                 bg="#151515", fg="#aaaaaa", justify="left",
                 wraplength=245).pack(fill="x", padx=14)

        self.logmsg("SMART READ FULL NOR — SAFE PREPARATION MODE")
        self.logmsg("Tidak mengirim perintah ke hardware secara otomatis.")
        self.scan_com()

    def logmsg(self, s):
        self.log.insert("end", s + "\n")
        self.log.see("end")

    def scan_com(self):
        if list_ports is None:
            self.com_label.config(text="pyserial belum tersedia")
            self.logmsg("COM scan: pyserial belum tersedia.")
            return
        ports = list(list_ports.comports())
        if not ports:
            self.com_label.config(text="Tidak ada COM terdeteksi")
            self.logmsg("COM scan: tidak ada port serial.")
            return
        lines = [f"{p.device} — {p.description or 'Serial device'}" for p in ports]
        self.com_label.config(text="\n".join(lines))
        self.logmsg("COM terdeteksi: " + " | ".join(p.device for p in ports))

    def open_wetool(self):
        if not os.path.exists(WETOOL):
            messagebox.showerror("WETOOL", "wetool.exe tidak ditemukan di external/")
            return
        try:
            subprocess.Popen([WETOOL], cwd=EXT)
            self.logmsg("WETOOL ASLI dibuka.")
        except Exception as e:
            self.logmsg("Gagal membuka WETOOL: " + repr(e))

    def prepare_read(self):
        # This stage deliberately prepares and opens the real tool only.
        self.read_btn.config(state="disabled")
        threading.Thread(target=self.read_worker, daemon=True).start()

    def read_worker(self):
        self.logmsg("SMART READ FULL NOR")
        self.logmsg("1. Mendeteksi COM/Teensy...")
        self.scan_com()
        self.logmsg("2. Membuka WETOOL ASLI...")
        if not os.path.exists(WETOOL):
            self.logmsg("ERROR: wetool.exe tidak ditemukan.")
            self.read_btn.config(state="normal")
            return
        try:
            subprocess.Popen([WETOOL], cwd=EXT)
            self.logmsg("WETOOL ASLI sudah dibuka.")
            self.logmsg("3. Silakan jalankan No.3 dari WETOOL ASLI.")
            self.logmsg("4. Lanjutkan READ ALL dari menu native WETOOL.")
            self.logmsg("Smart Repair TIDAK mengirim tombol otomatis pada tahap ini.")
            self.logmsg("Menunggu hasil READ dari WETOOL.")
        except Exception as e:
            self.logmsg("ERROR WETOOL: " + repr(e))
        finally:
            self.read_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
