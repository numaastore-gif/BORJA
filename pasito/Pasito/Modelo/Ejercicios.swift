import SwiftUI

struct Fase: Identifiable, Hashable {
    let id = UUID()
    let nombre: String
    let segundos: Int
    let consejo: String
}

/// Una sesión guiada con temporizador (andar o en casa).
struct Sesion: Identifiable {
    let id = UUID()
    let titulo: String
    let fases: [Fase]
    let minutos: Int
    let kcal: Int
    let color: Color
}

/// kcal ≈ MET × kg × horas.
func kcalEjercicio(met: Double, peso: Double, minutos: Int) -> Int {
    Int((met * peso * Double(minutos) / 60).rounded())
}

enum TipoEjercicio: String, CaseIterable, Identifiable {
    case andar = "Andar", piscina = "Piscina", casa = "En casa"
    var id: Self { self }
    var icono: String {
        switch self {
        case .andar: "figure.walk"
        case .piscina: "figure.pool.swim"
        case .casa: "house"
        }
    }
    var color: Color {
        switch self {
        case .andar: .hoja
        case .piscina: .cielo
        case .casa: .sol
        }
    }
}

// MARK: - Andar

enum RitmoAndar: String, CaseIterable, Identifiable {
    case tranquilo, ligero, rapido
    var id: Self { self }
    var nombre: String {
        switch self {
        case .tranquilo: "Tranquilo"
        case .ligero: "Ligero"
        case .rapido: "Rápido"
        }
    }
    var kmh: Double {
        switch self {
        case .tranquilo: 4
        case .ligero: 5
        case .rapido: 6
        }
    }
    var met: Double {
        switch self {
        case .tranquilo: 3.0
        case .ligero: 3.5
        case .rapido: 4.8
        }
    }
}

struct PlanAndar {
    let minutos: Int
    let ritmo: RitmoAndar
    let peso: Double

    var km: Double { ritmo.kmh * Double(minutos) / 60 }
    var pasos: Int { Int(km * 1350) }
    var kcal: Int { kcalEjercicio(met: ritmo.met, peso: peso, minutos: minutos) }
    var fases: [Fase] {
        let calentar = min(5, Int((Double(minutos) / 6).rounded()))
        return [
            Fase(nombre: "Calienta: paso suave", segundos: calentar * 60, consejo: "Ve soltando piernas y brazos."),
            Fase(nombre: "Paso \(ritmo.nombre.lowercased()) (\(Int(ritmo.kmh)) km/h)", segundos: (minutos - 2 * calentar) * 60,
                 consejo: "Puedes hablar, pero no cantar. Ese es el ritmo."),
            Fase(nombre: "Vuelta a la calma", segundos: calentar * 60, consejo: "Baja el ritmo y respira."),
        ].filter { $0.segundos > 0 }
    }
    var sesion: Sesion { Sesion(titulo: "Andar", fases: fases, minutos: minutos, kcal: kcal, color: .hoja) }
}

// MARK: - Piscina

struct SeriePiscina: Identifiable, Hashable {
    let id = UUID()
    let nombre: String
    let detalle: String
    let descanso: String
    let metros: Int
}

enum NivelPiscina: String, CaseIterable, Identifiable {
    case empiezo, medio, bien
    var id: Self { self }
    var nombre: String {
        switch self {
        case .empiezo: "Empiezo"
        case .medio: "Me defiendo"
        case .bien: "Nado bien"
        }
    }
    var met: Double {
        switch self {
        case .empiezo: 5.8
        case .medio: 7
        case .bien: 8.3
        }
    }
    var minutos: Int {
        switch self {
        case .empiezo: 25
        case .medio: 35
        case .bien: 45
        }
    }
    var series: [SeriePiscina] {
        switch self {
        case .empiezo: [
            SeriePiscina(nombre: "Calentamiento", detalle: "4 × 25 m braza suave", descanso: "descansa 30 s", metros: 100),
            SeriePiscina(nombre: "Piernas con tabla", detalle: "4 × 25 m", descanso: "descansa 30 s", metros: 100),
            SeriePiscina(nombre: "Nado", detalle: "6 × 25 m a tu estilo", descanso: "descansa 40 s", metros: 150),
            SeriePiscina(nombre: "Vuelta a la calma", detalle: "2 × 25 m espalda muy suave", descanso: "", metros: 50),
        ]
        case .medio: [
            SeriePiscina(nombre: "Calentamiento", detalle: "200 m suave mezclando estilos", descanso: "", metros: 200),
            SeriePiscina(nombre: "Piernas con tabla", detalle: "4 × 50 m", descanso: "descansa 20 s", metros: 200),
            SeriePiscina(nombre: "Crol", detalle: "8 × 50 m a ritmo cómodo", descanso: "descansa 20 s", metros: 400),
            SeriePiscina(nombre: "Brazos con pull-buoy", detalle: "4 × 25 m", descanso: "descansa 20 s", metros: 100),
            SeriePiscina(nombre: "Vuelta a la calma", detalle: "100 m espalda", descanso: "", metros: 100),
        ]
        case .bien: [
            SeriePiscina(nombre: "Calentamiento", detalle: "300 m progresivo", descanso: "", metros: 300),
            SeriePiscina(nombre: "Técnica", detalle: "6 × 50 m (25 ejercicio + 25 nado)", descanso: "descansa 15 s", metros: 300),
            SeriePiscina(nombre: "Serie principal", detalle: "4 × 200 m crol a ritmo constante", descanso: "descansa 30 s", metros: 800),
            SeriePiscina(nombre: "Velocidad", detalle: "8 × 25 m rápido", descanso: "descansa 30 s", metros: 200),
            SeriePiscina(nombre: "Vuelta a la calma", detalle: "200 m suave", descanso: "", metros: 200),
        ]
        }
    }
    var metros: Int { series.reduce(0) { $0 + $1.metros } }
}

// MARK: - En casa

enum EnergiaCasa: String, CaseIterable, Identifiable {
    case poca, normal, mucha
    var id: Self { self }
    var nombre: String { rawValue.capitalized }
    var minutos: Int {
        switch self {
        case .poca: 5
        case .normal: 10
        case .mucha: 15
        }
    }
    var ejercicios: [Fase] {
        func f(_ n: String, _ s: Int, _ c: String) -> Fase { Fase(nombre: n, segundos: s, consejo: c) }
        switch self {
        case .poca: return [
            f("Marcha en el sitio", 60, "Levanta las rodillas a tu ritmo."),
            f("Sentarse y levantarse de la silla", 45, "Despacio, sin dejarte caer."),
            f("Flexiones contra la pared", 45, "Brazos a la altura del pecho."),
            f("Círculos de brazos", 45, "Hacia delante y hacia atrás."),
            f("Estiramiento y respiración", 60, "Inspira en 4, suelta en 6."),
        ]
        case .normal: return [
            f("Marcha rápida en el sitio", 60, "Mueve también los brazos."),
            f("Sentadillas", 45, "Como si te sentaras en una silla."),
            f("Flexiones inclinadas en la mesa", 45, "Cuerpo recto como una tabla."),
            f("Zancadas alternas", 60, "Paso largo, rodilla de atrás hacia el suelo."),
            f("Plancha con rodillas", 30, "Aprieta el abdomen."),
            f("Puente de glúteo", 45, "Sube la cadera y aprieta."),
            f("Jumping jacks suaves", 45, "O abre y cierra sin saltar."),
            f("Estiramiento final", 60, "Piernas, espalda y cuello."),
        ]
        case .mucha: return [
            f("Calentamiento: marcha", 60, "Sube el ritmo poco a poco."),
            f("Sentadillas", 60, "Baja controlando."),
            f("Flexiones", 45, "Con rodillas si lo necesitas."),
            f("Zancadas", 60, "Alterna piernas."),
            f("Escaladores", 40, "Rodillas al pecho, rápido."),
            f("Plancha", 45, "Cuerpo recto."),
            f("Burpees sin salto", 45, "Baja, estira, sube."),
            f("Puente de glúteo", 60, "Pausa arriba 1 segundo."),
            f("Jumping jacks", 60, "¡Último empujón!"),
            f("Estiramiento final", 90, "Respira hondo."),
        ]
        }
    }
    func sesion(peso: Double) -> Sesion {
        Sesion(titulo: "En casa", fases: ejercicios, minutos: minutos,
               kcal: kcalEjercicio(met: 4, peso: peso, minutos: minutos), color: .sol)
    }
}
