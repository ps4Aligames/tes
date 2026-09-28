SMART REPAIR - WETOOL CONTROLLER TEST 2

Tujuan:
- Smart Repair hanya menjadi controller untuk WETOOL asli.
- Tidak ada implementasi READ FULL sendiri.
- WETOOL asli yang melakukan operasi hardware.

Perubahan TEST 2:
- WETOOL tidak lagi dijalankan hidden pada awal proses.
- Controller mencari window WETOOL dengan backend UIA dan Win32.
- Setelah handle/window ditemukan, WETOOL diminimalkan.
- Baru kemudian controller mencoba NO.3 lalu NO.1.
- READ FULL belum dipaksa pada TEST 2.

Portable:
- Smart_Repair_WETOOL_Controller_Test.exe
- external/wetool.exe
- external/spiway_v0.60_teensy2.0.hex

Build:
1. Upload repository ke GitHub.
2. Actions -> Build Smart Repair WETOOL Controller Test -> Run workflow.
3. Download artifact.
