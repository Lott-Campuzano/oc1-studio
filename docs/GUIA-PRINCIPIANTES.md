# Guía para principiantes absolutos

> Nunca has tocado una terminal y vienes de Ableton, FL Studio, Logic o
> GarageBand. Bienvenido: esta guía te lleva de la mano desde cero.
> Si sabes usar un DAW, ya sabes usar OC-1 STUDIO — solo cambia la pantalla.

---

## 1. ¿Qué es esto?

OC-1 STUDIO es un **mini-DAW que vive dentro de la Terminal** (esa ventana
negra con letras que los hackers usan en las películas). Hace lo esencial
de un DAW:

| En tu DAW | En OC-1 STUDIO |
|---|---|
| Pistas / canales | **TRACKS** (panel de la izquierda) |
| Piano roll / step sequencer | **El patrón**: 16 casillas, una nota por casilla |
| Tempo (BPM) | **BPM** (arriba, editable) |
| Tonalidad / escala | **key · scale** (informativo) |
| Knobs de reverb/delay/saturation | **ENCODERS** (abajo a la derecha, se giran con ↑/↓) |
| Presets de instrumento | **PRESETS** (tecla `t`) |
| Exportar / renderizar | **▶ espacio** (suena al momento) o exportar a Strudel / Ableton |
| Versionar proyectos (backup) | **GIT** (tecla `g`) — como "Guardar como… con historial infinito" |

La diferencia: en vez de ratón, escribes o pulsas teclas. Suena raro, pero
es **más rápido** que cualquier ratón: cada acción es 1 tecla.

---

## 2. Abrir la Terminal

**macOS**: `⌘ + espacio` → escribe `Terminal` → `Enter`.
(Abilities → Utilidades → Terminal también vale.)

**Windows**: botón inicio → escribe `powershell` → `Enter`.

**Linux**: `Ctrl + Alt + T`.

Verás una ventana con texto y un punto que parpadea. Eso es todo: ahí
vas a escribir (o pegar) unos comandos.

> 💡 Pegar en Terminal: macOS `⌘V` · Windows `clic derecho` · Linux `Ctrl+Shift+V`.
> Cada línea que veas abajo es **una orden completa**: pégala tal cual y dale `Enter`.

---

## 3. Instalar (una sola vez, ~2 minutos)

Abre la Terminal y pega estas 3 líneas, una por una:

```bash
cd "ruta/a/la/carpeta/oc1-studio"
```
*(Truco en macOS: escribe `cd ` con un espacio y luego **arrastra la carpeta
oc1-studio a la ventana de Terminal** — la ruta se escribe sola, da `Enter`.)*

```bash
python3 -m venv .venv
```
*(Esto crea una "burbuja" de Python dentro de la carpeta, para no tocar nada de tu sistema.)*

```bash
.venv/bin/pip install -e .
```
*(Esto instala OC-1 STUDIO con su única dependencia. Descarga ~10 MB.)*

En **Windows** la última línea es distinta:
```powershell
.venv\Scripts\pip install -e .
```

¿Ves mensajes y al final vuelve el punto parpadeante sin decir "error"?
✅ Instalado.

---

## 4. Arrancar y escuchar tu primer beat

```bash
.venv/bin/oc1studio
```
*(En Windows: `.venv\Scripts\oc1studio`)*

Se abre la interfaz: pista a pista, un secuenciador de 16 pasos, cuatro
encoders y una cinta con la forma de onda. Ahora:

1. Pulsa **`espacio`** → suena el demo `acid_808` por los altavoces del sistema. ▶
2. Pulsa **`espacio`** otra vez → para. ■
3. Pulsa **`↑`/`↓`** mientras seleccionas un ENCODER (con las flechas o el ratón)
   → giras reverb, delay, drive y volumen, como los knobs de tu interfaz de audio.
4. Pulsa **`t`** → la pista seleccionada cambia a otro preset (kick, hats, acid, bells…).
5. Pulsa **`c`** → cambia el color del estudio (naranja/azul/verde/blanco,
   claro u oscuro según tu sistema, como el modo de tu DAW).

¿Quieres verlo sin instalar nada todavía? El demo `demo_chip_boy.py` suena
8-bit de computadora vieja: cárgalo con `l` (abrir).

---

## 5. Editar tu primera pista (el "piano roll" en texto)

Pulsa **`⏎` (Enter)** sobre una pista (o su celda en la cuadrícula). Aparece
una línea de texto — el **patrón**. Funciona así:

```
a1 a1 ~ a2 ~ a1 ~ g1 ~ a1 a1 ~ bb1 ~ a2 ~ ~ e2
```

* Cada palabra = **una semicorchea** (un paso de tu step sequencer, 1/16).
* `~` = silencio (igual que dejar la casilla vacía en tu DAW).
* `a1`, `c#3`, `bb2` = notas: letra + octava. `c#3` es Do sostenido, `bb3` es Si bemol.
* `kick snare hat clap` = batería (como las casillas de un drum rack).

Cambia una `~` por `e3` y dale `Enter`: ya reescribiste la melodía.
Pulsa `s` para **guardar** — eso escribe el archivo `demos/demo_acid_808.py`,
que es **tu proyecto**, editable incluso con el Bloc de notas.

---

## 6. Tu música en el navegador: Strudel (opcional, gratis)

Strudel es como un DAW de live-coding que corre en strudel.cc, sin instalar nada.

* Tecla **`e`** → tu demo se abre en strudel.cc ya cargado. Dale PLAY ahí y
  edita el código en vivo (es la web oficial, `https://strudel.cc`).
* Tecla **`w`** → un "player" local con la misma estética TE y el editor
  embebido, con botones ▶ / ■ / ⧉ copiar.

---

## 7. Usarlo como plugin de Ableton (con Max for Live)

Piénsalo así: OC-1 STUDIO es el **secuenciador** (la "cabeza") y Ableton es
el **sonido** (los instrumentos que ya tienes). Se conectan por dentro de
tu propia máquina — no hay nube ni servidores.

1. En Ableton: crea una pista MIDI → añade un **Max MIDI Effect** vacío.
2. En Max: File → Open → elige `max/oc1-studio-bridge.maxpat`, selecciona
   todo (⌘A), copia, pega en el patcher del dispositivo y guarda (⌘S).
3. En OC-1 STUDIO pulsa **`v`** → aparece `LIVE` en verde.
4. Dale **play** en Ableton. El secuenciador de OC-1 se sincroniza y las
   notas entran por el dispositivo Max: suenan con el instrumento que
   pongas en esa pista (Operator, un drum rack, Serum, lo que quieras).

Sin Ableton: `oc1studio live demos/demo_acid_808.py` hace lo mismo en segundo plano.

---

## 8. Guardar en GitHub (tu backup con historial)

GitHub es como Google Drive para código: guarda cada versión, para siempre,
gratis y público si quieres.

```bash
oc1studio git add-remote origin https://github.com/TU-USUARIO/oc1-studio.git
oc1studio git push
```

*(La primera vez GitHub pedirá entrar: sigue el navegador.)*

Cada vez que guardes un demo y quieras subirlo: `oc1studio git commit -m "cambié el bajo"` → `oc1studio git push`.
En la interfaz es la tecla `g` (panel GIT) — botones COMMIT / PUSH / PULL.

---

## 9. Problemas típicos (y salida)

| Síntoma | Solución |
|---|---|
| `command not found` | No hiciste `cd` a la carpeta, o falta `./` — usa `.venv/bin/oc1studio` |
| No suena nada | El volumen master (encoder VOL) o el volumen del sistema; en Windows revisa que el altavoz predeterminado exista |
| La pantalla se ve partida | Agranda la ventana de la Terminal (mínimo ~100 columnas) |
| `textual` no se instala | Revisa que Python 3.10+ esté: `python3 --version` |
| Pegué el comando y no pasa nada | Los comandos van **uno por línea**, cada uno con su `Enter` |
| Quiero salir de la TUI | `q` (o `ctrl+q`) |

---

## 10. Glosario exprés

* **Terminal / consola**: ventana de texto donde se teclean órdenes.
* **Comando**: una orden escrita (cada bloque gris de esta guía).
* **`.venv`**: burbuja aislada de Python para este proyecto; borrarla no daña nada.
* **pip**: el "App Store" de Python (instala librerías).
* **Repositorio / repo**: tu carpeta de proyecto con historial de versiones (git).
* **Push / Pull**: subir tus cambios a GitHub / bajarlos.
* **UDP/puerto**: el "cable" interno por el que OC-1 habla con Ableton.

¿Dudas? Abre un *issue* en el repositorio de GitHub — los proyectos como
este viven de la gente que pregunta. 🎛️

---

*OC-1 STUDIO es hecho con **GLM-5.3-Flash-Free** y **OpenCode**: código,
documentación y publicación por IA; la música la pones tú.*
