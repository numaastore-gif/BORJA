# Instrucciones para Claude

Este repositorio tiene dos proyectos: `guardias/` (herramienta Python) y `pasito/` (app de iPhone).

## Pasito (`pasito/`)

App de iPhone (SwiftUI, iOS 17+) de dieta y ejercicio para personas a las que les cuesta empezar.
Todo el texto de la app y de los commits va en español.

**Cada cambio que pida el usuario se aplica en los dos sitios, en el mismo turno:**

1. **App real**: código en `pasito/Pasito/`. El proyecto de Xcode se genera con XcodeGen
   desde `pasito/project.yml` (no se versiona el `.xcodeproj`).
2. **Maqueta visual**: `pasito/prototipo/index.html`, publicada como Artifact en
   https://claude.ai/artifact/9n9NwD7TAWBay29jM2SKWq. Al terminar, vuelve a publicarla
   en esa misma URL (Artifact, `url` = esa dirección) para que el usuario la vea.

**Publicar una actualización**: hacer commit y push a la rama de la sesión. El workflow
`.github/workflows/ios.yml` compila la app en un Mac de GitHub en cada push que toque
`pasito/` y, si las claves de App Store Connect están en los secretos del repositorio,
la sube a TestFlight con un número de compilación nuevo.

- Después del push, comprueba que el job **Compilar** termina en verde (herramientas
  `mcp__github__actions_list` / `mcp__github__get_job_logs`). Si falla, corrige y vuelve a
  hacer push. No des el cambio por terminado con la compilación en rojo.
- Sube `MARKETING_VERSION` en `pasito/project.yml` cuando el cambio sea visible para el usuario
  (0.3 → 0.4…). El número de compilación lo pone el workflow.
- Las imágenes de los platos están en `pasito/Pasito/Assets.xcassets/<id-receta>.imageset/`.
- Los valores nutricionales de `Modelo/Alimentos.swift` deben venir de tablas reales (BEDCA/USDA).
- No bajes los mínimos de seguridad del plan (1.500 kcal hombre / 1.200 mujer, IMC objetivo ≥ 18,5).
