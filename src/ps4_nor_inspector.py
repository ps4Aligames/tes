import os, sys, time, threading, queue, hashlib, struct
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None

APP = "PS4 NOR Inspector v2"
READ_SIZE = 16 * 1024 * 1024

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP)
        self.geometry("820x620")
        self.minsize(720, 520)
        self.q = queue.Queue()
        self.stop_event = threading.Event()
        self.ser = None
        self.reading = False
        self._build()
        self.after(100, self._drain)
        self.refresh_ports()

    def _build(self):
        style = ttk.Style(self)
        try: style.theme_use('clam')
        except: pass
        top = ttk.Frame(self, padding=10); top.pack(fill='x')
        ttk.Label(top, text=APP, font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        ttk.Label(top, text='USB TTL / SPIWay-compatible workflow • diagnostic log', foreground='#555').pack(anchor='w')

        hw = ttk.LabelFrame(self, text='USB TTL / COM', padding=8); hw.pack(fill='x', padx=10, pady=5)
        self.port = tk.StringVar(); self.baud = tk.StringVar(value='115200')
        ttk.Label(hw, text='COM:').grid(row=0,column=0,sticky='w')
        self.combo = ttk.Combobox(hw, textvariable=self.port, width=18, state='readonly'); self.combo.grid(row=0,column=1,padx=5)
        ttk.Button(hw, text='Refresh COM', command=self.refresh_ports).grid(row=0,column=2,padx=5)
        ttk.Label(hw, text='Baud:').grid(row=0,column=3,padx=(20,0))
        ttk.Entry(hw, textvariable=self.baud, width=10).grid(row=0,column=4,padx=5)
        self.status = tk.StringVar(value='USB TTL: menunggu koneksi')
        ttk.Label(hw, textvariable=self.status).grid(row=0,column=5,padx=10,sticky='w')
        ttk.Button(hw, text='Connect', command=self.connect).grid(row=0,column=6,padx=3)
        ttk.Button(hw, text='Disconnect', command=self.disconnect).grid(row=0,column=7,padx=3)

        ops = ttk.LabelFrame(self, text='NOR Operations', padding=8); ops.pack(fill='x', padx=10, pady=5)
        self.btn_read = ttk.Button(ops, text='READ FULL NOR', command=self.start_read); self.btn_read.pack(side='left', padx=4)
        ttk.Button(ops, text='Stop', command=self.stop_read).pack(side='left', padx=4)
        ttk.Button(ops, text='Clear Log', command=self.clear_log).pack(side='left', padx=4)
        ttk.Button(ops, text='Save Log', command=self.save_log).pack(side='left', padx=4)
        ttk.Button(ops, text='Open NOR', command=self.open_nor).pack(side='left', padx=4)

        pb = ttk.Frame(self, padding=(10,3)); pb.pack(fill='x')
        self.progress = ttk.Progressbar(pb, mode='determinate', maximum=100); self.progress.pack(fill='x')
        self.pct = tk.StringVar(value='0%'); ttk.Label(pb, textvariable=self.pct).pack(anchor='e')

        lf = ttk.LabelFrame(self, text='Process Log', padding=6); lf.pack(fill='both', expand=True, padx=10, pady=5)
        self.log = tk.Text(lf, wrap='none', font=('Consolas', 10), bg='#111', fg='#ddd', insertbackground='white')
        sy = ttk.Scrollbar(lf, command=self.log.yview); self.log.configure(yscrollcommand=sy.set)
        self.log.pack(side='left', fill='both', expand=True); sy.pack(side='right', fill='y')
        self.write('=== PS4 NOR Inspector v2 ===')
        self.write('Pilih COM lalu Connect. READ FULL NOR memerlukan hardware/protokol yang sesuai.')

    def write(self, s):
        self.q.put(('log', s))

    def _drain(self):
        try:
            while True:
                typ, data = self.q.get_nowait()
                if typ == 'log':
                    self.log.insert('end', data + '\n'); self.log.see('end')
                elif typ == 'progress':
                    self.progress['value'] = data; self.pct.set(f'{data:.1f}%')
                elif typ == 'status': self.status.set(data)
                elif typ == 'done': self._finish(data)
        except queue.Empty: pass
        self.after(100, self._drain)

    def refresh_ports(self):
        if not list_ports:
            self.combo['values'] = []
            self.status.set('pyserial belum terpasang')
            return
        vals = [p.device for p in list_ports.comports()]
        self.combo['values'] = vals
        if vals and self.port.get() not in vals: self.port.set(vals[0])
        self.status.set('USB TTL: terdeteksi' if vals else 'USB TTL: menunggu koneksi')
        for p in list_ports.comports():
            self.write(f'COM detect: {p.device} | {p.description}')

    def connect(self):
        if not serial: messagebox.showerror('Dependency', 'pyserial belum terpasang. Jalankan pip install -r requirements.txt'); return
        if not self.port.get(): messagebox.showwarning('COM', 'Pilih COM terlebih dahulu.'); return
        try:
            self.ser = serial.Serial(self.port.get(), int(self.baud.get()), timeout=1)
            self.status.set(f'USB TTL: TERHUBUNG {self.port.get()}')
            self.write(f'[USB TTL] Connected: {self.port.get()} @ {self.baud.get()}')
        except Exception as e:
            self.status.set('USB TTL: gagal terhubung'); self.write(f'[ERROR] COM: {e}')

    def disconnect(self):
        if self.ser:
            try: self.ser.close()
            except: pass
        self.ser = None; self.status.set('USB TTL: menunggu koneksi'); self.write('[USB TTL] Disconnected')

    def start_read(self):
        if self.reading: return
        out = filedialog.asksaveasfilename(title='Simpan hasil FULL NOR', defaultextension='.bin', filetypes=[('BIN','*.bin')])
        if not out: return
        self.reading = True; self.stop_event.clear(); self.progress['value']=0
        self.btn_read.configure(state='disabled')
        threading.Thread(target=self._read_worker, args=(out,), daemon=True).start()

    def stop_read(self):
        if self.reading:
            self.stop_event.set(); self.write('[READ FULL NOR] Stop diminta...')

    def _read_worker(self, out):
        self.write('[READ FULL NOR] START')
        self.write(f'[READ FULL NOR] Target size: {READ_SIZE:,} bytes (16 MiB)')
        self.write('[READ FULL NOR] Checking COM / transport...')
        if not self.ser or not self.ser.is_open:
            self.write('[ERROR] COM belum terhubung. Tidak ada data hardware yang dibaca.')
            self.q.put(('done', False)); return
        self.write('[READ FULL NOR] COM connected. Hardware command sequence is adapter-specific.')
        self.write('[READ FULL NOR] Safety mode: no invented SPI command bytes are transmitted.')
        self.write('[READ FULL NOR] Untuk pembacaan nyata, isi protocol adapter harus disesuaikan dengan firmware SPIWay/Teensy Anda.')
        # Conservative transport test only: do not send unknown commands.
        try:
            with open(out, 'wb') as f:
                # Reserve an explicit placeholder file, never claim it is a valid dump.
                header = b'PS4NORI2_PLACEHOLDER\0'
                f.write(header)
            self.write('[READ FULL NOR] ABORTED: protocol adapter belum dikonfigurasi.')
            self.write(f'[READ FULL NOR] Placeholder saved: {out}')
        except Exception as e:
            self.write(f'[ERROR] Save: {e}')
        self.q.put(('done', False))

    def _finish(self, ok):
        self.reading=False; self.btn_read.configure(state='normal')
        if ok: self.write('[DONE] READ FULL NOR selesai.')

    def open_nor(self):
        p = filedialog.askopenfilename(filetypes=[('BIN','*.bin'),('All','*.*')])
        if not p: return
        try:
            size=os.path.getsize(p); sha=hashlib.sha256(Path(p).read_bytes()).hexdigest()
            self.write(f'[NOR] File: {p}'); self.write(f'[NOR] Size: {size:,} bytes'); self.write(f'[NOR] SHA-256: {sha}')
            if size not in (16*1024*1024, 8*1024*1024): self.write('[NOR] Warning: ukuran tidak umum untuk dump NOR.')
        except Exception as e: self.write(f'[ERROR] Open NOR: {e}')

    def clear_log(self): self.log.delete('1.0','end')
    def save_log(self):
        p=filedialog.asksaveasfilename(title='Save Log',defaultextension='.txt',filetypes=[('Text','*.txt')])
        if p:
            Path(p).write_text(self.log.get('1.0','end'),encoding='utf-8'); self.write(f'[LOG] Saved: {p}')

if __name__ == '__main__': App().mainloop()
