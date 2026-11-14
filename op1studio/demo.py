"""Modelo de demos: una canción = un archivo .py editable.

Un demo es Python plano, editable a mano:

    from op1studio.demo import Demo, Track

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

MELODIC_SOUNDS = ("sine", "square", "saw", "tri", "pluck", "bell", "fm", "noise")
DRUM_SOUNDS = ("kick", "snare", "hat", "clap")
SOUNDS = MELODIC_SOUNDS + DRUM_SOUNDS
FX_KEYS = ("reverb", "delay", "drive", "volume")


class DemoError(Exception):
    """No se pudo cargar o validar un demo."""


def _clamp(v, lo: float, hi: float) -> float:
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
        if isinstance(obj, Track):
            t = obj
        elif isinstance(obj, dict):
            allowed = {f.name for f in fields(cls)}
            t = cls(**{k: v for k, v in obj.items() if k in allowed})
        else:
            raise DemoError(f"pista no válida: {obj!r}")
        sound = str(t.sound).lower()
        if sound not in SOUNDS:
            sound = "saw"
        return cls(
            name=str(t.name)[:16] or "syn",
            sound=sound,
            pattern=str(t.pattern).strip() or "~",
            gain=_clamp(t.gain, 0.0, 1.5),
        )

    def tokens(self, steps: int | None = None) -> list[str]:
        """Lista de tokens del patrón; rellena/recorta a `steps` pasos."""
        toks = self.pattern.split() or ["~"]
        if steps is not None:
            if len(toks) < steps:
                toks = toks + ["~"] * (steps - len(toks))
            toks = toks[:steps]
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
        if isinstance(obj, Demo):
            d = obj
        elif isinstance(obj, dict):
            allowed = {f.name for f in fields(cls)}
            d = cls(**{k: v for k, v in obj.items() if k in allowed})
        else:
            raise DemoError("demo no válido: define `demo = Demo(...)`")

        tracks = [Track.from_obj(t) for t in (d.tracks or [])] or [Track()]
        raw_fx = dict(d.fx or {})
        fx = {k: round(_clamp(v, 0.0, 1.0), 2) for k, v in raw_fx.items() if k in FX_KEYS}
        style = str(getattr(d, "style", "clean")).lower()
        if style not in ("clean", "chip"):
            style = "clean"
        return cls(
            title=str(d.title)[:40] or "untitled",
            bpm=round(_clamp(d.bpm, 20, 300), 1),
            key=str(d.key).lower()[:2] or "a",
            scale=str(d.scale).lower()[:12] or "minor",
            steps=int(_clamp(d.steps, 1, 64)),
            style=style,
            tracks=tracks,
            fx=fx,
        )

    def normalized(self) -> "Demo":
        return Demo.from_obj(self)


def slugify(text: str) -> str:
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


_HEADER = '''"""{title} — demo OP-1 STUDIO

Edita este archivo: ES tu demo. Cada pista es un Track(...).
pattern: un token por semicorchea; '~' o '.' = silencio.
Notas: c3, c#3, bb3 — percusión: kick, snare, hat, clap.
Sonidos: {sounds}
Reproduce: python -m op1studio play <archivo>
Strudel:   python -m op1studio strudel <archivo>
"""
from op1studio.demo import Demo, Track

'''


def render(demo: Demo) -> str:
    """Serializa el demo como archivo .py legible y editable."""
    d = demo.normalized()

    def q(s: str) -> str:
        return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'

    def num(x) -> str:
        return f"{float(x):g}"

    lines = [_HEADER.format(title=d.title.replace('"""', "''"), sounds=", ".join(SOUNDS))]
    lines.append("demo = Demo(")
    lines.append(f"    title={q(d.title)},")
    lines.append(f"    bpm={num(d.bpm)},")
    lines.append(f"    key={q(d.key)},")
    lines.append(f"    scale={q(d.scale)},")
    lines.append(f"    steps={int(d.steps)},")
    if d.style == "chip":
        lines.append('    style="chip",')
    lines.append("    tracks=[")
    for t in d.tracks:
        lines.append("        Track(")
        lines.append(f"            name={q(t.name)}, sound={q(t.sound)},")
        lines.append(f"            pattern={q(t.pattern)},")
        lines.append(f"            gain={num(t.gain)},")
        lines.append("        ),")
    lines.append("    ],")
    ordered = [k for k in FX_KEYS if k in d.fx] + [k for k in d.fx if k not in FX_KEYS]
    lines.append("    fx={" + ", ".join(f"{q(k)}: {num(d.fx[k])}" for k in ordered) + "},")
    lines.append(")")
    return "\n".join(lines) + "\n"


_IMPORT_RE = re.compile(
    r"^\s*(?:from\s+op1studio[\w.]*\s+import\s+[\w, ]+|import\s+op1studio[\w.]*).*$",
    re.M,
)


def load(path: str | Path) -> Demo:
    """Ejecuta el archivo .py y devuelve el Demo validado."""
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
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(demo), encoding="utf-8")
    return path


def list_demos(directory: str | Path) -> list[Path]:
    d = Path(directory)
    if not d.is_dir():
        return []
    return sorted(d.glob("*.py"), key=lambda p: p.name.lower())
