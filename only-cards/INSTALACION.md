# Instalar el Booster en Odoo

Hay dos formas. La A es la más sencilla.

## A. Pegar el script en la inyección de código

1. Entrar en Odoo como administrador y abrir **Sitio web**.
2. Pulsar **Editar** → pestaña **Tema** → bajar hasta **Avanzado** → **Inyección de código**.
   (Según la versión también está en *Sitio web → Configuración → Ajustes → Código personalizado*.)
3. En el cuadro **Fin de `</body>`**, pegar:

   ```html
   <script>
   window.ONLY_CARDS_BOOSTER_CONFIG = {
     instagram: "https://www.instagram.com/TU_PERFIL/",
     envioGratisDesde: null   // p. ej. 100 para mostrar la barra de envío gratis
   };
   </script>
   <script>
   /* aquí va el contenido completo de booster/only-cards-booster.js */
   </script>
   ```

4. Guardar y abrir la tienda en una ventana privada para comprobarlo.

## B. Subirlo como archivo

1. *Sitio web → Configuración → Archivos adjuntos* (o desde el editor): subir `only-cards-booster.js`
   y copiar su URL pública (`/web/content/…`).
2. En la inyección de código, pegar `<script src="/web/content/…/only-cards-booster.js" defer></script>`
   y, antes de esa línea, el bloque de configuración del paso A.

## Configuración

Todo es opcional. Lo que no se ponga usa el valor por defecto que hay al principio del script.

| Clave | Para qué sirve |
|-------|----------------|
| `whatsapp` | Número en formato internacional sin `+` (`34634220287`) |
| `instagram` | URL del perfil. Se añade al SEO (`sameAs`) |
| `envio`, `devolucion` | Textos de confianza |
| `envioGratisDesde` | Importe en €. Con `null` no se muestra la barra de envío gratis |
| `recogida` | Dirección y horario de la tienda de Vigo; `null` para ocultarla |
| `modulos.<nombre>` | `false` para desactivar un módulo concreto |
| `franquicias` | Reglas para clasificar productos por nombre (cuando haya categorías en Odoo ya no hacen falta) |
| `enlacesRotos`, `textosACorregir` | Arreglos puntuales de la plantilla |

Ejemplo: desactivar la cabecera de marca y la barra de anuncios.

```js
window.ONLY_CARDS_BOOSTER_CONFIG = { modulos: { hero: false, barraAnuncios: false } };
```

> **A comprobar con el dueño:** el horario de recogida se ha leído de la configuración de Click & Collect
> de Odoo (jueves 17:15–20:15, viernes 17:30–20:30, sábado 10:30–14:30). Confirmadlo antes de publicarlo.

## Comprobar que funciona

- Tienda: debe salir la cabecera morada y los filtros «Todo · Pokémon · Yu-Gi-Oh! …».
- Ficha: bloque de confianza bajo «Añadir a la cesta», y en móvil la barra fija al hacer scroll.
- SEO: pegar la URL de una ficha en <https://search.google.com/test/rich-results>. Debe detectar *Producto* y *Ruta de navegación*.

## Quitarlo

Borrar los bloques de la inyección de código. El script no guarda nada en Odoo. Solo usa el
`localStorage` del navegador para recordar los filtros y los productos vistos.

## Vista previa sin instalar nada

```bash
node only-cards/herramientas/vista-previa.js
```

Abre la web real con Playwright, inyecta el script y guarda capturas antes y después en `only-cards/capturas/`,
además de un `informe.json` con los datos estructurados detectados. Termina con error si algún módulo falla.
