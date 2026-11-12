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

## Actualizar la app desde el chat

Cada vez que pides un cambio en el chat, Claude:

1. Cambia el código de la app (`Pasito/`) y la maqueta (`prototipo/`).
2. Vuelve a publicar la maqueta en el mismo enlace.
3. Hace push. GitHub compila la app en un Mac (workflow «App iOS») y, si las claves
   de Apple están configuradas, **sube la nueva versión a TestFlight**. A los 10–30 minutos
   te llega a tu iPhone en la app TestFlight.

## Publicar: configuración inicial (una sola vez)

Para que GitHub pueda subir la app hacen falta una cuenta de desarrollador de Apple y cuatro secretos.

1. **Apple Developer Program** (99 €/año): https://developer.apple.com/programs/
2. **Crea la app en App Store Connect** → Apps → «+» → Nueva app. Plataforma iOS,
   nombre «Pasito» (o el que quieras, si está cogido), idioma español.
   Identificador del paquete: regístralo en
   https://developer.apple.com/account/resources/identifiers con un valor único, por ejemplo
   `com.tunombre.pasito`.
3. **Clave de API**: App Store Connect → Usuarios y acceso → Integraciones →
   App Store Connect API → «+». Acceso: **Administrador**. Descarga el archivo `.p8`
   (solo se puede descargar una vez) y apunta el *Key ID* y el *Issuer ID*.
4. **Team ID**: https://developer.apple.com/account → Membresía.
5. En GitHub: repositorio → Settings → Secrets and variables → Actions.
   - Pestaña **Secrets** → New repository secret:

     | Nombre | Valor |
     |--------|-------|
     | `ASC_KEY_ID` | Key ID de la clave |
     | `ASC_ISSUER_ID` | Issuer ID |
     | `ASC_KEY_P8` | Contenido completo del archivo `.p8` (abre con un editor de texto y copia todo) |
     | `APPLE_TEAM_ID` | Team ID |

   - Pestaña **Variables** → New repository variable: `BUNDLE_ID` = el identificador del paso 2.
6. En TestFlight (dentro de la app en App Store Connect) añádete como probador interno
   e instala la app **TestFlight** en el iPhone.

Mientras no estén los secretos, el workflow solo compila (sirve para comprobar que el código está bien).
Las versiones llegan a **TestFlight**; mandarlas a revisión para la App Store pública se hace
desde App Store Connect (la primera vez hay que rellenar ficha, capturas y privacidad).

## Estructura

```
Pasito/
  PasitoApp.swift          Punto de entrada; aplica la apariencia elegida
  Tema.swift               Colores claro/oscuro, apariencia y componentes comunes
  Assets.xcassets          Icono de la app e imágenes de los platos (una por receta, mismo nombre que su id)
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
