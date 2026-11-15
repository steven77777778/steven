import AppIntents
import SwiftUI
import WidgetKit

private let waveUntilKey = "waveUntil"
private let actionKey = "action"   // 這次要播第幾個動作（每點一次換下一個）
/// 火星人的姿勢。小工具不是一格一格換圖，而是把身體、頭、手分開疊起來，
/// 只告訴系統「下一個姿勢」，中間的轉動由系統自己補，所以動作是平滑的。
struct PetPose: Equatable {
    var armL = 0.0      // 左手（畫面左側）轉動角度，正的是順時針
    var armR = 0.0      // 右手轉動角度，負的是往外舉起
    var head = 0.0      // 頭歪的角度
    var lean = 0.0      // 整個身體傾斜的角度
    var lift = 0.0      // 往上跳的高度（佔小工具高度的比例）
    var squash = 1.0    // 上下壓扁的比例

    static let rest = PetPose()
}

/// 每個動作是一串（姿勢, 花多久轉到這個姿勢）
private let actions: [[(pose: PetPose, seconds: Double)]] = [
    // 招手：右手高舉左右揮
    [(PetPose(armR: -158, head: 5), 0.35), (PetPose(armR: -122, head: 3), 0.3),
     (PetPose(armR: -158, head: 5), 0.3), (PetPose(armR: -122, head: 3), 0.3)],
    // 火星人舞：左傾時右手高舉、左手彎向胸前，再換邊
    [(PetPose(armL: -92, armR: -146, head: -7, lean: -9), 0.5), (PetPose(armL: 146, armR: 92, head: 7, lean: 9), 0.6),
     (PetPose(armL: -92, armR: -146, head: -7, lean: -9), 0.6), (PetPose(armL: 146, armR: 92, head: 7, lean: 9), 0.6)],
    // 跳躍：蹲下、跳起、落地
    [(PetPose(armL: -14, armR: 14, squash: 0.86), 0.25), (PetPose(armL: 160, armR: -160, lift: 0.14, squash: 1.04), 0.3),
     (PetPose(armL: 60, armR: -60, squash: 0.88), 0.3)]
]

/// 點桌面小工具時執行：記下「招手到什麼時候」，系統會接著重新載入小工具
struct WaveWidgetIntent: AppIntent {
    static var title: LocalizedStringResource = "招手"

    func perform() async throws -> some IntentResult {
        let defaults = UserDefaults.standard
        defaults.set((defaults.integer(forKey: actionKey) + 1) % actions.count, forKey: actionKey)
        let index = defaults.integer(forKey: actionKey) % actions.count
        let total = actions[index].reduce(0) { $0 + $1.seconds } + 0.4
        defaults.set(Date().addingTimeInterval(total).timeIntervalSince1970, forKey: waveUntilKey)
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
    var pose = PetPose.rest
    var seconds = 0.35   // 轉到這個姿勢要花的時間
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
        let now = Date()
        let until = Date(timeIntervalSince1970: UserDefaults.standard.double(forKey: waveUntilKey))
        var entries: [PetEntry] = []
        if now < until {
            // 依序排入這個動作的每個姿勢，最後回到站立
            var t = now
            for step in actions[UserDefaults.standard.integer(forKey: actionKey) % actions.count] {
                entries.append(PetEntry(date: t, pose: step.pose, seconds: step.seconds, slot: slot))
                t = t.addingTimeInterval(step.seconds)
            }
            entries.append(PetEntry(date: t, slot: slot))
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
                PuppetView(pose: entry.pose, seconds: entry.seconds)
                    .padding(4)   // 圖片本身四周已留白，供動作伸展
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

/// 把身體、頭、左右手四張圖疊起來，各自繞著關節轉動。
/// 四張圖的畫布都是 44×54 像素，關節位置用這個畫布的比例表示。
struct PuppetView: View {
    let pose: PetPose
    let seconds: Double

    private func part(_ name: String) -> some View {
        Image(name)
            .resizable()
            .interpolation(.none)
    }

    var body: some View {
        GeometryReader { geo in
            ZStack {
                part("pet-part-body")
                part("pet-part-head")
                    .rotationEffect(.degrees(pose.head), anchor: UnitPoint(x: 22.0 / 44, y: 24.0 / 54))
                part("pet-part-armL")
                    .rotationEffect(.degrees(pose.armL), anchor: UnitPoint(x: 16.5 / 44, y: 26.0 / 54))
                part("pet-part-armR")
                    .rotationEffect(.degrees(pose.armR), anchor: UnitPoint(x: 27.5 / 44, y: 26.0 / 54))
            }
            .scaleEffect(x: 1, y: pose.squash, anchor: UnitPoint(x: 0.5, y: 51.5 / 54))
            .rotationEffect(.degrees(pose.lean), anchor: UnitPoint(x: 0.5, y: 51.5 / 54))
            .offset(y: -pose.lift * geo.size.height)
            .animation(.easeInOut(duration: seconds), value: pose)
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
