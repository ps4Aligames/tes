SMART REPAIR EDITION BY ALI GAMES

ALL COMMANDS RESPONSIVE FIX
- COM detection is automatic; no COM number is hard-coded.
- Long file scanning/MD5 and device enumeration run off the Tkinter UI thread.
- Command buttons are locked only while a background operation is active to prevent conflicting operations.
- STOP PROSES requests a safe stop for background operations.
- Stage 1 UI follows WETOOL No.3 -> Serial ports -> SPIway/Juegos -> READ ALL without launching wetool.exe.
- Hardware READ ALL is not faked; actual SPIway protocol must be implemented/verified before claiming a real NOR dump.
