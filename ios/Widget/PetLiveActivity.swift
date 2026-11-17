import ActivityKit
import AppIntents
import SwiftUI
import WidgetKit

private func petSprite(_ name: String) -> some View {
    bmp(name)
        .resizable()
        .interpolation(.none)
        .scaledToFit()
}

struct PetLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: PetActivityAttributes.self) { context in
            // 鎖定畫面橫幅：純淨無文字干擾，只放火星人角色與極簡觸發鈕
            HStack {
                Spacer()
                petSprite(isBunnyApp ? (context.state.waving ? "bun-sway-2" : "bun-idle-0") : (context.state.waving ? "pet-wavejoy-2" : "pet-idleL-3"))
                    .frame(height: 94)
                Spacer()
                Button(intent: WaveLiveActivityIntent()) {
                    Image(systemName: "sparkles")
                        .font(.system(size: 15, weight: .semibold))
                        .padding(10)
                }
                .tint(Color(red: 0.85, green: 0.26, blue: 0.29))
            }
            .padding(.horizontal, 18)
            .padding(.vertical, 8)
            .activityBackgroundTint(Color(red: 0.08, green: 0.09, blue: 0.15).opacity(0.86))
            .activitySystemActionForegroundColor(.white)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.center) {
                    petSprite(isBunnyApp ? (context.state.waving ? "bun-sway-2" : "bun-idle-0") : (context.state.waving ? "pet-wavejoy-2" : "pet-idleL-0"))
                        .frame(height: 92)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Button(intent: WaveLiveActivityIntent()) {
                        Image(systemName: "sparkles")
                            .font(.system(size: 14, weight: .semibold))
                    }
                    .tint(Color(red: 0.85, green: 0.26, blue: 0.29))
                }
            } compactLeading: {
                petSprite(isBunnyApp ? (context.state.waving ? "bun-head-happy" : "bun-head") : (context.state.waving ? "pet-head-happy" : "pet-head"))
                    .frame(height: 22)
            } compactTrailing: {
                Circle()
                    .fill(Color(red: 0.92, green: 0.36, blue: 0.39))
                    .frame(width: 7, height: 7)
            } minimal: {
                petSprite(isBunnyApp ? (context.state.waving ? "bun-head-happy" : "bun-head") : (context.state.waving ? "pet-head-happy" : "pet-head"))
                    .frame(height: 20)
            }
        }
    }
}
