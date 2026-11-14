"""Paleta Teenage Engineering + temas para Textual (oscuros y claros).

OpenTUI (la librería original) es TypeScript/Zig y no corre en Python puro,
así que la TUI usa Textual — el equivalente en Python — con esta estética.
Temas dinámicos: en modo 'auto' siguen la apariencia del sistema (claro/oscuro).
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


def _shade(hex_color: str, factor: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#{:02x}{:02x}{:02x}".format(int(r * factor), int(g * factor), int(b * factor))


def make_theme(name: str, accent: str, dark: bool = True) -> Theme:
    base = name.replace("oc1-", "").replace("-light", "")
    secondary = _PAIRS.get(base, "#00a8ff")
    if dark:
        return Theme(
            name=name,
            primary=accent,
            secondary=secondary,
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
    # claro — cara "OC-1 field" blanca con tinta grafito
    a = _shade(accent, 0.75)
    return Theme(
        name=name,
        primary=a,
        secondary=_shade(secondary, 0.7),
        accent=a,
        foreground="#22201d",
        background="#f4f1ec",
        surface="#ffffff",
        panel="#e7e3dc",
        success="#0a8f4e",
        warning="#a06b00",
        error="#c22500",
        dark=False,
        variables={
            "block-cursor-background": a,
            "block-cursor-foreground": "#f4f1ec",
        },
    )


THEMES: dict[str, Theme] = {}
for _k, _v in ACCENTS.items():
    THEMES[f"oc1-{_k}"] = make_theme(f"oc1-{_k}", _v, dark=True)
    THEMES[f"oc1-{_k}-light"] = make_theme(f"oc1-{_k}-light", _v, dark=False)


def effective_theme(accent: str, mode: str) -> str:
    """accent='orange' + mode='dark'|'light' → nombre de tema Textual."""
    return f"oc1-{accent}-light" if mode == "light" else f"oc1-{accent}"


def accent_of(theme_name: str) -> str:
    """'oc1-orange-light' → 'orange' (nombre base del acento)."""
    return theme_name.replace("oc1-", "").replace("-light", "")


# color del punto de cada pista según sonido (estética de teclas estilo TE)
SOUND_COLORS = {
    "kick": "#00a8ff", "snare": "#00a8ff", "hat": "#00a8ff", "clap": "#00a8ff",
    "saw": "#ff5300", "square": "#ff5300", "sine": "#ff5300", "tri": "#ff5300", "fm": "#ff5300",
    "pluck": "#00d26a", "bell": "#00d26a", "noise": "#f0f0f0",
}


def sound_color(sound: str) -> str:
    return SOUND_COLORS.get(sound, "#e8e6e3")
