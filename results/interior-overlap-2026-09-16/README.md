# Archived translation candidates: integration and bounded continuation

2026-09-16 JST. **No new Hadwiger–Nelson lower bound is claimed.** This is the
translation/overlap series from the previous local bundle, not the newer
4,097/5,667-vertex reflection series. Existing reflection results and the
seven-color proof are unchanged.

## Archived result

| case | vertices | exact unit edges | archived five-color status |
|---|---:|---:|---|
| g3-shift-2 | 3,812 | 24,275 | UNKNOWN after a 10-second local probe |
| g3-shift-3 | 5,493 | 36,106 | UNKNOWN after a 10-second local probe |
| u | 15,908 | 103,045 | UNKNOWN after a 10-second local probe |
| one | 17,040 | 109,688 | explicit five-colorings: NOT_A and NOT_H_PHI |
| fork | 23,090 | 154,809 | UNKNOWN after a 10-second local probe |

All four unresolved cases have archived six-color witnesses. Six-colorability
of a finite graph does not establish that six colors are required. On integration,
all five archived graph-file hashes and all six complete coloring witnesses were
rechecked locally, including every saved edge and every stated terminal pin.
`ARCHIVE_INDEX.json` preserves their identities and records the original bundle
SHA-256. These are historical local results, not claims that the new Actions run
has already finished.

## Integration policy

The prior standalone patch is adapted to the current repository rather than
blindly applied. In particular, the current `hn_hex7_certificate.py` and reflection
code are not replaced. The corrected `hn_closed_trace_color_probe.py` is reused:
CaDiCaL195 is a positive-witness finder only; Glucose4 negatives require strict
DRAT verification. A failed calibration or proof check is an error, not a theorem.

This Git commit stores the result index, exact regeneration code, independent
audit and continuation workflow. The large original graph and coloring archives
are not duplicated in this commit. Their identities remain in the index; original
bytes are in the supplied local bundle. The workflow regenerates identical point
and edge sets and rejects any mismatch of the archived semantic SHA-256. It saves
new complete graphs, source G3, models, recipes, control proofs and logs as Actions
artifacts with 90-day retention. Archive those artifacts for longer-term storage.

## Continuation

Workflow `.github/workflows/hn-translation-resume.yml` runs on changes to that
workflow on main, or by manual dispatch. By default it tests the four unresolved
cases with CaDiCaL195 and Glucose4, at most four jobs concurrently. Each job has a
12-minute cap. Ordinary five-color probes have a 90-second cap, ordinary six-color
probes 30 seconds, and each of four positive-only cyclic-copy probes 15 seconds.
Timeout and unchecked UNSAT are not evidence.

For a translated copy t, the auxiliary search restricts its colors to
`C(copy_t[i]) = X_i + phase[t] (mod 5)`. Actual overlaps impose potential equations;
all original edges produce inequalities. A weighted disjoint-set structure
compresses the equations. Every SAT result is lifted and checked on **all original
edges**. An inconsistent phase system, auxiliary UNSAT or timeout rejects at most
that extra ansatz; it never rejects ordinary five-colorability. Eight regression
tests include exhaustive checks of all 64 graphs on four vertices under all five
second-copy phases (320 graph/phase combinations).

All new graphs receive the independent SymPy/Phi210 all-pairs audit, using primes
631 and 1051 rather than the construction's 211 and 421. Moduli are only necessary
filters; every survivor uses exact polynomial norm arithmetic.

The `one` case is an already-excluded control and is omitted from default A-search.
It remains manually reproducible. No terminal-forcing conclusion follows merely
from an ordinary five-color witness. The G3-shift terminals are at distance one;
they are not H_phi terminals.

## Reproduce locally

Obtain the original G3 from Actions run 35003232409, artifact 10410248491, and
check SHA-256 `90096518a3c10de93066f6fee70a0b16a218a094de5e5b35285089472d646b8a`.
Dependencies and the pinned DRAT checker are specified in the workflow.

```sh
PYTHONPATH=tools python -m unittest discover -s tools -p test_hn_translation_phase.py -v
python tools/hn_translation_resume.py --source /tmp/input/heptagon/G3.json \
  --case g3-shift-2 --solver glucose4 --checker /tmp/drat-trim \
  --seconds 90 --phase-seconds 15 --out /tmp/translation
```

The per-case `SUMMARY.json` in Actions is the current result, while
`ARCHIVE_INDEX.json` deliberately remains the historical checkpoint. Any candidate
non-five-colorability still requires independent review before promotion.
