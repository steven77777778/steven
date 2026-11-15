#!/usr/bin/env python3
"""將 MV 版火星人（A7 比例、身體和腿等長）匯出成 iOS App 與桌面小工具專用的 32-bit 透明 BMP。

用法：python3 pixel/export_ios.py  →  寫入 ios/Shared/Sprites/
"""
import glob
import os
import struct

import numpy as np
from PIL import Image

import generate as g

DESIGN = g.DESIGN_MV
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPRITES = os.path.join(ROOT, "ios", "Shared", "Sprites")


def save_bmp(name, img):
    """存成 32 位元無壓縮、帶 Alpha 遮罩的 BMP，保留完整透明背景。
    檔頭用 BITMAPV5HEADER：在雲端 Mac 上實測過，Apple 的解碼器讀得出這種寫法的透明度（V4 檔頭它讀不了）。"""
    os.makedirs(SPRITES, exist_ok=True)
    img = img.convert("RGBA")
    w, h = img.size
    px = img.tobytes("raw", "BGRA")
    data = b"".join(px[y * w * 4:(y + 1) * w * 4] for y in reversed(range(h)))
    hdr = struct.pack("<IiiHHIIiiII", 124, w, h, 1, 32, 3, len(data), 2835, 2835, 0, 0)
    hdr += struct.pack("<IIII", 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)
    hdr += b"BGRs" + bytes(48) + struct.pack("<IIII", 4, 0, 0, 0)
    with open(os.path.join(SPRITES, f"{name}.bmp"), "wb") as f:
        f.write(b"BM" + struct.pack("<IHHI", 138 + len(data), 0, 0, 138) + hdr + data)


def main():
    for old in glob.glob(os.path.join(SPRITES, "pet-*.bmp")):
        os.remove(old)
    # 桌布底圖：照同一種檔頭重寫一次（像素不變）
    for path in glob.glob(os.path.join(SPRITES, "bg-*.bmp")):
        save_bmp(os.path.basename(path)[:-4], Image.open(path))

    # 1. 輸出保留的動畫（每組 8 格原生 96×108 透明像素 BMP）
    for name, _, fn, _ in g.ANIMS:
        for i in range(g.FRAMES):
            im = g.to_image(g.render(DESIGN, fn(i / g.FRAMES)))
            save_bmp(f"pet-{name}-{i}", im)

    # 2. 輸出分層備援圖（供相容模式或預覽使用）
    straight = dict(armL=(0, 0, False), armR=(0, 0, False))
    layers = {k: np.array(g.to_image(g.render(DESIGN, straight, only=k))) for k in g.LAYERS}
    line = np.array([*g.PALETTE["line"], 255])
    is_line = {k: (v == line).all(axis=2) for k, v in layers.items()}
    fill = {k: (v[..., 3] > 0) & ~is_line[k] for k, v in layers.items()}
    for a, others in {
        "foreL": ["upperL"], "upperL": ["foreL"],
        "foreR": ["upperR"], "upperR": ["foreR"],
        "torso": ["legs"], "head": ["torso", "upperL", "upperR"]
    }.items():
        for o in others:
            layers[a][is_line[a] & fill[o]] = 0
    for k, v in layers.items():
        save_bmp(f"pet-part-{k}", Image.fromarray(v, "RGBA"))

    # 3. 靈動島（Dynamic Island）專用的章魚頭特寫（確保四角透明，對齊 96×108 高精細畫布）
    head_crop = g.to_image(g.render(DESIGN, {})).crop((28, 16, 68, 56))
    save_bmp("pet-head", head_crop)
    save_bmp("pet-head-happy", g.to_image(g.render(DESIGN, {"eyes": "wide"})).crop((28, 16, 68, 56)))

    total = len(glob.glob(os.path.join(SPRITES, "*.bmp")))
    print(f"Exported {total} BMP files to {SPRITES}")


if __name__ == "__main__":
    main()
