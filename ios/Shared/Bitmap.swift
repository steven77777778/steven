import SwiftUI
import UIKit

/// 讀取套件裡的 BMP 圖片（放在 Shared/Sprites，app 和小工具共用）。
/// 圖片都是 32 位元、無壓縮、含透明度的 BMP。
func bmp(_ name: String) -> Image {
    if let image = UIImage(named: "\(name).bmp") {
        return Image(uiImage: image)
    }
    return Image(systemName: "questionmark.square.dashed")
}
