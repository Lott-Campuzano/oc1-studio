"""Puente OP-1 STUDIO ↔ Ableton Live vía Max for Live (UDP, texto plano).

Protocolo (127.0.0.1):
  Python → Max : "op1 note <midi> <vel>"     (melódicas + percusión en GM)
                 "op1 bpm <x>"               (estado informativo)
  Max → Python : "op1 clock <paso 0-15>"     (reloj de 16avos desde transport)
                 "op1 transport play|stop"   (opcional)

El dispositivo Max (max/op1-studio-bridge.maxpat) convierte las notas a MIDI
(midiout) y emite el reloj de 16avos sincronizado con el transporte de Live.
"""
from __future__ import annotations

import socket
import threading
import time

from . import synth

GM_DRUM = {"kick": 36, "snare": 38, "hat": 42, "clap": 39,
           "ride": 51, "tom": 45, "rim": 37, "perc": 63}


class LiveBridge:
    """Servidor/cliente UDP que sincroniza OP-1 STUDIO con Ableton vía Max."""

    def __init__(self, demo, send_port: int = 7647, recv_port: int = 7648,
                 on_clock=None) -> None:
        self.demo = demo
        self.send_port = int(send_port)
        self.recv_port = int(recv_port)
        self.on_clock = on_clock          # callback(step) — hilo receptor
        self.step = -1
        self.bpm = float(demo.bpm)
        self.playing = False
        self._running = False
        self._last_clock = 0.0
        self._rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._rx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ---- ciclo de vida

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._rx.bind(("127.0.0.1", self.recv_port))
        threading.Thread(target=self._loop, daemon=True, name="op1-live").start()
        self.send_bpm()

    def stop(self) -> None:
        self._running = False
        try:
            self._rx.close()
        except OSError:
            pass

    @property
    def alive_clock(self) -> bool:
        """True si ha habido reloj de Ableton en los últimos 2 s."""
        return (time.time() - self._last_clock) < 2.0

    # ---- recepción (Max → Python)

    def _loop(self) -> None:
        while self._running:
            try:
                data, _ = self._rx.recvfrom(1024)
            except OSError:
                break
            parts = data.decode("utf-8", "ignore").strip().split()
            if len(parts) < 3 or parts[0] != "op1":
                continue
            kind = parts[1]
            if kind == "clock":
                try:
                    step = int(parts[2])
                except ValueError:
                    continue
                self._last_clock = time.time()
                self.playing = True
                self.step = step
                if self.on_clock:
                    self.on_clock(step)
            elif kind == "bpm":
                try:
                    self.bpm = float(parts[2])
                except ValueError:
                    pass
            elif kind == "transport":
                self.playing = parts[2].lower() == "play"
                if not self.playing:
                    self.step = -1

    # ---- envío (Python → Max)

    def _send(self, text: str) -> None:
        try:
            self._tx.sendto(text.encode("utf-8"), ("127.0.0.1", self.send_port))
        except OSError:
            pass

    def send_bpm(self) -> None:
        self._send(f"op1 bpm {float(self.demo.bpm):g}")

    def step_notes(self, step: int) -> list[tuple[int, int]]:
        """Notas MIDI (nota, velocidad) que suenan en `step` según el demo."""
        d = self.demo.normalized()
        out: list[tuple[int, int]] = []
        for tr in d.tracks:
            toks = tr.tokens(d.steps)
            if step >= len(toks):
                continue
            tok = toks[step]
            if tok in ("~", "."):
                continue
            vel = int(min(127, max(1, round(tr.gain * 110))))
            if tr.sound in GM_DRUM:
                out.append((GM_DRUM[tr.sound], vel))
            else:
                midi = synth.note_to_midi(tok)
                if midi is not None:
                    out.append((midi, vel))
        return out

    def send_step(self, step: int) -> None:
        for midi, vel in self.step_notes(step):
            self._send(f"op1 note {midi} {vel}")


def run_headless(demo, send_port: int = 7647, recv_port: int = 7648) -> None:
    """Puente LIVE sin interfaz: op1studio live <demo.py>."""
    bridge = LiveBridge(demo, send_port=send_port, recv_port=recv_port)
    last: list[int] = [-1]

    def on_clock(step: int) -> None:
        bridge.send_step(step)
        if step != last[0]:
            last[0] = step
            print(f"\r● LIVE paso {step + 1:02d}/{demo.steps} "
                  f"· bpm {bridge.bpm:g}  ", end="", flush=True)

    bridge.on_clock = on_clock
    bridge.start()
    print(f"● puente LIVE: notas → 127.0.0.1:{send_port} · "
          f"reloj ← :{recv_port}  (pon el dispositivo Max y dale play en Ableton)")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        bridge.stop()
        print("\n■ puente cerrado")
