# Strategy-reset handoff — current mainline

Updated 2026-09-16 JST.

This file is the short operational handoff for the current unconditional Hadwiger–Nelson mainline. Historical details remain in `HANDOFF.md`; the main strategy-reset checkpoint is in `results/strategy-reset-2026-09-16/SUMMARY.md` and `SUMMARY.json`, with later bounded follow-ups recorded separately. The old-field B status is superseded by `results/mod11-no-forced-equal-2026-09-16/README.md`.

## Current status

No new Hadwiger–Nelson lower bound has been proved. In particular, there is currently no ordinary planar unit-distance graph in this repository certified to require six colors.

### 1. Same-field palette growth is closed for targets A and B

The all1200 / wide494 Gen1 / wide494 Gen2 coordinate class admits an explicit mod-11 proper five-coloring. The valuation argument extends this to the whole real field `Q(sqrt3,sqrt5,sqrt11)`. Therefore unchanged same-field `p+d` growth cannot produce a non-5-colorable unit-distance graph, regardless of further generations.

The no-forced-equal follow-up strengthens this: for every distinct pair in that field, a proper five-coloring separating the pair exists. Thus target B is also impossible entirely within the old field. The argument uses translations of Madore's table and a single-vertex recoloring for coincident residue images; it applies more generally to any graph admitting a homomorphism to Gamma(F_11^2).

For Gen2, 875 explicit five-colorings were checked on all 80,678 saved edges and their vertex signatures separate all 73,223,151 distinct pairs. The ten regression tests and the full audit were rerun locally before integration. The written general proof is not Lean formalized or independently peer reviewed; no six-color construction or mixed-field exclusion is claimed.

Do not restart further 494-direction generations as an A- or B-search unless the construction leaves that arithmetic class. See `results/mod11-no-forced-equal-2026-09-16/PROOF_ja.md` and the accompanying evidence manifest and reproduction instructions.

### 2. Sevenfold geometry is the current field-escape reference

Haugland's 2026 sevenfold construction has been reproduced exactly through the 2,131-vertex / 12,530-edge graph. The geometry genuinely leaves the old degree-eight field. Proper five-color witnesses are independently validated.

For the tested natural terminal sets, exhaustive five-color terminal-state enumeration found no hidden interior relation beyond the terminal edges themselves. Therefore unchanged terminal-only splicing of those modules is not a useful five-color forcing mechanism.

### 3. A certified six-color scaffold exists, but it is two-distance

Parts' 31-vertex scaffold has been reproduced exactly with 57 unit edges and 56 edges of length `phi=(1+sqrt5)/2`. The two-distance graph is certified not 5-colorable and has a verified 6-coloring. Removing the phi edges leaves a 3-chromatic unit-distance graph.

This is not an HN witness. Its role is to provide a concrete six-color logical skeleton.

### 4. Current synthesis target

The missing component is an actual unit-distance gadget `H_phi` with terminals at Euclidean distance phi that is itself 5-colorable but forces its two terminals to different colors in every proper five-coloring. Such a gadget would allow the 56 virtual phi-edges in the certified six-color scaffold to be replaced by genuine unit-distance constructions.

The old real field cannot host such a gadget: the explicit finite-field five-coloring gives a same-colored pair at the phi displacement. Candidate searches must therefore use genuinely different geometry/field content.

A target-accessible mixed field such as `Q(zeta210)` is a natural search space because it contains both the sevenfold directions and pentagonal/phi structure, but no forcing claim follows merely from the field choice.

### 5. First bounded mixed-field phi assembly is closed negatively

Workflow `hn-phi-rhombus-interface`, Actions **35009411746**, tested two exact mixed-field rhombus assemblies (`same` and `alternating`) with exhaustive four-port five-color boundary relations.

For both variants the joined graph has **8,520 vertices / 50,584 exact unit-distance edges**. Full proper five-color witnesses exist for all four locally admissible boundary states `[0,1,0,1]`, `[0,1,0,2]`, `[0,1,2,1]`, and `[0,1,2,3]`. All parent edges were validated.

Therefore these bounded assemblies are:

- target A: **NOT_A**;
- desired phi-inequality gadget: **NOT_H_PHI**;
- specified pair B: **NOT_FORCED_EQUAL**.

This does not rule out other mixed-field phi gadgets. It does show that field escape plus exact phi accessibility is insufficient without stronger cross-coupling.

Detailed record: `results/strategy-reset-2026-09-16/PHI_RHOMBUS_FOLLOWUP.md`.

## Acceptance rules for the next experiments

- Positive ordinary five-colorability requires an explicit coloring validated on every exact unit edge.
- A terminal relation is accepted only after exhaustive state coverage or sound SAT/UNSAT checks; sample absence is not evidence.
- UNKNOWN, timeout, heuristic failure, graph size, local-repair distance, or solver hardness are never rigidity evidence.
- Before spending long SAT time, require real multi-contact/interior cross-coupling; one-point overlaps or terminal-only transparent joins are low priority.
- Any candidate 6-chromatic unit-distance graph must receive independent exact geometry completion and independent non-5-colorability confirmation before promotion.

## Recommended order

1. Search for `H_phi` or a stronger multiport five-color relation in mixed-field geometry outside the mod-11 barrier.
2. Prefer small modules whose complete boundary relation can be enumerated exactly.
3. Reject transparent joins early: require genuine interior cross-edges or multi-contact coupling before large SAT runs.
4. Compose only proved relations, not sampled ones, into the 31-vertex six-color scaffold or another explicit six-color skeleton.
5. If direct phi-inequality forcing remains transparent, pivot to a multiport relation and solve the composition problem as a finite CSP before building a large geometric union.
6. Keep seven-color attempts secondary: a genuine 7-chromatic unit-distance graph would settle HN, so it is not expected to be an easier intermediate target.

## Durable references

- `results/mod11-no-forced-equal-2026-09-16/README.md`
- `results/mod11-no-forced-equal-2026-09-16/SUMMARY.json`
- `results/strategy-reset-2026-09-16/SUMMARY.md`
- `results/strategy-reset-2026-09-16/SUMMARY.json`
- `results/strategy-reset-2026-09-16/PHI_RHOMBUS_FOLLOWUP.md`
- `research/strategy-reset-2026-09-16/ARITHMETIC_BARRIER.md`
- `research/strategy-reset-2026-09-16/PHI_TARGET_AND_INTERFACE_GATES.md`

This handoff supersedes the old p1q7/palette-growth section of `HANDOFF.md` for choosing new target-A experiments, while preserving those earlier results as historical diagnostics. The no-forced-equal follow-up supersedes older statements leaving B open within the old field.
