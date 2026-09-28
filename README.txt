SMART REPAIR NATIVE CONTROLLER — PROOF PACKAGE

This is based on the REAL supplied WETOOL/BwE files, not a simulated NOR reader.

Stage 1 target sequence:
No.3 -> detect COM/Teensy -> SPIway/Juegos -> READ ALL -> Read Full selesai -> F -> R
(R = Rename Non-Canonical, only once) -> BwE -> No.7 -> Y

The controller launches the original tools and keeps them outside the small controller EXE.
See PROOF_REPORT.txt for binary inspection evidence.

Actual hardware execution still requires Windows + the user's Teensy/SPI connection.
