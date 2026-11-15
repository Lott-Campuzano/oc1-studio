"""Detección del tema del sistema (claro/oscuro) para los temas dinámicos.

macOS: AppleInterfaceStyle · Linux (GNOME): gsettings · resto: dark.
"""
from __future__ import annotations

import shutil
import subprocess
import sys

# memo del último resultado (factor 0.0 = sin caducidad): leer el tema
# implica lanzar un subprocess y no queremos hacerlo en cada repaint
_CACHE: tuple[float, str] | None = None


def detect_system_mode() -> str:
    """Devuelve 'dark' o 'light' según la apariencia del sistema operativo."""
    global _CACHE
    if _CACHE is not None:      # ya detectado antes: reutilizar
        return _CACHE[1]
    mode = "dark"               # default conservador si nada funciona
    if sys.platform == "darwin":
        # macOS: `defaults read` falla (stdout vacío) en modo claro,
        # y dice "Dark" en modo oscuro — de ahí el else → light
        try:
            p = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=2,
            )
            mode = "dark" if p.stdout.strip().lower() == "dark" else "light"
        except Exception:
            mode = "dark"
    else:
        # Linux: solo GNOME expone el color-scheme por gsettings;
        # otros escritorios/WL quedan en el default oscuro
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
    _CACHE = (0.0, mode)        # guardar en memo con TTL "infinito"
    return mode


def invalidate_cache() -> None:
    """Fuerza una nueva detección en la próxima llamada."""
    global _CACHE
    _CACHE = None
