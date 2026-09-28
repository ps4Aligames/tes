import os
import subprocess
import threading
import time
import queue
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import serial.tools.list_ports
except Exception:
    serial = None

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
EXT = os.path.join(ROOT, "external")
WETOOL = os.path.join(EXT, "wetool.exe")
BWE = os.path.join(EXT, "BwE_PS4_NOR_Validator.exe")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("SMART REPAIR EDITION BY ALI GAMES")
        self.root.geometry("1120x680")
        self.root.configure(bg="#0d0d0d")
        self.proc = None
        self.q = queue.Queue()

        tk.Label(root, text="SMART REPAIR", fg="#d6b45a", bg="#0d0d0d",
                 font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=18, pady=(14,2))
        tk.Label(root, text="SMART REPAIR EDITION BY ALI GAMES  •  ORIGINAL PS4WETOOLS PRO",
                 fg="#b9b9b9", bg="#0d0d0d", font=("Segoe UI", 9)).pack(anchor="w", padx=20)

        bar = tk.Frame(root, bg="#151515")
        bar.pack(fill="x", padx=16, pady=12)
        self.buttons = []
        labels = [
            ("1  SMART READ FULL NOR", self.stage1),
            ("2  WIRATE NOR FULL PS4", self.not_ready),
            ("3  SMART PATCH WIRATE NOR", self.not_ready),
            ("4  SMART SYSCON PATCH", self.not_ready),
            ("5  SMART SYSCON REBUILD", self.not_ready),
        ]
        for text, cmd in labels:
            b = tk.Button(bar, text=text, command=cmd, bg="#202020", fg="#e6e6e6",
                          activebackground="#303030", activeforeground="#ffffff",
                          relief="flat", padx=10, pady=9)
            b.pack(side="left", padx=4, pady=8)
            self.buttons.append(b)

        body = tk.Frame(root, bg="#0d0d0d")
        body.pack(fill="both", expand=True, padx=16)
        left = tk.Frame(body, bg="#090909")
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(body, bg="#151515", width=300)
        right.pack(side="right", fill="y", padx=(12,0))
        right.pack_propagate(False)

        tk.Label(left, text="ACTIVITY / NATIVE TOOL OUTPUT", bg="#090909", fg="#d6b45a",
                 font=("Consolas", 10, "bold")).pack(anchor="w", padx=10, pady=8)
        self.log = tk.Text(left, bg="#050505", fg="#d9d9d9", insertbackground="white",
                           font=("Consolas", 10), relief="flat")
        self.log.pack(fill="both", expand=True, padx=8, pady=(0,8))

        tk.Label(right, text="CONNECTION", bg="#151515", fg="#d6b45a",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(14,6))
        self.com = tk.Label(right, text="Scanning COM...", bg="#151515", fg="#ddd",
                            justify="left", anchor="w")
        self.com.pack(fill="x", padx=14)
        tk.Button(right, text="REFRESH COM", command=self.scan_com,
                  bg="#242424", fg="white", relief="flat").pack(fill="x", padx=14, pady=10)

        tk.Label(right, text="TOOLS", bg="#151515", fg="#d6b45a",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(12,6))
        tk.Button(right, text="OPEN ORIGINAL WETOOL", command=self.open_wetool,
                  bg="#242424", fg="white", relief="flat").pack(fill="x", padx=14, pady=4)
        tk.Button(right, text="OPEN ORIGINAL BwE", command=self.open_bwe,
                  bg="#242424", fg="white", relief="flat").pack(fill="x", padx=14, pady=4)

        tk.Label(right, text="IMPORTANT", bg="#151515", fg="#d6b45a",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(18,6))
        tk.Label(right, text="Smart Repair does not emulate NOR reading.\n"
                             "The supplied original WETOOL and BwE executables remain the workers.\n"
                             "SPIway HEX is firmware for the Teensy workflow.",
                 bg="#151515", fg="#aaa", justify="left", wraplength=260).pack(fill="x", padx=14)

        self.scan_com()
        self.write("Controller started. Using the ORIGINAL supplied WETOOL/BwE files.")
        self.write("Stage 1 target: No.3 → COM/Teensy → SPIway/Juegos → READ ALL → F → R (Rename Non-Canonical) → BwE → No.7 → Y.")
        self.root.after(100, self.drain)

    def write(self, s):
        self.log.insert("end", s + "\n")
        self.log.see("end")

    def drain(self):
        try:
            while True:
                self.write(self.q.get_nowait())
        except queue.Empty:
            pass
        self.root.after(100, self.drain)

    def scan_com(self):
        if serial is None:
            self.com.config(text="pyserial not installed")
            return
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            self.com.config(text="No COM/Teensy detected")
            self.write("COM scan: no serial ports detected.")
        else:
            lines = [f"{p.device}  {p.description or ''}".strip() for p in ports]
            self.com.config(text="\n".join(lines))
            self.write("COM scan: " + " | ".join(lines))

    def open_wetool(self):
        if not os.path.exists(WETOOL):
            messagebox.showerror("WETOOL", "external/wetool.exe not found")
            return
        try:
            subprocess.Popen([WETOOL], cwd=EXT)
            self.write("Started ORIGINAL WETOOL: " + WETOOL)
        except Exception as e:
            self.write("WETOOL launch error: " + repr(e))

    def open_bwe(self):
        if not os.path.exists(BWE):
            messagebox.showerror("BwE", "external/BwE_PS4_NOR_Validator.exe not found")
            return
        try:
            subprocess.Popen([BWE], cwd=EXT)
            self.write("Started ORIGINAL BwE: " + BWE)
        except Exception as e:
            self.write("BwE launch error: " + repr(e))

    def stage1(self):
        if not os.path.exists(WETOOL):
            messagebox.showerror("Stage 1", "Original WETOOL missing.")
            return
        threading.Thread(target=self.stage1_worker, daemon=True).start()

    def stage1_worker(self):
        self.q.put("SMART READ FULL NOR: starting native-controller workflow.")
        self.q.put("Mempersiapkan koneksi...")
        self.scan_com()
        try:
            # Deliberately launch the real WETOOL. No fake READ ALL/NOR data is generated.
            self.proc = subprocess.Popen([WETOOL], cwd=EXT,
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True,
                                         bufsize=1)
            self.q.put("WETOOL asli dijalankan.")
            self.q.put("Membuka No.3...")
            # We only send the menu selector that is documented by the agreed workflow.
            # Subsequent hardware actions stay inside the original WETOOL so the controller
            # cannot fabricate a NOR result.
            try:
                self.proc.stdin.write("3\n")
                self.proc.stdin.flush()
                self.q.put("Perintah No.3 dikirim ke WETOOL asli.")
            except Exception as e:
                self.q.put("Tidak dapat mengirim No.3 via stdin: " + repr(e))
            # Stream native output if the original tool exposes it.
            deadline = time.time() + 8
            while time.time() < deadline and self.proc.poll() is None:
                line = self.proc.stdout.readline()
                if line:
                    self.q.put("[WETOOL] " + line.rstrip())
                else:
                    time.sleep(0.05)
            self.q.put("Menunggu interaksi/native workflow WETOOL; tidak membuat hasil NOR palsu.")
        except Exception as e:
            self.q.put("Stage 1 launch error: " + repr(e))

    def not_ready(self):
        messagebox.showinfo("Native controller", "Stage ini belum diaktifkan karena selector native WETOOL belum diverifikasi. Tidak ada simulasi yang dijalankan.")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
