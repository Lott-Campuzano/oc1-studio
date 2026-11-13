# OP-1 STUDIO

Estudio de música **en la terminal** con estética **Teenage Engineering** (OP-1):
secuenciador de 16 pasos, encoders ASCII, cuatro acentos de color (naranja, azul,
verde, blanco), demos guardados como **archivos `.py` editables** y **integración git**
para clonar, guardar cambios y subirlos a GitHub.

```
● OP-1 STUDIO   demo: acid_808   ·   126 BPM   ·   a minor   ·   ■
 ┌ TRACKS ───────┐ ┌ SECUENCIADOR ─────────────────────────┐ ┌ ENCODERS ─┐
 │ ● kick · kick │ │ PISTA │ 1  2  3  4  5  6 …            │ │ REVERB    │
 │ ● acid · saw  │ │ ● kick│ kick ~ ~ ~ kick ~ ~ …         │ │ ╭───╮ 18% │
 │ ● bell · bell │ │ ● acid│ a1 a1 ~ a2 ~ a1 ~ g1 …        │ │ DELAY     │
 └───────────────┘ └───────────────────────────────────────┘ └───────────┘
```

## Instalación

```bash
cd op1-studio
python3 -m venv .venv
.venv/bin/pip install -e .          # única dependencia: textual
```

Requisitos: Python ≥ 3.10, git (opcional, para la integración git),
y un reproductor del sistema: `afplay` (macOS), `aplay/paplay` (Linux),
o PowerShell (Windows) — todo automático.

## Uso

```bash
op1studio                       # abre la interfaz TUI (o: python -m op1studio)
op1studio play demos/demo_acid_808.py      # renderiza y suena (sintetizador local)
op1studio code demos/demo_acid_808.py      # imprime el código Strudel
op1studio strudel demos/demo_acid_808.py   # abre strudel.cc con el demo cargado
op1studio strudel --page demo.py           # player local con REPL Strudel embebido
op1studio new "mi-beat"                    # crea demos/mi-beat.py
op1studio list                             # lista los demos
```

### Teclas de la TUI

| Tecla      | Acción                          |
|------------|---------------------------------|
| `espacio`  | ▶/■ render + play (local)       |
| `s`        | guardar demo como `.py`         |
| `l`        | abrir demo                      |
| `e`        | abrir en **strudel.cc** (share) |
| `w`        | player local con Strudel (web)  |
| `g`        | panel **git**                   |
| `o`        | ajustes (color, auto-commit…)   |
| `a` / `d`  | añadir / borrar pista           |
| `t`        | aplicar preset a la pista       |
| `c`        | cambiar acento de color (TE)    |
| `↑/↓` en encoder | girar el encoder          |
| `⏎` en la pista o celda | editar patrón      |
| `q`        | salir                           |

Ctrl+P abre la paleta de comandos de Textual.

## Los demos son archivos `.py` editables

Cada demo es Python plano — ábrelo con tu editor y cámbialo a mano:

```python
from op1studio.demo import Demo, Track

demo = Demo(
    title="acid_808",
    bpm=126,
    key="a", scale="minor",
    tracks=[
        Track(name="acid", sound="saw",
              pattern="a1 a1 ~ a2 ~ a1 ~ g1 ~ a1 ~ bb1 ~ a2 ~ e2 ~", gain=0.75),
    ],
    fx={"reverb": 0.18, "delay": 0.12, "drive": 0.08, "volume": 0.9},
)
```

* `pattern`: **un token por semicorchea**; `~` o `.` = silencio.
* Notas: `c3`, `c#3` (sostenido), `bb3` (bemol). Percusión: `kick snare hat clap`.
* Sonidos: `sine square saw tri pluck bell fm noise kick snare hat clap`.

## Dos motores

1. **Sintetizador local** (100% stdlib): osciladores + percusión sintetizada +
   drive/echo/reverb → WAV 44.1 kHz → `afplay`/`aplay`/PowerShell. Sin dependencias.
2. **Strudel** (live coding en el navegador):
   * `e` → abre `strudel.cc/#<base64>` (formato share oficial) con el patrón convertido.
   * `w` → sirvo una página local (estética TE) con el REPL `<strudel-editor>`
     (`@strudel/repl` vía unpkg) y botones ▶/■/⧉; el audio lo genera Strudel.

## Git / GitHub

```bash
op1studio git init                                   # convierte la carpeta en repo
op1studio git add-remote origin https://github.com/tu-usuario/op1-demos.git
op1studio git commit -m "demo: acid_808"             # add -A + commit
op1studio git push                                   # almacena en GitHub
op1studio git pull                                   # baja cambios
op1studio git clone https://github.com/alguien/demos.git
```

En la TUI (tecla `g`) hay botones para **STATUS / COMMIT / PUSH / PULL /
REMOTE / CLONE / INIT / LOG**, y en Ajustes (`o`) puedes activar
**auto-commit al guardar** para versionar cada cambio de tus demos.
Autenticación con GitHub: HTTPS + token o SSH — la resuelve tu git de siempre.

## ¿OpenTUI?

[OpenTUI](https://opentui.com) es TypeScript/Zig y no corre dentro de un programa
Python, así que la interfaz usa **Textual** (el equivalente en Python) recreando
la estética: encoders ASCII giratorios, barra de encabezado con puntos de color,
botones de tecla OP-1 y 4 temas de acento intercambiables (`c`).

## Estructura

```
op1studio/
├── app.py      interfaz TUI (Textual, estética TE)
├── cli.py      línea de comandos
├── demo.py     modelo Demo/Track + guardar/cargar .py
├── synth.py    motor local (stdlib): render → WAV → player
├── strudel.py  codegen Strudel + share URL + player local
├── gitops.py   git: init/clone/commit/push/pull/remotes
├── settings.py ~/.op1studio/config.json
└── theme.py    paleta Teenage Engineering + temas Textual
demos/          tus demos (.py)
```
