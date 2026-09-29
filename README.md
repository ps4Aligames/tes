# Smart Repair Controller Test 6

Controller Windows untuk mengotomatisasi alur Test 5 dan tahap lanjutan WETOOL/BwE.

## Alur

```text
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
  -> tunggu hasil Read NOR muncul/berubah
  -> jalankan BwE PS4 NOR Validator
  -> kirim path hasil NOR + ENTER
  -> kirim 7
  -> tunggu console stabil / proses selesai
  -> kirim y
  -> TEST 6 selesai
```

## Struktur

- `main.py` — source controller.
- `external/wetool.exe` — WETOOL yang dipanggil controller.
- `external/BwE_PS4_NOR_Validator.exe` — validator BwE.
- `external/spiway_v0.60_teensy2.0.hex` — file HEX yang dibundel.
- `Smart_Repair_Controller_Test6.spec` — konfigurasi PyInstaller.
- `.github/workflows/build-windows.yml` — build otomatis di GitHub Actions.
- `build_windows.bat` — build lokal di Windows.

## Build lewat GitHub

1. Buat repository GitHub.
2. Upload seluruh isi folder ini.
3. Pastikan branch yang dipakai bernama `main` atau `master`.
4. Push ke repository.
5. Buka tab **Actions**.
6. Pilih **Build Windows EXE**.
7. Setelah selesai, ambil artifact `Smart_Repair_Controller_Test6-Windows`.

Workflow juga berjalan otomatis setiap push ke `main`/`master`.

## Build lokal

Di Windows dengan Python 3.13:

```bat
build_windows.bat
```

Hasil:

```text
dist\Smart_Repair_Controller_Test6.exe
```

## Catatan penting

Tahap load ke BwE saat ini mengasumsikan BwE menerima path file NOR sebagai input pertama setelah aplikasi dibuka. Build BwE yang diberikan terproteksi sehingga prompt internalnya belum dapat diverifikasi secara statis. Jika saat pengujian BwE meminta menu/tombol LOAD terlebih dahulu, urutan input pada `main.py` perlu disesuaikan.

Jangan redistribusikan `BwE_PS4_NOR_Validator.exe`, `wetool.exe`, atau file lain yang bukan milikmu tanpa izin dari pemiliknya. Untuk repository publik, pastikan kamu mempunyai hak distribusi atas binary yang disertakan.
