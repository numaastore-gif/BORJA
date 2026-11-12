import SwiftUI
import Combine

struct EjercicioView: View {
    @Environment(EstadoApp.self) private var estado
    @AppStorage("ejercicio.tipo") private var tipo: TipoEjercicio = .andar
    @AppStorage("andar.minutos") private var minutosAndar = 30
    @AppStorage("andar.ritmo") private var ritmo: RitmoAndar = .ligero
    @AppStorage("piscina.nivel") private var nivel: NivelPiscina = .empiezo
    @AppStorage("casa.energia") private var energia: EnergiaCasa = .normal
    @State private var sesion: Sesion?
    @State private var enPiscina = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    if estado.hoy.minutos > 0 {
                        Text("Hoy: \(estado.hoy.minutos) min · \(estado.hoy.kcalQuemadas) kcal")
                            .font(.subheadline.weight(.semibold)).foregroundStyle(.secondary)
                    }
                    Etiqueta("¿Qué quieres hacer hoy?")
                    HStack(spacing: 8) {
                        ForEach(TipoEjercicio.allCases) { t in
                            Button { tipo = t } label: {
                                VStack(spacing: 6) {
                                    Image(systemName: t.icono).font(.title2)
                                    Text(t.rawValue).font(.subheadline.weight(.bold))
                                }
                                .frame(maxWidth: .infinity).padding(.vertical, 14)
                                .background(tipo == t ? t.color.opacity(0.16) : Color.tarjeta,
                                            in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                                .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous)
                                    .stroke(tipo == t ? t.color : Color.linea, lineWidth: tipo == t ? 1.5 : 1))
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    switch tipo {
                    case .andar: andar
                    case .piscina: piscina
                    case .casa: casa
                    }
                }
                .padding(.horizontal).padding(.bottom)
            }
            .pantalla("Ejercicio")
            .fullScreenCover(item: $sesion) { SesionView(sesion: $0) }
            .fullScreenCover(isPresented: $enPiscina) { PiscinaView(nivel: nivel) }
        }
    }

    private var andar: some View {
        let plan = PlanAndar(minutos: minutosAndar, ritmo: ritmo, peso: estado.pesoActual)
        return VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 12) {
                Etiqueta("¿Cuánto tiempo?")
                Segmentos(opciones: [15, 30, 45, 60], seleccion: $minutosAndar, titulo: { "\($0)" }, detalle: { _ in "min" })
                Etiqueta("¿A qué ritmo?")
                Segmentos(opciones: RitmoAndar.allCases, seleccion: $ritmo, titulo: { $0.nombre }, detalle: { "\(Int($0.kmh)) km/h" })
                HStack(spacing: 8) {
                    Dato(valor: plan.km.es(), texto: "km")
                    Dato(valor: "\(plan.pasos)", texto: "pasos aprox.")
                    Dato(valor: "\(plan.kcal)", texto: "kcal")
                }
                ForEach(Array(plan.fases.enumerated()), id: \.offset) { i, f in
                    FilaNumerada(numero: i + 1, titulo: f.nombre, detalle: f.consejo, valor: "\(f.segundos / 60) min", color: .hoja)
                }
                Button { sesion = plan.sesion } label: {
                    Text("Empezar a andar").bold().frame(maxWidth: .infinity).padding(.vertical, 6)
                }
                .buttonStyle(.borderedProminent).tint(.hoja)
            }
            .tarjeta()
            Aviso(titulo: "Si no tienes tiempo de una vez",
                  texto: "Tres paseos de 10 minutos después de cada comida valen lo mismo y ayudan a controlar el azúcar en sangre.",
                  color: .hoja)
        }
    }

    private var piscina: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 12) {
                Etiqueta("¿Cómo nadas?")
                Segmentos(opciones: NivelPiscina.allCases, seleccion: $nivel, titulo: { $0.nombre }, detalle: { "\($0.minutos) min" })
                HStack(spacing: 8) {
                    Dato(valor: "\(nivel.metros)", texto: "metros")
                    Dato(valor: "\(nivel.minutos)", texto: "minutos")
                    Dato(valor: "\(kcalEjercicio(met: nivel.met, peso: estado.pesoActual, minutos: nivel.minutos))", texto: "kcal")
                }
                ForEach(Array(nivel.series.enumerated()), id: \.offset) { i, s in
                    FilaNumerada(numero: i + 1, titulo: s.nombre, detalle: s.descanso.isEmpty ? s.detalle : "\(s.detalle) · \(s.descanso)",
                                 valor: "\(s.metros) m", color: .cielo)
                }
                Button { enPiscina = true } label: {
                    Text("Empezar sesión").bold().frame(maxWidth: .infinity).padding(.vertical, 6)
                }
                .buttonStyle(.borderedProminent).tint(.cielo)
            }
            .tarjeta()
            Aviso(titulo: "La piscina es ideal para empezar",
                  texto: "El agua sostiene tu peso: mueves todo el cuerpo sin castigar rodillas ni espalda. Lleva gorro, gafas y una botella de agua; en la piscina también se suda.")
        }
    }

    private var casa: some View {
        VStack(alignment: .leading, spacing: 12) {
            Etiqueta("¿Cuánta energía tienes?")
            Segmentos(opciones: EnergiaCasa.allCases, seleccion: $energia, titulo: { $0.nombre }, detalle: { "\($0.minutos) min" })
            ForEach(Array(energia.ejercicios.enumerated()), id: \.offset) { i, e in
                FilaNumerada(numero: i + 1, titulo: e.nombre, detalle: nil, valor: "\(e.segundos) s", color: .sol)
            }
            Button { sesion = energia.sesion(peso: estado.pesoActual) } label: {
                Text("Empezar · \(energia.minutos) min").bold().frame(maxWidth: .infinity).padding(.vertical, 6)
            }
            .buttonStyle(.borderedProminent).tint(.sol)
        }
        .tarjeta()
    }
}

private struct FilaNumerada: View {
    let numero: Int
    let titulo: String
    let detalle: String?
    let valor: String
    let color: Color

    var body: some View {
        HStack(spacing: 10) {
            Text("\(numero)").font(.caption.weight(.heavy))
                .frame(width: 28, height: 28)
                .background(color.opacity(0.18), in: Circle())
                .foregroundStyle(color)
            VStack(alignment: .leading, spacing: 1) {
                Text(titulo).font(.subheadline)
                if let detalle { Text(detalle).font(.caption).foregroundStyle(.secondary) }
            }
            Spacer()
            Text(valor).font(.subheadline).monospacedDigit().foregroundStyle(.secondary)
        }
    }
}

// MARK: - Sesión guiada con temporizador (andar / en casa)

struct SesionView: View {
    @Environment(EstadoApp.self) private var estado
    @Environment(\.dismiss) private var cerrar
    let sesion: Sesion

    @State private var indice = 0
    @State private var restante = 0
    @State private var pausado = false
    @State private var terminado = false
    private let reloj = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    private var fase: Fase { sesion.fases[indice] }

    var body: some View {
        VStack(spacing: 18) {
            if terminado {
                Spacer()
                Image(systemName: "checkmark.circle.fill").font(.system(size: 96)).foregroundStyle(sesion.color)
                Text("¡Hecho!").font(.largeTitle.weight(.heavy))
                Text("\(sesion.minutos) minutos · unas \(sesion.kcal) kcal. Paso de ejercicio completado.")
                    .multilineTextAlignment(.center).foregroundStyle(.secondary)
                Spacer()
                Button { cerrar() } label: { Text("Volver").bold().frame(maxWidth: .infinity).padding(.vertical, 6) }
                    .buttonStyle(.borderedProminent)
            } else {
                HStack {
                    Etiqueta("\(sesion.titulo) · \(indice + 1) de \(sesion.fases.count)")
                    Spacer()
                    Button { cerrar() } label: { Image(systemName: "xmark").padding(6) }
                        .buttonStyle(.bordered).clipShape(Circle()).accessibilityLabel("Cerrar")
                }
                Spacer()
                ZStack {
                    Anillo(progreso: Double(restante) / Double(max(fase.segundos, 1)), color: sesion.color, grosor: 16)
                    Text(fase.segundos >= 120 ? String(format: "%d:%02d", restante / 60, restante % 60) : "\(restante)")
                        .font(.system(size: 56, weight: .heavy, design: .rounded)).monospacedDigit()
                        .contentTransition(.numericText(countsDown: true))
                }
                .frame(width: 220, height: 220)
                Text(fase.nombre).font(.title.weight(.heavy)).multilineTextAlignment(.center)
                Text(fase.consejo).foregroundStyle(.secondary).multilineTextAlignment(.center)
                HStack(spacing: 6) {
                    ForEach(sesion.fases.indices, id: \.self) { i in
                        Circle().fill(i <= indice ? sesion.color : Color.linea).frame(width: 8, height: 8)
                    }
                }
                Text(indice + 1 < sesion.fases.count ? "Después: \(sesion.fases[indice + 1].nombre)" : "Última parte")
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
                    .buttonStyle(.borderedProminent).tint(sesion.color)
                }
            }
        }
        .padding(24)
        .background(Color.fondo)
        .onAppear {
            restante = fase.segundos
            UIApplication.shared.isIdleTimerDisabled = true
        }
        .onDisappear { UIApplication.shared.isIdleTimerDisabled = false }
        .onReceive(reloj) { _ in
            guard !pausado, !terminado else { return }
            if restante > 1 { withAnimation { restante -= 1 } } else { siguiente() }
        }
        .sensoryFeedback(.impact, trigger: indice)
        .sensoryFeedback(.success, trigger: terminado)
    }

    private func siguiente() {
        if indice + 1 < sesion.fases.count {
            indice += 1
            restante = fase.segundos
        } else {
            terminado = true
            estado.registrarEjercicio(minutos: sesion.minutos, kcal: sesion.kcal)
        }
    }
}

// MARK: - Sesión de piscina: cronómetro y series para marcar

struct PiscinaView: View {
    @Environment(EstadoApp.self) private var estado
    @Environment(\.dismiss) private var cerrar
    let nivel: NivelPiscina

    @State private var segundos = 0
    @State private var hechas: Set<Int> = []
    @State private var pausado = false
    @State private var resultado: (minutos: Int, kcal: Int)?
    private let reloj = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    var body: some View {
        VStack(spacing: 16) {
            if let r = resultado {
                Spacer()
                Image(systemName: "checkmark.circle.fill").font(.system(size: 96)).foregroundStyle(Color.cielo)
                Text("¡Sesión terminada!").font(.largeTitle.weight(.heavy))
                Text("\(r.minutos) minutos en el agua · unas \(r.kcal) kcal.").foregroundStyle(.secondary)
                Spacer()
                Button { cerrar() } label: { Text("Volver").bold().frame(maxWidth: .infinity).padding(.vertical, 6) }
                    .buttonStyle(.borderedProminent)
            } else {
                HStack {
                    Etiqueta("Piscina · \(nivel.nombre)")
                    Spacer()
                    Button { cerrar() } label: { Image(systemName: "xmark").padding(6) }
                        .buttonStyle(.bordered).clipShape(Circle()).accessibilityLabel("Cerrar")
                }
                Text(String(format: "%d:%02d", segundos / 60, segundos % 60))
                    .font(.system(size: 52, weight: .heavy, design: .rounded)).monospacedDigit()
                    .padding(.top, 12)
                Text("Marca cada serie al terminarla").font(.footnote).foregroundStyle(.secondary)
                ScrollView {
                    VStack(spacing: 0) {
                        ForEach(Array(nivel.series.enumerated()), id: \.offset) { i, s in
                            Button {
                                if hechas.contains(i) { hechas.remove(i) } else { hechas.insert(i) }
                            } label: {
                                HStack(spacing: 12) {
                                    Image(systemName: hechas.contains(i) ? "checkmark.circle.fill" : "circle")
                                        .font(.title2).foregroundStyle(hechas.contains(i) ? Color.cielo : .secondary)
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(s.nombre).font(.body.weight(.semibold)).strikethrough(hechas.contains(i))
                                        Text(s.descanso.isEmpty ? s.detalle : "\(s.detalle) · \(s.descanso)")
                                            .font(.footnote).foregroundStyle(.secondary)
                                    }
                                    Spacer()
                                    Text("\(s.metros) m").font(.footnote).foregroundStyle(.secondary)
                                }
                                .padding(.vertical, 10)
                            }
                            .buttonStyle(.plain)
                            .sensoryFeedback(.selection, trigger: hechas.contains(i))
                            if i < nivel.series.count - 1 { Divider() }
                        }
                    }
                    .tarjeta()
                }
                HStack(spacing: 10) {
                    Button { pausado.toggle() } label: {
                        Text(pausado ? "Seguir" : "Pausa").bold().frame(maxWidth: .infinity).padding(.vertical, 6)
                    }
                    .buttonStyle(.bordered)
                    Button { terminar() } label: {
                        Text("Terminar").bold().frame(maxWidth: .infinity).padding(.vertical, 6)
                    }
                    .buttonStyle(.borderedProminent).tint(.cielo)
                }
            }
        }
        .padding(24)
        .background(Color.fondo)
        .onReceive(reloj) { _ in if !pausado && resultado == nil { segundos += 1 } }
    }

    private func terminar() {
        // Si no se ha usado el cronómetro (menos de 2 min), se cuenta la duración prevista.
        let minutos = segundos < 120 ? nivel.minutos : max(1, Int((Double(segundos) / 60).rounded()))
        let kcal = kcalEjercicio(met: nivel.met, peso: estado.pesoActual, minutos: minutos)
        estado.registrarEjercicio(minutos: minutos, kcal: kcal)
        resultado = (minutos, kcal)
    }
}
