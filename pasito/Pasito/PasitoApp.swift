import SwiftUI

@main
struct PasitoApp: App {
    @State private var estado = EstadoApp()
    @AppStorage("apariencia") private var apariencia: Apariencia = .sistema

    var body: some Scene {
        WindowGroup {
            RaizView()
                .environment(estado)
                .tint(.hoja)
                .preferredColorScheme(apariencia.esquema)
        }
    }
}
