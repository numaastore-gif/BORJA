import Foundation
import Observation

/// Todo lo que se guarda en el teléfono.
struct Datos: Codable {
    var bienvenidaHecha = false
    var perfil = Perfil()
    var pesos: [RegistroPeso] = []
    var registros: [String: RegistroDia] = [:]
    var recetasHechas: Set<String> = []
}

@Observable
final class EstadoApp {
    private(set) var datos: Datos { didSet { guardar() } }

    private static let clave = "datos.v2"
    private static let formato: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f
    }()

    init() {
        if let data = UserDefaults.standard.data(forKey: Self.clave),
           let d = try? JSONDecoder().decode(Datos.self, from: data) {
            datos = d
        } else {
            datos = Datos()
        }
    }

    private func guardar() {
        if let data = try? JSONEncoder().encode(datos) { UserDefaults.standard.set(data, forKey: Self.clave) }
    }

    static func dia(_ fecha: Date) -> String { formato.string(from: fecha) }

    // MARK: Perfil y plan

    var bienvenidaHecha: Bool {
        get { datos.bienvenidaHecha }
        set { datos.bienvenidaHecha = newValue }
    }
    var perfil: Perfil { datos.perfil }
    var pesos: [RegistroPeso] { datos.pesos }
    var pesoActual: Double { datos.pesos.last?.kg ?? datos.perfil.peso }
    var plan: Plan { Plan(perfil: datos.perfil, peso: pesoActual) }

    func guardarPerfil(_ p: Perfil) {
        datos.perfil = p
        if abs(pesoActual - p.peso) > 0.01 || datos.pesos.isEmpty { registrarPeso(p.peso) }
        datos.registros[Self.dia(.now)]?.menu = [:]
    }

    /// Guarda el peso de hoy (sustituye si ya había uno) y recalcula el menú.
    func registrarPeso(_ kg: Double) {
        let hoy = Calendar.current.startOfDay(for: .now)
        datos.pesos.removeAll { Calendar.current.isDate($0.fecha, inSameDayAs: hoy) }
        datos.pesos.append(RegistroPeso(fecha: hoy, kg: kg))
        datos.pesos.sort { $0.fecha < $1.fecha }
        datos.perfil.peso = kg
        hoy_.menu = [:]
    }

    // MARK: Hoy

    private var hoy_: RegistroDia {
        get { datos.registros[Self.dia(.now)] ?? RegistroDia() }
        set { datos.registros[Self.dia(.now)] = newValue }
    }
    var hoy: RegistroDia { hoy_ }

    var animo: Animo? {
        get { hoy_.animo }
        set { hoy_.animo = newValue }
    }
    var planMinimo: Bool { hoy_.animo == .sinGanas }
    var metaVasos: Int { planMinimo ? 4 : plan.vasos }
    var metaComidas: Int { planMinimo ? 2 : 3 }

    var menu: [TipoComida: String] {
        let guardado = hoy_.menu
        if guardado.count == TipoComida.allCases.count {
            return Dictionary(uniqueKeysWithValues: guardado.compactMap { k, v in TipoComida(rawValue: k).map { ($0, v) } })
        }
        return plan.mejorMenu()
    }
    func receta(de tipo: TipoComida) -> Receta { Recetas.receta(menu[tipo] ?? "") ?? Recetas.de(tipo)[0] }

    private func fijarMenu(_ m: [TipoComida: String]) {
        hoy_.menu = Dictionary(uniqueKeysWithValues: m.map { ($0.key.rawValue, $0.value) })
    }

    func cambiarReceta(de tipo: TipoComida) {
        var m = menu
        let opciones = Recetas.de(tipo)
        let i = opciones.firstIndex { $0.id == m[tipo] } ?? 0
        m[tipo] = opciones[(i + 1) % opciones.count].id
        fijarMenu(m)
        hoy_.comidas.remove(tipo)
    }

    func alternarComida(_ tipo: TipoComida) {
        if hoy_.comidas.contains(tipo) { hoy_.comidas.remove(tipo) } else { hoy_.comidas.insert(tipo) }
    }

    /// «La he comido» desde el detalle de una receta: la pone en el menú si no estaba.
    func comer(_ receta: Receta) {
        var m = menu
        m[receta.tipo] = receta.id
        fijarMenu(m)
        hoy_.comidas.insert(receta.tipo)
        datos.recetasHechas.insert(receta.id)
    }

    func comido(_ tipo: TipoComida) -> Bool { hoy_.comidas.contains(tipo) }

    func nutrientesHoy(soloComidas: Bool) -> Nutrientes {
        let p = plan
        return TipoComida.allCases.reduce(Nutrientes()) { acc, t in
            guard !soloComidas || hoy_.comidas.contains(t) else { return acc }
            return acc + p.racion(receta(de: t), para: t).total
        }
    }

    func tocarVaso(_ i: Int) { hoy_.vasos = hoy_.vasos == i + 1 ? i : i + 1 }
    func alternarAgua() { hoy_.vasos = hoy_.vasos >= metaVasos ? 0 : metaVasos }

    func registrarEjercicio(minutos: Int, kcal: Int) {
        hoy_.minutos += minutos
        hoy_.kcalQuemadas += kcal
    }
    func borrarEjercicioDeHoy() {
        hoy_.minutos = 0
        hoy_.kcalQuemadas = 0
    }

    // MARK: Pasos, racha y semana

    var pasos: [Bool] { [hoy_.vasos >= metaVasos, hoy_.comidas.count >= metaComidas, hoy_.minutos > 0] }
    var pasosHoy: Int { pasos.filter { $0 }.count }
    var diaCompleto: Bool { pasosHoy == 3 }

    private func pasos(de r: RegistroDia) -> Int {
        (r.vasos >= 6 ? 1 : 0) + (r.comidas.count >= 3 ? 1 : 0) + (r.minutos > 0 ? 1 : 0)
    }

    var racha: Int {
        let cal = Calendar.current
        var dia = cal.startOfDay(for: .now)
        if pasosHoy == 0 { dia = cal.date(byAdding: .day, value: -1, to: dia)! }
        var n = 0
        while true {
            let r = Self.dia(dia) == Self.dia(.now) ? (pasosHoy > 0 ? 1 : 0) : pasos(de: datos.registros[Self.dia(dia)] ?? RegistroDia())
            guard r > 0 else { break }
            n += 1
            dia = cal.date(byAdding: .day, value: -1, to: dia)!
        }
        return n
    }

    struct DiaSemana: Identifiable {
        var id: Date { fecha }
        let fecha: Date
        let pasos: Int
        let registro: RegistroDia
    }

    var semana: [DiaSemana] {
        let cal = Calendar.current
        return (0..<7).reversed().map { atras in
            let d = cal.date(byAdding: .day, value: -atras, to: cal.startOfDay(for: .now))!
            let r = datos.registros[Self.dia(d)] ?? RegistroDia()
            return DiaSemana(fecha: d, pasos: atras == 0 ? pasosHoy : pasos(de: r), registro: r)
        }
    }
    var vasosSemana: Int { semana.reduce(0) { $0 + $1.registro.vasos } }
    var minutosSemana: Int { semana.reduce(0) { $0 + $1.registro.minutos } }
    var kcalSemana: Int { semana.reduce(0) { $0 + $1.registro.kcalQuemadas } }
    var recetasHechas: Set<String> { datos.recetasHechas }

    var consejoDelDia: String {
        let consejos = [
            "Llena una botella de \(plan.litrosAgua.es()) litros por la mañana y déjala a la vista. Es toda el agua que necesitas hoy.",
            "Compra verdura ya lavada y cortada. Quitar excusas también es cuidarse.",
            "Pon las zapatillas al lado de la puerta. Salir a andar empieza ahí.",
            "Come sentado y sin pantallas. Notarás antes cuándo estás lleno.",
            "Si un día fallas, no pasa nada. Lo importante es volver mañana.",
            "Antes de picar, bebe un vaso de agua y espera 10 minutos.",
        ]
        let n = Calendar.current.ordinality(of: .day, in: .year, for: .now) ?? 0
        return consejos[n % consejos.count]
    }
}
