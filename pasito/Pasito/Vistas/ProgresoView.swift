import SwiftUI
import Charts

struct ProgresoView: View {
    @Environment(EstadoApp.self) private var estado
    @State private var pesoTexto = ""
    @FocusState private var escribiendo: Bool

    var body: some View {
        let p = estado.plan
        let semana = estado.semana
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    peso(p)
                    VStack(alignment: .leading, spacing: 12) {
                        Etiqueta("Últimos 7 días")
                        Chart(semana) { d in
                            BarMark(x: .value("Día", d.fecha, unit: .day), y: .value("Pasos", d.pasos))
                                .foregroundStyle(Calendar.current.isDateInToday(d.fecha) ? Color.sol : Color.hoja)
                                .cornerRadius(8)
                        }
                        .chartYScale(domain: 0...3)
                        .chartYAxis { AxisMarks(values: [0, 1, 2, 3]) }
                        .chartXAxis {
                            AxisMarks(values: .stride(by: .day)) { _ in
                                AxisValueLabel(format: .dateTime.weekday(.narrow), centered: true)
                            }
                        }
                        .frame(height: 140)
                        Text("\(semana.filter { $0.pasos == 3 }.count) días completos de 7. Los días a medias también suman.")
                            .font(.footnote).foregroundStyle(.secondary)
                    }
                    .tarjeta()

                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                        dato("\(estado.racha)", "días de racha")
                        dato("\(estado.vasosSemana)", "vasos de agua en 7 días")
                        dato("\(estado.minutosSemana)", "minutos de ejercicio")
                        dato("\(estado.kcalSemana)", "kcal quemadas en 7 días")
                    }

                    logros(p)
                }
                .padding(.horizontal).padding(.bottom)
            }
            .pantalla("Progreso")
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("Listo") { escribiendo = false }
                }
            }
        }
    }

    private func peso(_ p: Plan) -> some View {
        let inicial = estado.pesos.first?.kg ?? p.peso
        let perdido = inicial - p.peso
        return VStack(alignment: .leading, spacing: 12) {
            Etiqueta("Tu peso")
            HStack(spacing: 24) {
                VStack(alignment: .leading) {
                    Text("\(p.peso.es()) kg").font(.title.weight(.heavy)).monospacedDigit()
                    Text("ahora").font(.caption).foregroundStyle(.secondary)
                }
                VStack(alignment: .leading) {
                    Text("\(perdido > 0 ? "−" : "")\(abs(perdido).es()) kg").font(.title.weight(.heavy)).monospacedDigit()
                        .foregroundStyle(Color.hoja)
                    Text("desde el inicio").font(.caption).foregroundStyle(.secondary)
                }
            }
            if estado.pesos.count > 1 {
                Chart {
                    ForEach(estado.pesos) { r in
                        AreaMark(x: .value("Fecha", r.fecha), yStart: .value("Base", p.perfil.objetivo - 1), yEnd: .value("Peso", r.kg))
                            .foregroundStyle(Color.sol.opacity(0.12))
                        LineMark(x: .value("Fecha", r.fecha), y: .value("Peso", r.kg))
                            .foregroundStyle(Color.sol).lineStyle(StrokeStyle(lineWidth: 2.5))
                        PointMark(x: .value("Fecha", r.fecha), y: .value("Peso", r.kg)).foregroundStyle(Color.sol)
                    }
                    RuleMark(y: .value("Objetivo", p.perfil.objetivo))
                        .foregroundStyle(Color.hoja).lineStyle(StrokeStyle(lineWidth: 1.5, dash: [5, 4]))
                        .annotation(position: .top, alignment: .trailing) {
                            Text("Objetivo \(p.perfil.objetivo.es()) kg").font(.caption2.weight(.bold)).foregroundStyle(Color.hoja)
                        }
                }
                .chartYScale(domain: (p.perfil.objetivo - 1)...((estado.pesos.map(\.kg).max() ?? p.peso) + 1))
                .frame(height: 160)
            } else {
                Text("Registra tu peso cada semana y aquí verás cómo baja.").font(.footnote).foregroundStyle(.secondary)
            }
            Text("Faltan \(p.faltan.es()) kg. A \(p.ritmo.es()) kg por semana, unas \(p.semanas) semanas. Pésate una vez por semana, el mismo día y en ayunas.")
                .font(.footnote).foregroundStyle(.secondary)
            HStack {
                TextField("Peso de hoy (kg)", text: $pesoTexto)
                    .keyboardType(.decimalPad).focused($escribiendo)
                    .padding(11)
                    .background(Color.hueco, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
                Button("Guardar") {
                    if let kg = Double(pesoTexto.replacingOccurrences(of: ",", with: ".")), (35...300).contains(kg) {
                        estado.registrarPeso(kg)
                        pesoTexto = ""
                        escribiendo = false
                    }
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .tarjeta()
    }

    private func dato(_ valor: String, _ texto: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(valor).font(.title2.weight(.heavy)).monospacedDigit()
            Text(texto).font(.footnote).foregroundStyle(.secondary)
        }
        .tarjeta()
    }

    private func logros(_ p: Plan) -> some View {
        let perdido = (estado.pesos.first?.kg ?? p.peso) - p.peso
        return VStack(alignment: .leading, spacing: 12) {
            Etiqueta("Logros")
            LazyVGrid(columns: Array(repeating: GridItem(.flexible()), count: 3), spacing: 14) {
                logro("1", "Primer día", estado.racha >= 1 || estado.pasosHoy > 0)
                logro("3", "Racha de 3", estado.racha >= 3)
                logro("7", "Racha de 7", estado.racha >= 7)
                logro("−2", "Primeros 2 kg", perdido >= 2)
                logro("−5", "5 kg menos", perdido >= 5)
                logro("Meta", "Peso objetivo", p.faltan <= 0)
            }
        }
        .tarjeta()
    }

    private func logro(_ simbolo: String, _ nombre: String, _ conseguido: Bool) -> some View {
        VStack(spacing: 6) {
            Text(simbolo)
                .font(.headline.weight(.heavy))
                .frame(width: 56, height: 56)
                .background(conseguido ? Color.hoja.opacity(0.18) : Color.linea, in: Circle())
                .foregroundStyle(conseguido ? Color.hoja : .secondary)
            Text(nombre).font(.caption.weight(.semibold)).multilineTextAlignment(.center)
                .foregroundStyle(conseguido ? .primary : .secondary)
        }
    }
}
