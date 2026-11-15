import AppIntents
import SwiftUI
import WidgetKit

private let playKey = "play"       // 點了幾次（每點一次加一，用來觸發動畫並決定播哪個動作）
private let untilKey = "until"     // 目前的動作播到什麼時候

// 小工具動畫的做法
//
// 系統不保證準時更新小工具，連續排好幾個姿勢時中間的常被跳過。
// 但「一次更新裡」交給系統的動畫（含延遲與重複）會完整、平滑地播完。
// 所以整段動作在點擊後的那一次更新就全部交出去：
// 把每個關節的動作拆成一小段一小段，每段是「轉多少度、延遲多久開始、花多久」，
// 各段疊加起來就是完整的動作。每個關節各段的總和都是 0，所以播完自然回到站立，
// 之後不管系統多晚才送來「回到站立」的更新，畫面上都不會再動。

enum Ease { case inOut, out, into }

/// 一小段動作：變化量（角度、位移比例，或縮放倍率）、何時開始、花多久
struct Seg {
    let delta: Double
    let start: Double
    let dur: Double
    let ease: Ease

    var animation: Animation {
        let base: Animation
        switch ease {
        case .inOut: base = .easeInOut(duration: dur)
        case .out: base = .easeOut(duration: dur)
        case .into: base = .easeIn(duration: dur)
        }
        return base.delay(start)
    }
}

/// 把「(時間, 數值)」的關鍵點轉成一段段的變化量。起點是站立（0，縮放則是 1），最後一個關鍵點也必須回到站立。
private func track(_ keys: [(Double, Double)], eases: [Ease] = [], ratio: Bool = false) -> [Seg] {
    var segs: [Seg] = []
    var t = 0.0
    var v = ratio ? 1.0 : 0.0
    for (i, key) in keys.enumerated() {
        let delta = ratio ? key.1 / v : key.1 - v
        if abs(delta - (ratio ? 1 : 0)) > 0.0001 {
            segs.append(Seg(delta: delta, start: t, dur: key.0 - t, ease: i < eases.count ? eases[i] : .inOut))
        }
        t = key.0
        v = key.1
    }
    return segs
}

/// 一個完整的動作。角度單位是度，正的是順時針。
struct Move {
    var armL: [Seg] = []     // 左上臂（畫面左側）
    var foreL: [Seg] = []    // 左前臂相對上臂再彎
    var armR: [Seg] = []     // 右上臂，負的是往外舉起
    var foreR: [Seg] = []    // 右前臂
    var head: [Seg] = []     // 頭歪
    var lean: [Seg] = []     // 上半身傾斜（腿留在原地）
    var lift: [Seg] = []     // 往上跳（佔小工具高度的比例）
    var squash: [Seg] = []   // 上下壓扁的倍率
    var frontL = false       // 這個動作裡，左手要不要畫在頭的前面
    var frontR = false
    var total: Double        // 整段動作的長度（秒）
}

private let moves: [Move] = [
    // 招手：右手往右上舉，前臂左右揮三次
    Move(armR: track([(0.3, -115), (1.55, -115), (1.85, 0)]),
         foreR: track([(0.3, -20), (0.5, -72), (0.7, -12), (0.9, -72), (1.1, -12), (1.3, -72), (1.55, -20), (1.85, 0)]),
         head: track([(0.3, 4), (1.55, 4), (1.85, 0)]),
         frontR: true, total: 1.85),
    // 火星人舞：左傾時右手高舉、左手彎在胸前，再換邊
    Move(armL: track([(0.35, 22), (0.6, 22), (1.05, 135), (1.4, 135), (1.8, 0)]),
         foreL: track([(0.35, -128), (0.6, -128), (1.05, 12), (1.4, 12), (1.8, 0)]),
         armR: track([(0.35, -135), (0.6, -135), (1.05, -22), (1.4, -22), (1.8, 0)]),
         foreR: track([(0.35, -12), (0.6, -12), (1.05, 128), (1.4, 128), (1.8, 0)]),
         head: track([(0.35, -7), (0.6, -7), (1.05, 7), (1.4, 7), (1.8, 0)]),
         lean: track([(0.35, -8), (0.6, -8), (1.05, 8), (1.4, 8), (1.8, 0)]),
         frontL: true, frontR: true, total: 1.8),
    // 跳躍：蹲下、雙手上舉跳起、落地、站好
    Move(armL: track([(0.2, -14), (0.45, 160), (0.8, 160), (1.0, 62), (1.25, 0)]),
         armR: track([(0.2, 14), (0.45, -160), (0.8, -160), (1.0, -62), (1.25, 0)]),
         lift: track([(0.2, 0), (0.5, 0.14), (0.82, 0)], eases: [.inOut, .out, .into]),
         squash: track([(0.2, 0.86), (0.4, 1.04), (0.82, 1.0), (0.95, 0.86), (1.25, 1.0)], ratio: true),
         frontL: true, frontR: true, total: 1.25)
]

/// 點桌面小工具時執行：記下點擊次數，系統會接著重新載入小工具
struct WaveWidgetIntent: AppIntent {
    static var title: LocalizedStringResource = "做動作"

    func perform() async throws -> some IntentResult {
        let defaults = UserDefaults.standard
        let play = defaults.integer(forKey: playKey) + 1
        defaults.set(play, forKey: playKey)
        defaults.set(Date().addingTimeInterval(moves[play % moves.count].total + 0.5).timeIntervalSince1970, forKey: untilKey)
        return .result()
    }
}

/// 小工具放在主畫面的哪一格。底圖會換成那一格的桌布，看起來就像透明的。
enum PetSlot: String, AppEnum {
    case topLeft, topRight, midLeft, midRight, bottomLeft, bottomRight, none

    static var typeDisplayRepresentation: TypeDisplayRepresentation = "主畫面位置"
    static var caseDisplayRepresentations: [PetSlot: DisplayRepresentation] = [
        .topLeft: "左上",
        .topRight: "右上",
        .midLeft: "左中",
        .midRight: "右中",
        .bottomLeft: "左下",
        .bottomRight: "右下",
        .none: "不使用桌布底圖"
    ]
}

/// 長按小工具 →「編輯小工具」時看到的設定
struct PetWidgetConfig: WidgetConfigurationIntent {
    static var title: LocalizedStringResource = "火星人"
    static var description = IntentDescription("選擇小工具放在主畫面的哪個位置。")

    @Parameter(title: "主畫面位置", default: .topLeft)
    var slot: PetSlot
}

struct PetEntry: TimelineEntry {
    let date: Date
    var active = -1      // 正在播第幾個動作，-1 是站立
    let slot: PetSlot
}

struct PetProvider: AppIntentTimelineProvider {
    func placeholder(in context: Context) -> PetEntry {
        PetEntry(date: Date(), slot: .none)
    }

    func snapshot(for configuration: PetWidgetConfig, in context: Context) async -> PetEntry {
        PetEntry(date: Date(), slot: configuration.slot)
    }

    func timeline(for configuration: PetWidgetConfig, in context: Context) async -> Timeline<PetEntry> {
        let slot = configuration.slot
        let defaults = UserDefaults.standard
        let now = Date()
        let until = Date(timeIntervalSince1970: defaults.double(forKey: untilKey))
        var entries: [PetEntry] = []
        if now < until {
            // 只要兩次更新：開始播這個動作，以及播完後標記回站立
            entries.append(PetEntry(date: now, active: defaults.integer(forKey: playKey) % moves.count, slot: slot))
            entries.append(PetEntry(date: until, slot: slot))
        } else {
            entries.append(PetEntry(date: now, slot: slot))
        }
        return Timeline(entries: entries, policy: .never)
    }
}

struct PetWidgetView: View {
    let entry: PetEntry

    var body: some View {
        Button(intent: WaveWidgetIntent()) {
            ZStack {
                // 桌布底圖直接畫在內容裡（系統有時會把「小工具背景」拿掉，畫在內容裡才保險）
                wallpaper
                PuppetView(active: entry.active).padding(4)   // 圖片本身四周已留白，供動作伸展
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .buttonStyle(.plain)
        .unredacted()   // 系統還在載入時也直接顯示火星人，不要顯示灰色佔位方塊
        .containerBackground(for: .widget) { wallpaper }
    }

    /// 那一格的桌布，和主畫面桌布接在一起
    @ViewBuilder private var wallpaper: some View {
        if entry.slot == .none {
            Color.clear
        } else {
            Image("bg-\(entry.slot.rawValue)")
                .resizable()
                .scaledToFill()
        }
    }
}

/// 把各層圖疊起來，各自繞著關節轉動。每張圖的畫布都是 44×54 像素，
/// 關節位置用這個畫布上的像素座標表示。靜止時疊起來和完整的像素圖一模一樣。
struct PuppetView: View {
    let active: Int      // 正在播第幾個動作，-1 是站立

    /// 回到站立時所有小段同時、用同一條曲線歸零，總和一直是 0，所以畫面不會動
    private static let reset = Animation.linear(duration: 0.05)

    private func unit(_ x: Double, _ y: Double) -> UnitPoint {
        UnitPoint(x: x / 44, y: y / 54)
    }

    private func layer(_ name: String) -> AnyView {
        AnyView(Image("pet-part-\(name)").resizable().interpolation(.none))
    }

    /// 把某個關節在每個動作裡的每一小段，各包成一層旋轉
    private func turned(_ view: AnyView, _ pick: (Move) -> [Seg], anchor: UnitPoint) -> AnyView {
        var out = view
        for (k, move) in moves.enumerated() {
            let on = active == k
            for seg in pick(move) {
                out = AnyView(out
                    .rotationEffect(.degrees(on ? seg.delta : 0), anchor: anchor)
                    .animation(on ? seg.animation : PuppetView.reset, value: on))
            }
        }
        return out
    }

    private func squashed(_ view: AnyView) -> AnyView {
        var out = view
        for (k, move) in moves.enumerated() {
            let on = active == k
            for seg in move.squash {
                out = AnyView(out
                    .scaleEffect(x: 1, y: on ? seg.delta : 1, anchor: unit(22, 51.5))
                    .animation(on ? seg.animation : PuppetView.reset, value: on))
            }
        }
        return out
    }

    private func lifted(_ view: AnyView, height: Double) -> AnyView {
        var out = view
        for (k, move) in moves.enumerated() {
            let on = active == k
            for seg in move.lift {
                out = AnyView(out
                    .offset(y: on ? -seg.delta * height : 0)
                    .animation(on ? seg.animation : PuppetView.reset, value: on))
            }
        }
        return out
    }

    /// 一隻手：前臂繞手肘轉，整隻手再繞肩膀轉。
    /// 每隻手有兩份：一份在頭的後面（垂著時觸手蓋在上面），一份在頭的前面（舉起來時用），同一時間只顯示一份。
    private func arm(_ side: String, x: Double, upper: (Move) -> [Seg], fore: (Move) -> [Seg],
                     front: (Move) -> Bool, frontCopy: Bool) -> some View {
        let forearm = turned(layer("fore\(side)"), fore, anchor: unit(x, 31.2))
        let whole = turned(AnyView(ZStack { layer("upper\(side)"); forearm }), upper, anchor: unit(x, 25.6))
        let showFront = active >= 0 && front(moves[active])
        return whole
            .opacity(frontCopy == showFront ? 1 : 0)
            .animation(PuppetView.reset, value: showFront)
    }

    var body: some View {
        GeometryReader { geo in
            let upperBody = AnyView(ZStack {
                layer("torso")
                arm("L", x: 16.5, upper: { $0.armL }, fore: { $0.foreL }, front: { $0.frontL }, frontCopy: false)
                arm("R", x: 27.5, upper: { $0.armR }, fore: { $0.foreR }, front: { $0.frontR }, frontCopy: false)
                turned(layer("head"), { $0.head }, anchor: unit(22, 24))
                arm("L", x: 16.5, upper: { $0.armL }, fore: { $0.foreL }, front: { $0.frontL }, frontCopy: true)
                arm("R", x: 27.5, upper: { $0.armR }, fore: { $0.foreR }, front: { $0.frontR }, frontCopy: true)
            })
            let figure = AnyView(ZStack {
                layer("legs")
                turned(upperBody, { $0.lean }, anchor: unit(22, 37.2))
            })
            lifted(squashed(figure), height: geo.size.height)
        }
        .aspectRatio(44.0 / 54, contentMode: .fit)
    }
}

struct PetWidget: Widget {
    var body: some WidgetConfiguration {
        AppIntentConfiguration(kind: "PetWidget", intent: PetWidgetConfig.self, provider: PetProvider()) { entry in
            PetWidgetView(entry: entry)
        }
        .configurationDisplayName("火星人")
        .description("點一下，他會做一個動作。")
        .supportedFamilies([.systemSmall])
        .contentMarginsDisabled()   // 讓底圖鋪滿整個小工具
    }
}
