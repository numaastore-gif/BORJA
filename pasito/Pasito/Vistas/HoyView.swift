import SwiftUI

struct HoyView: View {
    @Environment(EstadoApp.self) private var estado
    @Binding var pestana: Pestana

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
                    Text(Date.now.formatted(.dateTime.weekday(.wide).day().month(.wide).locale(Locale(identifier: "es_ES"))).capitalizedPrimeraLetra)
                        .font(.subheadline.weight(.semibold)).foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    resumen
                    animo
                    if estado.planMinimo {
                        Aviso(titulo: "Hoy, lo mínimo también cuenta",
                              texto: "Menos agua, dos comidas del menú y diez minutos andando o dos de estirar. Lo importante es no romper la racha.",
                              color: .sol)
                    }
                    plan
                    llevas
                    if estado.diaCompleto {
                        Aviso(titulo: "¡Bien hecho!", texto: "Tres pasos completados. Tu racha va por \(estado.racha) días.", color: .hoja)
                    }
                    Aviso(titulo: "Consejo del día", texto: estado.consejoDelDia)
                }
                .padding(.horizontal).padding(.bottom)
            }
            .pantalla(saludo)
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
                    .font(.subheadline.weight(.bold)).foregroundStyle(Color.sol)
                Text(estado.diaCompleto ? "Día completado. Mañana, otro pasito."
                     : estado.planMinimo ? "Plan mínimo activado. Hoy vale con poco."
                     : "Agua, tu menú y moverte. Sin prisas.")
                    .font(.subheadline).foregroundStyle(.secondary)
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
        let hechos = estado.pasos
        return VStack(alignment: .leading, spacing: 0) {
            Etiqueta("Tu plan de hoy").padding(.bottom, 6)
            FilaPaso(hecho: hechos[0], accion: estado.alternarAgua,
                     titulo: "Bebe \(meta) vasos de agua",
                     detalle: "\(hoy.vasos) de \(meta) · \((Double(meta) * 0.25).es()) litros") {
                EmptyView()
            } extra: {
                LazyVGrid(columns: Array(repeating: GridItem(.fixed(28), spacing: 6), count: 6), alignment: .leading, spacing: 6) {
                    ForEach(0..<meta, id: \.self) { i in
                        Button { estado.tocarVaso(i) } label: {
                            Image(systemName: i < hoy.vasos ? "drop.fill" : "drop")
                                .font(.title3).foregroundStyle(Color.cielo).frame(width: 28, height: 34)
                        }
                        .accessibilityLabel("Vaso \(i + 1)")
                    }
                }
            }
            Divider()
            FilaPaso(hecho: hechos[1], accion: { pestana = .comer },
                     titulo: "Come \(estado.metaComidas) comidas de tu menú",
                     detalle: "\(hoy.comidas.count) de 4 registradas") {
                Button("Menú") { pestana = .comer }.botonMini()
            } extra: { EmptyView() }
            Divider()
            FilaPaso(hecho: hechos[2], accion: {
                         if hechos[2] { estado.borrarEjercicioDeHoy() } else { pestana = .ejercicio }
                     },
                     titulo: estado.planMinimo ? "Anda 10 min o estira 2" : "Haz ejercicio",
                     detalle: hoy.minutos > 0 ? "\(hoy.minutos) min · \(hoy.kcalQuemadas) kcal" : "Andar, piscina o en casa") {
                Button("Elegir") { pestana = .ejercicio }.botonMini()
            } extra: { EmptyView() }
        }
        .tarjeta()
    }

    private var llevas: some View {
        let p = estado.plan
        let n = estado.nutrientesHoy(soloComidas: true)
        return VStack(alignment: .leading, spacing: 12) {
            HStack {
                Etiqueta("Hoy llevas")
                Spacer()
                Text("objetivo \(Int(p.kcal)) kcal").font(.footnote).foregroundStyle(.secondary)
            }
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text("\(Int(n.kcal.rounded()))").font(.largeTitle.weight(.heavy)).monospacedDigit()
                Text("kcal · quedan \(Int(max(0, p.kcal - n.kcal).rounded()))").font(.subheadline).foregroundStyle(.secondary)
            }
            BarraMacro(nombre: "Proteínas", valor: n.proteinas, objetivo: p.proteinas, color: .ciruela)
            BarraMacro(nombre: "Hidratos", valor: n.hidratos, objetivo: p.hidratos, color: .trigo)
            BarraMacro(nombre: "Grasas", valor: n.grasas, objetivo: p.grasas, color: .cielo)
            BarraMacro(nombre: "Fibra", valor: n.fibra, objetivo: p.fibra, color: .hoja)
            if estado.hoy.kcalQuemadas > 0 {
                Text("Has quemado \(estado.hoy.kcalQuemadas) kcal con ejercicio. No las sumamos a lo que comes: así bajas de peso a ritmo constante.")
                    .font(.footnote).foregroundStyle(.secondary)
            }
        }
        .tarjeta()
    }
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
                    .font(.title).foregroundStyle(hecho ? Color.hoja : .secondary)
            }
            .accessibilityLabel(hecho ? "Hecho" : "Pendiente")
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

extension String {
    var capitalizedPrimeraLetra: String { prefix(1).uppercased() + dropFirst() }
}
