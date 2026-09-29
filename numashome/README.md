# nümashome — landing brutalista

Un único archivo `index.html` (HTML + CSS + JS vanilla). Three.js r128 se carga desde cdnjs.
Ábrelo directamente en el navegador o sírvelo con cualquier servidor estático.

## Secciones → secciones de Shopify

Cada bloque es independiente y lleva prefijo de clase propio, así que se puede
cortar en `sections/*.liquid` sin que un CSS pise a otro:

| Sección        | Clase raíz        | Función JS        |
|----------------|-------------------|-------------------|
| Header         | `.nh-header`      | `initHeader`      |
| Hero 3D        | `.nh-hero`        | `initHero`        |
| Marquee        | `.nh-marquee`     | `initMarquee`     |
| Proceso        | `.nh-process`     | `initProcess`     |
| Laboratorio    | `.nh-lab`         | `initLab`         |
| Colección      | `.nh-collection`  | `initCollection`  |
| Manifiesto     | `.nh-manifesto`   | `initManifesto`   |
| Cifras         | `.nh-stats`       | `initStats`       |
| Newsletter     | `.nh-news`        | `initNewsletter`  |
| Footer         | `.nh-footer`      | `initFooter`      |

- Los colores y las fuentes son tokens en `:root` (`--nh-*`).
- Las imágenes de producto se generan desde el atributo `data-form` de cada tarjeta
  (tipo, seed, altura, torsión, lados, ondulación). En Shopify basta con sustituir
  `.nh-card__img` por la imagen del producto y conservar `.nh-card__wire` para el hover.
- Los botones "Añadir" y "Encargar pieza" emiten `cart:add` por el bus interno: ahí
  es donde se conecta la Cart API (`/cart/add.js`).
- El formulario de newsletter solo simula la respuesta: hay que conectarlo al
  formulario de clientes de Shopify (`{% form 'customer' %}`).
