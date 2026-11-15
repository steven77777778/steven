import Foundation
import ImageIO
import CoreGraphics

let dir = URL(fileURLWithPath: CommandLine.arguments[1])
for url in try FileManager.default.contentsOfDirectory(at: dir, includingPropertiesForKeys: nil).sorted(by: { $0.path < $1.path }) {
    let name = url.lastPathComponent
    guard let src = CGImageSourceCreateWithURL(url as CFURL, nil) else { print("\(name): no image source"); continue }
    let type = CGImageSourceGetType(src) as String? ?? "?"
    guard let image = CGImageSourceCreateImageAtIndex(src, 0, nil) else {
        print("\(name): type \(type), status \(CGImageSourceGetStatus(src).rawValue), cannot create image"); continue
    }
    let w = image.width, h = image.height
    var pixels = [UInt8](repeating: 0, count: w * h * 4)
    let ctx = CGContext(data: &pixels, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w * 4,
                        space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
    ctx.draw(image, in: CGRect(x: 0, y: 0, width: w, height: h))
    let last = (h - 1) * w * 4 + (w - 1) * 4
    print("\(name): type \(type), \(w)x\(h), alphaInfo \(image.alphaInfo.rawValue), top-left RGBA \(Array(pixels[0..<4])), bottom-right RGBA \(Array(pixels[last..<last + 4]))")
}
