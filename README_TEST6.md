# Smart Repair Controller Test 6

Alur baru:

START
-> jalankan WETOOL
-> cari HWND
-> tunggu 1 detik
-> kirim 3
-> baca Version sampai Flash config
-> kirim 1
-> baca Version sampai Flash config
-> TEST 5 selesai
-> kirim f
-> kirim r
-> tunggu file hasil READ NOR muncul/berubah
-> jalankan BwE_PS4_NOR_Validator.exe
-> kirim path hasil NOR + ENTER
-> kirim 7
-> tunggu aktivitas console stabil
-> kirim y
-> TEST 6 selesai

Catatan:
- Build ini belum bisa diuji pada Windows di lingkungan pembuatan ini.
- BwE yang diberikan terproteksi Themida dan format prompt interaktifnya tidak dapat diverifikasi secara statis.
- Karena itu tahap LOAD mengasumsikan BwE menerima path file NOR sebagai input pertama setelah start.
- Jika build BwE meminta tombol/menu LOAD terlebih dahulu, satu langkah input perlu disesuaikan setelah diuji pada PC Windows.
