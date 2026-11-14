import SwiftUI
import WidgetKit

@main
struct MarsPetWidgetBundle: WidgetBundle {
    var body: some Widget {
        PetWidget()
        PetColorWidget()
        PetLiveActivity()
    }
}
