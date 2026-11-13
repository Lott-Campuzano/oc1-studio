"""Paleta Teenage Engineering + temas para Textual.

OpenTUI (la librería original) es TypeScript/Zig y no corre en Python puro,
así que la TUI usa Textual — el equivalente en Python — con esta estética:
fondo carbón, encoders naranja/azul/verde/blanco, tipografía monoespaciada.
"""
from __future__ import annotations

from textual.theme import Theme

ACCENTS = {
    "orange": "#ff5300",
    "blue": "#00a8ff",
    "green": "#00d26a",
    "white": "#f0f0f0",
}
_PAIRS = {"orange": "#00a8ff", "blue": "#ff5300", "green": "#f0f0f0", "white": "#00a8ff"}


def make_theme(name: str, accent: str) -> Theme:
    return Theme(
        name=name,
        primary=accent,
        secondary=_PAIRS.get(name.split("op1-")[-1], "#00a8ff"),
        accent=accent,
        foreground="#e8e6e3",
        background="#121212",
        surface="#1d1d1d",
        panel="#232323",
        success="#00d26a",
        warning="#ffb700",
        error="#ff2b00",
        dark=True,
        variables={
            "block-cursor-background": accent,
            "block-cursor-foreground": "#121212",
        },
    )


THEMES = {f"op1-{k}": make_theme(f"op1-{k}", v) for k, v in ACCENTS.items()}

# color del punto de cada pista según sonido (estética de teclas OP-1)
SOUND_COLORS = {
    "kick": "#00a8ff", "snare": "#00a8ff", "hat": "#00a8ff", "clap": "#00a8ff",
    "saw": "#ff5300", "square": "#ff5300", "sine": "#ff5300", "tri": "#ff5300", "fm": "#ff5300",
    "pluck": "#00d26a", "bell": "#00d26a", "noise": "#f0f0f0",
}


def sound_color(sound: str) -> str:
    return SOUND_COLORS.get(sound, "#e8e6e3")
