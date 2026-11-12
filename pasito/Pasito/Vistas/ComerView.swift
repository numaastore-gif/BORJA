import SwiftUI

struct ComerView: View {
    @Environment(EstadoApp.self) private var estado
    @State private var filtro: TipoComida?
    @State private var recetaAbierta: Receta?

    private var recetas: [Receta] {
        Catalogo.recetas.filter { filtro == nil || $0.tipo == filtro }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    platoFacil
                    Etiqueta("Recetas en 15 minutos o menos")
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack {
                            chip("Todo", activo: filtro == nil) { filtro = nil }
                            ForEach(TipoComida.allCases) { t in
                                chip(t.rawValue, activo: filtro == t) { filtro = t }
                            }
                        }
                    }
                    ForEach(recetas) { r in
                        Button { recetaAbierta = r } label: { FilaReceta(receta: r, hecha: estado.recetasHechas.contains(r.id)) }
                            .buttonStyle(.plain)
                    }
                    cambios
                }
                .padding(.horizontal)
                .padding(.bottom)
            }
            .background(Color.fondo)
            .navigationTitle("Comer")
            .sheet(item: $recetaAbierta) { DetalleRecetaView(receta: $0) }
        }
    }

    private func chip(_ texto: String, activo: Bool, accion: @escaping () -> Void) -> some View {
        Button(texto, action: accion)
            .font(.subheadline.weight(.semibold))
            .padding(.horizontal, 14).padding(.vertical, 8)
            .background(activo ? Color.primary : Color.tarjeta, in: Capsule())
            .foregroundStyle(activo ? Color(.systemBackground) : .primary)
    }

    private var platoFacil: some View {
        VStack(alignment: .leading, spacing: 10) {
            Etiqueta("El plato fácil")
            HStack(spacing: 16) {
                PlatoView().frame(width: 120, height: 120)
                VStack(alignment: .leading, spacing: 8) {
                    leyenda(.hoja, "½ verdura", "o ensalada")
                    leyenda(.sol, "¼ proteína", "huevo, pollo, pescado, legumbre")
                    leyenda(.trigo, "¼ hidratos", "arroz, pan, patata")
                }
                .font(.footnote)
            }
        }
        .tarjeta()
    }

    private func leyenda(_ color: Color, _ titulo: String, _ texto: String) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            RoundedRectangle(cornerRadius: 3).fill(color).frame(width: 12, height: 12)
            (Text(titulo).bold() + Text(": \(texto)"))
        }
    }

    private var cambios: some View {
        VStack(alignment: .leading, spacing: 10) {
            Etiqueta("Cambios pequeños")
            ForEach(Catalogo.cambios, id: \.antes) { c in
                HStack {
                    Text(c.antes).strikethrough().foregroundStyle(.secondary)
                    Spacer()
                    Image(systemName: "arrow.right").foregroundStyle(.secondary)
                    Spacer()
                    Text(c.despues).fontWeight(.semibold)
                }
                .font(.subheadline)
            }
        }
        .tarjeta()
    }
}

/// Plato dividido: mitad verdura, cuarto proteína, cuarto hidratos.
struct PlatoView: View {
    var body: some View {
        ZStack {
            Circle().fill(Color.tarjeta).overlay(Circle().stroke(Color.secondary.opacity(0.3), lineWidth: 2))
            sector(90, 270, .hoja)
            sector(270, 360, .sol)
            sector(0, 90, .trigo)
        }
    }

    private func sector(_ desde: Double, _ hasta: Double, _ color: Color) -> some View {
        GeometryReader { g in
            let c = CGPoint(x: g.size.width / 2, y: g.size.height / 2)
            let r = min(g.size.width, g.size.height) / 2 - 8
            Path { p in
                p.move(to: c)
                p.addArc(center: c, radius: r, startAngle: .degrees(desde), endAngle: .degrees(hasta), clockwise: false)
                p.closeSubpath()
            }
            .fill(color)
            .overlay(Path { p in p.move(to: c); p.addArc(center: c, radius: r, startAngle: .degrees(desde), endAngle: .degrees(hasta), clockwise: false); p.closeSubpath() }
                .stroke(Color.tarjeta, lineWidth: 3))
        }
    }
}

private struct FilaReceta: View {
    let receta: Receta
    let hecha: Bool

    private var color: Color {
        switch receta.tipo {
        case .desayuno: .cielo
        case .comida: .sol
        case .cena: .hoja
        case .picoteo: .trigo
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 14, style: .continuous).fill(color.opacity(0.18))
                if hecha {
                    Image(systemName: "checkmark").font(.title3.bold()).foregroundStyle(color)
                } else {
                    Text(String(receta.nombre.prefix(1))).font(.title3.weight(.heavy)).foregroundStyle(color)
                }
            }
            .frame(width: 54, height: 54)
            VStack(alignment: .leading, spacing: 2) {
                Text(receta.nombre).font(.body.weight(.semibold)).multilineTextAlignment(.leading)
                Text("\(receta.tipo.rawValue) · \(receta.ingredientes.count) ingredientes")
                    .font(.footnote).foregroundStyle(.secondary)
            }
            Spacer(minLength: 0)
            Text("\(receta.minutos) min")
                .font(.caption.weight(.bold))
                .padding(.horizontal, 8).padding(.vertical, 4)
                .background(Color.hoja.opacity(0.15), in: RoundedRectangle(cornerRadius: 8))
                .foregroundStyle(Color.hoja)
        }
        .padding(10)
        .background(Color.tarjeta, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}

struct DetalleRecetaView: View {
    @Environment(EstadoApp.self) private var estado
    @Environment(\.dismiss) private var cerrar
    let receta: Receta

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                Text("\(receta.tipo.rawValue) · \(receta.minutos) min · ~\(receta.kcal) kcal")
                    .font(.caption.weight(.bold)).foregroundStyle(Color.hoja)
                Text(receta.nombre).font(.title.weight(.heavy))
                Etiqueta("Ingredientes")
                ForEach(receta.ingredientes, id: \.self) { Label($0, systemImage: "circle.fill").labelStyle(Vineta()) }
                Etiqueta("Pasos")
                ForEach(Array(receta.pasos.enumerated()), id: \.offset) { i, p in
                    HStack(alignment: .firstTextBaseline, spacing: 10) {
                        Text("\(i + 1).").bold().monospacedDigit()
                        Text(p)
                    }
                }
                Button {
                    estado.marcarReceta(receta)
                    cerrar()
                } label: {
                    Text(estado.recetasHechas.contains(receta.id) ? "Hecha ✓" : "La he hecho")
                        .bold().frame(maxWidth: .infinity).padding(.vertical, 6)
                }
                .buttonStyle(.borderedProminent)
                .padding(.top, 8)
            }
            .padding(24)
        }
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
    }
}

private struct Vineta: LabelStyle {
    func makeBody(configuration: Configuration) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 10) {
            configuration.icon.font(.system(size: 6)).foregroundStyle(.secondary)
            configuration.title
        }
    }
}
