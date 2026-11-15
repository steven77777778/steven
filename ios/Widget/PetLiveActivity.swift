import ActivityKit
import AppIntents
import SwiftUI
import WidgetKit

private func petImage(_ name: String) -> some View {
    Image(name)
        .resizable()
        .interpolation(.none)
        .scaledToFit()
}

struct PetLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: PetActivityAttributes.self) { context in
            // 鎖定畫面上的樣子
            HStack(spacing: 16) {
                petImage(context.state.waving ? "pet-wave-2" : "pet-idle-0")
                    .frame(height: 120)
                Text(context.state.waving ? "やあ！" : "火星人")
                    .font(.title3.bold())
                    .foregroundStyle(.white)
                Spacer()
                Button(intent: WaveLiveActivityIntent()) {
                    Text("招手")
                }
                .tint(.red)
            }
            .padding()
            .activityBackgroundTint(.black)
            .activitySystemActionForegroundColor(.white)
        } dynamicIsland: { context in
            DynamicIsland {
                // 長按靈動島展開後的樣子
                DynamicIslandExpandedRegion(.leading) {
                    petImage(context.state.waving ? "pet-wave-2" : "pet-idle-0")
                        .frame(height: 110)
                }
                DynamicIslandExpandedRegion(.center) {
                    Text(context.state.waving ? "やあ！" : "火星人")
                        .font(.headline)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Button(intent: WaveLiveActivityIntent()) {
                        Text("招手")
                    }
                    .tint(.red)
                }
            } compactLeading: {
                petImage("pet-head")
                    .frame(height: 22)
            } compactTrailing: {
                Text(context.state.waving ? "👋" : "")
            } minimal: {
                petImage("pet-head")
                    .frame(height: 20)
            }
        }
    }
}
