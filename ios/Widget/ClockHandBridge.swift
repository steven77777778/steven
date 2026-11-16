import Foundation
import OSLog
import SwiftUI
import WidgetKit

// MARK: - ClockHandKit Runtime Bridge (Works on iOS 16+ & iOS 26 / iPhone 17!)
// 透過執行期橋接呼叫 Apple 時鐘小工具內建的 `WidgetKit._ClockHandRotationEffect`，
// 讓側載 `.ipa` 的桌面小工具可以 24 小時零耗電連續播放原生像素動畫！

private let clockLog = Logger(subsystem: "com.marspet.app", category: "ClockHandBridge")

public enum WidgetClockPeriod {
    case hourHand
    case minuteHand
    case secondHand
    case custom(Double)

    var duration: TimeInterval {
        switch self {
        case .hourHand: return 12 * 3600
        case .minuteHand: return 3600
        case .secondHand: return 60
        case .custom(let s): return s
        }
    }
}

private struct _ClockHandPayload: Encodable {
    let period: TimeInterval
    let timeZone: TimeZone
    let anchor: UnitPoint

    private enum CodingKeys: String, CodingKey {
        case period, timeZone, anchor, honorIdealizedDate
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(period, forKey: .period)
        try c.encode(timeZone, forKey: .timeZone)
        try c.encode(false, forKey: .honorIdealizedDate)
        var a = c.nestedUnkeyedContainer(forKey: .anchor)
        try a.encode(Double(anchor.x))
        try a.encode(Double(anchor.y))
    }
}

private func applyWidgetClockHand<V: View>(
    to view: V,
    period: WidgetClockPeriod,
    timeZone: TimeZone = .current,
    anchor: UnitPoint = .center
) -> AnyView {
    guard let clockType = _typeByName("9WidgetKit24_ClockHandRotationEffectV"),
          let decodableType = clockType as? any Decodable.Type,
          let json = try? JSONEncoder().encode(_ClockHandPayload(period: period.duration, timeZone: timeZone, anchor: anchor)),
          let decoded = try? JSONDecoder().decode(decodableType, from: json),
          let modifier = decoded as? any ViewModifier
    else {
        clockLog.error("ClockHand bridge unavailable; rendering static fallback.")
        return AnyView(view)
    }
    return AnyView(_openAndApply(view, modifier: modifier))
}

private func _openAndApply<V: View, M: ViewModifier>(_ view: V, modifier: M) -> some View {
    view.modifier(modifier)
}

public extension View {
    func widgetClockRotation(period: Double, anchor: UnitPoint = .center) -> some View {
        applyWidgetClockHand(to: self, period: .custom(period), anchor: anchor)
    }
}

// MARK: - 扇形遮罩逐格播放器（零殘影、100% 銳利原生像素不變形！）

private struct FrameArcMask: Shape {
    let startAngle: Double
    let endAngle: Double
    let radius: Double

    func path(in rect: CGRect) -> Path {
        var path = Path()
        path.addArc(
            center: CGPoint(x: rect.midX, y: rect.midY),
            radius: radius,
            startAngle: .degrees(startAngle),
            endAngle: .degrees(endAngle),
            clockwise: false
        )
        return path
    }
}

/// 在桌面小工具內連續循環播放一組原生像素影格（例如 8 格呼吸、招手、吹泡泡、火星人舞）。
/// 每一格都維持垂直不旋轉 + `.interpolation(.none)` 銳利像素邊緣，完全不會有斜轉鋸齒或斷手問題！
struct PixelAnimatedWidgetSprite: View {
    let frameNames: [String]
    let cycleDuration: Double

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let h = geo.size.height
            let box = max(w, h)
            let arcRadius = Double(box) * 48.0
            let stepAngle = 360.0 / Double(max(1, frameNames.count))

            ZStack {
                ForEach(Array(frameNames.enumerated()), id: \.offset) { index, name in
                    bmp(name)
                        .resizable()
                        .interpolation(.none)
                        .scaledToFit()
                        .frame(width: w, height: h)
                        .mask(
                            FrameArcMask(
                                startAngle: -stepAngle * Double(index + 1),
                                endAngle: -stepAngle * Double(index),
                                radius: arcRadius
                            )
                            .stroke(style: StrokeStyle(lineWidth: Double(box) * 1.6, lineCap: .butt))
                            .frame(width: w, height: h)
                            .widgetClockRotation(period: cycleDuration)
                            .offset(y: arcRadius)
                        )
                }
            }
            .frame(width: w, height: h)
        }
    }
}

/// 由好幾段圓弧組成的遮罩（角度單位：度）。
private struct MultiArcMask: Shape {
    let ranges: [(start: Double, end: Double)]
    let radius: Double

    func path(in rect: CGRect) -> Path {
        var path = Path()
        for range in ranges {
            var arc = Path()
            arc.addArc(
                center: CGPoint(x: rect.midX, y: rect.midY),
                radius: radius,
                startAngle: .degrees(-range.end),
                endAngle: .degrees(-range.start),
                clockwise: false
            )
            path.addPath(arc)
        }
        return path
    }
}

/// 待機：身體照常循環播放呼吸的 8 格；眼睛往左看 10 秒，慢慢移到右邊，往右看 10 秒，再慢慢移回來。
/// 做法是把四組只差在瞳孔位置的待機動畫疊在一起，再用一個轉得很慢的遮罩依時間表輪流露出其中一組。
struct IdleLookingSprite: View {
    let cycleDuration: Double

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let h = geo.size.height
            let box = max(w, h)
            let arcRadius = Double(box) * 48.0
            let degreesPerSecond = 360.0 / IdleLook.cycle

            ZStack {
                ForEach(IdleLook.schedule, id: \.set) { entry in
                    PixelAnimatedWidgetSprite(
                        frameNames: (0..<8).map { "pet-idle\(entry.set)-\($0)" },
                        cycleDuration: cycleDuration
                    )
                    .frame(width: w, height: h)
                    .mask(
                        MultiArcMask(
                            ranges: entry.spans.map { (start: $0.0 * degreesPerSecond, end: $0.1 * degreesPerSecond) },
                            radius: arcRadius
                        )
                        .stroke(style: StrokeStyle(lineWidth: Double(box) * 1.6, lineCap: .butt))
                        .frame(width: w, height: h)
                        .widgetClockRotation(period: IdleLook.cycle)
                        .offset(y: arcRadius)
                    )
                }
            }
            .frame(width: w, height: h)
        }
    }
}

/// 與 `PixelAnimatedWidgetSprite` 100% 同相位鎖定的「第 4 格（index 3）揮擊碎玻璃」播放器：
/// - 第 0～2 格（舉棒／舉紅棍蓄力）：液態玻璃完好無損
/// - 第 3 格（擊中瞬間！）：觸發強光震波 + 飛散玻璃晶屑 + 蜘蛛網色散裂紋
/// - 第 4～7 格（揮擊餘勢）：維持立體碎裂液態玻璃裂紋
struct ClockSyncedGlassShatter: View {
    let cycleDuration: Double
    let impactOrigin: UnitPoint

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let h = geo.size.height
            let box = max(w, h)
            let arcRadius = Double(box) * 48.0
            let stepAngle = 360.0 / 8.0 // 8 格動畫，每格 45°

            ZStack {
                // index 3（-180° .. -135°）：擊中瞬間閃光＋玻璃晶屑迸裂
                ShatteredLiquidGlassOverlay(impactOrigin: impactOrigin, intenseFlash: true)
                    .frame(width: w, height: h)
                    .mask(
                        FrameArcMask(
                            startAngle: -stepAngle * 4.0,
                            endAngle: -stepAngle * 3.0,
                            radius: arcRadius
                        )
                        .stroke(style: StrokeStyle(lineWidth: Double(box) * 1.6, lineCap: .butt))
                        .frame(width: w, height: h)
                        .widgetClockRotation(period: cycleDuration)
                        .offset(y: arcRadius)
                    )

                // index 4..7（-360° .. -180°）：揮擊後殘留蜘蛛網色散裂痕
                ShatteredLiquidGlassOverlay(impactOrigin: impactOrigin, intenseFlash: false)
                    .frame(width: w, height: h)
                    .mask(
                        FrameArcMask(
                            startAngle: -360.0,
                            endAngle: -stepAngle * 4.0,
                            radius: arcRadius
                        )
                        .stroke(style: StrokeStyle(lineWidth: Double(box) * 1.6, lineCap: .butt))
                        .frame(width: w, height: h)
                        .widgetClockRotation(period: cycleDuration)
                        .offset(y: arcRadius)
                    )
            }
            .frame(width: w, height: h)
        }
        .allowsHitTesting(false)
    }
}
