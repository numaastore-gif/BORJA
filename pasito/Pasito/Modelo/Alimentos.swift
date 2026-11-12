import Foundation

/// Tabla de alimentos, valores por 100 g (aproximados, de tablas BEDCA / USDA).
/// Orden: kcal, proteínas, hidratos, grasas, fibra, hierro mg, calcio mg, vitamina C mg, potasio mg, sodio mg.
enum Alimentos {
    private static func a(_ nombre: String, _ v: [Double], unidad: Unidad? = nil) -> Alimento {
        Alimento(nombre: nombre,
                 por100: Nutrientes(kcal: v[0], proteinas: v[1], hidratos: v[2], grasas: v[3], fibra: v[4],
                                    hierro: v[5], calcio: v[6], vitaminaC: v[7], potasio: v[8], sodio: v[9]),
                 unidad: unidad)
    }

    static let tabla: [String: Alimento] = [
        "pan": a("Pan integral", [247, 13, 41, 3.4, 7, 2.5, 107, 0, 250, 450]),
        "aguacate": a("Aguacate", [160, 2, 8.5, 14.7, 6.7, 0.6, 12, 10, 485, 7]),
        "huevo": a("Huevo", [143, 12.6, 0.7, 9.5, 0, 1.8, 56, 0, 138, 142], unidad: Unidad(gramos: 60, singular: "huevo", plural: "huevos")),
        "tomate": a("Tomate", [18, 0.9, 3.9, 0.2, 1.2, 0.3, 10, 14, 237, 5]),
        "yogur": a("Yogur griego 0 %", [59, 10, 3.6, 0.4, 0, 0.1, 110, 0, 141, 36]),
        "avena": a("Copos de avena", [372, 13.5, 58.7, 7, 10, 4.3, 54, 0, 362, 2]),
        "fresas": a("Fresas", [32, 0.7, 5.7, 0.3, 2, 0.4, 16, 59, 153, 1]),
        "nueces": a("Nueces", [654, 15, 7, 65, 6.7, 2.9, 98, 1.3, 441, 2]),
        "platano": a("Plátano", [89, 1.1, 20, 0.3, 2.6, 0.3, 5, 8.7, 358, 1]),
        "leche": a("Leche desnatada", [35, 3.4, 5, 0.1, 0, 0.05, 122, 1, 156, 44]),
        "garbanzos": a("Garbanzos cocidos", [139, 7.1, 17.5, 2.6, 6, 1.5, 38, 0.5, 170, 240]),
        "atun": a("Atún al natural (escurrido)", [116, 26, 0, 1, 0, 1.3, 11, 0, 237, 320]),
        "pepino": a("Pepino", [15, 0.7, 3.6, 0.1, 0.5, 0.3, 16, 2.8, 147, 2]),
        "aceite": a("Aceite de oliva virgen extra", [884, 0, 0, 100, 0, 0.6, 1, 0, 1, 2]),
        "pollo": a("Pechuga de pollo", [110, 23, 0, 1.6, 0, 0.4, 5, 0, 370, 65]),
        "arroz": a("Arroz integral (ya cocido)", [112, 2.3, 23, 0.8, 1.8, 0.5, 10, 0, 79, 5]),
        "verduras": a("Verduras para saltear", [35, 2, 5, 0.3, 2.5, 0.6, 30, 30, 250, 30]),
        "lentejas": a("Lentejas cocidas", [116, 9, 16.3, 0.4, 7.9, 3.3, 19, 1.5, 369, 2]),
        "zanahoria": a("Zanahoria", [41, 0.9, 6.8, 0.2, 2.8, 0.3, 33, 5.9, 320, 69]),
        "pimiento": a("Pimiento rojo", [31, 1, 4.2, 0.3, 2.1, 0.4, 7, 128, 211, 4]),
        "cebolla": a("Cebolla", [40, 1.1, 7.6, 0.1, 1.7, 0.2, 23, 7.4, 146, 4]),
        "espinacas": a("Espinacas frescas", [23, 2.9, 1.4, 0.4, 2.2, 2.7, 99, 28, 558, 79]),
        "salmon": a("Salmón", [208, 20, 0, 13, 0, 0.3, 9, 0, 363, 59]),
        "brocoli": a("Brócoli", [34, 2.8, 4, 0.4, 2.6, 0.7, 47, 89, 316, 33]),
        "patata": a("Patata", [77, 2, 15.7, 0.1, 2.2, 0.8, 12, 19.7, 425, 6]),
        "merluza": a("Merluza", [86, 17, 0, 1.8, 0, 0.3, 30, 0, 300, 100]),
        "calabacin": a("Calabacín", [17, 1.2, 2.2, 0.3, 1, 0.4, 16, 18, 261, 8]),
        "manzana": a("Manzana", [52, 0.3, 11.4, 0.2, 2.4, 0.1, 6, 4.6, 107, 1], unidad: Unidad(gramos: 150, singular: "manzana", plural: "manzanas")),
        "cacahuete": a("Crema de cacahuete 100 %", [588, 25, 12, 50, 6, 1.9, 43, 0, 649, 17]),
        "hummus": a("Hummus", [166, 7.9, 11.6, 9.6, 6, 2.4, 38, 0, 228, 380]),
        "queso": a("Queso fresco batido 0 %", [46, 8, 3.5, 0.1, 0, 0.1, 100, 0, 130, 40]),
        "kiwi": a("Kiwi", [61, 1.1, 11.7, 0.5, 3, 0.3, 34, 92.7, 312, 3], unidad: Unidad(gramos: 75, singular: "kiwi", plural: "kiwis")),
    ]
}
