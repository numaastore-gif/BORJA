import SwiftUI

@main
struct PasitoApp: App {
    @State private var estado = EstadoApp()

    var body: some Scene {
        WindowGroup {
            RaizView()
                .environment(estado)
                .tint(.hoja)
        }
    }
}
