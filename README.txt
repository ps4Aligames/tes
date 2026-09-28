SMART REPAIR EDITION BY ALI GAMES - WETOOL CONTROLLER TEST

Tujuan versi ini:
Smart Repair hanya menjadi controller untuk wetool.exe asli.
Tidak membuat mesin READ NOR sendiri dan tidak memilih COM secara manual.

Tes otomatis:
1. Jalankan WETOOL hidden/background.
2. Deteksi window WETOOL dengan Windows UI Automation.
3. Coba kirim NO. 3.
4. Tunggu lalu coba kirim NO. 1.
5. Baca kontrol/menu yang benar-benar terlihat oleh UI Automation.

Catatan:
Versi ini adalah diagnostic controller. Jika WETOOL menggunakan kontrol custom/terenkripsi yang tidak dapat dikendalikan UI Automation, log akan menunjukkan keterbatasannya. Jangan menganggap READ FULL sudah otomatis sebelum hasil tes membuktikan bahwa menu WETOOL benar-benar menerima perintah.

Firmware acuan tersedia di external/spiway_v0.60_teensy2.0.hex.
