import SwiftUI
import Combine

struct MovermeView: View {
    @Environment(EstadoApp.self) private var estado
    @State private var rutinaAbierta: Rutina?

    var body: some View {
        let rutina = Catalogo.rutina(estado.energia)
        let total = rutina.ejercicios.reduce(0) { $0 + $1.segundos }
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    Etiqueta("¿Cuánta energía tienes?")
                    HStack(spacing: 8) {
                        ForEach(Energia.allCases) { e in
                            let r = Catalogo.rutina(e)
                            Button { estado.energia = e } label: {
                                VStack(spacing: 2) {
                                    Text(e.rawValue).bold()
                                    Text("\(r.minutos) min").font(.caption).foregroundStyle(.secondary)
                                }
                                .frame(maxWidth: .infinity).padding(.vertical, 12)
                                .background(estado.energia == e ? Color.sol.opacity(0.18) : Color.tarjeta,
                                            in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                                .overlay(RoundedRectangle(cornerRadius: 16, style: .continuous)
                                    .stroke(estado.energia == e ? Color.sol : .clear, lineWidth: 1.5))
                            }
                            .buttonStyle(.plain)
                        }
                    }

                    VStack(alignment: .leading, spacing: 0) {
                        HStack(alignment: .firstTextBaseline) {
                            Text("Rutina de \(rutina.minutos) minutos").font(.title3.bold())
                            Spacer()
                            Text(rutina.descripcion).font(.footnote).foregroundStyle(.secondary)
                        }
                        .padding(.bottom, 8)
                        ForEach(Array(rutina.ejercicios.enumerated()), id: \.offset) { i, ej in
                            HStack(spacing: 10) {
                                Text("\(i + 1)").font(.caption.weight(.heavy))
                                    .frame(width: 28, height: 28)
                                    .background(Color.sol.opacity(0.18), in: Circle())
                                    .foregroundStyle(Color.sol)
                                Text(ej.nombre)
                                Spacer()
                                Text("\(ej.segundos) s").monospacedDigit().foregroundStyle(.secondary)
                            }
                            .font(.subheadline)
                            .padding(.vertical, 8)
                            if i < rutina.ejercicios.count - 1 { Divider() }
                        }
                        Button { rutinaAbierta = rutina } label: {
                            Text("Empezar · \(Int((Double(total) / 60).rounded())) min")
                                .bold().frame(maxWidth: .infinity).padding(.vertical, 6)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.sol)
                        .padding(.top, 12)
                    }
                    .tarjeta()

                    VStack(alignment: .leading, spacing: 10) {
                        Aviso(titulo: "¿Hoy no puedes ni esto?",
                              texto: "Sal a dar un paseo de 10 minutos después de comer. También cuenta como paso de hoy.",
                              color: .sol)
                        Button("He paseado 10 minutos") { estado.rutinaTerminada(minutos: 10) }
                            .buttonStyle(.bordered)
                            .disabled(estado.hoy.movimiento)
                    }
                }
                .padding(.horizontal)
                .padding(.bottom)
            }
            .background(Color.fondo)
            .navigationTitle("Moverme")
            .fullScreenCover(item: $rutinaAbierta) { RutinaEnCursoView(rutina: $0) }
        }
    }
}

/// Temporizador guiado, ejercicio a ejercicio.
struct RutinaEnCursoView: View {
    @Environment(EstadoApp.self) private var estado
    @Environment(\.dismiss) private var cerrar
    let rutina: Rutina

    @State private var indice = 0
    @State private var restante = 0
    @State private var pausado = false
    @State private var terminado = false
    private let reloj = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    private var actual: Ejercicio { rutina.ejercicios[indice] }

    var body: some View {
        VStack(spacing: 18) {
            if terminado {
                Spacer()
                Image(systemName: "checkmark.circle.fill").font(.system(size: 96)).foregroundStyle(Color.hoja)
                Text("¡Rutina hecha!").font(.largeTitle.weight(.heavy))
                Text("Has marcado el paso de moverte de hoy. Tu cuerpo te lo agradece.")
                    .multilineTextAlignment(.center).foregroundStyle(.secondary)
                Spacer()
                Button { cerrar() } label: { Text("Volver").bold().frame(maxWidth: .infinity).padding(.vertical, 6) }
                    .buttonStyle(.borderedProminent)
            } else {
                HStack {
                    Etiqueta("Ejercicio \(indice + 1) de \(rutina.ejercicios.count)")
                    Spacer()
                    Button { cerrar() } label: { Image(systemName: "xmark").padding(10) }
                        .buttonStyle(.bordered).clipShape(Circle())
                        .accessibilityLabel("Cerrar")
                }
                Spacer()
                ZStack {
                    Anillo(progreso: Double(restante) / Double(actual.segundos), color: .sol, grosor: 16)
                    Text("\(restante)").font(.system(size: 64, weight: .heavy, design: .rounded)).monospacedDigit()
                        .contentTransition(.numericText(countsDown: true))
                }
                .frame(width: 230, height: 230)
                Text(actual.nombre).font(.title.weight(.heavy)).multilineTextAlignment(.center)
                Text(actual.consejo).foregroundStyle(.secondary)
                HStack(spacing: 6) {
                    ForEach(rutina.ejercicios.indices, id: \.self) { i in
                        Circle().fill(i <= indice ? Color.sol : Color.secondary.opacity(0.25)).frame(width: 8, height: 8)
                    }
                }
                Text(indice + 1 < rutina.ejercicios.count ? "Después: \(rutina.ejercicios[indice + 1].nombre)" : "Último ejercicio")
                    .font(.footnote).foregroundStyle(.secondary)
                Spacer()
                HStack(spacing: 10) {
                    Button { pausado.toggle() } label: {
                        Text(pausado ? "Seguir" : "Pausa").bold().frame(maxWidth: .infinity).padding(.vertical, 6)
                    }
                    .buttonStyle(.bordered)
                    Button { siguiente() } label: {
                        Text("Siguiente").bold().frame(maxWidth: .infinity).padding(.vertical, 6)
                    }
                    .buttonStyle(.borderedProminent).tint(.sol)
                }
            }
        }
        .padding(24)
        .onAppear {
            restante = actual.segundos
            UIApplication.shared.isIdleTimerDisabled = true
        }
        .onDisappear { UIApplication.shared.isIdleTimerDisabled = false }
        .onReceive(reloj) { _ in
            guard !pausado, !terminado else { return }
            if restante > 1 {
                withAnimation { restante -= 1 }
            } else {
                siguiente()
            }
        }
        .sensoryFeedback(.impact, trigger: indice)
        .sensoryFeedback(.success, trigger: terminado)
    }

    private func siguiente() {
        if indice + 1 < rutina.ejercicios.count {
            indice += 1
            restante = actual.segundos
        } else {
            terminado = true
            estado.rutinaTerminada(minutos: rutina.minutos)
        }
    }
}
