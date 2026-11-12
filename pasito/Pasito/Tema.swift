import SwiftUI

extension Color {
    static let hoja = Color(red: 0.18, green: 0.55, blue: 0.34)
    static let sol = Color(red: 0.93, green: 0.59, blue: 0.25)
    static let cielo = Color(red: 0.24, green: 0.55, blue: 0.79)
    static let trigo = Color(red: 0.89, green: 0.76, blue: 0.42)
    static let fondo = Color(.systemGroupedBackground)
    static let tarjeta = Color(.secondarySystemGroupedBackground)
}

struct Tarjeta: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.tarjeta, in: RoundedRectangle(cornerRadius: 22, style: .continuous))
    }
}

extension View {
    func tarjeta() -> some View { modifier(Tarjeta()) }
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
            Circle().stroke(Color.secondary.opacity(0.2), lineWidth: grosor)
            Circle()
                .trim(from: 0, to: progreso)
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
        .background(color.opacity(0.15), in: RoundedRectangle(cornerRadius: 22, style: .continuous))
    }
}
