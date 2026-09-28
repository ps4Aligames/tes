# Smart Repair Native Controller

Smart Repair atua como **controller de comandos**. Não implementa nem simula o protocolo NOR.

Fluxo do Stage 1:
SMART READ FULL NOR → No.3 → COM/Teensy → SPIway/Juegos → READ ALL → Read Full selesai → F → R (Rename Non-Canonical) → BwE → No.7 → Y.

WETOOL, BwE e firmware SPIway são mantidos em `external/` como arquivos fornecidos pelo usuário.

Importante: a etapa READ ALL é executada pelo WETOOL. Smart Repair só envia as teclas F/R/7/Y depois da confirmação de término. Isso evita fingir que Smart Repair possui o protocolo interno do WETOOL.
