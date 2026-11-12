import SwiftUI

struct HoyView: View {
    @Environment(EstadoApp.self) private var estado
    @Binding var pestana: RaizView.Pestana
    @State private var rutinaAbierta: Rutina?
    @State private var verBienvenida = false

    private var saludo: String {
        switch Calendar.current.component(.hour, from: .now) {
        case ..<13: "Buenos días"
        case ..<20: "Buenas tardes"
        default: "Buenas noches"
        }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    resumen
                    animo
                    if estado.planMinimo {
                        Aviso(titulo: "Hoy, lo mínimo también cuenta",
                              texto: "Hemos encogido tu plan: menos agua, una fruta y dos minutos de estirar. Lo importante es no romper la racha.",
                              color: .sol)
                    }
                    plan
                    if estado.diaCompleto {
                        Aviso(titulo: "¡Bien hecho!", texto: "Has completado tus tres pasos. Tu racha va por \(estado.racha) días.", color: .hoja)
                    }
                    Aviso(titulo: "Consejo del día", texto: estado.consejoDelDia)
                }
                .padding(.horizontal)
                .padding(.bottom)
            }
            .background(Color.fondo)
            .navigationTitle(saludo)
            .toolbar {
                Button { verBienvenida = true } label: { Image(systemName: "person.crop.circle") }
                    .accessibilityLabel("Perfil")
            }
            .fullScreenCover(item: $rutinaAbierta) { RutinaEnCursoView(rutina: $0) }
            .fullScreenCover(isPresented: $verBienvenida) { BienvenidaView() }
        }
    }

    private var resumen: some View {
        HStack(spacing: 16) {
            ZStack {
                Anillo(progreso: Double(estado.pasosHoy) / 3)
                VStack(spacing: 0) {
                    Text("\(estado.pasosHoy)/3").font(.title.weight(.heavy))
                    Text("pasos").font(.caption2).foregroundStyle(.secondary)
                }
            }
            .frame(width: 100, height: 100)
            VStack(alignment: .leading, spacing: 6) {
                Label("\(estado.racha) días seguidos", systemImage: "flame.fill")
                    .font(.subheadline.weight(.bold))
                    .foregroundStyle(Color.sol)
                Text(estado.diaCompleto ? "Día completado. Mañana, otro pasito."
                     : estado.planMinimo ? "Plan mínimo activado. Hoy vale con poco."
                     : "Tres cosas pequeñas. Ninguna lleva más de 15 minutos.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .tarjeta()
    }

    private var animo: some View {
        VStack(alignment: .leading, spacing: 10) {
            Etiqueta("¿Cómo te sientes hoy?")
            HStack {
                ForEach(Animo.allCases) { a in
                    Button(a.rawValue) { estado.animo = estado.animo == a ? nil : a }
                        .buttonStyle(.bordered)
                        .tint(estado.animo == a ? .primary : .secondary)
                }
            }
        }
        .tarjeta()
    }

    private var plan: some View {
        let meta = estado.metaVasos
        let hoy = estado.hoy
        return VStack(alignment: .leading, spacing: 0) {
            Etiqueta("Tu plan de hoy").padding(.bottom, 6)

            FilaPaso(hecho: hoy.vasos >= meta, accion: estado.alternarAgua,
                     titulo: "Bebe \(meta) vasos de agua",
                     detalle: "\(hoy.vasos) de \(meta) · toca un vaso para sumarlo") {
                EmptyView()
            } extra: {
                HStack(spacing: 6) {
                    ForEach(0..<meta, id: \.self) { i in
                        Button { estado.tocarVaso(i) } label: {
                            Image(systemName: i < hoy.vasos ? "drop.fill" : "drop")
                                .font(.title2)
                                .foregroundStyle(Color.cielo)
                                .frame(width: 34, height: 40)
                        }
                        .accessibilityLabel("Vaso \(i + 1)")
                    }
                }
            }
            Divider()
            FilaPaso(hecho: hoy.verdura, accion: estado.alternarVerdura,
                     titulo: estado.planMinimo ? "Come una pieza de fruta" : "Pon verdura en una comida",
                     detalle: estado.planMinimo ? "La que tengas a mano" : "La mitad del plato, como en «Comer»") {
                Button("Ideas") { pestana = .comer }.botonMini()
            } extra: { EmptyView() }
            Divider()
            FilaPaso(hecho: hoy.movimiento, accion: estado.alternarMovimiento,
                     titulo: estado.planMinimo ? "Estira 2 minutos" : "Muévete \(estado.rutinaDeHoy.minutos) minutos",
                     detalle: estado.planMinimo ? "Sin levantarte del sofá, si quieres" : "Rutina guiada, sin material") {
                Button("Empezar") { rutinaAbierta = estado.rutinaDeHoy }.botonMini()
            } extra: { EmptyView() }
        }
        .tarjeta()
    }
}

extension Rutina: Identifiable {
    var id: String { "\(energia.rawValue)-\(minutos)" }
}

private struct FilaPaso<Accesorio: View, Extra: View>: View {
    let hecho: Bool
    let accion: () -> Void
    let titulo: String
    let detalle: String
    @ViewBuilder let accesorio: Accesorio
    @ViewBuilder let extra: Extra

    var body: some View {
        HStack(alignment: .center, spacing: 12) {
            Button(action: accion) {
                Image(systemName: hecho ? "checkmark.circle.fill" : "circle")
                    .font(.title)
                    .foregroundStyle(hecho ? Color.hoja : .secondary)
            }
            .accessibilityLabel(hecho ? "Desmarcar" : "Marcar")
            VStack(alignment: .leading, spacing: 2) {
                Text(titulo).font(.body.weight(.semibold))
                    .strikethrough(hecho).foregroundStyle(hecho ? .secondary : .primary)
                Text(detalle).font(.footnote).foregroundStyle(.secondary)
                extra.padding(.top, 6)
            }
            Spacer(minLength: 0)
            accesorio
        }
        .padding(.vertical, 10)
        .sensoryFeedback(.success, trigger: hecho)
    }
}

extension View {
    func botonMini() -> some View {
        self.font(.footnote.weight(.bold))
            .buttonStyle(.bordered)
            .tint(.sol)
    }
}
