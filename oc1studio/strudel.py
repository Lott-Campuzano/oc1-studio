"""Integración con Strudel (tidalcycles/strudel).

Dos modos:
  · share  → abre https://strudel.cc/#<base64-del-código> en el navegador.
  · page   → sirve una página local (estética TE) con el REPL embebido
             vía el web component <strudel-editor> (@strudel/repl en unpkg).
"""
from __future__ import annotations

import base64
import html
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

from .demo import Demo, DRUM_SOUNDS

# traducción de sonidos OC-1 → vocabulario de Strudel:
# DRUM_MAP  percusión OC-1 → samples estándar de strudel (bd, sn, hh…)
# SOUND_MAP ondas limpias → osciladores de strudel ('saw' → 'sawtooth')
# CHIP_MAP  estilo 8-bit: todo se aplana a cuadradas/triángulos toscos
DRUM_MAP = {"kick": "bd", "snare": "sn", "hat": "hh", "clap": "cp",
            "ride": "rd", "tom": "lt", "rim": "rs", "perc": "perc"}
SOUND_MAP = {"sine": "sine", "square": "square", "saw": "sawtooth", "tri": "triangle",
             "pluck": "sine", "bell": "triangle", "fm": "sawtooth", "noise": "noise"}
CHIP_MAP = {"sine": "triangle", "square": "square", "saw": "square", "tri": "triangle",
            "pluck": "square", "bell": "triangle", "fm": "square", "noise": "noise"}
DRUM_MAP = {"kick": "bd", "snare": "sn", "hat": "hh", "clap": "cp",
            "ride": "rd", "tom": "lt", "rim": "rs", "perc": "perc"}   # redefinición idéntica (inofensiva: misma tabla)


def _mini(pattern: str, drum: bool = False) -> str:
    """patrón OC-1 → mini-notación de strudel ('.'/'~' → '~'; drums → bd/sn/hh/cp)."""
    toks = []
    for tok in pattern.split():
        if tok in (".", "~"):
            toks.append("~")
        elif drum:
            toks.append(DRUM_MAP.get(tok.lower(), tok.lower()))
        else:
            toks.append(tok.lower())
    return " ".join(toks) or "~"


def to_strudel(demo: Demo) -> str:
    """Genera el código Strudel equivalente al demo.

    Una línea `$: …` por pista: sample de percusión u oscilador con
    nota; luego gain/room/delay según la pista y el fx global. En
    estilo chip se añaden coarse/crush (menos bits, reloj más tosco).
    """
    d = demo.normalized()
    chip = d.style == "chip"
    # setcpm define el tempo de strudel: ciclos por minuto = bpm/4
    # (un ciclo = un compás de 4 tiempos)
    lines = [f"setcpm({d.bpm:g}/4)"]
    fx = d.fx
    room = fx.get("reverb", 0.0)
    delay = fx.get("delay", 0.0)
    for t in d.tracks:
        drum = t.sound in DRUM_SOUNDS
        pat = _mini(t.pattern, drum)
        parts = []
        if drum:
            parts.append(f's("{pat}")')   # s() = samples de batería
            if chip:
                parts.append(".coarse(12)")   # sampleo a 1/12 de tasa
        else:
            parts.append(f'note("{pat}")')   # note() = tono melódico
            sound = CHIP_MAP.get(t.sound, "square") if chip else SOUND_MAP.get(t.sound, "square")
            parts.append(f'.s("{sound}")')
            if chip:  # computadora vieja: menos bits, reloj más tosco
                parts.append(".coarse(8).crush(4)")
        if t.gain != 1.0:
            parts.append(f".gain({t.gain:g})")   # gain de la pista → gain de strudel
        if room > 0.01:
            parts.append(f".room({room:g})")     # reverb global aplicado por pista
        if delay > 0.01:
            parts.append(f".delay({delay:g})")
        lines.append("$: " + "".join(parts))
    return "\n".join(lines) + "\n"


def share_url(demo: Demo) -> str:
    """URL de strudel.cc con el código en el fragmento (formato oficial share)."""
    b64 = base64.b64encode(to_strudel(demo).encode("utf-8")).decode("ascii")
    return "https://strudel.cc/#" + quote(b64, safe="")


# ---------------------------------------------------------------- player local
# Página del player: HTML+CSS con estética TE (barra de LEDs, botones
# de color) y el web component <strudel-editor> de @strudel/repl —
# el audio lo genera el navegador, este servidor solo entrega el HTML.

_PLAYER_HTML = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OC-1 STUDIO → Strudel</title>
<style>
  :root{--orange:#ff5300;--blue:#00a8ff;--green:#00d26a;--white:#f0f0f0;--bg:#121212;--ink:#e8e6e3}
  *{box-sizing:border-box}
  body{margin:0;height:100vh;display:flex;flex-direction:column;background:var(--bg);color:var(--ink);
       font-family:ui-monospace,Menlo,Consolas,monospace}
  header{display:flex;align-items:center;gap:14px;padding:12px 18px;border-bottom:1px solid #2a2a2a}
  .dot{width:11px;height:11px;border-radius:50%;display:inline-block}
  h1{font-size:13px;letter-spacing:3px;margin:0;color:var(--orange)}
  .spacer{flex:1}
  .meta{color:#8a8a8a;font-size:11px;letter-spacing:1px}
  .btn{border:0;border-radius:9px;padding:10px 16px;font:700 12px ui-monospace,monospace;
       letter-spacing:2px;cursor:pointer;color:#121212}
  .btn:active{transform:translateY(1px)}
  .b-orange{background:var(--orange)}.b-blue{background:var(--blue)}
  .b-green{background:var(--green)}.b-white{background:var(--white)}
  strudel-editor{flex:1;display:block;margin:14px;border:1px solid #2a2a2a;border-radius:12px;overflow:hidden;
       --code-font-family:ui-monospace,Menlo,monospace}
  footer{padding:8px 18px;border-top:1px solid #2a2a2a;color:#7a7a7a;font-size:11px;letter-spacing:1px}
</style></head>
<body>
<header>
  <span class="dot" style="background:var(--orange)"></span>
  <h1>OC-1 STUDIO → STRUDEL</h1>
  <span class="meta">__META__</span>
  <span class="spacer"></span>
  <button class="btn b-blue" id="play">▶ PLAY</button>
  <button class="btn b-white" id="stop">■ STOP</button>
  <button class="btn b-green" id="copy">⧉ COPIAR</button>
  <span class="dot" style="background:var(--blue)"></span>
</header>
<script src="https://unpkg.com/@strudel/repl@latest"></script>
<strudel-editor id="ed" code="__CODE_ATTR__"></strudel-editor>
<script type="text/plain" id="code">__CODE_RAW__</script>
<script>
  const ed = document.getElementById('ed');
  const repl = () => ed.editor ?? ed;            // StrudelMirror: evaluate / stop / setCode
  document.getElementById('play').onclick = () => repl().evaluate();
  document.getElementById('stop').onclick = () => { try { repl().stop(); } catch {} };
  document.getElementById('copy').onclick = async () => {
    const code = ed.code ?? document.getElementById('code').textContent;
    try { await navigator.clipboard.writeText(code); flash('✓ COPIADO'); }
    catch { flash('✗ SIN PERMISO'); }
  };
  function flash(msg){
    const b = document.getElementById('copy'), o = b.textContent;
    b.textContent = msg; setTimeout(() => b.textContent = o, 1200);
  }
</script>
<footer>OC-1 STUDIO · hecho con GLM-5.3-Flash-Free + OpenCode · servidor local · el audio lo reproduce strudel en tu navegador</footer>
</body></html>
"""


def player_html(demo: Demo) -> str:
    """Rellena la plantilla con el código Strudel y la ficha del demo.

    El código va dos veces: como atributo del <strudel-editor>
    (escapado para HTML) y en un <script type="text/plain"> de
    respaldo para el botón COPIAR.
    """
    code = to_strudel(demo)
    d = demo.normalized()
    meta = f"{d.title} · {d.bpm:g} bpm · {len(d.tracks)} pistas"
    return (_PLAYER_HTML
            .replace("__META__", html.escape(meta))
            .replace("__CODE_ATTR__", html.escape(code, quote=True))
            .replace("__CODE_RAW__", html.escape(code)))


class StrudelServer:
    """Sirve la página del player en 127.0.0.1 (hilo daemon).

    Solo GET /: una página que se regenera con update() cuando la
    TUI guarda cambios — el navegador recarga y sigue con su REPL.
    """

    def __init__(self, demo: Demo, port: int = 0):
        self.html = player_html(demo)
        # port=0 → el SO asigna un puerto libre (evita colisiones)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", port), self._make_handler())
        self.port = self.httpd.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}/"
        self.thread = threading.Thread(target=self.httpd.serve_forever,
                                       daemon=True, name="oc1-strudel")
        self.thread.start()

    def _make_handler(self):
        """Fábrica del handler: sirve outer.html con no-store (siempre fresco)."""
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                data = outer.html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):  # silencioso
                pass

        return Handler

    def update(self, demo: Demo) -> None:
        """Regenera la página (la TUI la llama al guardar el demo)."""
        self.html = player_html(demo)

    def stop(self) -> None:
        """Apaga el servidor y libera el puerto."""
        self.httpd.shutdown()
        self.httpd.server_close()


def launch_player(demo: Demo, port: int = 0) -> StrudelServer:
    """Atajo: construye y arranca el servidor del player."""
    return StrudelServer(demo, port=port)
