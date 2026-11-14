import AppIntents
import SwiftUI
import WidgetKit

private let waveUntilKey = "waveUntil"

/// 點桌面小工具時執行：記下「招手到什麼時候」，系統會接著重新載入小工具
struct WaveWidgetIntent: AppIntent {
    static var title: LocalizedStringResource = "招手"

    func perform() async throws -> some IntentResult {
        UserDefaults.standard.set(Date().addingTimeInterval(2.4).timeIntervalSince1970, forKey: waveUntilKey)
        return .result()
    }
}

struct PetEntry: TimelineEntry {
    let date: Date
    let frame: String
}

struct PetProvider: TimelineProvider {
    func placeholder(in context: Context) -> PetEntry {
        PetEntry(date: Date(), frame: "pet-idle")
    }

    func getSnapshot(in context: Context, completion: @escaping (PetEntry) -> Void) {
        completion(PetEntry(date: Date(), frame: "pet-idle"))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<PetEntry>) -> Void) {
        let now = Date()
        let until = Date(timeIntervalSince1970: UserDefaults.standard.double(forKey: waveUntilKey))
        var entries: [PetEntry] = []
        if now < until {
            // 招手期間每 0.4 秒換一個姿勢，結束後回到站立
            var t = now
            var i = 0
            while t < until {
                entries.append(PetEntry(date: t, frame: "pet-wave\(i % 3 + 1)"))
                t = t.addingTimeInterval(0.4)
                i += 1
            }
            entries.append(PetEntry(date: until, frame: "pet-idle"))
        } else {
            entries.append(PetEntry(date: now, frame: "pet-idle"))
        }
        completion(Timeline(entries: entries, policy: .never))
    }
}

struct PetWidgetView: View {
    let entry: PetEntry

    var body: some View {
        Button(intent: WaveWidgetIntent()) {
            frame
                .scaledToFit()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .buttonStyle(.plain)
        // 不畫自己的底色：主畫面設成「透明」樣式時，系統會把小工具的底板換成玻璃
        .containerBackground(for: .widget) { Color.clear }
    }

    /// 在「透明／染色」主畫面樣式下保留原本的顏色，不被系統染成單色
    @ViewBuilder private var frame: some View {
        if #available(iOS 18.0, *) {
            Image(entry.frame)
                .resizable()
                .interpolation(.none)
                .widgetAccentedRenderingMode(.fullColor)
        } else {
            Image(entry.frame)
                .resizable()
                .interpolation(.none)
        }
    }
}

struct PetWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "PetWidget", provider: PetProvider()) { entry in
            PetWidgetView(entry: entry)
        }
        .configurationDisplayName("火星人")
        .description("點一下，他會向你招手。")
        .supportedFamilies([.systemSmall, .systemLarge])
    }
}
