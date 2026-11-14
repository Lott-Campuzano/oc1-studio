"""Motor local ("PyMusic mode"): sintetizador 100% stdlib → WAV.

Sin dependencias externas: osciladores, percusión sintetizada,
FX (drive, echo, reverb-comb), mezcla y escritura de WAV a 44.1 kHz.
"""
from __future__ import annotations

import math
import random
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from .demo import Demo, Track

TAU = math.tau
SR = 44100

_NOTES = {"c": 0, "c#": 1, "db": 1, "d": 2, "d#": 3, "eb": 3, "e": 4, "f": 5,
          "f#": 6, "gb": 6, "g": 7, "g#": 8, "ab": 8, "a": 9, "a#": 10, "bb": 10, "b": 11}
_NOTE_RE = re.compile(r"^([a-g])(#|b)?(-?\d+)$", re.I)

CACHE_DIR = Path.home() / ".oc1studio" / "cache"

_DECAY = {"sine": 0.30, "square": 0.25, "saw": 0.28, "tri": 0.30,
          "pluck": 0.35, "bell": 0.90, "fm": 0.40, "noise": 0.15}


def note_to_freq(token: str) -> float | None:
    """'c#3' → frecuencia en Hz; None si el token no es una nota."""
    m = _NOTE_RE.match(token.strip())
    if not m:
        return None
    name = m.group(1).lower()
    acc = m.group(2) or ""
    octv = int(m.group(3))
    semi = _NOTES[name] + (1 if acc == "#" else -1 if acc == "b" else 0)
    midi = 12 * (octv + 1) + semi
    return 440.0 * 2.0 ** ((midi - 69) / 12.0)


def note_to_midi(token: str) -> int | None:
    """'c#3' → número MIDI (60 = c4); None si no es nota. Para el puente LIVE."""
    m = _NOTE_RE.match(token.strip())
    if not m:
        return None
    name = m.group(1).lower()
    acc = m.group(2) or ""
    octv = int(m.group(3))
    semi = _NOTES[name] + (1 if acc == "#" else -1 if acc == "b" else 0)
    return 12 * (octv + 1) + semi


# ---------------------------------------------------------------- voces

def _env_decay(n: int, decay: float, attack: float = 0.004) -> list[float]:
    a = max(1, int(attack * SR))
    out = []
    for i in range(n):
        out.append(i / a if i < a else math.exp(-(i - a) / (decay * SR)))
    return out


def _mel(shape: str, freq: float, dur: float, gain: float, chip: bool = False) -> list[float]:
    n = int(dur * SR)
    env = _env_decay(n, _DECAY.get(shape, 0.3))
    out = []
    for i in range(n):
        t = i / SR
        p = TAU * freq * t
        frac = (freq * t) % 1.0
        if shape == "sine":
            v = math.sin(p)
        elif shape == "square":
            v = (1.0 if frac < 0.25 else -1.0) if chip else (1.0 if math.sin(p) > 0 else -1.0)
        elif shape == "saw":
            v = 2.0 * frac - 1.0
        elif shape == "tri":
            v = 4.0 * abs(frac - 0.5) - 1.0
        elif shape == "noise":
            v = (1.0 if random.random() < 0.5 else -1.0) if chip else random.uniform(-1.0, 1.0)
        elif shape == "pluck":
            v = (math.sin(p) + 0.4 * math.sin(2.0 * p)) if not chip else (
                (1.0 if frac < 0.5 else -1.0) + 0.5 * (1.0 if frac < 0.25 else -1.0))
        elif shape == "bell":
            v = (math.sin(p) + 0.5 * math.sin(TAU * freq * 2.756 * t)
                 + 0.25 * math.sin(TAU * freq * 5.404 * t))
        else:  # fm
            v = math.sin(p + 3.0 * math.sin(TAU * freq * 2.0 * t))
        out.append(v * env[i] * gain)
    return out


def _kick(dur: float, gain: float, chip: bool = False) -> list[float]:
    n = int(dur * SR)
    out = []
    for i in range(n):
        t = i / SR
        f = 45.0 + 115.0 * math.exp(-t / 0.02)
        if chip:  # pulso cuadrado cayendo, estilo consola de 8 bits
            frac = (f * t) % 1.0
            v = 1.0 if frac < 0.25 else -1.0
            out.append(v * math.exp(-t / 0.18) * gain * 0.9)
        else:
            v = math.sin(TAU * f * t) * math.exp(-t / 0.25)
            click = 0.4 * random.uniform(-1, 1) * math.exp(-t / 0.006)
            out.append((v + click) * gain)
    return out


def _snare(dur: float, gain: float, chip: bool = False) -> list[float]:
    n = int(dur * SR)
    out = []
    for i in range(n):
        t = i / SR
        if chip:  # ruido de 1 bit + tono cuadrado
            nz = 1.0 if random.random() < 0.5 else -1.0
            tone = 1.0 if ((185.0 * t) % 1.0) < 0.5 else -1.0
            out.append((0.7 * nz + 0.4 * tone) * math.exp(-t / 0.1) * gain)
        else:
            v = 0.7 * random.uniform(-1, 1) + 0.5 * math.sin(TAU * 185.0 * t)
            out.append(v * math.exp(-t / 0.12) * gain)
    return out


def _hat(dur: float, gain: float, chip: bool = False) -> list[float]:
    n = int(dur * SR)
    out = []
    prev = 0.0
    for i in range(n):
        t = i / SR
        if chip:  # 1 bit, muy corto
            nz = 1.0 if random.random() < 0.5 else -1.0
            out.append(nz * math.exp(-t / 0.025) * gain * 0.7)
            continue
        nz = random.uniform(-1.0, 1.0)
        v = (nz - prev) * 0.8  # realce de agudos por diferencia
        prev = nz
        out.append(v * math.exp(-t / 0.035) * gain)
    return out


def _clap(dur: float, gain: float, chip: bool = False) -> list[float]:
    n = int(dur * SR)
    out = []
    for i in range(n):
        t = i / SR
        if chip:  # dos ráfagas de ruido de 1 bit
            nz = 1.0 if random.random() < 0.5 else -1.0
            a = math.exp(-t / 0.01) + 0.7 * math.exp(-((t - 0.02) ** 2) / 1e-5)
            out.append(nz * a * gain * 0.7)
            continue
        a = (math.exp(-t / 0.012)
             + 0.8 * math.exp(-((t - 0.014) ** 2) / 2e-5)
             + 0.6 * math.exp(-((t - 0.028) ** 2) / 2e-5)
             + 0.5 * math.exp(-t / 0.09))
        out.append(random.uniform(-1.0, 1.0) * a * gain * 0.8)
    return out


def _segment(tr: Track, tok: str, dur: float, chip: bool = False) -> list[float]:
    s = tr.sound
    if s == "kick":
        return _kick(dur, tr.gain, chip)
    if s == "snare":
        return _snare(dur, tr.gain, chip)
    if s == "hat":
        return _hat(dur, tr.gain, chip)
    if s == "clap":
        return _clap(dur, tr.gain, chip)
    freq = note_to_freq(tok)
    if freq is None:
        return []  # token desconocido ⇒ silencio
    return _mel(s, freq, dur, tr.gain, chip)


# ---------------------------------------------------------------- FX

def _add(buf: list[float], seg: list[float], i0: int) -> None:
    end = min(len(buf), i0 + len(seg))
    for i in range(i0, end):
        buf[i] += seg[i - i0]


def _drive(buf: list[float], amount: float) -> None:
    if amount <= 0.01:
        return
    k = 1.0 + amount * 7.0
    norm = math.tanh(k)
    for i, x in enumerate(buf):
        buf[i] = math.tanh(x * k) / norm


def _echo(buf: list[float], amount: float, step: float) -> None:
    if amount <= 0.01:
        return
    d = max(1, int(step * 3 * SR))  # corchea con puntillo
    g = min(0.5, amount * 0.6)
    for i in range(d, len(buf)):
        buf[i] += buf[i - d] * g


def _reverb(buf: list[float], amount: float) -> None:
    if amount <= 0.01:
        return
    for d, g in ((0.0297, 0.35), (0.0371, 0.30), (0.0411, 0.25), (0.0533, 0.20)):
        D = max(1, int(d * SR * (1.0 + amount)))
        for i in range(D, len(buf)):
            buf[i] += buf[i - D] * g * amount


def _decimate(buf: list[float], hold: int) -> None:
    """Sample-and-hold: baja la tasa efectiva ( crunch de reloj viejo )."""
    if hold <= 1:
        return
    last = 0.0
    for i, x in enumerate(buf):
        if i % hold == 0:
            last = x
        else:
            buf[i] = last


def _quantize(buf: list[float], levels: int) -> None:
    """Cuantización de amplitud ( profundidad de bits baja )."""
    if levels <= 1:
        return
    q = levels - 1
    for i, x in enumerate(buf):
        buf[i] = round(x * q) / q


# ---------------------------------------------------------------- render

def render(demo: Demo) -> list[float]:
    """Mezcla el demo completo (mono) y devuelve las muestras normalizadas."""
    d = demo.normalized()
    chip = d.style == "chip"
    step = 60.0 / d.bpm / 4.0
    total = int(step * d.steps * SR) + SR  # +1 s de cola
    buf = [0.0] * total
    for tr in d.tracks:
        for idx, tok in enumerate(tr.tokens(d.steps)):
            if tok in ("~", "."):
                continue
            seg = _segment(tr, tok, step, chip)
            if seg:
                _add(buf, seg, int(idx * step * SR))
    fx = d.fx
    _drive(buf, fx.get("drive", 0.0))
    _echo(buf, fx.get("delay", 0.0), step)
    _reverb(buf, fx.get("reverb", 0.0))
    if chip:  # post-proceso "computadora vieja": reloj ~7 kHz y 24 niveles
        _decimate(buf, 6)
        _quantize(buf, 24)
    vol = fx.get("volume", 1.0)
    if vol != 1.0:
        for i, x in enumerate(buf):
            buf[i] = x * vol
    peak = max((abs(x) for x in buf), default=1.0) or 1.0
    g = min(4.0, 0.92 / peak)
    if g != 1.0:
        for i, x in enumerate(buf):
            buf[i] = x * g
    return buf


def write_wav(samples: list[float], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        frames = bytearray()
        for s in samples:
            s = max(-1.0, min(1.0, s))
            frames += int(s * 32767).to_bytes(2, "little", signed=True)
        w.writeframes(bytes(frames))
    return path


def render_to_cache(demo: Demo) -> tuple[Path, list[float]]:
    """Renderiza y guarda el WAV en ~/.oc1studio/cache; devuelve (ruta, muestras)."""
    from .demo import slugify
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    samples = render(demo)
    path = CACHE_DIR / f"{slugify(demo.title)}.wav"
    write_wav(samples, path)
    return path, samples


BLOCKS = " ▁▂▃▄▅▆▇█"


def wave_preview(samples: list[float], width: int = 48) -> str:
    """Onda en ASCII (estilo cinta de OC-1)."""
    if not samples:
        return ""
    size = len(samples)
    out = []
    for i in range(width):
        a = int(i * size / width)
        b = max(a + 1, int((i + 1) * size / width))
        chunk = samples[a:b]
        v = max(abs(min(chunk)), abs(max(chunk)))
        out.append(BLOCKS[min(8, int(v * 8))])
    return "".join(out)


# ---------------------------------------------------------------- player

def player_cmd(path: Path) -> list[str]:
    if sys.platform == "darwin":
        return ["afplay", str(path)]
    if sys.platform == "win32":
        return ["powershell", "-NoProfile", "-c",
                f"(New-Object Media.SoundPlayer '{path}').PlaySync();"]
    for cmd in ("aplay", "paplay", "play"):
        if shutil.which(cmd):
            return [cmd, str(path)]
    raise RuntimeError("no hay reproductor de audio (afplay/aplay/paplay)")


def play_file(path: Path) -> None:
    subprocess.run(player_cmd(path), check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def spawn_player(path: Path) -> subprocess.Popen:
    return subprocess.Popen(player_cmd(path), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
