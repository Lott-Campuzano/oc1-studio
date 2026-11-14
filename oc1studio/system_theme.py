"""Detección del tema del sistema (claro/oscuro) para los temas dinámicos.

macOS: AppleInterfaceStyle · Linux (GNOME): gsettings · resto: dark.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

_CACHE: tuple[float, str] | None = None


def detect_system_mode() -> str:
    """Devuelve 'dark' o 'light' según la apariencia del sistema operativo."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE[1]
    mode = "dark"
    if sys.platform == "darwin":
        try:
            p = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=2,
            )
            mode = "dark" if p.stdout.strip().lower() == "dark" else "light"
        except Exception:
            mode = "dark"
    else:
        gs = shutil.which("gsettings")
        if gs:
            try:
                p = subprocess.run(
                    [gs, "get", "org.gnome.desktop.interface", "color-scheme"],
                    capture_output=True, text=True, timeout=2,
                )
                mode = "dark" if "dark" in (p.stdout or "").lower() else "light"
            except Exception:
                mode = "dark"
    _CACHE = (0.0, mode)
    return mode


def invalidate_cache() -> None:
    """Fuerza una nueva detección en la próxima llamada."""
    global _CACHE
    _CACHE = None
