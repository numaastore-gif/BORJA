import Foundation

/// Recetas con su ración base. La app las escala a las calorías de cada persona.
enum Recetas {
    private static func i(_ alimento: String, _ gramos: Double) -> Ingrediente { Ingrediente(alimento: alimento, gramos: gramos) }

    static let todas: [Receta] = [
        Receta(id: "tostada", nombre: "Tostada de aguacate, huevo y tomate", tipo: .desayuno, minutos: 7,
               ingredientes: [i("pan", 60), i("aguacate", 50), i("huevo", 60), i("tomate", 60)],
               pasos: ["Tuesta el pan.", "Machaca el aguacate con un tenedor, sal y unas gotas de limón.",
                       "Cuece el huevo 8 minutos (o hazlo a la plancha sin aceite).",
                       "Unta el aguacate, pon el huevo en rodajas y el tomate al lado."],
               porQue: "Grasa buena del aguacate, proteína del huevo y pan integral con fibra: te sacia hasta la comida."),
        Receta(id: "yogur", nombre: "Yogur griego con fresas, avena y nueces", tipo: .desayuno, minutos: 3,
               ingredientes: [i("yogur", 200), i("avena", 40), i("fresas", 100), i("nueces", 10)],
               pasos: ["Echa el yogur en un bol.", "Añade los copos de avena.", "Corta las fresas por encima.", "Trocea las nueces y espolvorea."],
               porQue: "Mucha proteína para pocas calorías. Las fresas aportan vitamina C sin apenas azúcar."),
        Receta(id: "tortitas", nombre: "Tortitas de avena y plátano", tipo: .desayuno, minutos: 10,
               ingredientes: [i("avena", 40), i("huevo", 60), i("platano", 100), i("leche", 100)],
               pasos: ["Tritura la avena, el huevo, medio plátano y la leche hasta tener una masa.",
                       "Calienta una sartén antiadherente con unas gotas de aceite.",
                       "Echa la masa en círculos pequeños; 1–2 minutos por lado.", "Sirve con el resto del plátano en rodajas."],
               porQue: "Dulce sin azúcar añadido. La avena da hidratos de absorción lenta."),
        Receta(id: "garbanzos", nombre: "Bol de garbanzos con atún y verduras", tipo: .comida, minutos: 10,
               ingredientes: [i("garbanzos", 200), i("atun", 80), i("tomate", 100), i("pepino", 80), i("aceite", 10)],
               pasos: ["Lava y escurre los garbanzos de bote.", "Corta el tomate y el pepino en dados.",
                       "Mézclalo todo con el atún escurrido.", "Aliña con el aceite, limón, sal y comino."],
               porQue: "Legumbre + pescado: proteína completa y mucha fibra. Sin cocinar."),
        Receta(id: "pollo", nombre: "Pollo a la plancha con arroz integral y verduras", tipo: .comida, minutos: 15,
               ingredientes: [i("pollo", 150), i("arroz", 150), i("verduras", 200), i("aceite", 10)],
               pasos: ["Sazona el pollo con pimentón y ajo en polvo.", "Hazlo a la plancha 4 minutos por lado.",
                       "En la misma sartén saltea las verduras 6 minutos con el aceite.",
                       "Calienta el arroz (vale el de vasito) y monta el plato: mitad verdura."],
               porQue: "El plato fácil en estado puro: ½ verdura, ¼ proteína, ¼ hidratos."),
        Receta(id: "lentejas", nombre: "Lentejas rápidas con verduras", tipo: .comida, minutos: 15,
               ingredientes: [i("lentejas", 250), i("zanahoria", 60), i("pimiento", 60), i("cebolla", 50), i("aceite", 10), i("pan", 30)],
               pasos: ["Pica la cebolla, la zanahoria y el pimiento.", "Sofríe 5 minutos con el aceite.",
                       "Añade las lentejas de bote lavadas, pimentón y un vaso de agua.", "Cuece 8 minutos. Acompaña con el pan."],
               porQue: "Mucho hierro y fibra. El pimiento aporta vitamina C, que ayuda a absorber ese hierro."),
        Receta(id: "tortilla", nombre: "Tortilla francesa con espinacas", tipo: .cena, minutos: 8,
               ingredientes: [i("huevo", 120), i("espinacas", 100), i("pan", 40), i("aceite", 5)],
               pasos: ["Saltea las espinacas 1 minuto con el aceite.", "Bate los huevos con sal.",
                       "Viértelos sobre las espinacas; cuaja y dobla.", "Acompaña con el pan."],
               porQue: "Cena ligera con proteína de calidad y hierro de las espinacas."),
        Receta(id: "salmon", nombre: "Salmón al horno con brócoli y patata", tipo: .cena, minutos: 20,
               ingredientes: [i("salmon", 120), i("brocoli", 200), i("patata", 150), i("aceite", 5)],
               pasos: ["Corta la patata en rodajas finas y hornéala 10 minutos a 200 °C (o 5 al microondas).",
                       "Añade el salmón y el brócoli en ramitos a la bandeja.", "Riega con el aceite, sal y limón.", "Hornea 10–12 minutos más."],
               porQue: "Omega-3 del salmón y vitamina C del brócoli. Todo en una bandeja."),
        Receta(id: "merluza", nombre: "Merluza con crema de calabacín", tipo: .cena, minutos: 15,
               ingredientes: [i("merluza", 150), i("calabacin", 250), i("cebolla", 50), i("patata", 80), i("aceite", 10)],
               pasos: ["Trocea calabacín, cebolla y patata; cúbrelos de agua y cuece 12 minutos.",
                       "Tritura con la mitad del aceite y sal.",
                       "Haz la merluza a la plancha con el resto del aceite, 3 minutos por lado.", "Sirve la crema y el pescado."],
               porQue: "Pocas calorías, mucho volumen. Ideal si llegas con hambre por la noche."),
        Receta(id: "manzana", nombre: "Manzana con crema de cacahuete", tipo: .merienda, minutos: 2,
               ingredientes: [i("manzana", 150), i("cacahuete", 15)],
               pasos: ["Corta la manzana en gajos.", "Moja cada gajo en la crema de cacahuete."],
               porQue: "Fruta con un poco de grasa y proteína: quita el antojo de dulce."),
        Receta(id: "hummus", nombre: "Palitos de zanahoria con hummus", tipo: .merienda, minutos: 3,
               ingredientes: [i("zanahoria", 120), i("hummus", 60)],
               pasos: ["Pela la zanahoria y córtala en palitos.", "Sírvela con el hummus para mojar."],
               porQue: "Crujiente y salado: sustituye a las patatas de bolsa."),
        Receta(id: "queso", nombre: "Queso batido con kiwi y nueces", tipo: .merienda, minutos: 2,
               ingredientes: [i("queso", 150), i("kiwi", 75), i("nueces", 10)],
               pasos: ["Echa el queso batido en un bol.", "Pela y corta el kiwi.", "Añade las nueces troceadas."],
               porQue: "Proteína para llegar a tu objetivo diario. Un kiwi cubre casi toda la vitamina C del día."),
    ]

    static func receta(_ id: String) -> Receta? { todas.first { $0.id == id } }
    static func de(_ tipo: TipoComida) -> [Receta] { todas.filter { $0.tipo == tipo } }

    static let cambios: [(antes: String, despues: String)] = [
        ("Refresco", "Agua con gas y limón"),
        ("Bollería", "Tostada con tomate"),
        ("Patatas de bolsa", "Zanahoria con hummus"),
        ("Picar sin hambre", "Fruta lavada a la vista"),
    ]
}
