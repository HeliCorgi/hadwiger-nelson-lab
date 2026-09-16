# Translation/overlap candidates: verified continuation checkpoint

2026-09-16 JST. **No new Hadwiger–Nelson lower bound is claimed.**
The resumed Actions run found proper five-colorings of both G3 translation
candidates. Their old UNKNOWN A statuses are superseded by **NOT_A**.
The two mixed-field candidates remain UNKNOWN.

This is the 3,812/5,493/15,908/23,090-vertex translation series, not the separate
4,097/5,667-vertex reflection series. Existing reflection code and the seven-color
proof have not been replaced.

## Current results

Run [35049612048](https://github.com/HeliCorgi/hadwiger-nelson-lab/actions/runs/35049612048),
source commit `fcb3e7fa3a494c46981fff4b6b22e901de5e02ea`, completed all eight jobs
successfully. Job success means the bounded experiment and validations finished,
not that a six-chromatic graph was found.

| case | vertices | unit edges | current A status | new full five-color witnesses |
|---|---:|---:|---|---:|
| g3-shift-2 | 3,812 | 24,275 | NOT_A | 1, CaDiCaL |
| g3-shift-3 | 5,493 | 36,106 | NOT_A | 2, CaDiCaL and Glucose |
| u | 15,908 | 103,045 | UNKNOWN | 0 |
| fork | 23,090 | 154,809 | UNKNOWN | 0 |
| one, historical control | 17,040 | 109,688 | NOT_A, already excluded | not rerun |

All eight ordinary five-color probes timed out at 90 seconds. All eight ordinary
six-color probes produced validated models. The positive-only cyclic-copy search
then found the three five-color models above. The remaining phase attempts timed
out at 15 seconds each; neither direct nor auxiliary timeout is forcing evidence.
A single valid five-color witness excludes target A regardless of another solver's
timeout. No candidate ordinary non-five-colorability proof was obtained.

The three new five-colorings and all eight six-colorings were downloaded and
checked locally on every original edge, including the recorded hard pins. Each
artifact ZIP digest and each graph semantic hash was checked. The point and edge
order agrees with the original archived geometry. Eight phase-encoding regression
tests passed in Actions; eight additional witness-verifier regression tests passed
locally after the run. The latter were not part of that Actions run.

## Why the extra search helped

For copy t of a common source, restrict colors to
`C(copy_t[i]) = X_i + phase[t] (mod 5)`. Actual coincident points impose equations
on the X_i; a weighted disjoint-set structure compresses them. Every original edge
adds a constraint. The successful offsets were `[0,1]` and `[0,1,2]`.

The auxiliary model is lifted to all original vertices and rechecked without
trusting the quotient or solver. An inconsistent phase system, auxiliary UNSAT or
timeout would only reject that extra restriction, never ordinary five-colorability.
These colorings do not establish a plane-wide five-coloring or a field-wide theorem.
The G3 translation terminals are at distance one, not phi.

## Geometry and proof policy

`tools/hn_translation_resume.py` reconstructs exactly the prior candidates from
G3, merges actual coincident points and includes every exact unit-distance pair.
`ARCHIVE_INDEX.json` preserves the historical semantic hashes and old outcomes;
it is deliberately not rewritten to hide the original UNKNOWN results.

Every Actions job independently audited the complete point-pair set using
`tools/hn_cyclotomic210_independent_audit.py`: SymPy generates Phi210, with separate
polynomial arithmetic and necessary residue filters at primes 631 and 1051 rather
than the construction's 211 and 421. Surviving norms are evaluated exactly. All
saved induced unit-edge sets matched. The geometry is not based on float tolerance.

The corrected `hn_closed_trace_color_probe.py` is reused. CaDiCaL195 is only a
positive-witness finder: negatives remain UNSAT_UNCHECKED because its proof-output
path failed earlier controls. Glucose4 negatives require strict DRAT verification.
Abstract K6/5 and K6/6 calibrations passed the stated policies in all jobs. K6 is a
solver control, not a planar unit-distance realization.

## Durable evidence and reproduction

`SUMMARY.json` contains the current status, all eight artifact IDs and ZIP hashes.
`G3_FIVE_COLORINGS.json.gz` stores all three complete new five-colorings directly
in Git. Its SHA-256 is
`c03df0aa616ad9071cef0401e55e2108526af40f276f17015b6c873644f12ecb`.
The digit strings omit the trailing newline; add one newline when checking their
recorded text-file hashes. The verifier handles this detail.

After extracting a corresponding Actions artifact (for example 10427788574 for
G3-shift-2 or 10428586075 for G3-shift-3):

```sh
python tools/hn_verify_translation_witness.py --graph /tmp/translation/GRAPH.json
PYTHONPATH=tools python -m unittest discover -s tools -p 'test_hn_translation_*.py' -v
python tools/hn_cyclotomic210_independent_audit.py \
  --graph /tmp/translation/GRAPH.json --out /tmp/independent.json
```

The witness-only verifier uses standard Python, no solver or geometry library;
its semantic hash binds the graph to the separate geometry audit. The last command
requires NumPy and SymPy and redoes the all-pairs geometry audit.

Full graphs, G3 source, CNFs, recipes, control proofs, six-colorings and logs are in
the eight Actions artifacts, expiring **2026-12-15** under 90-day retention. These
large archives are not all duplicated in Git; preserve them separately for longer
storage. The three decisive five-color witnesses are not subject to artifact expiry.
The original local bundle identity remains in `ARCHIVE_INDEX.json`.

## Next checkpoint

Only `u` and `fork` remain unresolved in this bounded series. The current workflow
is **manual-only**; `case=all` selects these two, not the already-excluded G3
candidates. Explicit G3 and `one` choices remain available as reproductions/controls.
The results commit does not launch another run. No polling or indefinite retries
are configured.

Do not infer that the remaining cases need six colors from their timeouts. A useful
next step must change the search restriction, use further interior constraints, or
supply a new verified model/proof; an unchanged failed phase search is not progress.
The run checkpoint preserves results and geometry, not a suspended SAT solver's
learned-clause state.
