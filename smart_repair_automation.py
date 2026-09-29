import ctypes
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))

def log(s):
    print(time.strftime("[%H:%M:%S]"), s, flush=True)

def key(vk, name):
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
    log("Kirim: " + name)

def send_text(s):
    vk = {"1":0x31, "7":0x37, "F":0x46, "R":0x52, "Y":0x59}
    for c in s:
        key(vk[c.upper()], c.upper())
        time.sleep(0.15)

def com_ports():
    try:
        import serial.tools.list_ports
        return {p.device for p in serial.tools.list_ports.comports()}
    except Exception:
        return set()

def wait_for_com(timeout):
    log("Menunggu WETool mendeteksi COM...")
    start=time.time()
    initial=com_ports()
    while time.time()-start < timeout:
        ports=com_ports()
        if ports:
            log("COM terdeteksi: " + ", ".join(sorted(ports)))
            return True
        time.sleep(0.5)
    log("Timeout: COM belum terdeteksi.")
    return False

def main():
    wetool=os.path.join(ROOT,"external","wetool.exe")
    bwe=os.path.join(ROOT,"external","BWE.exe")
    if not os.path.isfile(wetool):
        log("wetool.exe tidak ditemukan.")
        return 1

    log("=== SMART REPAIR CONTROLLER / REAL AUTOMATION ===")
    log("Firmware yang disiapkan: spiway_v0.60_teensy2.0.hex")

    subprocess.Popen([wetool], cwd=os.path.dirname(wetool))
    time.sleep(1.5)

    # Tahap WETool: 3
    send_text("3")

    # WETool yang bertugas mendeteksi COM.
    if not wait_for_com(30):
        log("Proses dihentikan agar tidak mengirim perintah terlalu cepat.")
        return 2

    time.sleep(1.0)
    send_text("1")
    time.sleep(1.0)
    send_text("F")
    time.sleep(1.0)
    send_text("R")

    log("Tahap WETool selesai.")

    if not os.path.isfile(bwe):
        log("BWE.exe belum tersedia di external\\BWE.exe")
        log("Salin BWE.exe ke folder external lalu jalankan kembali.")
        return 3

    time.sleep(1.5)
    subprocess.Popen([bwe], cwd=os.path.dirname(bwe))
    time.sleep(1.5)
    send_text("7")
    time.sleep(1.0)
    send_text("Y")

    log("SELESAI: 3 -> COM -> 1 -> F -> R -> BWE -> 7 -> Y")
    return 0

if __name__ == "__main__":
    sys.exit(main())
