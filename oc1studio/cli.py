"""CLI de OC-1 STUDIO.

    oc1studio              → interfaz TUI (estilo OC-1)
    oc1studio play X.py    → renderiza y reproduce el demo
    oc1studio code X.py    → imprime el código Strudel
    oc1studio strudel X.py → abre strudel.cc con el demo (--page: player local)
    oc1studio new NAME     → crea demos/NAME.py
    oc1studio list         → lista los demos
    oc1studio git clone|status|commit|push|pull|add-remote|remotes
"""
from __future__ import annotations

import argparse
import datetime
import sys
import webbrowser
from pathlib import Path

from . import demo as demoio
from . import gitops, settings
from . import live_bridge
from . import strudel as strudelio
from . import synth
from . import __version__, __credits__


def _load_or_exit(path: str) -> demoio.Demo:
    try:
        return demoio.load(path)
    except demoio.DemoError as e:
        print(f"✗ {e}", file=sys.stderr)
        raise SystemExit(2)


def cmd_play(args) -> None:
    d = _load_or_exit(args.demo)
    path, samples = synth.render_to_cache(d)
    dur = len(samples) / synth.SR
    print(f"● {d.title} — {d.bpm:g} bpm · {len(d.tracks)} pistas · {dur:.1f}s")
    print(f"  {synth.wave_preview(samples, 64)}")
    print(f"  wav: {path}")
    synth.play_file(path)


def cmd_code(args) -> None:
    print(strudelio.to_strudel(_load_or_exit(args.demo)), end="")


def cmd_strudel(args) -> None:
    d = _load_or_exit(args.demo)
    if args.page:
        server = strudelio.launch_player(d, port=args.port)
        print(f"● player local → {server.url}   (ctrl+c para salir)")
        try:
            import time
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            server.stop()
            print("\n■ servidor cerrado")
    else:
        url = strudelio.share_url(d)
        webbrowser.open(url)
        print(f"● strudel.cc listo (dale PLAY en el navegador):\n  {url}")


def cmd_new(args) -> None:
    d = demoio.chip_demo(args.name) if args.chip else demoio.default_demo(args.name)
    path = Path(settings.get("demo_dir", "demos")) / f"{demoio.slugify(args.name)}.py"
    demoio.save(d, path)
    print(f"● demo creado → {path}")


def cmd_live(args) -> None:
    d = _load_or_exit(args.demo)
    cfg = settings.load()
    live_bridge.run_headless(d,
                             send_port=int(cfg.get("live_send_port", 7647)),
                             recv_port=int(cfg.get("live_recv_port", 7648)))


def cmd_list(args) -> None:
    demos = demoio.list_demos(settings.get("demo_dir", "demos"))
    if not demos:
        print("(sin demos — crea uno: oc1studio new mi-demo)")
        return
    for p in demos:
        print(f"● {p}")


def cmd_git(args) -> None:
    if args.git_cmd == "clone":
        dest = args.dest or gitops.default_dest(args.url)
        out = gitops.clone(args.url, dest)
        print(f"● clonado → {out}")
        return
    cwd = Path(args.repo).expanduser()
    try:
        if args.git_cmd == "status":
            out = gitops.status(cwd) or "✓ todo guardado (working tree limpio)"
        elif args.git_cmd == "init":
            out = gitops.init(cwd)
        elif args.git_cmd == "commit":
            msg = args.message or f"demo: cambios {datetime.datetime.now():%Y-%m-%d %H:%M}"
            out = gitops.commit(cwd, msg)
        elif args.git_cmd == "push":
            out = gitops.push(cwd, args.remote)
        elif args.git_cmd == "pull":
            out = gitops.pull(cwd, args.remote)
        elif args.git_cmd == "add-remote":
            out = gitops.add_remote(cwd, args.name, args.url)
        elif args.git_cmd == "remotes":
            rs = gitops.remotes(cwd)
            out = "\n".join(f"{k}\t{v}" for k, v in rs.items()) or "(sin remotes)"
        elif args.git_cmd == "log":
            out = gitops.log(cwd)
        else:  # pragma: no cover
            out = ""
        print(f"● {out}")
    except gitops.GitError as e:
        print(f"✗ {e}", file=sys.stderr)
        raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="oc1studio",
        description="OC-1 STUDIO — música en la terminal con estética Teenage Engineering.",
    )
    p.add_argument("--version", action="version",
                   version=f"OC-1 STUDIO v{__version__} · {__credits__}")
    sub = p.add_subparsers(dest="cmd")

    c = sub.add_parser("play", help="reproduce un demo (.py)")
    c.add_argument("demo")
    c = sub.add_parser("code", help="imprime el código Strudel del demo")
    c.add_argument("demo")
    c = sub.add_parser("strudel", help="abre el demo en strudel.cc")
    c.add_argument("demo")
    c.add_argument("--page", action="store_true", help="player local con REPL embebido")
    c.add_argument("--port", type=int, default=0)
    c = sub.add_parser("new", help="crea un demo nuevo")
    c.add_argument("name")
    c.add_argument("--chip", action="store_true", help="estilo 8-bit (computadora vieja)")
    c = sub.add_parser("live", help="puente LIVE headless para Ableton (Max for Live)")
    c.add_argument("demo")
    sub.add_parser("list", help="lista los demos")

    g = sub.add_parser("git", help="clone / status / commit / push / pull / add-remote")
    gs = g.add_subparsers(dest="git_cmd", required=True)

    def repo_opt(sp):
        sp.add_argument("-r", "--repo", default=".", help="ruta del repositorio (por defecto: .)")

    gs.add_parser("status"); repo_opt(gs.choices["status"])
    gs.add_parser("init"); repo_opt(gs.choices["init"])
    c = gs.add_parser("commit"); c.add_argument("-m", "--message", default=None); repo_opt(c)
    c = gs.add_parser("push"); c.add_argument("--remote", default="origin"); repo_opt(c)
    c = gs.add_parser("pull"); c.add_argument("--remote", default="origin"); repo_opt(c)
    c = gs.add_parser("add-remote"); c.add_argument("name"); c.add_argument("url"); repo_opt(c)
    gs.add_parser("remotes"); repo_opt(gs.choices["remotes"])
    c = gs.add_parser("log"); repo_opt(c)
    c = gs.add_parser("clone"); c.add_argument("url"); c.add_argument("dest", nargs="?")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd is None:
        from .app import OP1App
        OP1App().run()
        return 0
    return {"play": cmd_play, "code": cmd_code, "strudel": cmd_strudel,
            "new": cmd_new, "list": cmd_list, "git": cmd_git,
            "live": cmd_live}[args.cmd](args) or 0
