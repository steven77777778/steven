#!/usr/bin/env python3
"""寫出同一張圖的幾種 BMP 檔頭變體，用來測 Apple 的解碼器認得哪一種。（只用標準函式庫）"""
import struct, sys, os, zlib

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
W, H = 8, 6
# 左上角透明，其餘是不透明的紅色
px = [[(0, 0, 0, 0) if (x < 3 and y < 3) else (216, 67, 74, 255) for x in range(W)] for y in range(H)]
bgra = b"".join(bytes((b, g, r, a)) for row in reversed(px) for (r, g, b, a) in row)
MASKS = struct.pack("<IIII", 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)


def write(name, header):
    off = 14 + len(header)
    with open(os.path.join(out, name), "wb") as f:
        f.write(b"BM" + struct.pack("<IHHI", off + len(bgra), 0, 0, off) + header + bgra)


def core(size, comp):
    return struct.pack("<IiiHHIIiiII", size, W, H, 1, 32, comp, len(bgra), 2835, 2835, 0, 0)

write("v3_rgb.bmp", core(40, 0))                                             # 40 位元組檔頭，無遮罩
write("v3_bitfields3.bmp", core(40, 3) + MASKS[:12])                         # 檔頭後接 RGB 三個遮罩
write("v3_bitfields4.bmp", core(40, 6) + MASKS)                              # BI_ALPHABITFIELDS
write("v3info56.bmp", core(56, 3) + MASKS)                                   # Adobe 的 56 位元組檔頭
write("v4_bitfields.bmp", core(108, 3) + MASKS + b"BGRs" + bytes(48))        # 目前失敗的寫法
write("v4_bitfields_win.bmp", core(108, 3) + MASKS + b" niW" + bytes(48))
write("v5_bitfields.bmp", core(124, 3) + MASKS + b"BGRs" + bytes(48) + struct.pack("<IIII", 4, 0, 0, 0))
write("v5_rgb.bmp", core(124, 0) + MASKS + b"BGRs" + bytes(48) + struct.pack("<IIII", 4, 0, 0, 0))

# 對照組：PNG
def chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in px)
with open(os.path.join(out, "control.png"), "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
