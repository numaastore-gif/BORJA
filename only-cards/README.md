# Only Cards: mejoras para only-cards.com

Material para proponer al dueño de [only-cards.com](https://www.only-cards.com), una tienda Odoo 18 de cartas
coleccionables (Pokémon, Yu-Gi-Oh!, Riftbound) con recogida en Vigo.

| Archivo | Qué es |
|---------|--------|
| [PROPUESTA.md](PROPUESTA.md) | Documento para el dueño: hallazgos, mejoras, capturas antes/después y paquetes |
| [AUDITORIA.md](AUDITORIA.md) | Auditoría técnica, comercial y SEO de la web actual |
| [INSTALACION.md](INSTALACION.md) | Cómo instalar y configurar el script en Odoo |
| `booster/only-cards-booster.js` | El script de mejoras: JavaScript sin dependencias, configurable por módulos |
| `herramientas/vista-previa.js` | Inyecta el script en la web real y saca capturas antes/después |
| `imagenes/` | Las 18 fotos de producto: `originales/`, `mejoradas/` (1200×1200, re-encuadradas) y `comparativa.jpg` |
| `herramientas/encuadrar-imagenes.py` | Descarga las fotos de la tienda y las re-encuadra (recorte al producto, lienzo cuadrado, margen y sombra iguales) |
| `herramientas/servidor-demo.py` | Vista previa navegable: la web real con el script y las fotos nuevas aplicadas, en `http://localhost:8080` |
| `capturas/` | Capturas de escritorio y móvil, e `informe.json` con los datos estructurados detectados |

Regenerar las capturas (necesita Playwright y acceso a www.only-cards.com):

```bash
python3 only-cards/herramientas/encuadrar-imagenes.py   # necesita Pillow y numpy
node only-cards/herramientas/vista-previa.js
```

Ver la web mejorada en el navegador (tienda, fichas, filtros y carrito funcionan contra la tienda real, sin modificarla):

```bash
python3 only-cards/herramientas/servidor-demo.py      # http://localhost:8080
DEMO_SIN_BOOSTER=1 DEMO_SIN_IMAGENES=1 python3 only-cards/herramientas/servidor-demo.py 8081   # la web tal cual, para comparar
```

Versión que se abre sin servidor (doble clic en `only-cards/demo/index.html`; necesita internet para estilos y tipografías):

```bash
python3 only-cards/herramientas/exportar-demo.py
```
