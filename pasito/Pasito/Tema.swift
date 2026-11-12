import SwiftUI
import UIKit

// MARK: - Apariencia elegible (Automático / Claro / Oscuro)

enum Apariencia: String, CaseIterable, Identifiable {
    case sistema, claro, oscuro
    var id: Self { self }
    var nombre: String {
        switch self {
        case .sistema: "Automático"
        case .claro: "Claro"
        case .oscuro: "Oscuro"
        }
    }
    var icono: String {
        switch self {
        case .sistema: "circle.lefthalf.filled"
        case .claro: "sun.max.fill"
        case .oscuro: "moon.fill"
        }
    }
    var esquema: ColorScheme? {
        switch self {
        case .sistema: nil
        case .claro: .light
        case .oscuro: .dark
        }
    }
}

// MARK: - Colores (cada uno con versión clara y oscura)

extension UIColor {
    convenience init(hex: UInt32) {
        self.init(red: CGFloat((hex >> 16) & 0xFF) / 255,
                  green: CGFloat((hex >> 8) & 0xFF) / 255,
                  blue: CGFloat(hex & 0xFF) / 255, alpha: 1)
    }
}

extension Color {
    init(claro: UInt32, oscuro: UInt32) {
        self.init(uiColor: UIColor { $0.userInterfaceStyle == .dark ? UIColor(hex: oscuro) : UIColor(hex: claro) })
    }

    static let hoja = Color(claro: 0x2E8B57, oscuro: 0x5CC28A)
    static let sol = Color(claro: 0xEE9640, oscuro: 0xF3A75B)
    static let cielo = Color(claro: 0x3E8CC9, oscuro: 0x6EB0E6)
    static let trigo = Color(claro: 0xD9AE3F, oscuro: 0xE2BE5C)
    static let ciruela = Color(claro: 0xB2507A, oscuro: 0xE07FA6)
    static let aviso = Color(claro: 0xC2512F, oscuro: 0xF08A66)
    static let fondo = Color(claro: 0xF5F8F3, oscuro: 0x131915)
    static let tarjeta = Color(claro: 0xFFFFFF, oscuro: 0x1C241F)
    static let hueco = Color(claro: 0xEEF2EC, oscuro: 0x131915)
    static let linea = Color(claro: 0xDCE4DC, oscuro: 0x2A352E)
}

// MARK: - Componentes comunes

struct Tarjeta: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.tarjeta, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).stroke(Color.linea, lineWidth: 1))
    }
}

extension View {
    func tarjeta() -> some View { modifier(Tarjeta()) }

    func botonMini() -> some View {
        font(.footnote.weight(.bold)).buttonStyle(.bordered).tint(.sol)
    }

    /// Fondo de pantalla común.
    func pantalla(_ titulo: String) -> some View {
        background(Color.fondo).navigationTitle(titulo)
    }
}

struct Etiqueta: View {
    let texto: String
    init(_ texto: String) { self.texto = texto }
    var body: some View {
        Text(texto.uppercased())
            .font(.caption.weight(.bold))
            .tracking(0.8)
            .foregroundStyle(.secondary)
    }
}

struct Anillo: View {
    var progreso: Double
    var color: Color = .hoja
    var grosor: CGFloat = 12

    var body: some View {
        ZStack {
            Circle().stroke(Color.linea, lineWidth: grosor)
            Circle()
                .trim(from: 0, to: min(1, max(0, progreso)))
                .stroke(color, style: StrokeStyle(lineWidth: grosor, lineCap: .round))
                .rotationEffect(.degrees(-90))
                .animation(.easeOut(duration: 0.5), value: progreso)
        }
    }
}

struct Aviso: View {
    let titulo: String
    let texto: String
    var color: Color = .cielo

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(titulo).font(.headline)
            Text(texto).font(.subheadline)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(color.opacity(0.16), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
    }
}

/// Barra de progreso de un macro: «Proteínas 80 / 125 g».
struct BarraMacro: View {
    let nombre: String
    let valor: Double
    let objetivo: Double
    let color: Color
    var unidad = "g"

    var body: some View {
        VStack(spacing: 4) {
            HStack {
                Text(nombre).font(.footnote.weight(.semibold))
                Spacer()
                Text("\(Int(valor.rounded())) / \(Int(objetivo.rounded())) \(unidad)")
                    .font(.footnote).monospacedDigit().foregroundStyle(.secondary)
            }
            GeometryReader { g in
                ZStack(alignment: .leading) {
                    Capsule().fill(Color.linea)
                    Capsule().fill(color).frame(width: g.size.width * min(1, objetivo > 0 ? valor / objetivo : 0))
                }
            }
            .frame(height: 8)
            .animation(.easeOut, value: valor)
        }
    }
}

/// «P 37 g · H 50 g · G 14 g» en los colores de cada macro.
struct LineaMacros: View {
    let n: Nutrientes
    var body: some View {
        HStack(spacing: 8) {
            Text("P \(Int(n.proteinas.rounded())) g").foregroundStyle(Color.ciruela)
            Text("H \(Int(n.hidratos.rounded())) g").foregroundStyle(Color.trigo)
            Text("G \(Int(n.grasas.rounded())) g").foregroundStyle(Color.cielo)
        }
        .font(.caption.weight(.bold)).monospacedDigit()
    }
}

/// Dato grande con etiqueta pequeña debajo.
struct Dato: View {
    let valor: String
    let texto: String
    var color: Color = .primary

    var body: some View {
        VStack(spacing: 2) {
            Text(valor).font(.title2.weight(.heavy)).monospacedDigit().foregroundStyle(color)
            Text(texto).font(.caption2).foregroundStyle(.secondary).multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 10)
        .background(Color.hueco, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
    }
}

/// Selector en forma de botones iguales (minutos, ritmo, nivel…).
struct Segmentos<T: Hashable>: View {
    let opciones: [T]
    @Binding var seleccion: T
    let titulo: (T) -> String
    var detalle: (T) -> String? = { _ in nil }

    var body: some View {
        HStack(spacing: 6) {
            ForEach(opciones, id: \.self) { o in
                let activo = o == seleccion
                Button { seleccion = o } label: {
                    VStack(spacing: 2) {
                        Text(titulo(o)).font(.subheadline.weight(.bold))
                        if let d = detalle(o) { Text(d).font(.caption2).opacity(0.75) }
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .foregroundStyle(activo ? Color.fondo : .primary)
                    .background(activo ? Color.primary : Color.tarjeta, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                    .overlay(RoundedRectangle(cornerRadius: 14, style: .continuous).stroke(Color.linea, lineWidth: activo ? 0 : 1))
                }
                .buttonStyle(.plain)
            }
        }
    }
}

extension Double {
    /// 85,7 con coma decimal.
    func es(_ decimales: Int = 1) -> String {
        formatted(.number.precision(.fractionLength(decimales)).locale(Locale(identifier: "es_ES")))
    }
}
