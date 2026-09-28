SMART REPAIR - WETOOL CONTROLLER TEST 3

Tujuan test:
1. Jalankan WETOOL asli.
2. Cari HWND WETOOL berdasarkan PID.
3. Aktifkan WETOOL ke foreground.
4. Kirim angka 3 + ENTER melalui Win32 SendInput.
5. Tunggu 2 detik.
6. Kirim angka 1 + ENTER melalui Win32 SendInput.

Test ini TIDAK membuat engine READ FULL sendiri.
READ FULL belum dipanggil otomatis; test hanya membuktikan jalur input controller.

Catatan: pada TEST 3 WETOOL sengaja terlihat selama pengujian agar mudah dibuktikan bahwa perintah benar-benar masuk. Jika ini berhasil, tahap berikutnya baru kita ubah agar WETOOL diminimalkan/background.
