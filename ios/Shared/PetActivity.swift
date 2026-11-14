import ActivityKit
import AppIntents

/// 靈動島（即時動態）的狀態：火星人有沒有在招手
struct PetActivityAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var waving: Bool
    }
}

/// 在靈動島或鎖定畫面按「招手」時執行：招手兩秒後放下
struct WaveLiveActivityIntent: LiveActivityIntent {
    static var title: LocalizedStringResource = "招手"

    func perform() async throws -> some IntentResult {
        await setWaving(true)
        try? await Task.sleep(nanoseconds: 2_000_000_000)
        await setWaving(false)
        return .result()
    }

    private func setWaving(_ waving: Bool) async {
        for activity in Activity<PetActivityAttributes>.activities {
            await activity.update(ActivityContent(state: .init(waving: waving), staleDate: nil))
        }
    }
}
