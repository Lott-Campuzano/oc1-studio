"""Configuración persistente de OC-1 STUDIO (~/.oc1studio/config.json).

Un solo JSON plano, sin dependencias: load() lo fusiona con DEFAULTS
(por si faltan claves o el archivo no existe) y save() lo reescribe
completo. También migra configs de eras anteriores sin quejarse.
"""
from __future__ import annotations

import json
from pathlib import Path

# dónde vive la config; CONFIG_FILE es la fuente de verdad
CONFIG_DIR = Path.home() / ".oc1studio"
_OLD_DIR = Path.home() / ".op1studio"   # renombrado: migración silenciosa
CONFIG_FILE = CONFIG_DIR / "config.json"

# valores de fábrica — toda clave nueva añadida aquí hereda un valor
# seguro para usuarios con config vieja en el disco
DEFAULTS = {
    "accent": "orange",         # orange | blue | green | white
    "appearance": "auto",       # auto (sigue al sistema) | dark | light
    "steps": 16,                # pasos del secuenciador
    "auto_commit": False,       # commit automático en git al guardar
    "demo_dir": "demos",        # carpeta de demos (relativa a cwd)
    "volume": 0.9,
    "live_send_port": 7647,     # OC-1 → Max for Live (notas)
    "live_recv_port": 7648,     # Max for Live → OC-1 (reloj de 16avos)
}


def load() -> dict:
    """Config efectiva: DEFAULTS + lo que haya en disco (migrado si hace falta)."""
    # 1) partir de los valores de fábrica
    cfg = dict(DEFAULTS)
    try:
        # 2) superponer el JSON del usuario (claves no listadas quedan como default)
        cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001 — config corrupta ⇒ valores por defecto
        pass
    if not CONFIG_FILE.exists():
        # 3) si nunca hubo config nueva pero sí la antigua (era OP-1), copiarla
        old = _OLD_DIR / "config.json"
        if old.exists():  # migra la config de la era OP-1
            try:
                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                CONFIG_FILE.write_text(old.read_text(encoding="utf-8"))
                cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
            except Exception:
                pass
    # 4) normalizar valores heredados de versiones anteriores
    a = str(cfg.get("accent", ""))
    if a.startswith("oc1-"):        # antes se guardaba con prefijo de tema
        cfg["accent"] = a.replace("oc1-", "").replace("-light", "")
    if cfg.get("appearance") not in ("auto", "dark", "light"):
        cfg["appearance"] = DEFAULTS["appearance"]
    if cfg.get("accent") not in DEFAULTS.get("accent", "") and cfg["accent"] not in ("orange", "blue", "green", "white"):
        cfg["accent"] = "orange"    # acento inválido ⇒ volver al de fábrica
    return cfg


def save(cfg: dict) -> None:
    """Escribe el dict completo como JSON legible (indent=2)."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get(key: str, default=None):
    """Lectura puntual de una clave (recarga el JSON cada vez)."""
    return load().get(key, DEFAULTS.get(key, default))


def update(**kw) -> dict:
    """Fusiona cambios en la config actual, persiste y devuelve la nueva."""
    cfg = load()
    cfg.update(kw)
    save(cfg)
    return cfg
