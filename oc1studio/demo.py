"""Modelo de demos: una canción = un archivo .py editable.

Un demo es Python plano, editable a mano:

    from oc1studio.demo import Demo, Track

    demo = Demo(
        title="acid_808",
        bpm=126,
        key="a",
        scale="minor",
        tracks=[
            Track(name="acid", sound="saw", pattern="a1 a1 ~ a2 ~ g1 ~", gain=0.75),
        ],
        fx={"reverb": 0.18, "delay": 0.12, "drive": 0.08, "volume": 0.9},
    )

Reglas de `pattern`: un token por semicorchea (1/16); "~" o "." = silencio.
Notas: c3, c#3 (sostenido), bb3 (bemol). Percusión: kick, snare, hat, clap.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from pathlib import Path

# vocabulario del patrón: sonidos melódicos (tono) y de percusión (ritmo)
MELODIC_SOUNDS = ("sine", "square", "saw", "tri", "pluck", "bell", "fm", "noise")
DRUM_SOUNDS = ("kick", "snare", "hat", "clap")
SOUNDS = MELODIC_SOUNDS + DRUM_SOUNDS
FX_KEYS = ("reverb", "delay", "drive", "volume")   # orden canónico del dict fx


class DemoError(Exception):
    """No se pudo cargar o validar un demo."""


def _clamp(v, lo: float, hi: float) -> float:
    """Fuerza v al rango [lo, hi]; NaN/None/basura → lo (mínimo)."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        v = lo
    return max(lo, min(hi, v))


@dataclass
class Track:
    """Una pista: sonido + patrón de 16 pasos + volumen."""

    name: str = "syn"
    sound: str = "saw"
    pattern: str = "c3 ~ e3 ~"
    gain: float = 0.8

    @classmethod
    def from_obj(cls, obj) -> "Track":
        """Acepta Track, dict o nada y devuelve una Track validada.

        El dict puede traer claves de más (se filtran a los campos
        reales del dataclass) y cualquier valor sucio se normaliza:
        sonido desconocido → 'saw', nombre ≤16 chars, gain en [0, 1.5].
        """
        if isinstance(obj, Track):
            t = obj
        elif isinstance(obj, dict):
            allowed = {f.name for f in fields(cls)}
            t = cls(**{k: v for k, v in obj.items() if k in allowed})
        else:
            raise DemoError(f"pista no válida: {obj!r}")
        sound = str(t.sound).lower()
        if sound not in SOUNDS:
            sound = "saw"   # sonido inventado → el de fábrica
        return cls(
            name=str(t.name)[:16] or "syn",
            sound=sound,
            pattern=str(t.pattern).strip() or "~",   # patrón vacío = silencio
            gain=_clamp(t.gain, 0.0, 1.5),
        )

    def tokens(self, steps: int | None = None) -> list[str]:
        """Lista de tokens del patrón; rellena/recorta a `steps` pasos."""
        toks = self.pattern.split() or ["~"]
        if steps is not None:
            if len(toks) < steps:
                toks = toks + ["~"] * (steps - len(toks))   # relleno con silencios
            toks = toks[:steps]                             # o recorte al largo exacto
        return toks


@dataclass
class Demo:
    """Una canción: tempo, tonalidad, pistas y efectos."""

    title: str = "untitled"
    bpm: float = 128.0
    key: str = "a"
    scale: str = "minor"
    steps: int = 16
    style: str = "clean"        # clean | chip (computadora vieja / 8-bit)
    tracks: list[Track] = field(default_factory=list)
    fx: dict = field(default_factory=dict)

    @classmethod
    def from_obj(cls, obj) -> "Demo":
        """Valida y normaliza un demo desde Track, dict u otro Demo.

        Es el filtro por el que pasa TODO: sin él, un demo del disco
        podría romper el synth o el puente MIDI con valores imposibles.
        """
        if isinstance(obj, Demo):
            d = obj
        elif isinstance(obj, dict):
            allowed = {f.name for f in fields(cls)}   # claves desconocidas → fuera
            d = cls(**{k: v for k, v in obj.items() if k in allowed})
        else:
            raise DemoError("demo no válido: define `demo = Demo(...)`")

        tracks = [Track.from_obj(t) for t in (d.tracks or [])] or [Track()]
        # fx: solo las 4 claves conocidas, recortadas a [0, 1] y redondeadas
        raw_fx = dict(d.fx or {})
        fx = {k: round(_clamp(v, 0.0, 1.0), 2) for k, v in raw_fx.items() if k in FX_KEYS}
        style = str(getattr(d, "style", "clean")).lower()
        if style not in ("clean", "chip"):
            style = "clean"
        return cls(
            title=str(d.title)[:40] or "untitled",
            bpm=round(_clamp(d.bpm, 20, 300), 1),       # 20-300 bpm es lo musical
            key=str(d.key).lower()[:2] or "a",
            scale=str(d.scale).lower()[:12] or "minor",
            steps=int(_clamp(d.steps, 1, 64)),          # 1-64 pasos
            style=style,
            tracks=tracks,
            fx=fx,
        )

    def normalized(self) -> "Demo":
        """Copia validada de sí mismo (para no mutar el original)."""
        return Demo.from_obj(self)


def slugify(text: str) -> str:
    """'¡Mi Demo!' → 'mi-demo': nombre seguro de archivo, ≤40 chars."""
    s = re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-")
    return (s or "untitled")[:40]


def default_demo(title: str = "acid_808") -> Demo:
    """Demo de fábrica: kick + hats + snare + acid bass + bells."""
    return Demo(
        title=title,
        bpm=126.0,
        key="a",
        scale="minor",
        steps=16,
        tracks=[
            Track(name="kick", sound="kick",
                  pattern="kick ~ ~ ~ kick ~ ~ ~ kick ~ ~ ~ kick ~ kick ~", gain=1.0),
            Track(name="hats", sound="hat",
                  pattern="~ ~ hat ~ hat ~ hat ~ hat ~ hat ~ hat ~ hat ~ hat hat", gain=0.5),
            Track(name="snare", sound="snare",
                  pattern="~ ~ ~ ~ snare ~ ~ ~ ~ ~ ~ ~ snare clap ~ ~", gain=0.8),
            Track(name="acid", sound="saw",
                  pattern="a1 a1 ~ a2 ~ a1 ~ g1 ~ a1 a1 ~ bb1 ~ a2 ~ ~ e2", gain=0.75),
            Track(name="bell", sound="bell",
                  pattern="~ ~ a4 ~ ~ ~ e5 ~ ~ ~ c5 ~ ~ ~ a4 ~", gain=0.45),
        ],
        fx={"reverb": 0.18, "delay": 0.12, "drive": 0.08, "volume": 0.9},
    )


def chip_demo(title: str = "chip_boy") -> Demo:
    """Demo de fábrica 8-bit: pulsos cuadrados, ruido 1-bit y eco Game Boy."""
    return Demo(
        title=title,
        bpm=140.0,
        key="e",
        scale="minor",
        steps=16,
        style="chip",
        tracks=[
            Track(name="kick", sound="kick",
                  pattern="kick ~ ~ ~ kick ~ kick ~ kick ~ ~ ~ kick ~ ~ ~ ~", gain=1.0),
            Track(name="noise", sound="hat",
                  pattern="hat hat hat ~ hat ~ hat hat hat ~ hat hat hat ~ hat hat", gain=0.45),
            Track(name="snare", sound="snare",
                  pattern="~ ~ ~ ~ snare ~ ~ ~ ~ ~ ~ ~ snare ~ ~ ~", gain=0.8),
            Track(name="pulse", sound="square",
                  pattern="e2 ~ e2 e3 ~ e2 ~ d2 ~ e2 ~ g2 ~ e2 ~ b2 ~", gain=0.6),
            Track(name="arp", sound="pluck",
                  pattern="e4 b4 e5 ~ d5 b4 g4 ~ e4 b4 e5 ~ fs5 b5 e6 ~", gain=0.5),
        ],
        fx={"reverb": 0.0, "delay": 0.22, "drive": 0.15, "volume": 0.9},
    )


# cabecera que se escribe dentro de cada .py guardado: la "carátula"
# del demo, con la mini-referencia del formato
_HEADER = '''"""{title} — demo OC-1 STUDIO

Edita este archivo: ES tu demo. Cada pista es un Track(...).
pattern: un token por semicorchea; '~' o '.' = silencio.
Notas: c3, c#3, bb3 — percusión: kick, snare, hat, clap.
Sonidos: {sounds}
Reproduce: python -m oc1studio play <archivo>
Strudel:   python -m oc1studio strudel <archivo>
"""
from oc1studio.demo import Demo, Track

'''


def render(demo: Demo) -> str:
    """Serializa el demo como archivo .py legible y editable."""
    d = demo.normalized()

    def q(s: str) -> str:
        """Cadena → literal Python con comillas escapadas."""
        return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'

    def num(x) -> str:
        """Número compacto: 0.9 y no 0.90000000000000002."""
        return f"{float(x):g}"

    # el título entra en un docstring: neutraliza comillas triples
    lines = [_HEADER.format(title=d.title.replace('"""', "''"), sounds=", ".join(SOUNDS))]
    lines.append("demo = Demo(")
    lines.append(f"    title={q(d.title)},")
    lines.append(f"    bpm={num(d.bpm)},")
    lines.append(f"    key={q(d.key)},")
    lines.append(f"    scale={q(d.scale)},")
    lines.append(f"    steps={int(d.steps)},")
    if d.style == "chip":        # el estilo se omite si es el default 'clean'
        lines.append('    style="chip",')
    lines.append("    tracks=[")
    for t in d.tracks:
        lines.append("        Track(")
        lines.append(f"            name={q(t.name)}, sound={q(t.sound)},")
        lines.append(f"            pattern={q(t.pattern)},")
        lines.append(f"            gain={num(t.gain)},")
        lines.append("        ),")
    lines.append("    ],")
    # fx en orden canónico (reverb, delay, drive, volume) y extras al final
    ordered = [k for k in FX_KEYS if k in d.fx] + [k for k in d.fx if k not in FX_KEYS]
    lines.append("    fx={" + ", ".join(f"{q(k)}: {num(d.fx[k])}" for k in ordered) + "},")
    lines.append(")")
    return "\n".join(lines) + "\n"


# detecta los imports de oc1studio en el código del demo: el loader
# ya inyecta Demo/Track en el namespace, así que esos imports sobran
# (y permitirlos ejecutaría código arbitrario del archivo)
_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+oc1studio[\w.]*\s+import\s+[\w, ]+|import\s+oc1studio[\w.]*).*$",
    re.M,
)


def load(path: str | Path) -> Demo:
    """Ejecuta el archivo .py y devuelve el Demo validado.

    Es un exec acotado: el src corre en un namespace propio donde
    solo existen Demo y Track (por eso se borran sus imports del
    archivo). Cualquier excepción del usuario se traduce a DemoError
    con el archivo y la línea en el mensaje.
    """
    path = Path(path)
    src = path.read_text(encoding="utf-8")
    src = _IMPORT_RE.sub("", src)  # el loader ya aporta Demo/Track
    ns: dict = {"Demo": Demo, "Track": Track}
    try:
        exec(compile(src, str(path), "exec"), ns)
    except DemoError:
        raise
    except Exception as e:  # noqa: BLE001 — mensaje útil para el usuario
        raise DemoError(f"{path}: error al ejecutar → {e.__class__.__name__}: {e}") from e
    obj = ns.get("demo")
    if obj is None:
        raise DemoError(f"{path}: el archivo debe definir `demo = Demo(...)`")
    return Demo.from_obj(obj)


def save(demo: Demo, path: str | Path) -> Path:
    """render() → archivo: crea la carpeta si no existe."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(demo), encoding="utf-8")
    return path


def list_demos(directory: str | Path) -> list[Path]:
    """Los .py de una carpeta, ordenados sin distinguir mayúsculas."""
    d = Path(directory)
    if not d.is_dir():
        return []
    return sorted(d.glob("*.py"), key=lambda p: p.name.lower())
