import Foundation

enum Catalogo {
    static let recetas: [Receta] = [
        Receta(id: "tostada", nombre: "Tostada de aguacate y huevo", tipo: .desayuno, minutos: 7, kcal: 380,
               ingredientes: ["1 rebanada de pan integral", "½ aguacate maduro", "1 huevo", "Sal, pimienta y unas gotas de limón"],
               pasos: ["Tuesta el pan.", "Machaca el aguacate con limón y sal.", "Haz el huevo a la plancha o cocido.", "Monta y a comer."]),
        Receta(id: "yogur", nombre: "Yogur natural con fruta y avena", tipo: .desayuno, minutos: 3, kcal: 290,
               ingredientes: ["1 yogur natural sin azúcar", "1 plátano o un puñado de fresas", "2 cucharadas de copos de avena", "Canela al gusto"],
               pasos: ["Echa el yogur en un bol.", "Corta la fruta por encima.", "Añade la avena y la canela."]),
        Receta(id: "garbanzos", nombre: "Bol de garbanzos con atún", tipo: .comida, minutos: 10, kcal: 520,
               ingredientes: ["1 bote de garbanzos cocidos (lavados)", "1 lata de atún al natural", "Tomates cherry", "½ pepino", "Aceite de oliva y limón"],
               pasos: ["Escurre y lava los garbanzos.", "Corta tomate y pepino.", "Mezcla todo con el atún.", "Aliña con aceite, limón y sal."]),
        Receta(id: "pollo", nombre: "Pollo a la plancha con verduras de bolsa", tipo: .comida, minutos: 15, kcal: 480,
               ingredientes: ["1 pechuga de pollo en filetes", "1 bolsa de verduras para saltear", "1 cucharada de aceite de oliva", "Pimentón y ajo en polvo"],
               pasos: ["Sazona el pollo con las especias.", "Hazlo a la plancha 4 min por lado.", "En la misma sartén saltea las verduras 6 min.", "Sirve: la mitad del plato, verdura."]),
        Receta(id: "tortilla", nombre: "Tortilla francesa con espinacas", tipo: .cena, minutos: 8, kcal: 310,
               ingredientes: ["2 huevos", "Un puñado de espinacas frescas", "Queso fresco (opcional)", "Sal"],
               pasos: ["Saltea las espinacas 1 minuto.", "Bate los huevos con sal.", "Vierte sobre las espinacas y dobla la tortilla."]),
        Receta(id: "crema", nombre: "Crema de calabacín exprés", tipo: .cena, minutos: 15, kcal: 220,
               ingredientes: ["2 calabacines", "½ cebolla", "1 patata pequeña", "Agua o caldo", "1 quesito (opcional)"],
               pasos: ["Trocea todo y cúbrelo de agua.", "Cuece 12 minutos (o 5 en olla rápida).", "Tritura con el quesito y la sal."]),
        Receta(id: "manzana", nombre: "Manzana con crema de cacahuete", tipo: .picoteo, minutos: 2, kcal: 200,
               ingredientes: ["1 manzana", "1 cucharada de crema de cacahuete 100 %"],
               pasos: ["Corta la manzana en gajos.", "Moja cada gajo en la crema."]),
        Receta(id: "hummus", nombre: "Palitos de zanahoria con hummus", tipo: .picoteo, minutos: 3, kcal: 180,
               ingredientes: ["2 zanahorias", "3 cucharadas de hummus"],
               pasos: ["Pela y corta las zanahorias en palitos.", "Sírvelas con el hummus."]),
    ]

    static let cambios: [(antes: String, despues: String)] = [
        ("Refresco", "Agua con gas y limón"),
        ("Bollería", "Tostada con tomate"),
        ("Patatas de bolsa", "Puñado de frutos secos"),
        ("Picar sin hambre", "Fruta lavada a la vista"),
    ]

    static let consejos = [
        "Deja una botella de agua llena encima de la mesa. Si la ves, la bebes.",
        "Compra verdura ya lavada y cortada. Quitar excusas también es cuidarse.",
        "Pon las zapatillas al lado de la puerta. Salir a caminar empieza ahí.",
        "Come sentado y sin pantallas. Notarás antes cuándo estás lleno.",
        "Si un día fallas, no pasa nada. Lo importante es volver mañana.",
    ]

    static func rutina(_ energia: Energia) -> Rutina {
        switch energia {
        case .poca:
            return Rutina(energia: .poca, minutos: 5, descripcion: "Suave, sin sudar", ejercicios: [
                Ejercicio(nombre: "Marcha en el sitio", segundos: 60, consejo: "Levanta las rodillas a tu ritmo."),
                Ejercicio(nombre: "Sentarse y levantarse de la silla", segundos: 45, consejo: "Despacio, sin dejarte caer."),
                Ejercicio(nombre: "Flexiones contra la pared", segundos: 45, consejo: "Brazos a la altura del pecho."),
                Ejercicio(nombre: "Círculos de brazos", segundos: 45, consejo: "Hacia delante y hacia atrás."),
                Ejercicio(nombre: "Estiramiento y respiración", segundos: 60, consejo: "Inspira en 4, suelta en 6."),
            ])
        case .normal:
            return Rutina(energia: .normal, minutos: 10, descripcion: "Activa el cuerpo", ejercicios: [
                Ejercicio(nombre: "Marcha rápida en el sitio", segundos: 60, consejo: "Mueve también los brazos."),
                Ejercicio(nombre: "Sentadillas", segundos: 45, consejo: "Como si te sentaras en una silla."),
                Ejercicio(nombre: "Flexiones inclinadas en la mesa", segundos: 45, consejo: "Cuerpo recto como una tabla."),
                Ejercicio(nombre: "Zancadas alternas", segundos: 60, consejo: "Paso largo, rodilla de atrás hacia el suelo."),
                Ejercicio(nombre: "Plancha con rodillas", segundos: 30, consejo: "Aprieta el abdomen."),
                Ejercicio(nombre: "Puente de glúteo", segundos: 45, consejo: "Sube la cadera y aprieta."),
                Ejercicio(nombre: "Jumping jacks suaves", segundos: 45, consejo: "O abre y cierra sin saltar."),
                Ejercicio(nombre: "Estiramiento final", segundos: 60, consejo: "Piernas, espalda y cuello."),
            ])
        case .mucha:
            return Rutina(energia: .mucha, minutos: 15, descripcion: "Para días buenos", ejercicios: [
                Ejercicio(nombre: "Calentamiento: marcha", segundos: 60, consejo: "Sube el ritmo poco a poco."),
                Ejercicio(nombre: "Sentadillas", segundos: 60, consejo: "Baja controlando."),
                Ejercicio(nombre: "Flexiones", segundos: 45, consejo: "Con rodillas si lo necesitas."),
                Ejercicio(nombre: "Zancadas", segundos: 60, consejo: "Alterna piernas."),
                Ejercicio(nombre: "Escaladores", segundos: 40, consejo: "Rodillas al pecho, rápido."),
                Ejercicio(nombre: "Plancha", segundos: 45, consejo: "Cuerpo recto."),
                Ejercicio(nombre: "Burpees sin salto", segundos: 45, consejo: "Baja, estira, sube."),
                Ejercicio(nombre: "Puente de glúteo", segundos: 60, consejo: "Pausa arriba 1 segundo."),
                Ejercicio(nombre: "Jumping jacks", segundos: 60, consejo: "¡Último empujón!"),
                Ejercicio(nombre: "Estiramiento final", segundos: 90, consejo: "Respira hondo."),
            ])
        }
    }

    static let estiramientoMinimo = Rutina(energia: .poca, minutos: 2, descripcion: "Plan mínimo", ejercicios: [
        Ejercicio(nombre: "Estira los brazos hacia el techo", segundos: 30, consejo: "Crece hacia arriba."),
        Ejercicio(nombre: "Gira el cuello despacio", segundos: 30, consejo: "Hacia los dos lados."),
        Ejercicio(nombre: "Toca las puntas de los pies", segundos: 30, consejo: "Sin forzar, rodillas sueltas."),
        Ejercicio(nombre: "Respira hondo", segundos: 30, consejo: "Inspira en 4, suelta en 6."),
    ])
}
