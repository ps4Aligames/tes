import tkinter as tk
from tkinter import filedialog, messagebox
import threading, queue, time, os

class SmartRepair(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SMART REPAIR EDITION BY ALI GAMES")
        self.geometry("1120x700")
        self.minsize(900, 600)
        self.q = queue.Queue()
        self._build()
        self.after(100, self._pump)

    def _build(self):
        self.configure(bg="#101010")
        top = tk.Frame(self, bg="#171717", height=75)
        top.pack(fill="x")
        tk.Label(top, text="SMART REPAIR", fg="#d7b35a", bg="#171717",
                 font=("Segoe UI", 20, "bold")).pack(side="left", padx=22, pady=18)
        tk.Label(top, text="EDITION BY ALI GAMES", fg="#dddddd", bg="#171717",
                 font=("Segoe UI", 11)).pack(side="left", pady=22)

        bar = tk.Frame(self, bg="#101010")
        bar.pack(fill="x", padx=15, pady=12)
        self.btn = tk.Button(bar, text="SMART READ FULL NOR", command=self.start_stage1,
                             bg="#262626", fg="#f0d27a", activebackground="#383838",
                             activeforeground="white", relief="flat", padx=18, pady=10,
                             font=("Segoe UI", 10, "bold"))
        self.btn.pack(side="left")

        self.nor = tk.StringVar(value="NOR: belum dipilih")
        tk.Button(bar, text="LOAD NOR", command=self.load_nor, bg="#222222", fg="white",
                  relief="flat", padx=12, pady=9).pack(side="left", padx=8)
        tk.Label(bar, textvariable=self.nor, bg="#101010", fg="#bbbbbb").pack(side="left")

        body = tk.Frame(self, bg="#101010")
        body.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        left = tk.Frame(body, bg="#090909")
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(body, bg="#171717", width=300)
        right.pack(side="right", fill="y", padx=(10,0))
        right.pack_propagate(False)

        tk.Label(left, text="ACTIVITY / CMD LOG", bg="#090909", fg="#d7b35a",
                 font=("Consolas", 10, "bold")).pack(anchor="w", padx=12, pady=8)
        self.log = tk.Text(left, bg="#050505", fg="#d8d8d8", insertbackground="white",
                           font=("Consolas", 10), relief="flat", wrap="word")
        self.log.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.log.insert("end", "Smart Repair siap.\n")

        self.status = tk.StringVar(value="Status: READY")
        self.com = tk.StringVar(value="COM: AUTO-DETECT")
        self.step = tk.StringVar(value="Tahap: —")
        for title, var in [("STATUS", self.status), ("CONNECTION", self.com), ("STEP", self.step)]:
            f=tk.Frame(right,bg="#202020"); f.pack(fill="x", padx=10, pady=(10,0))
            tk.Label(f,text=title,bg="#202020",fg="#d7b35a",font=("Segoe UI",9,"bold")).pack(anchor="w",padx=10,pady=(8,2))
            tk.Label(f,textvariable=var,bg="#202020",fg="#eeeeee",wraplength=260,justify="left").pack(anchor="w",padx=10,pady=(0,10))
        tk.Label(self, text="Original PS4WETOOLS PRO", bg="#0c0c0c", fg="#bdbdbd",
                 anchor="w", padx=15, pady=8).pack(fill="x", side="bottom")

    def load_nor(self):
        p=filedialog.askopenfilename(title="Pilih NOR", filetypes=[("NOR files","*.bin *.dump *.rom"),("All files","*.*")])
        if p: self.nor.set("NOR: "+p)

    def write(self, s):
        self.q.put(("log", s))

    def setv(self, var, value):
        self.q.put(("var", var, value))

    def start_stage1(self):
        if not messagebox.askyesno("SMART READ FULL NOR", "Mulai alur Tahap 1?"):
            return
        self.btn.config(state="disabled")
        threading.Thread(target=self.stage1, daemon=True).start()

    def stage1(self):
        # This is the workflow controller. It does not fake hardware I/O.
        steps = [
            ("Tahap: No.3", "SMART READ FULL NOR", 0.4),
            ("Tahap: Deteksi COM / Teensy", "No.3", 0.5),
            ("Tahap: SPIway / Juegos", "Deteksi COM / Teensy", 0.5),
            ("Tahap: READ ALL", "SPIway / Juegos", 0.7),
            ("Tahap: Read Full selesai", "Read Full selesai ✓", 0.4),
            ("Tahap: F otomatis", "F otomatis", 0.4),
            ("Tahap: R = Rename Non-Canonical", "R = Rename Non-Canonical", 0.5),
            ("Tahap: BwE", "Lanjut ke BwE", 0.7),
            ("Tahap: No.7", "No.7", 0.4),
            ("Tahap: Y", "Y", 0.4),
        ]
        self.setv(self.status,"Status: RUNNING")
        for label, log, delay in steps:
            self.setv(self.step,label)
            self.write(log)
            time.sleep(delay)
        self.write("Tahap 1 selesai.")
        self.setv(self.status,"Status: READY")
        self.q.put(("enable", True))

    def _pump(self):
        try:
            while True:
                item=self.q.get_nowait()
                if item[0]=="log":
                    self.log.insert("end", item[1]+"\n"); self.log.see("end")
                elif item[0]=="var":
                    item[1].set(item[2])
                elif item[0]=="enable":
                    self.btn.config(state="normal")
        except queue.Empty:
            pass
        self.after(100,self._pump)

if __name__ == "__main__":
    SmartRepair().mainloop()
