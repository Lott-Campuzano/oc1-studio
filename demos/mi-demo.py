"""mi-demo — demo OP-1 STUDIO

Edita este archivo: ES tu demo. Cada pista es un Track(...).
pattern: un token por semicorchea; '~' o '.' = silencio.
Notas: c3, c#3, bb3 — percusión: kick, snare, hat, clap.
Sonidos: sine, square, saw, tri, pluck, bell, fm, noise, kick, snare, hat, clap
Reproduce: python -m op1studio play <archivo>
Strudel:   python -m op1studio strudel <archivo>
"""
from op1studio.demo import Demo, Track


demo = Demo(
    title="mi-demo",
    bpm=126,
    key="a",
    scale="minor",
    steps=16,
    tracks=[
        Track(
            name="kick", sound="kick",
            pattern="kick ~ ~ ~ kick ~ ~ ~ kick ~ ~ ~ kick ~ kick ~",
            gain=1,
        ),
        Track(
            name="hats", sound="hat",
            pattern="~ ~ hat ~ hat ~ hat ~ hat ~ hat ~ hat ~ hat ~ hat hat",
            gain=0.5,
        ),
        Track(
            name="snare", sound="snare",
            pattern="~ ~ ~ ~ snare ~ ~ ~ ~ ~ ~ ~ snare clap ~ ~",
            gain=0.8,
        ),
        Track(
            name="acid", sound="saw",
            pattern="a1 a1 ~ a2 ~ a1 ~ g1 ~ a1 a1 ~ bb1 ~ a2 ~ ~ e2",
            gain=0.75,
        ),
        Track(
            name="bell", sound="bell",
            pattern="~ ~ a4 ~ ~ ~ e5 ~ ~ ~ c5 ~ ~ ~ a4 ~",
            gain=0.45,
        ),
    ],
    fx={"reverb": 0.18, "delay": 0.12, "drive": 0.08, "volume": 0.9},
)
