import AppIntents
import SwiftUI
import WidgetKit

private let playKey = "play"       // 點了幾次（每點一次加一，用來觸發動畫並決定播哪個動作）
private let untilKey = "until"     // 目前的動作播到什麼時候

// 小工具動畫的做法（依實機錄影確認過的系統行為）
//
// 1. 小工具每次更新時，系統會把畫面從舊姿勢平滑地轉到新姿勢 —— 這個可靠。
// 2. 系統大約一秒才肯更新一次，排得更密的更新會被丟掉。
// 3. 一次更新裡的重複動畫、延遲動畫、關鍵影格，系統都不會播。
//
// 所以每個動作只用少數幾個姿勢，每個姿勢間隔一秒以上，轉動時間拉長到接近間隔，
// 讓火星人一直在動而不是停住等；每一步都是完整的姿勢，就算中間某一步被丟掉，
// 也只是少一個來回，最後一定回到站立。

/// 火星人的姿勢。角度的單位是度，正的是順時針。
/// 這些數字和 pixel/preview_widget.py 裡的一致，可以用那支程式先預覽。
struct PetPose: Equatable {
    var armL = 0.0      // 左上臂（畫面左側）
    var foreL = 0.0     // 左前臂相對上臂再彎的角度
    var armR = 0.0      // 右上臂，負的是往外舉起
    var foreR = 0.0     // 右前臂
    var head = 0.0      // 頭歪的角度
    var lean = 0.0      // 上半身傾斜的角度（腿留在原地）
    var lift = 0.0      // 往上的位移（佔火星人高度的比例）

    static let rest = PetPose()
}

/// 動作裡的一步：轉到這個姿勢、轉多久
struct PetStep {
    var pose: PetPose
    var seconds: Double
}

private let stepGap = 1.15   // 每一步之間的間隔（秒），要比系統願意更新的最短間隔長

private let waveA = PetPose(armR: -115, foreR: -70, head: 4)
private let waveB = PetPose(armR: -115, foreR: -10, head: 4)
private let danceL = PetPose(armL: 22, foreL: -128, armR: -135, foreR: -12, head: -7, lean: -8)
private let danceR = PetPose(armL: 135, foreL: 12, armR: -22, foreR: 128, head: 7, lean: 8)
private let cheer = PetPose(armL: 150, foreL: 14, armR: -150, foreR: -14, lift: 0.05)

private let actions: [[PetStep]] = [
    // 招手：右手舉到頭旁邊，前臂往外、往內揮
    [PetStep(pose: waveA, seconds: 0.5), PetStep(pose: waveB, seconds: 0.8),
     PetStep(pose: waveA, seconds: 0.8), PetStep(pose: .rest, seconds: 0.5)],
    // 火星人舞：左傾時右手高舉、左手彎在胸前，再換邊
    [PetStep(pose: danceL, seconds: 0.6), PetStep(pose: danceR, seconds: 0.9), PetStep(pose: .rest, seconds: 0.6)],
    // 歡呼：雙手高舉、身體往上
    [PetStep(pose: cheer, seconds: 0.5), PetStep(pose: .rest, seconds: 0.5)]
]

/// 點桌面小工具時執行：記下點擊次數，系統會接著重新載入小工具
struct WaveWidgetIntent: AppIntent {
    static var title: LocalizedStringResource = "做動作"

    func perform() async throws -> some IntentResult {
        let defaults = UserDefaults.standard
        let play = defaults.integer(forKey: playKey) + 1
        defaults.set(play, forKey: playKey)
        let steps = actions[play % actions.count]
        defaults.set(Date().addingTimeInterval(stepGap * Double(steps.count - 1) + 0.3).timeIntervalSince1970, forKey: untilKey)
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
    var step = PetStep(pose: .rest, seconds: 0.4)
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
            // 依序排入這個動作的每一步，最後一步是回到站立
            var t = now
            for step in actions[defaults.integer(forKey: playKey) % actions.count] {
                entries.append(PetEntry(date: t, step: step, slot: slot))
                t = t.addingTimeInterval(stepGap)
            }
            // 保險：萬一「回到站立」那一步被系統丟掉，稍後再送一次
            entries.append(PetEntry(date: t.addingTimeInterval(1.0), slot: slot))
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
                PuppetView(pose: entry.step.pose)
                    .animation(.easeInOut(duration: entry.step.seconds), value: entry.step.pose)
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

/// 把各層圖疊起來，各自繞著關節轉動。每張圖的畫布都是 44×54 像素，
/// 關節位置用這個畫布上的像素座標表示。靜止時疊起來和完整的像素圖一模一樣。
struct PuppetView: View {
    let pose: PetPose

    private func unit(_ x: Double, _ y: Double) -> UnitPoint {
        UnitPoint(x: x / 44, y: y / 54)
    }

    private func layer(_ name: String) -> some View {
        Image("pet-part-\(name)")
            .resizable()
            .interpolation(.none)
    }

    /// 一隻手：前臂繞手肘轉，整隻手再繞肩膀轉。
    /// 每隻手畫兩份：一份在頭的後面（垂著時觸手蓋在上面），一份在頭的前面（舉起來時用），同一時間只顯示一份。
    private func arm(_ side: String, upper: Double, fore: Double, x: Double, front: Bool) -> some View {
        let raised = abs(upper) > 45 || abs(fore) > 45
        return ZStack {
            layer("upper\(side)")
            layer("fore\(side)")
                .rotationEffect(.degrees(fore), anchor: unit(x, 31.2))
        }
        .rotationEffect(.degrees(upper), anchor: unit(x, 25.6))
        .opacity(raised == front ? 1 : 0)
    }

    var body: some View {
        GeometryReader { geo in
            ZStack {
                layer("legs")
                ZStack {
                    layer("torso")
                    arm("L", upper: pose.armL, fore: pose.foreL, x: 16.5, front: false)
                    arm("R", upper: pose.armR, fore: pose.foreR, x: 27.5, front: false)
                    layer("head")
                        .rotationEffect(.degrees(pose.head), anchor: unit(22, 24))
                    arm("L", upper: pose.armL, fore: pose.foreL, x: 16.5, front: true)
                    arm("R", upper: pose.armR, fore: pose.foreR, x: 27.5, front: true)
                }
                .rotationEffect(.degrees(pose.lean), anchor: unit(22, 37.2))
            }
            .offset(y: -pose.lift * geo.size.height)
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
        .description("點一下，他會招手、跳舞或歡呼。")
        .supportedFamilies([.systemSmall])
        .contentMarginsDisabled()   // 讓底圖鋪滿整個小工具
    }
}
