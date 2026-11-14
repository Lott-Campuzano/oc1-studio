"""chip_boy — demo OC-1 STUDIO (estilo chip: computadora vieja / 8-bit)

Edita este archivo: ES tu demo. Cada pista es un Track(...).
pattern: un token por semicorchea; '~' o '.' = silencio.
Notas: c3, c#3, bb3 — percusión: kick, snare, hat, clap.
Sonidos: sine, square, saw, tri, pluck, bell, fm, noise, kick, snare, hat, clap
Reproduce: python -m oc1studio play <archivo>
Strudel:   python -m oc1studio strudel <archivo>
"""
from oc1studio.demo import Demo, Track

demo = Demo(
    title="chip_boy",
    bpm=140,
    key="e",
    scale="minor",
    steps=16,
    style="chip",
    tracks=[
        Track(
            name="kick", sound="kick",
            pattern="kick ~ ~ ~ kick ~ kick ~ kick ~ ~ ~ kick ~ ~ ~ ~",
            gain=1,
        ),
        Track(
            name="noise", sound="hat",
            pattern="hat hat hat ~ hat ~ hat hat hat ~ hat hat hat ~ hat hat",
            gain=0.45,
        ),
        Track(
            name="snare", sound="snare",
            pattern="~ ~ ~ ~ snare ~ ~ ~ ~ ~ ~ ~ snare ~ ~ ~",
            gain=0.8,
        ),
        Track(
            name="pulse", sound="square",
            pattern="e2 ~ e2 e3 ~ e2 ~ d2 ~ e2 ~ g2 ~ e2 ~ b2 ~",
            gain=0.6,
        ),
        Track(
            name="arp", sound="pluck",
            pattern="e4 b4 e5 ~ d5 b4 g4 ~ e4 b4 e5 ~ fs5 b5 e6 ~",
            gain=0.5,
        ),
    ],
    fx={"reverb": 0, "delay": 0.22, "drive": 0.15, "volume": 0.9},
)
