"""Operaciones git para OC-1 STUDIO (subprocess, sin dependencias).

Clonar, guardar cambios (commit) y almacenar en remoto (push/pull).
Funciona con GitHub vía HTTPS (token/PAT o credencial guardada) o SSH.

Todas las funciones hablan con el binario `git` via _run() — nada de
librerías — y convierten los fallos en GitError para que la TUI los
pueda mostrar sin crash.
"""
from __future__ import annotations

import datetime
import shutil
import subprocess
from pathlib import Path


class GitError(RuntimeError):
    """Fallo en una operación git."""


def has_git() -> bool:
    """True si el binario git está disponible en el PATH."""
    return shutil.which("git") is not None


def _run(args: list[str], cwd: Path, check: bool = True) -> str:
    """Ejecuta `git <args>` en cwd y devuelve su salida limpia.

    check=True → returncode != 0 lanza GitError con stderr (o stdout).
    check=False → tolera el fallo (p. ej. `status` en un no-repo).
    """
    if not has_git():
        raise GitError("git no está instalado (https://git-scm.com)")
    p = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if check and p.returncode != 0:
        raise GitError((p.stderr or p.stdout).strip() or f"git {args[0]} falló")
    return (p.stdout or p.stderr).strip()


def is_repo(path: Path) -> bool:
    """True si path es un árbol de trabajo git (rev-parse lo confirma)."""
    try:
        return _run(["rev-parse", "--is-inside-work-tree"], path, check=False) == "true"
    except GitError:
        return False


def init(path: Path) -> str:
    """git init + primer commit de todo lo que ya exista en la carpeta."""
    if is_repo(path):
        return "ya es un repositorio git"
    _run(["init"], path)
    _run(["add", "-A"], path, check=False)   # por si ya hay demos: stagéalos
    r = _run(["commit", "-m", "OC-1 STUDIO: primer commit"], path, check=False)
    return "repositorio inicializado" + (f" · {r.splitlines()[0]}" if r else "")


def status(path: Path) -> str:
    """`status --short --branch`: vacío ⇔ árbol limpio."""
    return _run(["status", "--short", "--branch"], path, check=False)


def current_branch(path: Path) -> str:
    """Nombre corto de la rama actual (p. ej. 'main')."""
    return _run(["rev-parse", "--abbrev-ref", "HEAD"], path)


def add_all(path: Path) -> None:
    """Staging de todo (incluye nuevos y borrados) — `add -A`."""
    _run(["add", "-A"], path)


def commit(path: Path, msg: str) -> str:
    """Guarda cambios con mensaje; devuelve la primera línea del resultado."""
    if not status(path):
        return "sin cambios que guardar"
    add_all(path)
    out = _run(["commit", "-m", msg], path)
    return out.splitlines()[0] if out else "sin cambios que guardar"


def auto_commit(path: Path, title: str) -> str | None:
    """Commit automático de los demos si hay repo y hay cambios.

    Devuelve None (en silencio) si no aplica o si git falla: el
    auto-commit nunca debe interrumpir al usuario.
    """
    if not is_repo(path):
        return None
    if not status(path):
        return None
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        return commit(path, f"demo: {title} — {ts}")
    except GitError:
        return None


def push(path: Path, remote: str = "origin") -> str:
    """Sube la rama actual, creando upstream si es la primera vez."""
    branch = current_branch(path)
    return _run(["push", "--set-upstream", remote, branch], path)


def pull(path: Path, remote: str = "origin") -> str:
    """Baja y fusiona la rama actual desde remote."""
    branch = current_branch(path)
    return _run(["pull", remote, branch], path)


def remotes(path: Path) -> dict[str, str]:
    """Diccionario nombre→url de los remotos (solo líneas '(fetch)')."""
    out = _run(["remote", "-v"], path, check=False)
    result: dict[str, str] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and "(fetch)" in line:   # ignora las líneas (push)
            result[parts[0]] = parts[1]
    return result


def add_remote(path: Path, name: str, url: str) -> str:
    """Añade un remote o actualiza su url si ya existe (idempotente)."""
    if name in remotes(path):
        _run(["remote", "set-url", name, url], path)
        return f"remote '{name}' actualizado → {url}"
    _run(["remote", "add", name, url], path)
    return f"remote '{name}' añadido → {url}"


def clone(url: str, dest: str) -> Path:
    """Clona url en dest (que debe no existir o estar vacío)."""
    dest_path = Path(dest).expanduser()
    if dest_path.exists() and any(dest_path.iterdir()):
        raise GitError(f"el destino ya existe y no está vacío: {dest_path}")
    _run(["clone", url, str(dest_path)], cwd=dest_path.parent if dest_path.parent.exists() else Path("."))
    return dest_path


def log(path: Path, n: int = 10) -> str:
    """Últimos n commits, una línea cada uno."""
    out = _run(["log", f"-{n}", "--oneline", "--decorate"], path, check=False)
    return out or "(sin commits)"


def default_dest(url: str) -> str:
    """Nombre de carpeta sugerido para clonar una url ('x/y.git' → 'y')."""
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name or "repo"
