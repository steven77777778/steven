import AppIntents
import SwiftUI
import WidgetKit

private let playKey = "play"       // 點了幾次（每點一次加一，用來觸發動畫並決定播哪個動作）
private let untilKey = "until"     // 目前的動作播到什麼時候

/// 火星人的姿勢。小工具不是一格一格換圖，而是把腿、身體、頭、上臂、前臂分開疊起來，
/// 只告訴系統「下一個姿勢」，中間的轉動由系統自己補，所以動作是平滑的。
/// 角度的單位是度，正的是順時針。
struct PetPose: Equatable {
    var armL = 0.0      // 左上臂（畫面左側）
    var foreL = 0.0     // 左前臂相對上臂再彎的角度
    var armR = 0.0      // 右上臂，負的是往外舉起
    var foreR = 0.0     // 右前臂
    var head = 0.0      // 頭歪的角度
    var lean = 0.0      // 上半身傾斜的角度（腿留在原地）
    var lift = 0.0      // 往上跳的高度（佔小工具高度的比例）
    var squash = 1.0    // 上下壓扁的比例

    static let rest = PetPose()
}

/// 動作裡的一步：轉到這個姿勢、花多久、要不要來回擺動
struct PetStep {
    var pose: PetPose
    var seconds: Double
    var swings = 1      // 大於 1 時在上一個姿勢和這個姿勢之間來回擺（要是奇數，最後才會停在這個姿勢）
    var hold = 0.0      // 轉到之後多停多久（只用在「分段」方式）
}

private let waveA = PetPose(armR: -152, foreR: 48, head: 4)
private let waveB = PetPose(armR: -152, foreR: -12, head: 4)
private let danceL = PetPose(armL: 22, foreL: -128, armR: -148, foreR: -12, head: -7, lean: -8)
private let danceR = PetPose(armL: 148, foreL: 12, armR: -22, foreR: 128, head: 7, lean: 8)
private let crouch = PetPose(armL: -14, armR: 14, squash: 0.86)
private let leap = PetPose(armL: 160, armR: -160, lift: 0.14, squash: 1.04)
private let land = PetPose(armL: 62, armR: -62, squash: 0.86)

/// 「分段」方式：系統大約一秒才肯更新一次小工具，所以每一步隔一秒以上，
/// 快速的來回動作交給單一步驟裡的重複動畫。
private let stepActions: [[PetStep]] = [
    [PetStep(pose: waveA, seconds: 0.4, hold: 0.7), PetStep(pose: waveB, seconds: 0.22, swings: 5, hold: 0.1),
     PetStep(pose: .rest, seconds: 0.4)],
    [PetStep(pose: danceL, seconds: 0.5, hold: 0.6), PetStep(pose: danceR, seconds: 0.6, hold: 0.5),
     PetStep(pose: danceL, seconds: 0.6, hold: 0.5), PetStep(pose: .rest, seconds: 0.5)],
    [PetStep(pose: leap, seconds: 0.35, hold: 0.75), PetStep(pose: .rest, seconds: 0.3)]
]

/// 「連續」方式（實驗）：整段動作用關鍵影格一次交給系統播，不必等系統更新。
private let keyframeActions: [[PetStep]] = [
    [PetStep(pose: waveA, seconds: 0.3), PetStep(pose: waveB, seconds: 0.2), PetStep(pose: waveA, seconds: 0.2),
     PetStep(pose: waveB, seconds: 0.2), PetStep(pose: waveA, seconds: 0.2), PetStep(pose: waveB, seconds: 0.2),
     PetStep(pose: .rest, seconds: 0.3)],
    [PetStep(pose: danceL, seconds: 0.35), PetStep(pose: danceR, seconds: 0.45), PetStep(pose: danceL, seconds: 0.45),
     PetStep(pose: danceR, seconds: 0.45), PetStep(pose: .rest, seconds: 0.3)],
    [PetStep(pose: crouch, seconds: 0.2), PetStep(pose: leap, seconds: 0.25), PetStep(pose: leap, seconds: 0.15),
     PetStep(pose: land, seconds: 0.25), PetStep(pose: .rest, seconds: 0.25)]
]

/// 點桌面小工具時執行：記下點擊次數，系統會接著重新載入小工具
struct WaveWidgetIntent: AppIntent {
    static var title: LocalizedStringResource = "做動作"

    func perform() async throws -> some IntentResult {
        let defaults = UserDefaults.standard
        let play = defaults.integer(forKey: playKey) + 1
        defaults.set(play, forKey: playKey)
        let total = stepActions[play % stepActions.count].reduce(0.0) { $0 + $1.seconds * Double($1.swings) + $1.hold }
        defaults.set(Date().addingTimeInterval(total).timeIntervalSince1970, forKey: untilKey)
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

enum PetMotion: String, AppEnum {
    case steps, keyframes

    static var typeDisplayRepresentation: TypeDisplayRepresentation = "動畫方式"
    static var caseDisplayRepresentations: [PetMotion: DisplayRepresentation] = [
        .steps: "分段（穩定）",
        .keyframes: "連續（實驗）"
    ]
}

/// 長按小工具 →「編輯小工具」時看到的設定
struct PetWidgetConfig: WidgetConfigurationIntent {
    static var title: LocalizedStringResource = "火星人"
    static var description = IntentDescription("選擇小工具放在主畫面的哪個位置，以及動畫方式。")

    @Parameter(title: "主畫面位置", default: .topLeft)
    var slot: PetSlot

    @Parameter(title: "動畫方式", default: .steps)
    var motion: PetMotion
}

struct PetEntry: TimelineEntry {
    let date: Date
    var step = PetStep(pose: .rest, seconds: 0.35)
    var play = 0
    let slot: PetSlot
    let motion: PetMotion
}

struct PetProvider: AppIntentTimelineProvider {
    func placeholder(in context: Context) -> PetEntry {
        PetEntry(date: Date(), slot: .none, motion: .steps)
    }

    func snapshot(for configuration: PetWidgetConfig, in context: Context) async -> PetEntry {
        PetEntry(date: Date(), slot: configuration.slot, motion: configuration.motion)
    }

    func timeline(for configuration: PetWidgetConfig, in context: Context) async -> Timeline<PetEntry> {
        let slot = configuration.slot
        let motion = configuration.motion
        let defaults = UserDefaults.standard
        let play = defaults.integer(forKey: playKey)
        let now = Date()
        let until = Date(timeIntervalSince1970: defaults.double(forKey: untilKey))
        var entries: [PetEntry] = []
        if motion == .steps, now < until {
            // 依序排入這個動作的每一步
            var t = now
            for step in stepActions[play % stepActions.count] {
                entries.append(PetEntry(date: t, step: step, play: play, slot: slot, motion: motion))
                t = t.addingTimeInterval(step.seconds * Double(step.swings) + step.hold)
            }
        } else {
            // 站立。「連續」方式靠 play 數字改變來觸發整段關鍵影格動畫
            entries.append(PetEntry(date: now, play: play, slot: slot, motion: motion))
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
                pet.padding(4)   // 圖片本身四周已留白，供動作伸展
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .buttonStyle(.plain)
        .unredacted()   // 系統還在載入時也直接顯示火星人，不要顯示灰色佔位方塊
        .containerBackground(for: .widget) { wallpaper }
    }

    @ViewBuilder private var pet: some View {
        switch entry.motion {
        case .steps:
            PuppetView(pose: entry.step.pose)
                .animation(stepAnimation, value: entry.step.pose)
        case .keyframes:
            let steps = keyframeActions[entry.play % keyframeActions.count]
            Color.clear
                .keyframeAnimator(initialValue: PetPose.rest, trigger: entry.play) { _, pose in
                    PuppetView(pose: pose)
                } keyframes: { _ in
                    KeyframeTrack(\.armL) { for s in steps { CubicKeyframe(s.pose.armL, duration: s.seconds) } }
                    KeyframeTrack(\.foreL) { for s in steps { CubicKeyframe(s.pose.foreL, duration: s.seconds) } }
                    KeyframeTrack(\.armR) { for s in steps { CubicKeyframe(s.pose.armR, duration: s.seconds) } }
                    KeyframeTrack(\.foreR) { for s in steps { CubicKeyframe(s.pose.foreR, duration: s.seconds) } }
                    KeyframeTrack(\.head) { for s in steps { CubicKeyframe(s.pose.head, duration: s.seconds) } }
                    KeyframeTrack(\.lean) { for s in steps { CubicKeyframe(s.pose.lean, duration: s.seconds) } }
                    KeyframeTrack(\.lift) { for s in steps { CubicKeyframe(s.pose.lift, duration: s.seconds) } }
                    KeyframeTrack(\.squash) { for s in steps { CubicKeyframe(s.pose.squash, duration: s.seconds) } }
                }
        }
    }

    private var stepAnimation: Animation {
        let base = Animation.easeInOut(duration: entry.step.seconds)
        return entry.step.swings > 1 ? base.repeatCount(entry.step.swings, autoreverses: true) : base
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

    /// 一隻手：前臂繞手肘轉，整隻手再繞肩膀轉
    private func arm(_ side: String, upper: Double, fore: Double, x: Double) -> some View {
        ZStack {
            layer("upper\(side)")
            layer("fore\(side)")
                .rotationEffect(.degrees(fore), anchor: unit(x, 31.2))
        }
        .rotationEffect(.degrees(upper), anchor: unit(x, 25.6))
        // 垂著的手在觸手後面，舉起來的手在頭前面
        .zIndex(abs(upper) > 45 || abs(fore) > 45 ? 3 : 1)
    }

    var body: some View {
        GeometryReader { geo in
            ZStack {
                layer("legs")
                ZStack {
                    layer("torso")
                    arm("L", upper: pose.armL, fore: pose.foreL, x: 16.5)
                    arm("R", upper: pose.armR, fore: pose.foreR, x: 27.5)
                    layer("head")
                        .rotationEffect(.degrees(pose.head), anchor: unit(22, 24))
                        .zIndex(2)
                }
                .rotationEffect(.degrees(pose.lean), anchor: unit(22, 37.2))
            }
            .scaleEffect(x: 1, y: pose.squash, anchor: unit(22, 51.5))
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
        .description("點一下，他會做一個動作。")
        .supportedFamilies([.systemSmall])
        .contentMarginsDisabled()   // 讓底圖鋪滿整個小工具
    }
}
