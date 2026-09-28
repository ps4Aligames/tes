SMART REPAIR WETOOL CONTROLLER TEST 7

Perubahan utama:
- Info chip Version -> Flash config ditampilkan SATU KALI saja.
- Saat READ FULL berjalan, Smart Repair hanya menampilkan SATU baris status/progress terbaru dari output WETOOL + animasi loading. Tidak membuat persentase palsu.
- Setelah READ FULL benar-benar mencapai akhir berdasarkan output WETOOL, urutan otomatis: F -> R.
- Setelah itu Smart Repair menjalankan BwE PS4 NOR Validator dan mencoba membuka dialog Open lalu memasukkan path NOR hasil READ.
- WETOOL tetap menjadi engine utama; Smart Repair hanya controller.

Catatan: bagian BwE menggunakan dialog Open Windows sebagai uji controller. Keberhasilan load tetap harus diverifikasi dari tampilan BwE.
