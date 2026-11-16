// 編譯前的檢查：用 Apple 的影像解碼器（iPhone 上用的是同一套）讀每一張 BMP，
// 確認火星人的圖讀得出透明背景、桌布底圖尺寸正確。任何一張不對就讓編譯失敗。
import Foundation
import ImageIO
import CoreGraphics

let dir = URL(fileURLWithPath: CommandLine.arguments[1])
let files = try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil)
    .filter { $0.pathExtension == "bmp" }.sorted { $0.path < $1.path }
var failures = 0
for url in files {
    let name = url.lastPathComponent
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
        print("FAIL \(name): cannot decode"); failures += 1; continue
    }
    let w = image.width, h = image.height
    var pixels = [UInt8](repeating: 0, count: w * h * 4)
    let ctx = CGContext(data: &pixels, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4,
                        space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    ctx.draw(image, in: CGRect(x: 0, y: 0, width: w, height: h))
    let alphas = stride(from: 3, to: pixels.count, by: 4).map { pixels[$0] }
    let transparent = alphas.filter { $0 == 0 }.count, opaque = alphas.filter { $0 == 255 }.count
    if name.hasPrefix("pet-") || name.hasPrefix("bun-") {
        // 火星人：左上角必須是透明的，而且要同時有透明和不透明的像素
        if pixels[3] != 0 || transparent == 0 || opaque == 0 {
            print("FAIL \(name): transparency lost (corner alpha \(pixels[3]), transparent \(transparent), opaque \(opaque))")
            failures += 1
        }
    } else if opaque != w * h {
        print("FAIL \(name): background should be fully opaque"); failures += 1
    }
}
print("checked \(files.count) BMP files, \(failures) failed")
exit(failures == 0 && !files.isEmpty ? 0 : 1)
