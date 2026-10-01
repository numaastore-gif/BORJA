# Análisis de programas STEP 7 Classic → Excel de E/S y causa-efecto

Herramientas para documentar un proyecto STEP 7 V5.x (archivado `.zip`/`.zap`)
sin tener STEP 7 instalado: descompila los bloques MC7 a AWL, reconstruye la
lógica booleana de cada `=`, `S` y `R`, expande las llamadas a FB/FC con los
operandos reales y genera un Excel con entradas, salidas, marcas,
temporizadores, DB, matriz causa-efecto, referencias cruzadas, avisos y una
hoja **Consulta** (escribes `A22.3`, `46M2` o una palabra del comentario y te
lista qué entradas activan / permiten / bloquean esa salida).

## Pasos

1. **Exportar el proyecto a JSON** (`exportador/`, .NET 8). Usa la librería
   abierta [DotNetSiemensPLCToolBoxLibrary](https://github.com/jogibear9988/DotNetSiemensPLCToolBoxLibrary)
   para leer el proyecto y descompilar MC7. Clónala junto a este repositorio
   (ver la ruta en `Exp.csproj`) y crea dos ficheros vacíos
   `externalDlls/libnodave_jfkmod.dll` y `libnodave_jfkmod64.dll` en ella (solo
   se usan para comunicación online).

   ```bash
   dotnet run -c Release --project analisis_plc/exportador -- RUTA/PROYECTO.s7p salida/
   ```
   Genera `cpus.json` y un `progN.json` por programa S7 (bloques, AWL por
   segmento, interfaces, DB y tabla de símbolos).

2. **Analizar**: `python analisis_plc/analizar.py salida/prog3.json salida/prog3.pkl`
3. **Generar el Excel**:
   `python analisis_plc/generar_excel.py salida/prog3.pkl analisis_plc/C600_LANGHAMMER/config.json salida.xlsx`
   (`config.json` lleva los datos de portada).

## Límites conocidos

- Los saltos (`SPB`, `SPBN`, `SPA`, `SPL`) se modelan como condiciones de
  camino; las condiciones muy largas se resumen.
- Accesos indirectos (punteros, `DB[...]`) y temporizadores por software dentro
  de FB no se resuelven por completo; se avisa en la hoja de avisos.
- Sin el plano eléctrico, la hoja del plano se deduce del BMK del símbolo
  (convención Langhammer: hoja 200+byte para entradas y 400+byte para salidas) y
  queda marcada como pendiente de verificar.
- La traducción al español de los comentarios es orientativa (glosario).
