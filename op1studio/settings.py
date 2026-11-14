"""Configuración persistente de OP-1 STUDIO (~/.op1studio/config.json)."""
from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".op1studio"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "accent": "orange",         # orange | blue | green | white
    "appearance": "auto",       # auto (sigue al sistema) | dark | light
    "steps": 16,                # pasos del secuenciador
    "auto_commit": False,       # commit automático en git al guardar
    "demo_dir": "demos",        # carpeta de demos (relativa a cwd)
    "volume": 0.9,
    "live_send_port": 7647,     # OP-1 → Max for Live (notas)
    "live_recv_port": 7648,     # Max for Live → OP-1 (reloj de 16avos)
}


def load() -> dict:
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001 — config corrupta ⇒ valores por defecto
        pass
    # migración desde versiones anteriores
    a = str(cfg.get("accent", ""))
    if a.startswith("op1-"):
        cfg["accent"] = a.replace("op1-", "").replace("-light", "")
    if cfg.get("appearance") not in ("auto", "dark", "light"):
        cfg["appearance"] = DEFAULTS["appearance"]
    if cfg.get("accent") not in DEFAULTS.get("accent", "") and cfg["accent"] not in ("orange", "blue", "green", "white"):
        cfg["accent"] = "orange"
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
