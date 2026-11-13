"""Configuración persistente de OP-1 STUDIO (~/.op1studio/config.json)."""
from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".op1studio"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "accent": "op1-orange",     # op1-orange | op1-blue | op1-green | op1-white
    "steps": 16,                # pasos del secuenciador
    "auto_commit": False,       # commit automático en git al guardar
    "demo_dir": "demos",        # carpeta de demos (relativa a cwd)
    "volume": 0.9,
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001 — config corrupta ⇒ valores por defecto
        pass
    return cfg


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get(key: str, default=None):
    return load().get(key, DEFAULTS.get(key, default))


def update(**kw) -> dict:
    cfg = load()
    cfg.update(kw)
    save(cfg)
    return cfg
