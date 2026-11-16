import Foundation

/// 待機時眼睛的節奏：停在一邊 holdSeconds 秒，再經過兩個過渡位置慢慢移到另一邊，如此循環。
/// app 和小工具共用這張時間表，兩邊才會一致。
enum IdleLook {
    static let holdSeconds = 10.0     // 往左看、往右看各停多久
    static let stepSeconds = 0.5      // 每個過渡位置停多久（兩個過渡位置，所以移動一次約 1 秒）
    static var cycle: Double { (holdSeconds + stepSeconds * 2) * 2 }

    /// 每組待機動畫在一個循環裡出現的時段（秒）。順序：左 → A → B → 右 → B → A → 左
    static var schedule: [(set: String, spans: [(Double, Double)])] {
        let h = holdSeconds, s = stepSeconds
        return [
            ("L", [(0, h)]),
            ("A", [(h, h + s), (2 * h + 3 * s, 2 * h + 4 * s)]),
            ("B", [(h + s, h + 2 * s), (2 * h + 2 * s, 2 * h + 3 * s)]),
            ("R", [(h + 2 * s, 2 * h + 2 * s)])
        ]
    }

    /// 某個時間點該用哪一組（app 裡用）
    static func set(at date: Date) -> String {
        let t = date.timeIntervalSince1970.truncatingRemainder(dividingBy: cycle)
        for entry in schedule where entry.spans.contains(where: { t >= $0.0 && t < $0.1 }) {
            return entry.set
        }
        return "L"
    }
}
