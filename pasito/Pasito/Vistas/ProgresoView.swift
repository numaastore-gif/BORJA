import SwiftUI
import Charts

struct ProgresoView: View {
    @Environment(EstadoApp.self) private var estado

    var body: some View {
        let semana = estado.semana
        let completos = semana.filter { $0.pasos == 3 }.count
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    VStack(alignment: .leading, spacing: 12) {
                        Etiqueta("Últimos 7 días")
                        Chart(Array(semana.enumerated()), id: \.offset) { i, d in
                            BarMark(x: .value("Día", d.fecha, unit: .day), y: .value("Pasos", d.pasos))
                                .foregroundStyle(i == semana.count - 1 ? Color.sol : Color.hoja)
                                .cornerRadius(8)
                        }
                        .chartYScale(domain: 0...3)
                        .chartYAxis { AxisMarks(values: [0, 1, 2, 3]) }
                        .chartXAxis {
                            AxisMarks(values: .stride(by: .day)) { _ in
                                AxisValueLabel(format: .dateTime.weekday(.narrow), centered: true)
                            }
                        }
                        .frame(height: 150)
                        Text("\(completos) días completos de 7. Los días a medias también suman.")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                    .tarjeta()

                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                        dato("\(estado.racha)", "días de racha")
                        dato("\(estado.vasosSemana)", "vasos de agua en 7 días")
                        dato("\(estado.recetasHechas.count)", "recetas cocinadas")
                        dato("\(estado.minutosSemana)", "minutos en movimiento")
                    }

                    VStack(alignment: .leading, spacing: 12) {
                        Etiqueta("Logros")
                        LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 3), spacing: 14) {
                            logro("1", "Primer día", estado.registros.values.contains { estado.pasosCompletados($0) > 0 })
                            logro("3", "Racha de 3", estado.racha >= 3)
                            logro("7", "Racha de 7", estado.racha >= 7)
                            logro("H₂O", "Semana hidratada", estado.vasosSemana >= 42)
                            logro("Chef", "3 recetas", estado.recetasHechas.count >= 3)
                            logro("30", "Un mes", estado.racha >= 30)
                        }
                    }
                    .tarjeta()
                }
                .padding(.horizontal)
                .padding(.bottom)
            }
            .background(Color.fondo)
            .navigationTitle("Progreso")
        }
    }

    private func dato(_ valor: String, _ texto: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(valor).font(.title.weight(.heavy)).monospacedDigit()
            Text(texto).font(.footnote).foregroundStyle(.secondary)
        }
        .tarjeta()
    }

    private func logro(_ simbolo: String, _ nombre: String, _ conseguido: Bool) -> some View {
        VStack(spacing: 6) {
            Text(simbolo)
                .font(.headline.weight(.heavy))
                .frame(width: 58, height: 58)
                .background(conseguido ? Color.hoja.opacity(0.18) : Color.secondary.opacity(0.15), in: Circle())
                .foregroundStyle(conseguido ? Color.hoja : .secondary)
            Text(nombre).font(.caption.weight(.semibold)).multilineTextAlignment(.center)
                .foregroundStyle(conseguido ? .primary : .secondary)
        }
    }
}
