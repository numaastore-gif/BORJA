import Foundation

enum Animo: String, CaseIterable, Codable, Identifiable {
    case conGanas = "Con ganas", normal = "Normal", sinGanas = "Sin ganas"
    var id: String { rawValue }
}

enum Energia: String, CaseIterable, Codable, Identifiable {
    case poca = "Poca", normal = "Normal", mucha = "Mucha"
    var id: String { rawValue }
}

enum Objetivo: String, CaseIterable, Codable {
    case comer = "Comer bien", mover = "Moverme", ambos = "Las dos cosas"
}

enum TipoComida: String, CaseIterable, Codable, Identifiable {
    case desayuno = "Desayuno", comida = "Comida", cena = "Cena", picoteo = "Picoteo"
    var id: String { rawValue }
}

struct Receta: Identifiable, Hashable {
    let id: String
    let nombre: String
    let tipo: TipoComida
    let minutos: Int
    let kcal: Int
    let ingredientes: [String]
    let pasos: [String]
}

struct Ejercicio: Identifiable, Hashable {
    let id = UUID()
    let nombre: String
    let segundos: Int
    let consejo: String
}

struct Rutina {
    let energia: Energia
    let minutos: Int
    let descripcion: String
    let ejercicios: [Ejercicio]
}

/// Registro de un día: lo que se guarda para la racha y el progreso.
struct RegistroDia: Codable, Equatable {
    var vasos = 0
    var verdura = false
    var movimiento = false
    var minutosMovimiento = 0
}
