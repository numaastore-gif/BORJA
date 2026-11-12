# Pasito

App de iPhone para personas a las que les cuesta comer bien y hacer ejercicio.
La idea: nada de contar calorías ni rutinas de una hora. Tres pasos pequeños al día
(agua, algo verde, unos minutos de movimiento) y una racha que anima a volver mañana.
Si un día no hay ganas, el plan se encoge en lugar de saltarse.

## Pantallas (v0.3)

| Pestaña    | Qué hace |
|------------|----------|
| Bienvenida | Qué te cuesta más, sexo, edad, altura, peso, peso objetivo y actividad. Valida que el objetivo sea un peso saludable |
| Hoy        | Anillo con 3 pasos (agua, comidas del menú, ejercicio), racha, ánimo («Sin ganas» activa el plan mínimo), kcal y macros que llevas |
| Comer      | Menú del día que cuadra tus macros, con cambio de plato. Recetas con imagen, ingredientes en gramos ajustados a tu ración, pasos, macros y micronutrientes |
| Ejercicio  | Qué quieres hacer hoy: andar (tiempo y ritmo, km, pasos, kcal), piscina (series por nivel, cronómetro) o en casa (rutinas guiadas) |
| Progreso   | Registro y gráfica de peso con línea de objetivo, semana, cifras y logros |
| Mi plan    | IMC, gasto diario, calorías objetivo, ritmo y fecha estimada, macros, explicación de cada nutriente y **apariencia: automática, clara u oscura** |

## Cómo se calcula el plan

- Gasto basal con la fórmula de Mifflin-St Jeor × factor de actividad (1,2 / 1,375 / 1,55).
- Déficit de 500 kcal como máximo (o el 20 % del gasto), sin bajar nunca de 1.500 kcal (hombre) o 1.200 kcal (mujer). Ritmo ≈ 0,4–0,5 kg por semana.
- Proteínas 1,6 g por kilo de peso objetivo; grasas 30 % de las kcal; hidratos el resto; fibra 14 g por cada 1.000 kcal (mín. 25 g).
- Calorías por comida: desayuno 25 %, comida 35 %, cena 25 %, media tarde 15 %. Cada receta se escala a esas calorías y el menú elige la combinación más cercana a los macros.
- Valores de los alimentos por 100 g (aproximados, de tablas BEDCA / USDA) en `Modelo/Alimentos.swift`.
- Cada vez que se registra el peso, el plan y el menú se recalculan.

## Ver el prototipo sin Mac

`prototipo/index.html` es una maqueta interactiva en HTML que imita la app. Ábrela en cualquier navegador.

## Abrir en Xcode

Requisitos: Mac con Xcode 15 o posterior; la app funciona en iOS 17 o posterior.

```bash
brew install xcodegen      # una sola vez
cd pasito
xcodegen                   # genera Pasito.xcodeproj a partir de project.yml
open Pasito.xcodeproj
```

Elige un simulador de iPhone y pulsa ▶︎. Para probar en tu propio iPhone, en
*Signing & Capabilities* selecciona tu equipo (Apple ID).

Sin XcodeGen: crea un proyecto nuevo *iOS App* (SwiftUI) llamado Pasito, borra los
archivos que trae y arrastra dentro la carpeta `Pasito/`.

## Estructura

```
Pasito/
  PasitoApp.swift          Punto de entrada; aplica la apariencia elegida
  Tema.swift               Colores claro/oscuro, apariencia y componentes comunes
  Assets.xcassets          Imágenes de los platos (una por receta, mismo nombre que su id)
  Modelo/
    Modelos.swift          Perfil, nutrientes, recetas, registros
    Alimentos.swift        Tabla de alimentos por 100 g
    Recetas.swift          Las 12 recetas y los cambios pequeños
    Ejercicios.swift       Andar, piscina y rutinas en casa
    Plan.swift             Calorías, macros, escalado de raciones y menú
    EstadoApp.swift        Estado y guardado en el teléfono
  Vistas/
    RaizView.swift         Pestañas y bienvenida
    HoyView.swift
    ComerView.swift        Menú, recetas y detalle de receta
    EjercicioView.swift    Elección, temporizador y sesión de piscina
    ProgresoView.swift
    MiPlanView.swift       Plan, nutrientes y apariencia
    BienvenidaView.swift
```

Las imágenes de los platos son ilustraciones provisionales. Para poner fotos reales,
sustituye `Assets.xcassets/<receta>.imageset/<receta>.png` por la foto (mismo nombre).

## Pendiente / ideas para depurar

- Fotos reales de los platos.
- Recordatorios (notificaciones) para beber agua y moverse.
- Leer pasos de Apple Salud (HealthKit) y contarlos como movimiento.
- Más recetas y lista de la compra semanal.
- Widget de pantalla de inicio con el anillo de hoy.
