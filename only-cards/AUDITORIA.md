# Auditoría de www.only-cards.com

Revisión hecha el 8 de noviembre de 2026 sobre la web en producción: HTML, sitemap, robots, fichas de producto, y navegación con un navegador real en escritorio y en móvil (iPhone 13).

## Qué es la web hoy

- **Plataforma:** Odoo 18 eCommerce (con Click & Collect), montada por agencia.net.
- **Catálogo:** 18 productos sellados de TCG: 15 de Pokémon, 2 de Yu-Gi-Oh! y 1 de Riftbound. 7 están agotados (39 %).
- **Idiomas:** español (por defecto) e inglés.
- **Contacto:** info@only-cards.com, +34 634 220 287 (WhatsApp) e Instagram.
- **Analítica:** Google Analytics 4 (`G-W0G8EV4QQV`), con banner de cookies.
- **Rendimiento:** unas 13 peticiones, ~270 KB, carga completa en ~2,4 s. Está bien: el problema no es la velocidad.

## Problemas encontrados

Por impacto, de mayor a menor.

### Fallos que hay que corregir ya

| # | Problema | Dónde | Efecto |
|---|----------|-------|--------|
| 1 | **El enlace «Condiciones generales de venta» del pie da 404.** Las condiciones reales están en `/terms`. | Pie, en todas las páginas | Mala imagen, y obligación legal de tener las condiciones accesibles (LSSI). |
| 2 | **El filtro de precio muestra precios sin IVA** (6,61 € – 190,08 €) mientras que los productos se ven con IVA (8 € – 230 €). | `/shop`, barra lateral | El cliente ve cifras que no cuadran. Desconfía. |
| 3 | **El título de la página de tienda está en inglés** («Products \| ONLY CARDS») también en la versión española. | `<title>` de `/shop` | Es lo que aparece en Google y en la pestaña del navegador. |
| 4 | **Errata:** «Grantía de devolución de 15 días». | Todas las fichas de producto | Un detalle, pero se ve en cada producto. |
| 5 | **Productos sin descripción** (p. ej. Colección Prémium Ditto). | Fichas | Sin texto no hay SEO ni argumentos de venta. |

### Lo que frena las ventas

- **No hay portada.** La raíz del dominio es directamente el listado de productos: no dice qué es Only Cards, por qué comprar aquí, ni qué ventajas tiene.
- **No hay categorías.** No se puede navegar por juego (Pokémon / Yu-Gi-Oh! / Riftbound), por idioma ni por tipo (caja, ETB, colección, blíster). El menú superior está vacío.
- **La tienda física de Vigo no aparece en ningún sitio.** Odoo tiene configurada la recogida en *Calle Colombia 25 – bajo, 36204 Vigo* con horario (jue, vie y sáb), pero eso solo se descubre en la ficha, dentro del widget de stock. Es una gran ventaja competitiva que no se está aprovechando, ni en la web ni en Google.
- **Faltan señales de confianza** (original y sellado, plazos de envío, devoluciones, atención directa) en la tienda y junto al botón de compra.
- **Los productos agotados son un callejón sin salida.** Solo se ofrece un aviso por email; la tienda vive de WhatsApp y no lo usa ahí.
- **Las preventas no destacan.** «Reserva 12 Noviembre» solo aparece en el nombre: no hay insignia, fecha clara ni cuenta atrás.
- **No se da el precio por sobre** en cajas y blísteres, que es justo lo que compara un jugador.
- **Móvil:** el botón «Añadir a la cesta» desaparece al leer la descripción, y no hay un acceso rápido a WhatsApp.

### Imágenes

- Las 18 fotos tienen tamaños de 300×300 a 1024×1024 y proporciones distintas (apaisadas, verticales, cuadradas).
- Los márgenes y fondos no son coherentes: unas tienen bandas blancas enormes, otras fondo gris o azulado y otras ninguno.
- El listado recorta en cuadrado («cover»), así que productos verticales u horizontales salen cortados.
- Solución entregada en `imagenes/mejoradas/`: 1200×1200, producto completo, centrado, mismo margen y sombra.

### SEO

- No hay `meta description` en ninguna página.
- El JSON-LD de producto de Odoo es mínimo: no incluye descripción, marca, idioma, estado, preventa ni migas de pan.
- No hay datos estructurados de **tienda local** (dirección, coordenadas, horario), así que no se aprovecha el SEO local en Vigo.
- Los nombres de producto mezclan formatos («Yu Gi Oh Lata…», «Riftbound: …», «… Español») y no siguen un patrón SEO.
- El sitemap no incluye `lastmod` en los productos.

## Qué resuelve el script (sin tocar Odoo)

`booster/only-cards-booster.js` se instala pegando una línea en la inyección de código de Odoo. Está probado contra la web real (capturas en `capturas/`):

| Módulo | Qué hace | Problema que resuelve |
|--------|----------|-----------------------|
| Barra de anuncios | Mensajes rotativos: envío, original sellado, devoluciones, recogida en Vigo, WhatsApp | Confianza |
| Cabecera de marca | Presentación de Only Cards encima del catálogo, con sus ventajas | No hay portada |
| Filtros rápidos | Chips por juego (Pokémon 15, Yu-Gi-Oh! 2, Riftbound 1), por idioma (ES/EN) y «Solo disponibles». Recuerda la elección | No hay categorías |
| Insignias | Idioma (ES/EN) y «Preventa · 12 nov» sobre la foto | Preventas e idioma |
| Precio por sobre | «5,56 € / sobre» en cajas y blísteres | Comparar precios |
| Agotados | Botón «Avísame cuando vuelva» que abre WhatsApp con el producto ya escrito | Agotados sin salida |
| Ficha de producto | Bloque de confianza (original, envío, devolución, recogida en Vigo, WhatsApp) y cuenta atrás de preventa | Confianza y urgencia |
| Barra fija en móvil | Nombre, precio y «Añadir a la cesta» siempre visibles al hacer scroll | Conversión en móvil |
| Vistos recientemente | Carrusel con los últimos productos vistos | Recuperar el interés |
| WhatsApp flotante | Botón con el mensaje preparado según la página | Atención directa |
| SEO | Enriquece el JSON-LD de Odoo (descripción, marca, idioma, estado, preventa, SKU), añade migas de pan, la tienda local con dirección y horario, la lista de productos y la `meta description` | SEO y SEO local |
| Correcciones | Repara el enlace roto de condiciones y la errata «Grantía» | Fallos 1 y 4 |
| Envío gratis | Barra de progreso en el carrito (se activa cuando el dueño decida un umbral) | Ticket medio |

Cada módulo se puede desactivar por separado. Si Odoo cambia su HTML, el módulo afectado no hace nada: el script nunca bloquea la tienda. Tampoco se ejecuta dentro del editor de Odoo.

## Lo que conviene arreglar en el propio Odoo

El script es la solución rápida. Lo definitivo es esto (tiempos aproximados):

1. **Condiciones de venta:** cambiar el enlace del pie a `/terms`, o crear la página. *5 min.*
2. **Filtro de precio con IVA:** en *Ajustes → Facturación/Contabilidad → Visualización de precios*, mostrar impuestos incluidos, o revisar la lista de precios del sitio web. *15 min.*
3. **Título de la tienda en español:** *Sitio web → Tienda → Optimizar SEO* en la versión ES. *5 min.*
4. **Categorías de eCommerce:** Pokémon, Yu-Gi-Oh!, Riftbound, One Piece…, y debajo Cajas / ETB / Colecciones / Blísteres / Preventas. Añadirlas al menú. *1-2 h.*
5. **Atributo «Idioma»** (Español / Inglés / Japonés) como filtro nativo. *30 min.*
6. **Página de inicio real**, con novedades, preventas y la tienda de Vigo con mapa. *Medio día.*
7. **Descripción y meta description** en cada producto, con nombres normalizados: «Pokémon – Dominio Delta – Caja 36 sobres (ES)». *15 min por producto.*
8. **Google Business Profile** de la tienda de Vigo, enlazado a la web. *1 h.*
9. **Merchant Center / Google Shopping** con el feed de Odoo. *2-3 h.*
10. **Newsletter y cupón de bienvenida** (con el módulo de marketing por email de Odoo) para captar público en las preventas. *2 h.*
