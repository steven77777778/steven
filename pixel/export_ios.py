#!/usr/bin/env python3
"""把選定的造型（A7）輸出成 iOS app 用的圖片：每個動畫 8 格，全部是原生像素。

用法：python3 pixel/export_ios.py   →  寫入 ios/Shared/Assets.xcassets/
"""
import glob
import os
import shutil
import struct

import numpy as np
from PIL import Image

import generate as g

DESIGN = g.VARIANTS["A7"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "ios", "Shared", "Assets.xcassets")
SPRITES = os.path.join(ROOT, "ios", "Shared", "Sprites")      # app 與小工具共用的 BMP 圖片


def save(name, img):
    """存成 32 位元、無壓縮、帶 Alpha 遮罩的 BMP，透明背景會保留。
    檔頭用 BITMAPV5HEADER：在雲端 Mac 上實測過，Apple 的解碼器讀得出這種寫法的透明度（V4 檔頭它讀不了）。"""
    os.makedirs(SPRITES, exist_ok=True)
    img = img.convert("RGBA")
    w, h = img.size
    px = img.tobytes("raw", "BGRA")
    data = b"".join(px[y * w * 4:(y + 1) * w * 4] for y in reversed(range(h)))      # BMP 由下往上存
    with open(os.path.join(SPRITES, f"{name}.bmp"), "wb") as f:
        f.write(bmp_bytes(w, h, data))


def bmp_bytes(w, h, data):
    hdr = struct.pack("<IiiHHIIiiII", 124, w, h, 1, 32, 3, len(data), 2835, 2835, 0, 0)
    hdr += struct.pack("<IIII", 0x00FF0000, 0x0000FF00, 0x000000FF, 0xFF000000)     # R G B A 遮罩
    hdr += b"BGRs" + bytes(48) + struct.pack("<IIII", 4, 0, 0, 0)                   # sRGB 色彩空間
    return b"BM" + struct.pack("<IHHI", 138 + len(data), 0, 0, 138) + hdr + data


def main():
    for old in glob.glob(os.path.join(SPRITES, "pet-*.bmp")):
        os.remove(old)
    # 桌布底圖：照同一種檔頭重寫一次（像素不變）
    for path in glob.glob(os.path.join(SPRITES, "bg-*.bmp")):
        save(os.path.basename(path)[:-4], Image.open(path))
    for name, _, fn, _ in g.ANIMS:
        if name == "walk":                    # 走路這個動作 app 裡不用
            continue
        for i in range(g.FRAMES):
            save(f"pet-{name}-{i}", g.to_image(g.render(DESIGN, fn(i / g.FRAMES))))
    # 小工具用的分層圖：腿、身體、頭、左右上臂、左右前臂，畫布大小相同，疊起來就是完整的火星人。
    # 小工具裡由系統把各層繞著關節轉動，動作才會平滑。
    straight = dict(armL=(0, 0, False), armR=(0, 0, False))
    layers = {k: np.array(g.to_image(g.render(DESIGN, straight, only=k))) for k in g.LAYERS}
    line = np.array([*g.PALETTE["line"], 255])
    is_line = {k: (v == line).all(axis=2) for k, v in layers.items()}
    fill = {k: (v[..., 3] > 0) & ~is_line[k] for k, v in layers.items()}
    # 各層自己的外框在關節處會變成多餘的橫線，把「蓋在相鄰部位上」的那段外框擦掉
    for a, others in {"foreL": ["upperL"], "upperL": ["foreL"], "foreR": ["upperR"], "upperR": ["foreR"],
                      "torso": ["legs"], "head": ["torso", "upperL", "upperR"]}.items():
        for o in others:
            layers[a][is_line[a] & fill[o]] = 0
    for k, v in layers.items():
        save(f"pet-part-{k}", Image.fromarray(v, "RGBA"))
    # 檢查：照小工具的順序疊起來，應該和完整的圖幾乎一樣
    comp = Image.new("RGBA", (DESIGN["W"], DESIGN["H"]))
    for k in ("legs", "torso", "upperL", "foreL", "upperR", "foreR", "head"):
        comp.alpha_composite(Image.fromarray(layers[k], "RGBA"))
    full = np.array(g.to_image(g.render(DESIGN, straight)))
    print("layer composite differs from full sprite in", int((np.array(comp) != full).any(axis=2).sum()), "pixels")
    comp.save(os.path.join(ROOT, "pixel", "out", "layers-check.png"))
    # 靈動島用的頭部特寫
    save("pet-head", g.to_image(g.render(DESIGN, {})).crop((12, 8, 32, 27)))
    print("exported", len(glob.glob(os.path.join(SPRITES, "*.bmp"))), "bmp files")


if __name__ == "__main__":
    main()
