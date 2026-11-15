import SwiftUI
import UIKit

private var bmpCache: [String: UIImage] = [:]
private let bmpLock = NSLock()

/// 讀取套件裡的 BMP 像素圖（app 和小工具共用）。
func bmp(_ name: String) -> Image {
    if let image = loadBMP(name) {
        return Image(uiImage: image)
    }
    return Image(systemName: "sparkles")
}

/// 自己解析 32 位元 BMP，不經過系統的解碼器。
/// 系統對 BMP 透明度的支援會因檔頭寫法而異；直接讀像素可以保證透明背景一定正確。
private func loadBMP(_ name: String) -> UIImage? {
    bmpLock.lock()
    defer { bmpLock.unlock() }
    if let hit = bmpCache[name] { return hit }

    guard let url = Bundle.main.url(forResource: name, withExtension: "bmp")
            ?? Bundle.main.url(forResource: name, withExtension: "bmp", subdirectory: "Sprites"),
          let data = try? Data(contentsOf: url), data.count > 54 else { return nil }
    let bytes = [UInt8](data)
    func u32(_ o: Int) -> Int {
        Int(bytes[o]) | Int(bytes[o + 1]) << 8 | Int(bytes[o + 2]) << 16 | Int(bytes[o + 3]) << 24
    }
    let offset = u32(10)
    let width = u32(18)
    let signedHeight = Int(Int32(truncatingIfNeeded: u32(22)))   // 正數：由下往上存；負數：由上往下
    let height = abs(signedHeight)
    let bitsPerPixel = Int(bytes[28]) | Int(bytes[29]) << 8
    guard bitsPerPixel == 32, width > 0, height > 0, bytes.count >= offset + width * height * 4 else {
        return UIImage(data: data)   // 不是預期的格式就交給系統試試
    }

    // 檔案裡每個像素是 B、G、R、A；整理成由上往下的順序，並把顏色乘上透明度
    var pixels = [UInt8](repeating: 0, count: width * height * 4)
    for row in 0..<height {
        let src = offset + (signedHeight > 0 ? height - 1 - row : row) * width * 4
        let dst = row * width * 4
        for i in stride(from: 0, to: width * 4, by: 4) {
            let a = Int(bytes[src + i + 3])
            pixels[dst + i] = UInt8(Int(bytes[src + i]) * a / 255)
            pixels[dst + i + 1] = UInt8(Int(bytes[src + i + 1]) * a / 255)
            pixels[dst + i + 2] = UInt8(Int(bytes[src + i + 2]) * a / 255)
            pixels[dst + i + 3] = UInt8(a)
        }
    }
    let info = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)
    guard let provider = CGDataProvider(data: Data(pixels) as CFData),
          let cgImage = CGImage(width: width, height: height, bitsPerComponent: 8, bitsPerPixel: 32,
                                bytesPerRow: width * 4, space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: info,
                                provider: provider, decode: nil, shouldInterpolate: false, intent: .defaultIntent)
    else { return nil }
    let image = UIImage(cgImage: cgImage, scale: 1, orientation: .up)
    bmpCache[name] = image
    return image
}
