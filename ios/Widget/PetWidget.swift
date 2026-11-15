import AppIntents
import SwiftUI
import WidgetKit

private let waveUntilKey = "waveUntil"
private let actionKey = "action"   // 這次要播第幾個動作（每點一次換下一個）
// 小工具換圖太頻繁會被系統跳過，所以每個動作只挑 4 個關鍵姿勢，
// 用系統跟得上的間隔播放：每一步的肢體變化大，看起來快，但不會掉格。
private let actions: [(name: String, keyFrames: [Int])] = [
    ("wave", [1, 3, 5, 7]),    // 手往右、往左、往右、往左
    ("dance", [0, 2, 4, 6]),   // 中、右傾、中、左傾
    ("jump", [1, 2, 4, 6])     // 蹲、起跳、最高點、落地
]
private let frameSeconds = 0.3
private let actionSeconds = frameSeconds * 8    // 4 個關鍵姿勢連播兩輪

/// 點桌面小工具時執行：記下「招手到什麼時候」，系統會接著重新載入小工具
struct WaveWidgetIntent: AppIntent {
    static var title: LocalizedStringResource = "招手"

    func perform() async throws -> some IntentResult {
        let defaults = UserDefaults.standard
        defaults.set((defaults.integer(forKey: actionKey) + 1) % actions.count, forKey: actionKey)
        defaults.set(Date().addingTimeInterval(actionSeconds).timeIntervalSince1970, forKey: waveUntilKey)
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
    let frame: String
    let slot: PetSlot
}

struct PetProvider: AppIntentTimelineProvider {
    func placeholder(in context: Context) -> PetEntry {
        PetEntry(date: Date(), frame: "pet-idle-0", slot: .none)
    }

    func snapshot(for configuration: PetWidgetConfig, in context: Context) async -> PetEntry {
        PetEntry(date: Date(), frame: "pet-idle-0", slot: configuration.slot)
    }

    func timeline(for configuration: PetWidgetConfig, in context: Context) async -> Timeline<PetEntry> {
        let slot = configuration.slot
        let now = Date()
        let until = Date(timeIntervalSince1970: UserDefaults.standard.double(forKey: waveUntilKey))
        var entries: [PetEntry] = []
        if now < until {
            // 動作期間每隔 frameSeconds 換一格，結束後回到站立
            let action = actions[UserDefaults.standard.integer(forKey: actionKey) % actions.count]
            var t = now
            var i = 0
            while t < until {
                entries.append(PetEntry(date: t, frame: "pet-\(action.name)-\(action.keyFrames[i % action.keyFrames.count])", slot: slot))
                t = t.addingTimeInterval(frameSeconds)
                i += 1
            }
            entries.append(PetEntry(date: until, frame: "pet-idle-0", slot: slot))
        } else {
            entries.append(PetEntry(date: now, frame: "pet-idle-0", slot: slot))
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
                Image(entry.frame)
                    .resizable()
                    .interpolation(.none)
                    .scaledToFit()
                    .id(entry.frame)
                    .transition(.identity)   // 換圖時直接切換，不要淡入淡出
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
