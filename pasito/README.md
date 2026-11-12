# Pasito

App de iPhone para personas a las que les cuesta comer bien y hacer ejercicio.
La idea: nada de contar calorías ni rutinas de una hora. Tres pasos pequeños al día
(agua, algo verde, unos minutos de movimiento) y una racha que anima a volver mañana.
Si un día no hay ganas, el plan se encoge en lugar de saltarse.

## Pantallas (v0.1)

| Pestaña   | Qué hace |
|-----------|----------|
| Hoy       | Anillo con los 3 pasos, racha, vasos de agua, ánimo del día («Sin ganas» activa el plan mínimo) y consejo |
| Comer     | El plato fácil (½ verdura, ¼ proteína, ¼ hidratos), recetas de ≤15 min con filtro, cambios pequeños |
| Moverme   | Rutinas sin material de 5, 10 o 15 min según la energía, con temporizador guiado |
| Progreso  | Gráfica de los últimos 7 días, cifras de la semana y logros |
| Bienvenida| Dos preguntas al abrir por primera vez (qué cuesta más, cuánto tiempo hay) |

## Ver el prototipo sin Mac

`prototipo/index.html` es una maqueta interactiva en HTML que imita la app. Ábrela en cualquier navegador.

## Abrir en Xcode

Requisitos: Mac con Xcode 15 o posterior (iOS 17+).

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
  PasitoApp.swift        Punto de entrada
  Tema.swift             Colores y componentes comunes (tarjeta, anillo, aviso)
  Modelo/
    Modelos.swift        Tipos: receta, ejercicio, rutina, registro del día
    Catalogo.swift       Recetas, rutinas, consejos (contenido de ejemplo)
    EstadoApp.swift      Estado, racha, semana; guarda en UserDefaults
  Vistas/
    RaizView.swift       Barra de pestañas y bienvenida
    HoyView.swift
    ComerView.swift      Incluye el plato y el detalle de receta
    MovermeView.swift    Incluye el temporizador de la rutina
    ProgresoView.swift
    BienvenidaView.swift
```

## Pendiente / ideas para depurar

- Recordatorios (notificaciones) para beber agua y moverse.
- Leer pasos de Apple Salud (HealthKit) y contarlos como movimiento.
- Más recetas y lista de la compra semanal.
- Widget de pantalla de inicio con el anillo de hoy.
