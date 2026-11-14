"""OC-1 STUDIO — interfaz TUI (Textual) con estética Teenage Engineering.

Layout: TRACKS | secuenciador + cinta | ENCODERS + preview Strudel.
Teclas: espacio ▶/■ · s guardar · l abrir · e strudel · w player · g git
        o ajustes · a/d pistas · t preset · c color · q salir.
"""
from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path
from typing import Callable

from rich.style import Style
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (Button, Checkbox, DataTable, Footer, Input, Label,
                             ListItem, ListView, Log, RadioButton, RadioSet, Static)

from . import demo as demoio
from . import gitops, settings, system_theme, theme
from . import live_bridge
from . import strudel as strudelio
from . import synth
from .demo import DemoError, slugify

# ----------------------------------------------------------------- presets

PRESETS = [
    dict(name="kick", sound="kick",
         pattern="kick ~ ~ ~ kick ~ ~ ~ kick ~ ~ ~ kick ~ kick ~"),
    dict(name="snare", sound="snare",
         pattern="~ ~ ~ ~ snare ~ ~ ~ ~ ~ snare ~ ~ ~ snare ~"),
    dict(name="hats", sound="hat",
         pattern="hat ~ hat hat ~ hat ~ hat hat ~ hat ~ hat ~ hat hat"),
    dict(name="clap", sound="clap",
         pattern="~ ~ ~ ~ clap ~ ~ ~ ~ ~ ~ ~ clap ~ ~ ~"),
    dict(name="acid", sound="saw",
         pattern="a1 a1 ~ a2 ~ a1 ~ g1 ~ a1 ~ bb1 ~ a2 ~ e2 ~"),
    dict(name="bass", sound="square",
         pattern="c2 ~ c2 ~ d#2 ~ c2 ~ g1 ~ c2 ~ a#1 ~ c2 ~ g2 ~"),
    dict(name="pluck", sound="pluck",
         pattern="a3 ~ c4 ~ e4 ~ a4 ~ g4 ~ e4 ~ c4 ~ a3 ~"),
    dict(name="bells", sound="bell",
         pattern="~ ~ a4 ~ ~ ~ e5 ~ ~ ~ c5 ~ ~ ~ a4 ~"),
    dict(name="ruido", sound="noise",
         pattern="~ ~ ~ n ~ ~ ~ ~ ~ ~ ~ n ~ ~ ~ ~"),
]

ENCODERS = [  # (clave fx, etiqueta, color TE)
    ("reverb", "REVERB", "#00d26a"),
    ("delay", "DELAY", "#f0f0f0"),
    ("drive", "DRIVE", "#ff5300"),
    ("volume", "VOL", "#00a8ff"),
]


# ----------------------------------------------------------------- widgets

class TopBar(Static):
    """Barra superior estilo OC-1: punto de color + estado."""

    def update_state(self, app: "OP1App") -> None:
        accent = theme.ACCENTS.get(theme.accent_of(app.theme), "#ff5300")
        t = app.demo
        state = "▶" if app._playing else "■"
        txt = Text()
        txt.append("● ", style=Style(color=accent, bold=True))
        txt.append("OC-1 STUDIO", style=Style(bold=True))
        txt.append(f"   demo: {t.title}", style=Style(color="#9a9a9a"))
        txt.append(f"   ·   {t.bpm:g} BPM", style=Style(color="#e8e6e3"))
        txt.append(f"   ·   {t.key} {t.scale}", style=Style(color="#9a9a9a"))
        txt.append(f"   ·   {state}", style=Style(color=accent, bold=True))
        txt.append(f"   ·   {theme.accent_of(app.theme)}"
                   f"{'/claro' if 'light' in app.theme else ''}",
                   style=Style(color="#6a6a6a"))
        if app._bridge is not None:
            live_ok = app._bridge.alive_clock
            txt.append("   ·   LIVE", style=Style(
                color="#00d26a" if live_ok else "#8a8a8a", bold=True))
            if live_ok and app._live_step >= 0:
                txt.append(f" {app._live_step + 1:02d}/{t.steps}",
                           style=Style(color="#00d26a"))
        self.update(txt)


class Encoder(Static, can_focus=True):
    """Encoder giratorio ASCII (estética OC-1): ↑/↓ giran, 0 pone a cero."""

    BINDINGS = [
        Binding("up", "enc_up", "+", show=False),
        Binding("down", "enc_down", "–", show=False),
        Binding("enter", "enc_zero", "0", show=False),
    ]

    def __init__(self, key: str, label: str, color: str) -> None:
        super().__init__(id=f"enc-{key}", classes="encoder")
        self.fx_key = key
        self.enc_label = label
        self.enc_color = color
        self.value = 0.0

    def on_mount(self) -> None:
        self.redraw()

    def set_value(self, v: float) -> None:
        self.value = round(max(0.0, min(1.0, v)), 2)
        self.redraw()

    def redraw(self) -> None:
        frac = self.value
        ring = [0, 1, 2, 5, 8, 7, 6, 3]  # sentido horario en matriz 3×3
        cells = [" "] * 9
        cells[ring[min(7, round(frac * 7))]] = "●"
        art = (
            f"╭───╮\n"
            f"│{cells[0]}{cells[1]}{cells[2]}│\n"
            f"│{cells[3]} {cells[5]}│\n"
            f"╰───╯"
        )
        content = Text()
        content.append(f" {self.enc_label}\n", style=Style(color=self.enc_color, bold=True))
        content.append(art + "\n", style=Style(color=self.enc_color))
        content.append(f" {int(round(frac * 100)):>3}%", style=Style(color="#8a8a8a"))
        self.update(content)

    def _turn(self, delta: float) -> None:
        self.set_value(self.value + delta)
        self.app.sync_fx(self.fx_key, self.value)

    def action_enc_up(self) -> None:
        self._turn(+0.05)

    def action_enc_down(self) -> None:
        self._turn(-0.05)

    def action_enc_zero(self) -> None:
        self.set_value(0.0)
        self.app.sync_fx(self.fx_key, 0.0)


# ----------------------------------------------------------------- pantallas

class PatternScreen(ModalScreen):
    """Editor del patrón de una pista (una línea, estilo live coding)."""

    BINDINGS = [Binding("escape", "close", "CANCELAR")]

    def __init__(self, track_index: int) -> None:
        super().__init__()
        self.track_index = track_index

    def compose(self) -> ComposeResult:
        t = self.app.demo.tracks[self.track_index]
        with Vertical(id="dialog"):
            yield Static(f"PATTERN — {t.name} [{t.sound}]",
                         classes="modal-title", id="pat-title")
            yield Input(value=t.pattern, id="pat-in")
            yield Static("un token por semicorchea · '~' = silencio · ej: a1 ~ a2 ~ c#3",
                         classes="hint")
            with Horizontal(classes="btnrow"):
                yield Button("APLICAR ⏎", id="pat-ok", classes="btn b-green")
                yield Button("CANCELAR esc", id="pat-cancel", classes="btn b-white")

    def on_mount(self) -> None:
        self.query_one("#pat-in", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._apply()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pat-ok":
            self._apply()
        else:
            self.app.pop_screen()

    def _apply(self) -> None:
        val = self.query_one("#pat-in", Input).value.strip() or "~"
        self.app.demo.tracks[self.track_index].pattern = val
        self.app.pop_screen()
        self.app.main_screen.refresh_all()
        self.app.notify("● pattern aplicado")

    def action_close(self) -> None:
        self.app.pop_screen()


class OpenScreen(ModalScreen):
    """Lista de demos .py de la carpeta de demos."""

    BINDINGS = [Binding("escape", "close", "CERRAR")]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("ABRIR DEMO", classes="modal-title label-blue")
            yield ListView(id="open-list")
            yield Button("CERRAR esc", id="open-close", classes="btn b-white")

    def on_mount(self) -> None:
        self._files = demoio.list_demos(self.app.demo_dir())
        lv = self.query_one("#open-list", ListView)
        for p in self._files:
            lv.append(ListItem(Label(f"● {p.name}")))
        if not self._files:
            lv.append(ListItem(Label("(carpeta vacía — crea: oc1studio new X)")))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        i = event.list_view.index
        if i is not None and i < len(self._files):
            self.app.do_open(self._files[i])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()

    def action_close(self) -> None:
        self.app.pop_screen()


class GitScreen(ModalScreen):
    """Panel git: status, commit, push, pull, remote, clone."""

    BINDINGS = [Binding("escape", "close", "CERRAR")]

    def compose(self) -> ComposeResult:
        with Vertical(id="git-dialog"):
            yield Static("GIT — GUARDAR / CLONAR / SINCRONIZAR",
                         classes="modal-title label-orange")
            yield Input(placeholder="mensaje de commit…", id="git-msg")
            with Horizontal(classes="btnrow"):
                yield Button("COMMIT", id="git-commit", classes="btn b-orange")
                yield Button("STATUS", id="git-status", classes="btn b-green")
                yield Button("PUSH", id="git-push", classes="btn b-blue")
                yield Button("PULL", id="git-pull", classes="btn b-white")
            yield Input(placeholder="https://github.com/tu-usuario/tu-repo.git", id="git-url")
            with Horizontal(classes="btnrow"):
                yield Button("REMOTE", id="git-remote", classes="btn b-white")
                yield Button("CLONE", id="git-clone", classes="btn b-blue")
                yield Button("INIT REPO", id="git-init", classes="btn b-green")
                yield Button("LOG", id="git-log", classes="btn b-orange")
            yield Log(id="git-out")
            yield Button("CERRAR esc", id="git-close", classes="btn b-white")

    def _log(self, text: str) -> None:
        self.query_one("#git-out", Log).write(text)

    def _run(self, fn: Callable[[], str]) -> None:
        def work() -> None:
            try:
                out = fn()
            except Exception as e:  # noqa: BLE001
                out = f"✗ {e}"
            self.app.call_from_thread(self._log, str(out))
        self.app.run_worker(work, thread=True, exclusive=True, group="git")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        cwd = self.app.workspace
        if bid == "git-close":
            self.app.pop_screen()
            return
        if bid == "git-commit":
            msg = self.query_one("#git-msg", Input).value.strip() or f"demo: {self.app.demo.title}"
            self._run(lambda: gitops.commit(cwd, msg))
        elif bid == "git-status":
            self._run(lambda: gitops.status(cwd) or "✓ working tree limpio")
        elif bid == "git-push":
            self._run(lambda: gitops.push(cwd))
        elif bid == "git-pull":
            self._run(lambda: gitops.pull(cwd))
        elif bid == "git-remote":
            url = self.query_one("#git-url", Input).value.strip()
            if url:
                self._run(lambda: gitops.add_remote(cwd, "origin", url))
        elif bid == "git-clone":
            url = self.query_one("#git-url", Input).value.strip()
            if url:
                self._run(lambda: f"● clonado → {gitops.clone(url, gitops.default_dest(url))}")
        elif bid == "git-init":
            self._run(lambda: gitops.init(cwd))
        elif bid == "git-log":
            self._run(lambda: gitops.log(cwd))

    def action_close(self) -> None:
        self.app.pop_screen()


class SettingsScreen(ModalScreen):
    """Ajustes: apariencia (sistema), color de acento, auto-commit, puertos LIVE."""

    BINDINGS = [Binding("escape", "close", "CERRAR")]

    def compose(self) -> ComposeResult:
        cfg = settings.load()
        with Vertical(id="dialog"):
            yield Static("AJUSTES", classes="modal-title label-blue")
            yield Static("APARIENCIA ('auto' sigue al sistema):", classes="hint")
            with RadioSet(id="mode-set"):
                for label, val in (("auto (sistema)", "auto"), ("oscuro", "dark"), ("claro", "light")):
                    yield RadioButton(label, value=(cfg.get("appearance", "auto") == val),
                                      id=f"md-{val}")
            yield Static("COLOR (estilo OC-1):", classes="hint")
            with RadioSet(id="theme-set"):
                for key in theme.ACCENTS:
                    yield RadioButton(key, value=(cfg.get("accent", "orange") == key),
                                      id=f"ac-{key}")
            yield Checkbox("auto-commit en git al guardar [s]",
                           value=bool(cfg.get("auto_commit")), id="opt-autocommit")
            yield Static("CARPETA DE DEMOS (⏎ guarda):", classes="hint")
            yield Input(value=str(cfg.get("demo_dir", "demos")), id="opt-demodir")
            yield Static("PUERTOS LIVE (⏎ guarda · reinicia LIVE con v):", classes="hint")
            with Horizontal(classes="btnrow"):
                yield Input(value=str(cfg.get("live_send_port", 7647)),
                            id="opt-send", classes="tin")
                yield Input(value=str(cfg.get("live_recv_port", 7648)),
                            id="opt-recv", classes="tin")
            yield Button("CERRAR esc", id="set-close", classes="btn b-white")
            yield Static("hecho con GLM-5.3-Flash-Free + OpenCode", classes="hint credit")

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        rid = event.pressed.id or ""
        if rid.startswith("md-"):
            self.app.set_appearance(rid[3:])
        elif rid.startswith("ac-"):
            self.app.set_accent(rid[3:])

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        settings.update(auto_commit=event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        iid = event.input.id or ""
        if iid == "opt-demodir":
            settings.update(demo_dir=event.value.strip() or "demos")
            self.app.notify(f"● carpeta de demos: {event.value}")
        elif iid in ("opt-send", "opt-recv"):
            try:
                port = int(event.value)
                key = "live_send_port" if iid == "opt-send" else "live_recv_port"
                settings.update(**{key: max(1024, min(65535, port))})
                self.app.notify(f"● {key}: {port} (reinicia LIVE con v)")
            except ValueError:
                self.app.notify("✗ puerto no válido", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.pop_screen()

    def action_close(self) -> None:
        self.app.pop_screen()


# ----------------------------------------------------------------- pantalla principal

class StudioScreen(Screen):
    """Pantalla principal del estudio."""

    def compose(self) -> ComposeResult:
        app = self.app
        yield TopBar(id="topbar")
        with Horizontal(id="main"):
            with Vertical(id="left"):
                yield Static("TRACKS", classes="panel-label label-blue")
                yield ListView(id="tracks")
                with Horizontal(classes="btnrow"):
                    yield Button("+", id="btn-add", classes="btn b-green")
                    yield Button("–", id="btn-del", classes="btn b-white")
                    yield Button("PRESET", id="btn-preset", classes="btn b-orange")
            with Vertical(id="center"):
                yield DataTable(id="grid", cursor_type="cell")
                yield Static(id="tape", classes="tape")
                with Horizontal(id="transport"):
                    yield Input(id="in-bpm", classes="tin")
                    yield Input(id="in-key", classes="tin")
                    yield Input(id="in-scale", classes="tin")
            with Vertical(id="right"):
                yield Static("ENCODERS", classes="panel-label label-orange")
                for key, label, color in ENCODERS:
                    yield Encoder(key, label, color)
                yield Static("STRUDEL ←", classes="panel-label label-green")
                with VerticalScroll(id="sdx-wrap"):
                    yield Static(id="sdx")
        yield Footer()

    def on_mount(self) -> None:
        # tras montar los hijos, pinta todo
        self.call_after_refresh(self.refresh_all)

    # ---- refresco

    def refresh_all(self) -> None:
        self.build_grid()
        self.refresh_tracks()
        self.refresh_encoders()
        self.refresh_transport()
        self.refresh_sdx()
        self.update_topbar()

    def update_topbar(self) -> None:
        self.query_one("#topbar", TopBar).update_state(self.app)

    def build_grid(self) -> None:
        app = self.app
        grid = self.query_one("#grid", DataTable)
        grid.clear(columns=True)
        grid.add_column("PISTA", key="name")
        for i in range(app.demo.steps):
            grid.add_column(f"{i + 1}", key=f"s{i}")
        for t in app.demo.tracks:
            row = [Text(f"● {t.name}", style=Style(color=theme.sound_color(t.sound), bold=True))]
            for tok in t.tokens(app.demo.steps):
                rest = tok in ("~", ".")
                row.append(Text("~" if rest else tok,
                                style=Style(color="#5a5a5a" if rest else "#e8e6e3",
                                            bold=not rest)))
            grid.add_row(*row)

    def refresh_tracks(self) -> None:
        lv = self.query_one("#tracks", ListView)
        lv.clear()
        for t in self.app.demo.tracks:
            dot = Text()
            dot.append("● ", style=Style(color=theme.sound_color(t.sound), bold=True))
            dot.append(t.name, style=Style(bold=True))
            dot.append(f" · {t.sound}", style=Style(color="#8a8a8a"))
            lv.append(ListItem(Label(dot)))

    def refresh_encoders(self) -> None:
        for key, _label, _color in ENCODERS:
            enc = self.query_one(f"#enc-{key}", Encoder)
            enc.set_value(self.app.demo.fx.get(key, 0.0))

    def refresh_transport(self) -> None:
        d = self.app.demo
        self.query_one("#in-bpm", Input).value = f"{d.bpm:g}"
        self.query_one("#in-key", Input).value = d.key
        self.query_one("#in-scale", Input).value = d.scale

    def refresh_sdx(self) -> None:
        code = strudelio.to_strudel(self.app.demo)
        self.query_one("#sdx", Static).update(Text(code.rstrip(), style=Style(color="#7bd88f")))

    def show_tape(self, preview: str) -> None:
        state = "▶" if self.app._playing else "■"
        tape = Text()
        tape.append(f"{state} ", style=Style(color="#ff5300", bold=True))
        tape.append(f"{self.app.demo.bpm:g}bpm ", style=Style(color="#e8e6e3"))
        tape.append(preview, style=Style(color="#ff5300"))
        self.query_one("#tape", Static).update(tape)

    # ---- interacciones

    def sel_track_index(self) -> int:
        lv = self.query_one("#tracks", ListView)
        i = lv.index
        if i is None or not (0 <= i < len(self.app.demo.tracks)):
            i = 0
        return i

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "tracks":
            i = event.list_view.index
            if i is not None:
                self.app.push_screen(PatternScreen(i))

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        row = event.coordinate.row
        if 0 <= row < len(self.app.demo.tracks):
            self.app.push_screen(PatternScreen(row))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        iid = event.input.id or ""
        d = self.app.demo
        try:
            if iid == "in-bpm":
                d.bpm = max(20.0, min(300.0, float(event.value or d.bpm)))
            elif iid == "in-key":
                d.key = (event.value or d.key).lower()[:2]
            elif iid == "in-scale":
                d.scale = (event.value or d.scale).lower()[:12]
            else:
                return
        except ValueError:
            self.app.notify("✗ valor no válido", severity="error")
            return
        self.refresh_transport()
        self.refresh_sdx()
        self.update_topbar()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        app = self.app
        bid = event.button.id or ""
        if bid == "btn-add":
            app.action_add_track()
        elif bid == "btn-del":
            app.action_del_track()
        elif bid == "btn-preset":
            app.action_cycle_preset()


# ----------------------------------------------------------------- App

class OP1App(App):
    TITLE = "OC-1 STUDIO"
    CSS_PATH = None

    CSS = """
    #topbar { height: 1; background: $panel; padding: 0 1; }
    #main { height: 1fr; }
    #left { width: 30; border-right: solid $panel; padding: 0 1; }
    #center { width: 1fr; padding: 0 1; }
    #right { width: 26; border-left: solid $panel; padding: 0 1; }
    .panel-label { height: 1; color: $accent; text-style: bold; }
    .label-blue { color: #00a8ff; }
    .label-orange { color: #ff5300; }
    .label-green { color: #00d26a; }
    #tracks { height: 1fr; margin-bottom: 1; }
    .btnrow { height: 3; }
    Button.btn { min-width: 6; height: 3; }
    #grid { height: 1fr; }
    .tape { height: 3; border-top: solid $panel; color: $accent; }
    #transport { height: 3; }
    .tin { width: 1fr; }
    .encoder { height: 6; content-align: center top; }
    .encoder:focus { background: $boost; }
    #sdx-wrap { height: 1fr; }
    #sdx { padding: 0 1; color: #7bd88f; }
    #dialog, #git-dialog {
              width: 72; max-width: 92; height: auto; max-height: 88%;
              background: $surface; border: round $primary; padding: 1 2; }
    .modal-title { text-style: bold; height: 1; margin-bottom: 1; }
    .hint { color: $text-muted; height: 1; }
    .credit { content-align: center middle; color: $text-disabled; }
    #git-out { height: 12; border: round $panel; margin: 1 0; }
    #open-list { height: 12; border: round $panel; margin-bottom: 1; }
    Input { height: 3; }
    RadioSet { height: 6; margin-bottom: 1; }
    CheckBox { height: 3; }
    """

    BINDINGS = [
        Binding("space", "play", "▶/■"),
        Binding("s", "save", "GUARDAR"),
        Binding("l", "open", "ABRIR"),
        Binding("e", "strudel", "STRUDEL ↗"),
        Binding("w", "strudel_page", "PLAYER ↗"),
        Binding("g", "git", "GIT"),
        Binding("o", "settings", "AJUSTES"),
        Binding("a", "add_track", "+TRACK"),
        Binding("d", "del_track", "–TRACK"),
        Binding("t", "cycle_preset", "PRESET"),
        Binding("c", "cycle_theme", "COLOR"),
        Binding("v", "toggle_live", "LIVE"),
        Binding("q", "quit", "SALIR"),
        Binding("ctrl+s", "save", "GUARDAR", show=False),
        Binding("ctrl+q", "quit", "SALIR", show=False),
    ]

    def __init__(self, demo: demoio.Demo | None = None, demo_path: str | Path | None = None):
        super().__init__()
        self.demo = (demo or demoio.default_demo()).normalized()
        self.demo_path = Path(demo_path) if demo_path else None
        self._proc: subprocess.Popen | None = None
        self._playing = False
        self._play_id = 0
        self._server: strudelio.StrudelServer | None = None
        self._preset_i = 0
        self._bridge: live_bridge.LiveBridge | None = None
        self._live_step = -1
        self.main_screen: StudioScreen | None = None

    # ---- ciclo de vida

    def get_default_screen(self) -> StudioScreen:
        self.main_screen = StudioScreen()
        return self.main_screen

    def on_mount(self) -> None:
        for t in theme.THEMES.values():
            self.register_theme(t)
        cfg = settings.load()
        self._accent = str(cfg.get("accent", "orange"))
        self._appearance = str(cfg.get("appearance", "auto"))
        self.theme = self._theme_name()
        # temas dinámicos: sondea la apariencia del sistema cada 5 s
        self.set_interval(5.0, self._check_system_theme)

    def _theme_name(self) -> str:
        mode = self._appearance
        if mode == "auto":
            mode = system_theme.detect_system_mode()
        return theme.effective_theme(self._accent, mode)

    def reapply_theme(self) -> None:
        self.theme = self._theme_name()
        settings.update(appearance=self._appearance, accent=self._accent)
        if self.main_screen is not None:
            self.main_screen.update_topbar()

    def _check_system_theme(self) -> None:
        if self._appearance != "auto":
            return
        system_theme.invalidate_cache()
        name = self._theme_name()
        if name != self.theme:
            self.theme = name
            self.notify(f"● tema del sistema: {'claro' if 'light' in name else 'oscuro'}")
            if self.main_screen is not None:
                self.main_screen.update_topbar()

    def set_appearance(self, mode: str) -> None:
        if mode in ("auto", "dark", "light"):
            self._appearance = mode
            self.reapply_theme()

    def set_accent(self, key: str) -> None:
        if key in theme.ACCENTS:
            self._accent = key
            self.reapply_theme()

    def on_unmount(self) -> None:
        self._teardown()

    def _teardown(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None
        if self._server is not None:
            self._server.stop()
            self._server = None
        if self._bridge is not None:
            self._bridge.stop()
            self._bridge = None

    def action_quit(self) -> None:
        self._teardown()
        self.exit()

    # ---- utilidades

    def demo_dir(self) -> Path:
        d = Path(str(settings.get("demo_dir", "demos"))).expanduser()
        return d if d.is_absolute() else Path.cwd() / d

    @property
    def workspace(self) -> Path:
        """Carpeta raíz del repo git (padre de la carpeta de demos)."""
        if self.demo_path is not None:
            return self.demo_path.resolve().parent.parent
        return (self.demo_dir().resolve().parent)

    def sync_fx(self, key: str, value: float) -> None:
        self.demo.fx[key] = round(value, 2)
        if self.main_screen is not None:
            self.main_screen.refresh_sdx()

    def _sync_bridge(self) -> None:
        """Mantén el puente LIVE al día tras cargar/guardar un demo."""
        if self._bridge is not None:
            self._bridge.demo = self.demo
            self._bridge.send_bpm()

    # ---- acciones

    def action_play(self) -> None:
        proc = self._proc
        if proc is not None and proc.poll() is None:
            proc.terminate()
            self._proc = None
            self._playing = False
            self.notify("■ stop")
            self.main_screen.update_topbar()  # type: ignore[union-attr]
            self.main_screen.refresh_sdx()  # type: ignore[union-attr]
            return
        self._play_id += 1
        token = self._play_id
        self.run_worker(lambda: self._render_and_play(token),
                        thread=True, exclusive=True, group="audio", name="render")

    def _render_and_play(self, token: int) -> None:
        try:
            path, samples = synth.render_to_cache(self.demo)
            preview = synth.wave_preview(samples, 72)
        except Exception as e:  # noqa: BLE001
            self.call_from_thread(self.notify, f"✗ render: {e}", severity="error")
            return
        if token != self._play_id:
            return  # el usuario paró mientras se renderizaba
        self.call_from_thread(self._on_rendered, path, preview, token)

    def _on_rendered(self, path: Path, preview: str, token: int) -> None:
        if token != self._play_id:
            return
        self._playing = True
        self.main_screen.show_tape(preview)  # type: ignore[union-attr]
        self.main_screen.update_topbar()  # type: ignore[union-attr]
        try:
            self._proc = synth.spawn_player(path)
        except Exception as e:  # noqa: BLE001
            self.notify(f"✗ player: {e}", severity="error")

    def action_save(self) -> None:
        path = self.demo_path or (self.demo_dir() / f"{slugify(self.demo.title)}.py")
        try:
            demoio.save(self.demo, path)
        except OSError as e:
            self.notify(f"✗ no se pudo guardar: {e}", severity="error")
            return
        self.demo_path = Path(path)
        self.notify(f"● guardado → {path.name}")
        self._sync_bridge()
        if settings.get("auto_commit") and gitops.is_repo(self.workspace):
            def work() -> None:
                out = gitops.auto_commit(self.workspace, self.demo.title)
                self.call_from_thread(self.notify, f"git: {out}" if out else "git: sin cambios")
            self.run_worker(work, thread=True, exclusive=True, group="git")
        if self.main_screen is not None:
            self.main_screen.update_topbar()

    def action_open(self) -> None:
        self.push_screen(OpenScreen())

    def do_open(self, path: Path) -> None:
        try:
            d = demoio.load(path)
        except DemoError as e:
            self.notify(f"✗ {e}", severity="error")
            return
        self.demo = d
        self.demo_path = Path(path)
        self.pop_screen()  # cierra el modal
        self._sync_bridge()
        if self.main_screen is not None:
            self.main_screen.refresh_all()
        self.notify(f"● {d.title} cargado")

    def action_strudel(self) -> None:
        url = strudelio.share_url(self.demo)
        webbrowser.open(url)
        self.notify("● strudel.cc abierto — dale PLAY en el navegador")

    def action_strudel_page(self) -> None:
        if self._server is None:
            self._server = strudelio.launch_player(self.demo)
        else:
            self._server.update(self.demo)
        webbrowser.open(self._server.url)
        self.notify(f"● player local → {self._server.url}")

    def action_git(self) -> None:
        self.push_screen(GitScreen())

    def action_settings(self) -> None:
        self.push_screen(SettingsScreen())

    def action_add_track(self) -> None:
        n = len(self.demo.tracks) + 1
        t = demoio.Track(name=f"syn{n}", sound="saw", pattern="c3 ~ e3 ~ g3 ~", gain=0.8)
        self.demo.tracks.append(t)
        self.main_screen.refresh_all()  # type: ignore[union-attr]
        self.notify(f"● +track: {t.name}")

    def action_del_track(self) -> None:
        if len(self.demo.tracks) <= 1:
            self.notify("✗ mínimo 1 pista", severity="warning")
            return
        i = self.main_screen.sel_track_index()  # type: ignore[union-attr]
        gone = self.demo.tracks.pop(i)
        self.main_screen.refresh_all()  # type: ignore[union-attr]
        self.notify(f"● –track: {gone.name}")

    def action_cycle_preset(self) -> None:
        p = PRESETS[self._preset_i % len(PRESETS)]
        self._preset_i += 1
        i = self.main_screen.sel_track_index()  # type: ignore[union-attr]
        t = self.demo.tracks[i]
        t.name, t.sound, t.pattern = p["name"], p["sound"], p["pattern"]
        self.main_screen.refresh_all()  # type: ignore[union-attr]
        self.notify(f"● preset → {p['name']} (pista {t.name})")

    def action_cycle_theme(self) -> None:
        names = list(theme.ACCENTS)
        try:
            i = (names.index(self._accent) + 1) % len(names)
        except (ValueError, AttributeError):
            i = 0
        self.set_accent(names[i])
        self.notify(f"● color: {names[i]}")

    # ---- LIVE (Ableton / Max for Live)

    def action_toggle_live(self) -> None:
        if self._bridge is not None:
            self._bridge.stop()
            self._bridge = None
            self._live_step = -1
            self.notify("■ LIVE apagado ( Ableton desconectado )")
        else:
            cfg = settings.load()
            self._bridge = live_bridge.LiveBridge(
                self.demo,
                send_port=int(cfg.get("live_send_port", 7647)),
                recv_port=int(cfg.get("live_recv_port", 7648)),
                on_clock=self._on_live_clock,
            )
            self._bridge.start()
            self.notify(f"● LIVE: notas → 127.0.0.1:{cfg.get('live_send_port', 7647)}"
                        f" · reloj ← :{cfg.get('live_recv_port', 7648)}  (dale play en Ableton)")
        if self.main_screen is not None:
            self.main_screen.update_topbar()

    def _on_live_clock(self, step: int) -> None:
        """Hilo del puente: envía las notas del paso y actualiza la UI."""
        if self._bridge is not None:
            self._bridge.send_step(step)
        self.call_from_thread(self._live_step_ui, step)

    def _live_step_ui(self, step: int) -> None:
        self._live_step = step
        if self.main_screen is not None:
            self.main_screen.update_topbar()
