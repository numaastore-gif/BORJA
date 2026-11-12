import Foundation

/// Plan de calorías y macros de una persona.
/// Gasto basal con Mifflin-St Jeor, déficit moderado (máx. 500 kcal o 20 %) y suelos de seguridad.
struct Plan {
    let perfil: Perfil
    let peso: Double

    let basal: Double
    let gasto: Double
    let kcal: Double
    let deficit: Double
    /// kg por semana
    let ritmo: Double
    let faltan: Double
    let semanas: Int
    let proteinas: Double
    let grasas: Double
    let hidratos: Double
    let fibra: Double
    let vasos: Int
    let hierro: Double
    let calcio: Double
    let vitaminaC: Double
    let potasio = 3500.0
    let sodioMax = 2000.0

    init(perfil: Perfil, peso: Double) {
        self.perfil = perfil
        self.peso = peso
        basal = 10 * peso + 6.25 * perfil.altura - 5 * Double(perfil.edad) + (perfil.sexo == .hombre ? 5 : -161)
        gasto = basal * perfil.actividad.factor
        let suelo: Double = perfil.sexo == .hombre ? 1500 : 1200
        kcal = max(suelo, ((gasto - min(500, gasto * 0.2)) / 10).rounded() * 10)
        deficit = gasto - kcal
        ritmo = deficit * 7 / 7700
        faltan = max(0, peso - perfil.objetivo)
        semanas = ritmo > 0 ? Int((faltan / ritmo).rounded(.up)) : 0
        proteinas = max(1.6 * perfil.objetivo, 1.2 * peso).rounded()
        grasas = (kcal * 0.30 / 9).rounded()
        hidratos = ((kcal - proteinas * 4 - grasas * 9) / 4).rounded()
        fibra = max(25, (kcal / 1000 * 14).rounded())
        vasos = min(12, max(6, Int((peso * 30 / 250).rounded())))
        hierro = perfil.sexo == .mujer && perfil.edad < 51 ? 18 : 8
        calcio = perfil.edad > 50 ? 1200 : 1000
        vitaminaC = perfil.sexo == .hombre ? 90 : 75
    }

    var imc: Double { peso / pow(perfil.altura / 100, 2) }
    var imcObjetivo: Double { perfil.objetivo / pow(perfil.altura / 100, 2) }
    var categoriaIMC: String {
        switch imc {
        case ..<18.5: "bajo peso"
        case ..<25: "peso saludable"
        case ..<30: "sobrepeso"
        default: "obesidad"
        }
    }
    var fechaObjetivo: Date { Calendar.current.date(byAdding: .day, value: semanas * 7, to: .now) ?? .now }
    var litrosAgua: Double { Double(vasos) * 0.25 }

    func kcal(para tipo: TipoComida) -> Double { kcal * tipo.fraccion }

    /// Escala la receta para que su ración dé las kcal de esa comida.
    func racion(_ receta: Receta, para tipo: TipoComida? = nil) -> Racion {
        let objetivo = kcal(para: tipo ?? receta.tipo)
        let base = receta.ingredientes.reduce(0.0) { $0 + (Alimentos.tabla[$1.alimento]?.por100.kcal ?? 0) * $1.gramos / 100 }
        let factor = min(1.8, max(0.6, objetivo / max(base, 1)))
        var total = Nutrientes()
        let lineas: [Racion.Linea] = receta.ingredientes.compactMap { ing in
            guard let a = Alimentos.tabla[ing.alimento] else { return nil }
            var g = ing.gramos * factor
            let texto: String
            if let u = a.unidad {
                let n = max(1, Int((g / u.gramos).rounded()))
                g = Double(n) * u.gramos
                texto = "\(n) \(n > 1 ? u.plural : u.singular) (\(Int(g)) g)"
            } else {
                g = g < 20 ? max(1, g.rounded()) : (g / 5).rounded() * 5
                texto = ing.alimento == "aceite" ? "\(Int(g)) g · \((g / 10).es()) cda" : "\(Int(g)) g"
            }
            total = total + a.por100.por(g / 100)
            return Racion.Linea(nombre: a.nombre, gramos: g, texto: texto)
        }
        return Racion(lineas: lineas, total: total, factor: factor)
    }

    /// Combinación de recetas (una por comida) que más se acerca a los macros del día.
    func mejorMenu() -> [TipoComida: String] {
        var mejor: [TipoComida: String] = [:]
        var mejorPuntos = Double.infinity
        let raciones = Dictionary(uniqueKeysWithValues: TipoComida.allCases.map { t in
            (t, Recetas.de(t).map { ($0.id, racion($0, para: t).total) })
        })
        for d in raciones[.desayuno] ?? [] {
            for c in raciones[.comida] ?? [] {
                for n in raciones[.cena] ?? [] {
                    for m in raciones[.merienda] ?? [] {
                        let t = d.1 + c.1 + n.1 + m.1
                        var p = 2 * pow((t.proteinas - proteinas) / proteinas, 2)
                        p += pow((t.hidratos - hidratos) / hidratos, 2)
                        p += pow((t.grasas - grasas) / grasas, 2)
                        if t.fibra < fibra { p += pow((t.fibra - fibra) / fibra, 2) }
                        if p < mejorPuntos {
                            mejorPuntos = p
                            mejor = [.desayuno: d.0, .comida: c.0, .cena: n.0, .merienda: m.0]
                        }
                    }
                }
            }
        }
        return mejor
    }

    /// Comprueba los datos de la bienvenida. Devuelve el error a mostrar o nil.
    static func validar(_ p: Perfil) -> String? {
        if p.edad < 16 || p.edad > 90 { return "La edad debe estar entre 16 y 90 años." }
        if p.altura < 120 || p.altura > 230 { return "Revisa la altura: escríbela en centímetros (por ejemplo, 172)." }
        if p.peso < 35 || p.peso > 300 { return "Revisa el peso actual en kilos." }
        if p.objetivo >= p.peso { return "El peso objetivo tiene que ser menor que el actual." }
        let minimo = 18.5 * pow(p.altura / 100, 2)
        if p.objetivo < minimo {
            return "Ese objetivo queda por debajo de un peso saludable. Con tu altura, el mínimo recomendable es \(minimo.es()) kg."
        }
        return nil
    }
}
