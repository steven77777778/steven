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
CROP = (12, 14, 89, 105)     # 每一格裁切的範圍（左、上、右、下），和 pixel/preview_glass.py 一致
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

    # 1. 輸出動畫。每一格都裁成同一個範圍：CROP 是所有格子合起來的外框再留 2 像素，
    #    這樣火星人在小工具裡會盡量大，而且各格之間位置不會跳。
    frames = {(name, i): g.to_image(g.render(DESIGN, fn(i / g.FRAMES)))
              for name, _, fn, _ in g.ANIMS for i in range(g.FRAMES)}
    alpha = np.zeros((DESIGN["H"], DESIGN["W"]), bool)
    for im in frames.values():
        alpha |= np.array(im)[..., 3] > 0
    xs, ys = np.where(alpha.any(axis=0))[0], np.where(alpha.any(axis=1))[0]
    box = (max(0, xs.min() - 2), max(0, ys.min() - 2), min(DESIGN["W"], xs.max() + 3), min(DESIGN["H"], ys.max() + 3))
    assert box == CROP, f"裁切範圍變了：{box}，請同步更新 CROP 和 Swift 裡的擊中位置"
    for (name, i), im in frames.items():
        save_bmp(f"pet-{name}-{i}", im.crop(CROP))

    # 3. 靈動島（Dynamic Island）專用的章魚頭特寫（確保四角透明，對齊 96×108 高精細畫布）
    head_crop = g.to_image(g.render(DESIGN, {})).crop((28, 16, 68, 56))
    save_bmp("pet-head", head_crop)
    save_bmp("pet-head-happy", g.to_image(g.render(DESIGN, {"eyes": "joy"})).crop((28, 16, 68, 56)))

    total = len(glob.glob(os.path.join(SPRITES, "*.bmp")))
    print(f"Exported {total} BMP files to {SPRITES}")


if __name__ == "__main__":
    main()
