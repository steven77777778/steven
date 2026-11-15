import AppIntents
import SwiftUI
import WidgetKit

private let playKey = "mars_play_idx"
private let untilKey = "mars_play_until"

/// 小工具裡的動作：平常是待機呼吸，點一下輪流播球棒、乒乓球（每組 8 格原生像素）。
enum MarsWidgetAction: String, CaseIterable, AppEnum {
    case idle
    case bat
    case pingpong

    static var typeDisplayRepresentation: TypeDisplayRepresentation = "點擊後的動作"
    static var caseDisplayRepresentations: [MarsWidgetAction: DisplayRepresentation] = [
        .idle:     "輪流播放球棒、乒乓球（推薦）",
        .bat:      "固定：球棒擊破紅墨",
        .pingpong: "固定：胸前顛乒乓球"
    ]

    /// 8 格播完一輪的秒數
    var cycleDuration: Double {
        switch self {
        case .idle:     return 1.50
        case .bat:      return 0.96
        case .pingpong: return 0.96
        }
    }

    /// 點擊後這個動作持續播多久才回到待機
    var holdSeconds: Double {
        self == .idle ? 0 : 3.4
    }

    var frameNames: [String] {
        (0..<8).map { "pet-\(rawValue)-\($0)" }
    }

    static let tapRotation: [MarsWidgetAction] = [.bat, .pingpong]
}

/// 點擊桌面小工具時執行：切換到下一個動作，播完自動回到待機呼吸
struct WaveWidgetIntent: AppIntent {
    static var title: LocalizedStringResource = "和火星人互動"

    func perform() async throws -> some IntentResult {
        let defaults = UserDefaults.standard
        let next = defaults.integer(forKey: playKey) + 1
        defaults.set(next, forKey: playKey)
        let action = MarsWidgetAction.tapRotation[next % MarsWidgetAction.tapRotation.count]
        defaults.set(Date().addingTimeInterval(action.holdSeconds).timeIntervalSince1970, forKey: untilKey)
        return .result()
    }
}

/// 小工具背景與 iPhone 17 液態玻璃風格設定（長按小工具 → 編輯小工具）
enum PetBackdropStyle: String, AppEnum {
    case topLeft, topRight, midLeft, midRight, bottomLeft, bottomRight
    case liquidGlass
    case marsDuskGlass
    case clearSystem

    static var typeDisplayRepresentation: TypeDisplayRepresentation = "小工具風格與背景"
    static var caseDisplayRepresentations: [PetBackdropStyle: DisplayRepresentation] = [
        .topLeft:       "透明（桌布底圖）：左上",
        .topRight:      "透明（桌布底圖）：右上",
        .midLeft:       "透明（桌布底圖）：左中",
        .midRight:      "透明（桌布底圖）：右中",
        .bottomLeft:    "透明（桌布底圖）：左下",
        .bottomRight:   "透明（桌布底圖）：右下",
        .liquidGlass:   "液態玻璃",
        .marsDuskGlass: "火星暮光玻璃",
        .clearSystem:   "系統原生玻璃"
    ]

    var isWallpaperSlice: Bool {
        switch self {
        case .topLeft, .topRight, .midLeft, .midRight, .bottomLeft, .bottomRight:
            return true
        default:
            return false
        }
    }
}

struct PetWidgetConfig: WidgetConfigurationIntent {
    static var title: LocalizedStringResource = "火星人桌寵"
    static var description = IntentDescription("選擇小工具放在主畫面的哪一格（底圖會換成那一格的桌布，看起來像透明），以及點擊後的動作。")

    // 預設用桌布底圖營造透明感；位置要選小工具實際所在的那一格，底圖才會和桌布接起來
    @Parameter(title: "主畫面位置與風格", default: .bottomRight)
    var style: PetBackdropStyle

    @Parameter(title: "點擊動作偏好", default: .idle)
    var pinnedAction: MarsWidgetAction

    // 預設關閉：透明底圖上不需要玻璃碎裂效果
    @Parameter(title: "揮棒時敲碎玻璃的特效", default: false)
    var shatterGlass: Bool
}

struct PetEntry: TimelineEntry {
    let date: Date
    let action: MarsWidgetAction
    let style: PetBackdropStyle
    let shatterGlass: Bool
    let crackedAftermathBy: MarsWidgetAction?
}

struct PetProvider: AppIntentTimelineProvider {
    func placeholder(in context: Context) -> PetEntry {
        PetEntry(date: .now, action: .idle, style: .bottomRight, shatterGlass: false, crackedAftermathBy: nil)
    }

    func snapshot(for configuration: PetWidgetConfig, in context: Context) async -> PetEntry {
        let previewAct = configuration.pinnedAction
        return PetEntry(
            date: .now,
            action: previewAct,
            style: configuration.style,
            shatterGlass: configuration.shatterGlass,
            crackedAftermathBy: nil
        )
    }

    func timeline(for configuration: PetWidgetConfig, in context: Context) async -> Timeline<PetEntry> {
        let defaults = UserDefaults.standard
        let now = Date()
        let until = Date(timeIntervalSince1970: defaults.double(forKey: untilKey))

        var entries: [PetEntry] = []
        if now < until {
            let act: MarsWidgetAction
            if configuration.pinnedAction != .idle {
                act = configuration.pinnedAction
            } else {
                let idx = defaults.integer(forKey: playKey)
                act = MarsWidgetAction.tapRotation[idx % MarsWidgetAction.tapRotation.count]
            }
            let breaksGlass = configuration.shatterGlass && act == .bat

            entries.append(PetEntry(
                date: now,
                action: act,
                style: configuration.style,
                shatterGlass: configuration.shatterGlass,
                crackedAftermathBy: nil
            ))

            if breaksGlass {
                let healTime = until.addingTimeInterval(3.5)
                entries.append(PetEntry(
                    date: until,
                    action: .idle,
                    style: configuration.style,
                    shatterGlass: configuration.shatterGlass,
                    crackedAftermathBy: act
                ))
                entries.append(PetEntry(
                    date: healTime,
                    action: .idle,
                    style: configuration.style,
                    shatterGlass: configuration.shatterGlass,
                    crackedAftermathBy: nil
                ))
            } else {
                entries.append(PetEntry(
                    date: until,
                    action: .idle,
                    style: configuration.style,
                    shatterGlass: configuration.shatterGlass,
                    crackedAftermathBy: nil
                ))
                entries.append(PetEntry(
                    date: until.addingTimeInterval(1.2),
                    action: .idle,
                    style: configuration.style,
                    shatterGlass: configuration.shatterGlass,
                    crackedAftermathBy: nil
                ))
            }
        } else {
            entries.append(PetEntry(
                date: now,
                action: .idle,
                style: configuration.style,
                shatterGlass: configuration.shatterGlass,
                crackedAftermathBy: nil
            ))
        }
        return Timeline(entries: entries, policy: .never)
    }
}

struct PetWidgetView: View {
    let entry: PetEntry
    @Environment(\.widgetFamily) private var family
    @Environment(\.widgetRenderingMode) private var renderingMode

    private func impactPoint(for act: MarsWidgetAction) -> UnitPoint {
        if family == .systemMedium {
            return UnitPoint(x: 0.62, y: 0.74)
        } else {
            return UnitPoint(x: 0.74, y: 0.74)
        }
    }

    var body: some View {
        Button(intent: WaveWidgetIntent()) {
            ZStack {
                backdropContent

                // 1×1 與 2×1 皆為 100% 零文字純淨桌面寵物！（無任何標籤框或文字框干擾）
                petStage

                if entry.shatterGlass && renderingMode == .fullColor {
                    if entry.action == .bat {
                        ClockSyncedGlassShatter(
                            cycleDuration: entry.action.cycleDuration,
                            impactOrigin: impactPoint(for: entry.action)
                        )
                    } else if let brokenBy = entry.crackedAftermathBy {
                        ShatteredLiquidGlassOverlay(
                            impactOrigin: impactPoint(for: brokenBy),
                            intenseFlash: false
                        )
                    }
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .buttonStyle(.plain)
        .unredacted()
        .containerBackground(for: .widget) {
            containerBg
        }
    }

    private var petStage: some View {
        ZStack {
            // 腳下的陰影只在玻璃風格下畫；透明（桌布底圖）時不畫，火星人直接站在桌布上
            if !entry.style.isWallpaperSlice {
                VStack {
                    Spacer()
                    Ellipse()
                        .fill(.black.opacity(0.24))
                        .frame(width: family == .systemMedium ? 68 : 60, height: 9)
                        .blur(radius: 2)
                        .padding(.bottom, 10)
                }
            }

            PixelAnimatedWidgetSprite(
                frameNames: entry.action.frameNames,
                cycleDuration: entry.action.cycleDuration
            )
            .padding(.vertical, 6)
            .padding(.horizontal, family == .systemMedium ? 24 : 6)
        }
    }

    @ViewBuilder
    private var backdropContent: some View {
        if entry.style.isWallpaperSlice {
            bmp("bg-\(entry.style.rawValue)")
                .resizable()
                .scaledToFill()
        } else if entry.style == .marsDuskGlass {
            ZStack {
                LinearGradient(
                    colors: [
                        Color(red: 0.12, green: 0.12, blue: 0.23).opacity(0.80),
                        Color(red: 0.34, green: 0.14, blue: 0.22).opacity(0.70)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                ContainerRelativeShape()
                    .strokeBorder(
                        LinearGradient(
                            colors: [.white.opacity(0.45), .white.opacity(0.06), Color(red: 0.95, green: 0.45, blue: 0.48).opacity(0.32)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 1.2
                    )
            }
        } else if entry.style == .liquidGlass {
            ZStack {
                LinearGradient(
                    colors: [
                        .white.opacity(0.14),
                        .white.opacity(0.02),
                        Color(red: 0.88, green: 0.30, blue: 0.34).opacity(0.08)
                    ],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                ContainerRelativeShape()
                    .strokeBorder(
                        LinearGradient(
                            colors: [.white.opacity(0.50), .white.opacity(0.08), .white.opacity(0.28)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 1.1
                    )
            }
        } else {
            Color.clear
        }
    }

    @ViewBuilder
    private var containerBg: some View {
        if entry.style.isWallpaperSlice {
            bmp("bg-\(entry.style.rawValue)")
                .resizable()
                .scaledToFill()
        } else if entry.style == .clearSystem {
            Color.clear
        } else {
            Rectangle().fill(.ultraThinMaterial)
        }
    }
}

struct PetWidget: Widget {
    var body: some WidgetConfiguration {
        AppIntentConfiguration(kind: "PetWidget", intent: PetWidgetConfig.self, provider: PetProvider()) { entry in
            PetWidgetView(entry: entry)
        }
        .configurationDisplayName("火星人桌寵")
        .description("平常待機呼吸，點一下輪流播球棒、乒乓球。")
        .supportedFamilies([.systemSmall])   // 桌布底圖只對應小尺寸的六個位置
        .contentMarginsDisabled()
    }
}
