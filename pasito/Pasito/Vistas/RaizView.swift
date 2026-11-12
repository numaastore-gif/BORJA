import SwiftUI

enum Pestana: Hashable { case hoy, comer, ejercicio, progreso, plan }

struct RaizView: View {
    @Environment(EstadoApp.self) private var estado
    @State private var pestana = Pestana.hoy

    var body: some View {
        TabView(selection: $pestana) {
            HoyView(pestana: $pestana)
                .tabItem { Label("Hoy", systemImage: "sun.max") }.tag(Pestana.hoy)
            ComerView()
                .tabItem { Label("Comer", systemImage: "fork.knife") }.tag(Pestana.comer)
            EjercicioView()
                .tabItem { Label("Ejercicio", systemImage: "figure.walk") }.tag(Pestana.ejercicio)
            ProgresoView()
                .tabItem { Label("Progreso", systemImage: "chart.bar") }.tag(Pestana.progreso)
            MiPlanView()
                .tabItem { Label("Mi plan", systemImage: "chart.pie") }.tag(Pestana.plan)
        }
        .fullScreenCover(isPresented: Binding(
            get: { !estado.bienvenidaHecha },
            set: { if !$0 { estado.bienvenidaHecha = true } }
        )) {
            BienvenidaView()
        }
    }
}
