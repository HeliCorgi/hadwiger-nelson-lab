# Human-readable note: the `q0=q10` five-vertex palette gate

**Scope.** This is a finite statement inside the pinned quotient/C88 system. It is not an unconditional unit-distance gadget and does not change the Hadwiger–Nelson bound.

Inside the 267-qnode left bag of the six-vertex `p`–`q` separator proof, the forced equality

`q0 = q10`

has a minimum vertex separator

`T = {q14, q18, q54, q55, q256}`

of size five.

Removing `T` leaves `q10` by itself on one side and the 261-qnode component containing `q0` on the other. In fact `q10` has degree exactly five in the left bag and its neighborhood is exactly `T`.

## State filter

Up to color renaming there are 52 possible color partitions of five labeled boundary vertices. The large `q0` side extends only three:

- `01230`, with `q0` forced to color `4`;
- `01233`, with `q0` forced to color `4`;
- `01234`, with `q0` allowed colors `3` or `4`.

The singleton `q10` side extends 26 boundary states. Its intersection with the large-side table is only

`01230`, `01233`.

The reason the third large-side state disappears is elementary: `01234` uses all five colors on the five neighbors of `q10`, leaving no color for `q10` itself.

In each of the two surviving states the five neighbors of `q10` use only four colors, and `q10` is forced to the missing fifth color, namely color `4`. The large side also forces `q0` to color `4` in those two states. Therefore `q0=q10`.

So this equality factors as

`large 261-node side -> 3 boundary states -> degree-5 palette gate removes 01234 -> 2 states -> same missing color on both endpoints`.

This is substantially more explanatory than a direct SAT query for `q0 != q10`.

## What is still nonlocal

The remaining difficult part is the large-side assertion that only `01230`, `01233`, and `01234` extend. Pairwise equality/disequality relations do **not** characterize either the two globally viable separator states or the four augmented `[q0]+T` states. Thus a purely pairwise description still misses a disjunctive relation.

The augmented color-symmetric states on `[q0,q14,q18,q54,q55,q256]` are

- `012304`
- `012340`
- `012341`
- `012344`

(where canonical restricted-growth relabeling is used).

This suggests that the next useful explanatory language should allow a small finite disjunction / palette constraint, rather than only pairwise equality atoms.

## Evidence

Discovery of the recursive minimum separator and its boundary table:

- `tools/separator_left_recursive_interfaces.py`
- `results/separator-left-recursive-interfaces/analysis.json`
- workflow run `34697314517` (CaDiCaL195)

Independent solver re-enumeration and palette-gate analysis:

- `tools/separator_left_q0_q10_compression.py`
- `results/separator-left-q0-q10-compression/analysis.json`
- `results/separator-left-q0-q10-compression/SUMMARY.md`
- workflow run `34697626060` (Glucose4)

Evidence level: **independently solver-rechecked finite statement** for the stated quotient left bag. Both computations share the repository's quotient construction/min-cut helper, so this is not a fully independent graph reconstruction.
