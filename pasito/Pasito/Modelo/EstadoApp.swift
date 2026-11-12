import Foundation
import Observation

/// Estado global. Guarda los registros por día en UserDefaults (suficiente para la v0.1).
@Observable
final class EstadoApp {
    var bienvenidaHecha: Bool { didSet { guardar() } }
    var objetivo: Objetivo = .ambos { didSet { guardar() } }
    var energia: Energia = .normal { didSet { guardar() } }
    var animo: Animo? = nil
    var recetasHechas: Set<String> = [] { didSet { guardar() } }
    private(set) var registros: [String: RegistroDia] = [:] { didSet { guardar() } }

    private let defaults = UserDefaults.standard
    private static let formato: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()

    init() {
        bienvenidaHecha = defaults.bool(forKey: "bienvenidaHecha")
        if let raw = defaults.string(forKey: "objetivo"), let o = Objetivo(rawValue: raw) { objetivo = o }
        if let raw = defaults.string(forKey: "energia"), let e = Energia(rawValue: raw) { energia = e }
        recetasHechas = Set(defaults.stringArray(forKey: "recetasHechas") ?? [])
        if let data = defaults.data(forKey: "registros"),
           let r = try? JSONDecoder().decode([String: RegistroDia].self, from: data) {
            registros = r
        }
    }

    private func guardar() {
        defaults.set(bienvenidaHecha, forKey: "bienvenidaHecha")
        defaults.set(objetivo.rawValue, forKey: "objetivo")
        defaults.set(energia.rawValue, forKey: "energia")
        defaults.set(Array(recetasHechas), forKey: "recetasHechas")
        if let data = try? JSONEncoder().encode(registros) { defaults.set(data, forKey: "registros") }
    }

    // MARK: Día de hoy

    static func clave(_ fecha: Date) -> String { formato.string(from: fecha) }

    var hoy: RegistroDia {
        get { registros[Self.clave(.now)] ?? RegistroDia() }
        set { registros[Self.clave(.now)] = newValue }
    }

    var planMinimo: Bool { animo == .sinGanas }
    var metaVasos: Int { planMinimo ? 4 : 6 }
    var rutinaDeHoy: Rutina { planMinimo ? Catalogo.estiramientoMinimo : Catalogo.rutina(energia) }

    func pasosCompletados(_ r: RegistroDia, metaVasos: Int = 6) -> Int {
        (r.vasos >= metaVasos ? 1 : 0) + (r.verdura ? 1 : 0) + (r.movimiento ? 1 : 0)
    }
    var pasosHoy: Int { pasosCompletados(hoy, metaVasos: metaVasos) }
    var diaCompleto: Bool { pasosHoy == 3 }

    /// Días seguidos con al menos un paso hecho. Si hoy aún no hay nada, se cuenta desde ayer.
    var racha: Int {
        let cal = Calendar.current
        var dia = cal.startOfDay(for: .now)
        if pasosHoy == 0 { dia = cal.date(byAdding: .day, value: -1, to: dia)! }
        var n = 0
        while let r = registros[Self.clave(dia)], pasosCompletados(r) > 0 {
            n += 1
            dia = cal.date(byAdding: .day, value: -1, to: dia)!
        }
        return n
    }

    /// Últimos 7 días (de más antiguo a hoy) con los pasos completados.
    var semana: [(fecha: Date, pasos: Int)] {
        let cal = Calendar.current
        return (0..<7).reversed().map { atras in
            let d = cal.date(byAdding: .day, value: -atras, to: .now)!
            let r = registros[Self.clave(d)] ?? RegistroDia()
            return (d, atras == 0 ? pasosHoy : pasosCompletados(r))
        }
    }

    var vasosSemana: Int { semanaRegistros.reduce(0) { $0 + $1.vasos } }
    var minutosSemana: Int { semanaRegistros.reduce(0) { $0 + $1.minutosMovimiento } }
    private var semanaRegistros: [RegistroDia] {
        semana.map { registros[Self.clave($0.fecha)] ?? RegistroDia() }
    }

    // MARK: Acciones

    func tocarVaso(_ i: Int) { hoy.vasos = hoy.vasos == i + 1 ? i : i + 1 }
    func alternarAgua() { hoy.vasos = hoy.vasos >= metaVasos ? 0 : metaVasos }
    func alternarVerdura() { hoy.verdura.toggle() }
    func alternarMovimiento() { hoy.movimiento.toggle() }

    func rutinaTerminada(minutos: Int) {
        hoy.movimiento = true
        hoy.minutosMovimiento += minutos
    }

    func marcarReceta(_ r: Receta) {
        recetasHechas.insert(r.id)
        hoy.verdura = true
    }

    var consejoDelDia: String {
        let n = Calendar.current.ordinality(of: .day, in: .year, for: .now) ?? 0
        return Catalogo.consejos[n % Catalogo.consejos.count]
    }
}
