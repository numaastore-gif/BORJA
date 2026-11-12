import SwiftUI

struct RaizView: View {
    @Environment(EstadoApp.self) private var estado
    @State private var pestana = Pestana.hoy

    enum Pestana { case hoy, comer, moverme, progreso }

    var body: some View {
        TabView(selection: $pestana) {
            HoyView(pestana: $pestana)
                .tabItem { Label("Hoy", systemImage: "sun.max") }
                .tag(Pestana.hoy)
            ComerView()
                .tabItem { Label("Comer", systemImage: "fork.knife") }
                .tag(Pestana.comer)
            MovermeView()
                .tabItem { Label("Moverme", systemImage: "figure.walk") }
                .tag(Pestana.moverme)
            ProgresoView()
                .tabItem { Label("Progreso", systemImage: "chart.bar") }
                .tag(Pestana.progreso)
        }
        .fullScreenCover(isPresented: Binding(
            get: { !estado.bienvenidaHecha },
            set: { estado.bienvenidaHecha = !$0 }
        )) {
            BienvenidaView()
        }
    }
}
