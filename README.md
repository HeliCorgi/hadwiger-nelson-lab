# hadwiger-nelson-lab

Computational research workspace for the Hadwiger–Nelson problem.

> This repository does **not** claim a solution of the Hadwiger–Nelson problem. The active program searches for unconditional finite planar unit-distance constructions that would improve the lower bound, while preserving older conditional and negative results as audited components.

## Active objective

The active target is one of:

- **A:** a finite planar unit-distance graph that is not 5-colorable; or
- **B:** a finite 5-colorable planar unit-distance graph with two fixed, distinct actual points that receive the same color in every proper 5-coloring.

For target B, any strictly positive Euclidean distance is sufficient by the Lean-checked `PositiveDistance` reduction.

## Current strategy-reset checkpoint

The former p1q7 / palette-growth mainline is no longer the preferred A-search.

### Same-field growth is closed for A

The all1200 / wide494 Gen1 / wide494 Gen2 coordinate class admits an explicit mod-11 proper five-coloring, and the valuation argument extends the five-color upper bound to the whole real field `Q(sqrt3,sqrt5,sqrt11)`.

Therefore unchanged same-field `p+d` growth cannot produce target A, regardless of further generations. This does not settle target B.

### Field escape has been reproduced exactly

A sevenfold construction has been reconstructed exactly through a **2,131-vertex / 12,530-edge** unit-distance graph whose geometry genuinely leaves the old field. Proper five-color witnesses are independently validated.

For the natural terminal sets tested so far, exhaustive five-color boundary-state enumeration found no hidden interior relation beyond the terminal edges themselves. Terminal-only splicing of those modules is therefore not a useful five-color forcing mechanism.

### A concrete six-color scaffold exists, but it is two-distance

A 31-vertex scaffold has been reconstructed with:

- **57 unit-distance edges**;
- **56 edges of length `phi=(1+sqrt5)/2`**.

The full two-distance graph is certified not 5-colorable and has a verified 6-coloring. Removing the phi edges leaves a 3-chromatic unit-distance graph.

This is **not** an HN witness. It is a concrete six-color logical skeleton whose long constraints still need to be realized by genuine unit-distance gadgets.

## Current synthesis target: `H_phi`

The main missing component is an actual unit-distance gadget `H_phi` with terminals at Euclidean distance phi that:

1. is 5-colorable; and
2. forces its two terminals to receive different colors in every proper 5-coloring.

Such a gadget would allow the 56 virtual phi-edges in the two-distance six-color scaffold to be replaced by genuine unit-distance constructions.

The old real field cannot host such a gadget, so searches must use genuinely different geometry/field content.

## Latest bounded mixed-field test

Workflow `hn-phi-rhombus-interface`, Actions run **35009411746**, tested two exact mixed-field rhombus assemblies with exhaustive four-port five-color boundary relations.

For both variants:

- **8,520 vertices / 50,584 exact unit-distance edges**;
- target A: **NOT_A**;
- desired phi-inequality gadget: **NOT_H_PHI**;
- specified pair B: **NOT_FORCED_EQUAL**;
- all four locally admissible four-port states have full validated five-color witnesses.

So field escape plus exact phi accessibility is not sufficient by itself. The next useful candidates should have genuine multi-contact/interior cross-coupling, and their complete five-color boundary relation should be computed before large composition attempts.

## Operational continuation

Use [`STRATEGY_RESET_HANDOFF.md`](STRATEGY_RESET_HANDOFF.md) as the current short handoff.

Primary durable references:

- [`results/strategy-reset-2026-09-16/SUMMARY.md`](results/strategy-reset-2026-09-16/SUMMARY.md)
- [`results/strategy-reset-2026-09-16/SUMMARY.json`](results/strategy-reset-2026-09-16/SUMMARY.json)
- [`results/strategy-reset-2026-09-16/PHI_RHOMBUS_FOLLOWUP.md`](results/strategy-reset-2026-09-16/PHI_RHOMBUS_FOLLOWUP.md)
- [`research/strategy-reset-2026-09-16/ARITHMETIC_BARRIER.md`](research/strategy-reset-2026-09-16/ARITHMETIC_BARRIER.md)
- [`research/strategy-reset-2026-09-16/PHI_TARGET_AND_INTERFACE_GATES.md`](research/strategy-reset-2026-09-16/PHI_TARGET_AND_INTERFACE_GATES.md)

Historical operational details remain in [`HANDOFF.md`](HANDOFF.md), and broader background remains in [`RESEARCH.md`](RESEARCH.md).

## Evidence policy

Whenever a search produces a lemma-like or theorem-like statement, preserve:

- the exact statement and scope;
- exact geometry or a sound completion argument;
- explicit positive colorings validated on every claimed edge;
- solver/checker identity for negative claims;
- independent confirmation before promoting candidate A/B results;
- compact hashes, artifact IDs, and regeneration code.

UNKNOWN, timeout, heuristic failure, solver difficulty, graph size, or absence from a sampled coloring family are never treated as forcing evidence.

## Current recommended order

1. Search for `H_phi` or a stronger multiport five-color relation outside the mod-11 barrier.
2. Prefer small modules whose complete boundary relation can be enumerated exactly.
3. Reject transparent one-point/terminal-only joins early; require real interior cross-coupling.
4. Compose only proved boundary relations into the 31-vertex six-color scaffold or another explicit six-color skeleton.
5. If direct phi-inequality forcing remains transparent, pivot to a multiport relation and solve the finite composition CSP before building a large geometric union.
6. Keep 7-chromatic attempts secondary: a genuine 7-chromatic unit-distance graph would settle HN and is not expected to be an easier intermediate target.
