# PS4 NOR Inspector v2

A Windows GUI diagnostic shell for PS4 NOR inspection.

## Important
The project intentionally **does not transmit undocumented SPI command bytes**. `READ FULL NOR` currently validates the COM connection and creates a clearly marked placeholder file until the exact SPIWay v0.60 / Teensy 2.0 command protocol is supplied. This prevents a false or corrupted NOR dump.

## Run
```powershell
py -m pip install -r requirements.txt
py src/ps4_nor_inspector.py
```

## Build EXE locally
```powershell
py -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --name PS4_NOR_Inspector src/ps4_nor_inspector.py
```

Output: `dist/PS4_NOR_Inspector.exe`

## GitHub Actions
Push the repository and run **Build Windows EXE**. The workflow uploads the EXE as an artifact.

## Next hardware integration step
Provide the exact command/response protocol used by your SPIWay v0.60 + Teensy 2.0 setup (or a known-good serial log). Then the transport layer can be implemented without guessing.
