import Foundation

enum Sexo: String, Codable, CaseIterable, Identifiable {
    case hombre = "Hombre", mujer = "Mujer"
    var id: Self { self }
}

enum Actividad: String, Codable, CaseIterable, Identifiable {
    case sedentaria, ligera, moderada
    var id: Self { self }
    var factor: Double {
        switch self {
        case .sedentaria: 1.2
        case .ligera: 1.375
        case .moderada: 1.55
        }
    }
    var nombre: String {
        switch self {
        case .sedentaria: "Sedentaria"
        case .ligera: "Ligera"
        case .moderada: "Moderada"
        }
    }
    var detalle: String {
        switch self {
        case .sedentaria: "Trabajo sentado, casi no camino"
        case .ligera: "Camino algo o me muevo en el trabajo"
        case .moderada: "Ejercicio 3–5 días por semana"
        }
    }
}

enum Meta: String, Codable, CaseIterable, Identifiable {
    case comer = "Comer bien", mover = "Moverme", ambos = "Las dos cosas"
    var id: Self { self }
    var detalle: String {
        switch self {
        case .comer: "Pico entre horas o como lo primero que pillo"
        case .mover: "Me cuesta empezar a hacer ejercicio"
        case .ambos: "Quiero cambiar un poco de todo"
        }
    }
}

enum Animo: String, Codable, CaseIterable, Identifiable {
    case conGanas = "Con ganas", normal = "Normal", sinGanas = "Sin ganas"
    var id: Self { self }
}

enum TipoComida: String, Codable, CaseIterable, Identifiable {
    case desayuno, comida, cena, merienda
    var id: Self { self }
    var nombre: String {
        switch self {
        case .desayuno: "Desayuno"
        case .comida: "Comida"
        case .cena: "Cena"
        case .merienda: "Media tarde"
        }
    }
    /// Parte de las calorías del día que va a esta comida.
    var fraccion: Double {
        switch self {
        case .desayuno: 0.25
        case .comida: 0.35
        case .cena: 0.25
        case .merienda: 0.15
        }
    }
}

struct Perfil: Codable, Equatable {
    var sexo = Sexo.hombre
    var edad = 35
    var altura = 170.0
    var peso = 80.0
    var objetivo = 72.0
    var actividad = Actividad.ligera
    var meta = Meta.ambos
}

/// Nutrientes de una cantidad de comida (o por 100 g en la tabla de alimentos).
struct Nutrientes: Equatable {
    var kcal = 0.0, proteinas = 0.0, hidratos = 0.0, grasas = 0.0, fibra = 0.0
    var hierro = 0.0, calcio = 0.0, vitaminaC = 0.0, potasio = 0.0, sodio = 0.0

    static func + (a: Nutrientes, b: Nutrientes) -> Nutrientes {
        Nutrientes(kcal: a.kcal + b.kcal, proteinas: a.proteinas + b.proteinas, hidratos: a.hidratos + b.hidratos,
                   grasas: a.grasas + b.grasas, fibra: a.fibra + b.fibra, hierro: a.hierro + b.hierro,
                   calcio: a.calcio + b.calcio, vitaminaC: a.vitaminaC + b.vitaminaC,
                   potasio: a.potasio + b.potasio, sodio: a.sodio + b.sodio)
    }

    func por(_ f: Double) -> Nutrientes {
        Nutrientes(kcal: kcal * f, proteinas: proteinas * f, hidratos: hidratos * f, grasas: grasas * f,
                   fibra: fibra * f, hierro: hierro * f, calcio: calcio * f, vitaminaC: vitaminaC * f,
                   potasio: potasio * f, sodio: sodio * f)
    }
}

struct Unidad {
    let gramos: Double
    let singular: String
    let plural: String
}

struct Alimento {
    let nombre: String
    let por100: Nutrientes
    var unidad: Unidad? = nil
}

struct Ingrediente: Hashable {
    let alimento: String
    let gramos: Double
}

struct Receta: Identifiable, Hashable {
    let id: String
    let nombre: String
    let tipo: TipoComida
    let minutos: Int
    let ingredientes: [Ingrediente]
    let pasos: [String]
    let porQue: String
    /// Nombre de la imagen en Assets (se llama igual que el id).
    var imagen: String { id }
}

/// Una receta ajustada a la ración de una persona.
struct Racion {
    struct Linea: Identifiable {
        let id = UUID()
        let nombre: String
        let gramos: Double
        let texto: String
    }
    let lineas: [Linea]
    let total: Nutrientes
    let factor: Double
}

/// Lo que se guarda de cada día.
struct RegistroDia: Codable, Equatable {
    var vasos = 0
    var comidas: Set<TipoComida> = []
    /// Menú del día: tipo de comida (rawValue) → id de receta. Vacío = el que calcula el plan.
    var menu: [String: String] = [:]
    var minutos = 0
    var kcalQuemadas = 0
    var animo: Animo? = nil
}

struct RegistroPeso: Codable, Identifiable, Equatable {
    var id: Date { fecha }
    let fecha: Date
    let kg: Double
}
