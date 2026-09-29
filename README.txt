SMART REPAIR CONTROLLER - TAHAP 1 REAL AUTOMATION

Urutan:
WETool -> 3 -> WETool mendeteksi COM -> 1 -> F -> R -> BWE -> 7 -> Y

WETool tidak digantikan. Program hanya menunggu COM yang terlihat di Windows
setelah WETool dijalankan, lalu melanjutkan urutan.

Firmware yang disertakan:
external/spiway_v0.60_teensy2.0.hex

BWE.exe belum disertakan karena belum ada pada ZIP yang diberikan.
Salin BWE.exe ke:
external\BWE.exe

Untuk menjalankan:
1. Install Python + pyserial:
   pip install -r requirements.txt
2. Jalankan START.bat.

Catatan:
- Pengiriman tombol diarahkan ke jendela yang sedang aktif.
- Jangan klik jendela lain selama otomasi berjalan.
- Uji dahulu tanpa melakukan operasi destruktif pada perangkat.
