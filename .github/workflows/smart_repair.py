import os
import sys
import time
import platform
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import serial
    from serial.tools import list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


APP_NAME = "Smart Repair Safe Read"
APP_VERSION = "1.0.0"


class SmartRepairApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("760x540")
        self.root.minsize(680, 480)

        self.serial_conn = None
        self.stop_monitor = False
        self.monitor_thread = None
        self.last_ports = []

        self.status_var = tk.StringVar(value="Menunggu perangkat...")
        self.com_var = tk.StringVar(value="Tidak terhubung")
        self.diagnosis_var = tk.StringVar(value="Belum ada diagnosis")
        self.platform_var = tk.StringVar(value=f"{platform.system()} {platform.release()}")

        self.build_ui()
        self.refresh_ports()
        self.start_monitor()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text=APP_NAME,
            font=("Segoe UI", 18, "bold")
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            main,
            text="Safe Read • COM/USB Detection • Diagnostic Log",
            font=("Segoe UI", 9)
        )
        subtitle.pack(anchor="w", pady=(0, 12))

        status_box = ttk.LabelFrame(main, text="Device Status", padding=12)
        status_box.pack(fill="x", pady=(0, 10))

        row1 = ttk.Frame(status_box)
        row1.pack(fill="x", pady=3)

        ttk.Label(row1, text="Status:", width=14).pack(side="left")
        self.status_label = ttk.Label(
            row1,
            textvariable=self.status_var,
            font=("Segoe UI", 10, "bold")
        )
        self.status_label.pack(side="left")

        row2 = ttk.Frame(status_box)
        row2.pack(fill="x", pady=3)

        ttk.Label(row2, text="USB / COM:", width=14).pack(side="left")
        ttk.Label(
            row2,
            textvariable=self.com_var,
            font=("Segoe UI", 10, "bold")
        ).pack(side="left")

        row3 = ttk.Frame(status_box)
        row3.pack(fill="x", pady=3)

        ttk.Label(row3, text="System:", width=14).pack(side="left")
        ttk.Label(row3, textvariable=self.platform_var).pack(side="left")

        controls = ttk.Frame(main)
        controls.pack(fill="x", pady=(0, 10))

        ttk.Label(controls, text="COM Port:").pack(side="left")

        self.port_combo = ttk.Combobox(
            controls,
            width=25,
            state="readonly"
        )
        self.port_combo.pack(side="left", padx=8)

        ttk.Button(
            controls,
            text="Refresh",
            command=self.refresh_ports
        ).pack(side="left", padx=3)

        ttk.Button(
            controls,
            text="Safe Read",
            command=self.safe_read
        ).pack(side="left", padx=3)

        ttk.Button(
            controls,
            text="Disconnect",
            command=self.disconnect
        ).pack(side="left", padx=3)

        diagnosis_box = ttk.LabelFrame(main, text="Diagnosis", padding=12)
        diagnosis_box.pack(fill="x", pady=(0, 10))

        ttk.Label(
            diagnosis_box,
            textvariable=self.diagnosis_var,
            wraplength=680,
            justify="left"
        ).pack(anchor="w")

        log_box = ttk.LabelFrame(main, text="Diagnostic Log", padding=8)
        log_box.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_box,
            height=12,
            wrap="word",
            font=("Consolas", 9)
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            log_box,
            orient="vertical",
            command=self.log_text.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        bottom = ttk.Frame(main)
        bottom.pack(fill="x", pady=(8, 0))

        ttk.Button(
            bottom,
            text="Save Log",
            command=self.save_log
        ).pack(side="left")

        ttk.Button(
            bottom,
            text="Clear Log",
            command=self.clear_log
        ).pack(side="left", padx=6)

        ttk.Label(
            bottom,
            text=f"{APP_NAME} {APP_VERSION} • READ ONLY",
        ).pack(side="right")

        self.log("Application started.")
        self.log("Safe Read mode aktif. Tidak ada operasi write/erase/flash.")

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}\n"

        def append():
            self.log_text.insert("end", line)
            self.log_text.see("end")

        if self.root.winfo_exists():
            self.root.after(0, append)

    def get_ports(self):
        if not SERIAL_AVAILABLE:
            return []

        try:
            return list(list_ports.comports())
        except Exception as exc:
            self.log(f"ERROR membaca daftar COM: {exc}")
            return []

    def refresh_ports(self):
        ports = self.get_ports()
        self.last_ports = ports

        values = []
        for port in ports:
            description = port.description or "Unknown device"
            values.append(f"{port.device} - {description}")

        self.port_combo["values"] = values

        if values:
            self.port_combo.current(0)
            self.status_var.set("Perangkat COM terdeteksi")
            self.com_var.set(values[0])
            self.diagnosis_var.set(
                "COM terdeteksi. Pilih port yang sesuai lalu gunakan Safe Read."
            )
            self.log("COM device terdeteksi: " + ", ".join(p.device for p in ports))
        else:
            self.port_combo.set("")
            self.status_var.set("USB/COM menunggu...")
            self.com_var.set("Tidak terhubung")
            self.diagnosis_var.set(
                "Belum ada COM terdeteksi. Periksa kabel USB, driver, dan perangkat."
            )

    def start_monitor(self):
        self.stop_monitor = False
        self.monitor_thread = threading.Thread(
            target=self.monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()

    def monitor_loop(self):
        previous = set()

        while not self.stop_monitor:
            try:
                ports = self.get_ports()
                current = {p.device for p in ports}

                if current != previous:
                    previous = current
                    self.root.after(0, self.refresh_ports)

            except Exception:
                pass

            time.sleep(2)

    def selected_device(self):
        selection = self.port_combo.get().strip()

        if not selection:
            return None

        return selection.split(" - ", 1)[0].strip()

    def safe_read(self):
        if not SERIAL_AVAILABLE:
            self.status_var.set("PySerial belum tersedia")
            self.diagnosis_var.set(
                "Library pyserial belum terpasang. Jalankan: python -m pip install pyserial"
            )
            self.log("ERROR: pyserial tidak tersedia.")
            return

        port_name = self.selected_device()

        if not port_name:
            messagebox.showwarning(
                APP_NAME,
                "Pilih COM port terlebih dahulu."
            )
            return

        self.log(f"Safe Read dimulai pada {port_name}")
        self.status_var.set(f"Safe Read: {port_name}")
        self.diagnosis_var.set(
            "Mencoba membuka port dalam mode aman/read-only. "
            "Tidak mengirim perintah write, erase, atau flash."
        )

        threading.Thread(
            target=self._safe_read_worker,
            args=(port_name,),
            daemon=True
        ).start()

    def _safe_read_worker(self, port_name):
        connection = None

        try:
            connection = serial.Serial(
                port=port_name,
                baudrate=115200,
                timeout=1,
                write_timeout=1
            )

            self.serial_conn = connection

            self.root.after(
                0,
                lambda: self._connected(port_name)
            )

            # Deliberately do not transmit anything.
            time.sleep(0.3)

            waiting = connection.in_waiting
            data = b""

            if waiting:
                data = connection.read(waiting)

            if data:
                preview = data[:64].hex(" ")
                self.log(f"Data received ({len(data)} bytes): {preview}")
                self.root.after(
                    0,
                    lambda: self.diagnosis_var.set(
                        f"COM {port_name} aktif. Menerima {len(data)} byte."
                    )
                )
            else:
                self.log("Tidak ada data otomatis dari perangkat.")
                self.root.after(
                    0,
                    lambda: self.diagnosis_var.set(
                        f"COM {port_name} terbuka, tetapi tidak ada data otomatis."
                    )
                )

        except Exception as exc:
            error_text = str(exc)
            self.log(f"ERROR Safe Read {port_name}: {error_text}")

            self.root.after(
                0,
                lambda: self._connection_error(port_name, error_text)
            )

        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

            self.serial_conn = None

    def _connected(self, port_name):
        self.status_var.set(f"USB/COM TERHUBUNG: {port_name}")
        self.com_var.set(port_name)
        self.log(f"USB/COM terhubung: {port_name}")

    def _connection_error(self, port_name, error_text):
        self.status_var.set(f"COM gagal dibuka: {port_name}")
        self.diagnosis_var.set(
            "COM terdeteksi tetapi gagal dibuka. "
            "Kemungkinan port sedang digunakan aplikasi lain, "
            "driver bermasalah, atau perangkat terputus."
        )

    def disconnect(self):
        if self.serial_conn is not None:
            try:
                self.serial_conn.close()
            except Exception:
                pass

        self.serial_conn = None
        self.status_var.set("Terputus")
        self.com_var.set("Tidak terhubung")
        self.diagnosis_var.set("Perangkat telah diputus.")
        self.log("COM disconnected.")

    def save_log(self):
        filename = filedialog.asksaveasfilename(
            title="Save Diagnostic Log",
            defaultextension=".txt",
            filetypes=[
                ("Text file", "*.txt"),
                ("Log file", "*.log"),
                ("All files", "*.*")
            ],
            initialfile="Smart_Repair_Safe_Read.log"
        )

        if not filename:
            return

        try:
            text = self.log_text.get("1.0", "end-1c")

            with open(filename, "w", encoding="utf-8") as file:
                file.write(text)

            self.log(f"Log saved: {filename}")
            messagebox.showinfo(
                APP_NAME,
                "Diagnostic log berhasil disimpan."
            )

        except Exception as exc:
            messagebox.showerror(
                APP_NAME,
                f"Gagal menyimpan log:\n{exc}"
            )

    def clear_log(self):
        self.log_text.delete("1.0", "end")
        self.log("Log cleared.")

    def on_close(self):
        self.stop_monitor = True
        self.disconnect()
        self.root.destroy()


def main():
    root = tk.Tk()
    SmartRepairApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
