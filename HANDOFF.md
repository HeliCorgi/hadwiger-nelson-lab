# Handoff — P2 forcing / semantic-interface program

Last updated: 2026-09-12

## Scope and proof discipline

This repository continues the finite five-color forcing program inherited from `HeliCorgi/five-color-forcing-anatomy` at pinned upstream commit

`d1e80998bda337d9fa721f2e96d203ae54e97fc8`.

The main conditional formulas are

- `A = H* ∧ C88`;
- `B = H* ∧ (c(217) != c(490))`.

`H*` is the first minimal core from `B5_MULTICORE.json`; `C88` is `C_min` from `B5_P2_LEMMA.json`.

No result in this handoff is an unconditional finite unit-distance 6-chromatic graph. Nothing here changes the known Hadwiger–Nelson lower bound. Always distinguish conditional finite statements from genuine geometric statements.

## Research-recording policy: preserve interesting mathematics, not only wins

The user should not have to decide which computational observations are mathematically interesting. Future work must proactively preserve structures that look non-generic, concise, symmetric, extremal, unexpectedly rigid, recurrent, or informative as negative results.

Use these evidence labels:

1. **proved / independently verified finite statement**;
2. **exact computational observation** not yet independently reimplemented;
3. **empirical pattern** over a sample;
4. **conjectural interpretation**.

For each important observation record the precise claim, why it matters, generating code/results, solver/checker and exhaustive/sample scope, independent-verification status, and all conditionality. Prefer a human explanation over a raw SAT/UNSAT verdict whenever possible.

For geometric observations, record exact coordinates/distances when practical and state explicitly whether the object is genuinely unit-distance or only abstract/conditional.

## Closed lane — support `<=4` port-free equality interfaces

**Evidence level: independently verified finite statement.**

The port-free equality language observes only the equality partition of colors on a selected set of non-port vertices. There are 391 non-port vertices and 76,245 pair-atoms.

The terminal producing computation, workflow run `34683854626`, ended with:

- upstream seed fooling pairs: **872**;
- lab-generated pairs: **6139**;
- full validated A/B records: **7011**;
- unique difference cuts: **7008**;
- duplicate cuts: **3**;
- completed fixed-pivot roots: **23,440 / 23,440**;
- cut-library SHA-256: `a58cb579f1fa725107ef10a776b290c089a8ff0cfc12dc4d75fa1fe82ba5ccfa`.

An independent reconstruction/checker workflow, run `34693564501`, rebuilt the 7011 witness pairs and the same 7008 unique cuts from saved colorings, reproduced the same SHA-256, and exhausted all **9,810,580 / 9,810,580** increasing first triples with a different C++ four-set decomposition. The verifier matched literal brute force on 600 randomized toy instances.

Finite conclusion:

> **For the pinned A/B system, no port-free equality semantic interface supported on at most four vertices exists.**

Searching exactly four vertices is complete for support `<=4`, because a separator on fewer vertices remains a separator after adding arbitrary non-port vertices.

Evidence:

- `results/exact-cegis-loop/MASTER_FINAL.json`;
- `results/independent-fourset-verify/RECONSTRUCTION.json`;
- `results/independent-fourset-verify/VERIFICATION.json`;
- `results/independent-fourset-verify/SUMMARY.md`;
- `tools/reconstruct_fourset_cuts_independent.py`;
- `tools/verify_fourset_exhaustion_independent.cpp`.

This is conditional and non-geometric. Do **not** restart the support-4 master as unfinished work.

Historical Run-4 counter correction: run `34562068005` added **2705** sound cuts and made **2705** oracle calls, while its checkpoint `fast_candidates` counter is **2702**. Do not identify those counters.

## Verified structural backbone

For `Q = H*/C88`:

- 305 vertices / 1599 edges;
- `Q` is 5-colorable;
- `Q + pq` is not 5-colorable and is vertex-critical under single-vertex deletion;
- no articulation point or 2-vertex cut;
- `p`–`q` vertex connectivity in `Q` is 6.

Evidence: `results/quotient-critical/analysis.json`.

A minimum `p`–`q` separator is

`S = {0, 6, 8, 9, 10, 266}`.

Deleting it gives a 261-qnode `p` side and a 38-qnode `q` side. Of 202 canonical boundary equality states:

- `p` side extends exactly `012202`, `012203`;
- `q` side extends 81 states;
- the intersection is exactly `012203`.

For that unique global state both sides force their port to the same singleton boundary color. CaDiCaL discovery was independently re-enumerated with Glucose4.

Evidence:

- `results/separator-interface/analysis.json`;
- `results/separator-verify/analysis.json`.

The normalized SAT contradiction also has an independently checked LRAT proof; see `results/proof-lrat/`.

## Current headline of the human-proof lane

The large 261-qnode side is no longer best thought of as a 202-row SAT table. It now has a **hierarchical palette/interface explanation**.

At the outer boundary, including the port `p=q5`, the 267-qnode left bag forces three equalities:

- `q5=q6`;
- `q0=q10`;
- `q8=q9`.

After contracting them, the four tracked classes

- `A={q5,q6}`;
- `B={q0,q10}`;
- `C={q8,q9}`;
- `D={q266}`

have an ordinary class graph equal to **`K4` minus exactly the edge `C-D`**. Therefore exactly two color-symmetric outer states remain: `C=D` gives `012202`; otherwise `D` takes a fourth color and gives `012203`.

Evidence: `results/separator-left-compression/` and workflow run `34694157711`.

The important update is that **all three forced equalities now have explicit recursive palette/interface explanations**. They are still finite computational proofs with exact SAT leaves, not purely hand-derived graph theorems, but they are substantially more human-readable than the original 267-node SAT statement.

A consolidated narrative is in:

- `results/separator-left-recursive-chain/HUMAN_NOTE.md`.

## Equality 1 — `q5=q6`: local K4 plus a conditional missing-color gate

**Evidence level: finite exact statement; key palette predicates checked independently with CaDiCaL195 and Glucose4.**

First, there is a genuinely local graph lemma:

`q5=q22`

because their common neighbors

`{q0,q4,q8,q21}`

form a `K4`. If q5 and q22 had distinct colors, those four common neighbors would have only three colors available, impossible for a K4.

Next consider the q6–q22 minimum separator

`T4 = {q0,q4,q8,q17,q21,q30,q59,q68,q105,q223}`.

Its minimum cut size is 10. Removing it isolates q22 as a singleton; moreover q22 has degree exactly 10 in the left bag and

`N(q22)=T4`.

The first attempted palette statement was too strong: q6's color is **not** absent from T4 in every q6-side coloring. Both solvers exhibit colorings where q6 shares a color with some boundary vertex. This failed hypothesis is preserved because it identifies the correct conditional statement.

The exact condition actually needed is:

> **If the T4 boundary uses at most four colors, then q6's color is absent from every T4 vertex.**

Both CaDiCaL195 and Glucose4 independently found no counterexample to this condition. They also independently verify:

> **Every q6-side boundary coloring uses at least four colors.**

Now any coloring that also extends to singleton q22 must leave at least one color unused on `N(q22)=T4`, so T4 uses at most four colors. Combining the two q6-side facts:

- T4 uses at least four colors;
- global compatibility with q22 gives at most four colors;
- hence T4 uses exactly four colors;
- conditional q6-side lemma says q6 uses the unique missing fifth color;
- q22, adjacent to all of T4, must also use that unique missing fifth color.

Thus `q6=q22`; together with local `q5=q22`, this gives

> **`q5=q6`.**

This avoids enumerating all canonical color partitions of a ten-vertex separator.

Evidence:

- `results/separator-left-q5-q6-palette-proof/analysis.json`;
- `results/separator-left-q5-q6-palette-proof/SUMMARY.md`;
- `tools/separator_left_q5_q6_palette_proof.py`;
- workflow run `34698930121` (final conditional version; earlier run recorded the intentionally overstrong failed hypothesis).

## Equality 2 — `q0=q10`: two nested degree-5 palette gates

**Evidence level: finite exact computation; state tables independently solver-rechecked.**

A minimum q0–q10 separator is

`T1 = {q14,q18,q54,q55,q256}`.

Removing T1 isolates q10 as a singleton, with degree 5 and exactly

`N(q10)=T1`.

The large q0 side extends only three of the 52 canonical five-boundary states:

- `01230`, q0 forced to color 4;
- `01233`, q0 forced to color 4;
- `01234`, q0 allowed colors 3 or 4.

The singleton q10 side rejects only the all-five-colors state `01234`. The two globally viable states use four colors on T1, so q10 is forced to the missing fifth color, exactly q0's forced color. Hence `q0=q10`.

Evidence:

- `results/separator-left-q0-q10-compression/`;
- corrected successful workflow run `34697626060`.

### Why the three-state q0-side language is interesting

Those three q0-side states are exactly captured by eight pairwise disequalities on T1. After replacing T1 vertices by their exact forced-equality classes, seven of the eight required disequalities are ordinary graph edges. The only residual relation is

`q18 != q256`.

Evidence: `results/separator-left-q0-side-relation/`, run `34697795357`.

That residual forced disequality itself factors through another minimum five-vertex separator

`T2 = {q23,q35,q57,q86,q159}`.

Again q256 is a degree-5 singleton with

`N(q256)=T2`.

The q18 side extends eight states:

`00121, 00123, 01121, 01123, 01212, 01213, 01231, 01234`.

The q256 side removes exactly the all-five-colors state `01234`. On every one of the seven globally viable states:

- every color available to q18 is already **used** on T2;
- the colors available to q256 are exactly the colors **missing** from T2.

Hence their option sets are disjoint and `q18!=q256`.

CaDiCaL195 and Glucose4 enumerate the same interface table exactly.

Evidence:

- `results/separator-left-q18-q256-compression/`;
- run `34698220055`.

### The remaining non-pairwise content on the q18 side

The eight q18-side states share five pairwise disequalities. Those five conditions alone admit exactly nine states: the eight real states plus one extra partition

`01232`.

Thus **all higher-order information at this five-boundary layer is concentrated in one forbidden state**.

Equivalently, the residual rule can be written as the palette-containment implication

> if `q57=q159`, then `c(q35)` belongs to `{c(q23),c(q57),c(q86)}`.

Fixing `01232` is UNSAT in both CaDiCaL195 and Glucose4; nearby valid state `01231` is SAT in both. A direct induced-core explanation remains global: the best deletion-minimal core found has **236 vertices / 1263 edges**. A simple attempted local proof using two adjacent vertices each forced to the fifth color also fails: there are no such witness vertices even after expanding the four anchor colors to exact forced-equality classes.

Evidence:

- `results/separator-left-q18-forbidden-state-core/`;
- `results/separator-left-q18-palette-witness/`;
- runs `34698355290`, `34698438837`.

This is an important negative result: the useful compression is the **single forbidden partition / palette implication**, not a hidden tiny induced subgraph or the simplest fifth-color collision gadget.

## Equality 3 — `q8=q9`: a seven-boundary missing-color gate via q104

**Evidence level: finite exact computation; full boundary enumeration agrees between CaDiCaL195 and Glucose4.**

The direct q8–q9 minimum cut in the left bag is 14, but scanning intermediate vertices in their exact forced-equality class finds a much better route through q104.

Both q8–q104 and q9–q104 have minimum cut 7, using the same separator

`T3 = {q4,q5,q33,q62,q68,q78,q226}`.

Removing T3 leaves q8 and q9 together in a 259-qnode component and isolates q104 as a singleton. Moreover

- `deg(q104)=7`;
- `N(q104)=T3`.

Exact seven-boundary enumeration gives:

- large q8/q9 side: 12 extendable states;
- singleton q104 side: 81 states;
- intersection: exactly 2 states.

The two common states are

- `0112323`;
- `0112333`.

Both use exactly four boundary colors. In each state q8, q9 and q104 are all forced to the same unique missing fifth color.

The other ten large-side states use all five colors on T3 and are automatically rejected by singleton q104, because q104 is adjacent to every boundary vertex.

Thus the human explanation is:

> the large side permits 12 states; q104's full-neighborhood palette gate discards the ten five-color states; in the two surviving four-color states q8, q9 and q104 all equal the missing color.

Therefore

> **`q8=q9`.**

Evidence:

- `results/separator-left-equality-class-cut-routes/`;
- `results/separator-left-q8-q9-via-q104/analysis.json`;
- `results/separator-left-q8-q9-via-q104/SUMMARY.md`;
- runs `34698593630`, `34698686504`.

The cut-route scan also shows the contrast between the three target equality classes:

- q0–q10 compresses directly to width 5;
- q8–q9 compresses through q104 to width 7;
- q5–q6 cannot be routed below width 10 even through its 13-member equality class, so its conditional palette proof above is the useful compression.

## What has and has not been achieved

The original large-side statement

`202 canonical outer boundary states -> exactly 2`

now has a hierarchical explanation:

1. three forced equalities reduce the outer relation to `K4-e`;
2. `q5=q6` follows from one local K4 equality plus a conditional four-color/missing-color gate on a ten-boundary separator;
3. `q0=q10` follows from a five-boundary degree-5 missing-color gate, whose only non-edge residual relation recursively factors through another five-boundary degree-5 used-color/missing-color gate;
4. `q8=q9` follows from a seven-boundary degree-7 singleton gate through q104.

This is a substantial human-readable compression of the finite proof. However, it is **not yet a purely graph-theoretic hand proof**: several leaves are exact SAT-verified palette predicates or small boundary-state languages. Treat them as independently solver-crosschecked finite lemmas, not informal theorems proved without computation.

No part of this section is geometric, and none implies `χ(R²)>=6`.

## Current next work, in priority order

1. **Turn the palette leaves into smaller/certificate-style lemmas.** The best targets are:
   - q5/q6 large-side predicates: why T4 needs at least four colors, and why q6's color disappears whenever T4 uses at most four;
   - q8/q9 large-side 12-state language: seek a small conjunction/disjunction or palette clause system explaining why only the two four-color states survive q104;
   - q18-side forbidden partition `01232`: seek a structural proof of the palette-containment implication. The simplest adjacent-fifth-color witness has already been ruled out.
2. **Build a standalone proof-tree checker/certificate** for the hierarchical left-side explanation. This would separate trust in the readable decomposition from trust in one SAT implementation and make the finite argument easier to audit.
3. **Geometric bridge work.** Continue looking for a way to turn a conditional same-color relation into an unconditional unit-distance forcing pair, ideally at Euclidean distance at least `1/2` so the rotation-doubling bridge applies.
4. **Richer semantic observables.** The support-4 equality-only language is exhausted; the palette implications above are evidence that richer observables can compress information differently.
5. **Support-5 equality search only with an explanatory reason.** Do not increase support merely because five is the next integer.

The eventual Hadwiger–Nelson objective remains geometric: an unconditional forced-mono pair at Euclidean distance at least `1/2`, or an equivalent finite 6-chromatic unit-distance construction.

## Evidence/checkpoint invariants

Preserve these rules:

- every A/B witness must validate against its defining formula;
- oracle UNKNOWN never creates a blocking cut;
- heuristic failure is never proof;
- terminal finite claims require independent reconstruction or certificate checking before theorem-level promotion;
- conditional quotient/SAT statements must never be presented as unconditional geometric results;
- when a proposed local explanation fails, record the failure if it rules out a natural proof shape;
- proactively record mathematically interesting negative results and structural near-misses, not only wins.

## Resume checklist

1. Do **not** restart the support-4 equality CEGIS/master; that lane is closed and independently verified.
2. Read `results/separator-left-recursive-chain/HUMAN_NOTE.md` and the three equality sections above before continuing the human-proof lane.
3. Treat the outer three equalities as **explained by a hierarchical finite proof tree**, not as unresolved raw SAT statements.
4. The cleanest remaining human-proof targets are the q5/q6 conditional palette predicates, the q8/q9 large-side 12-state language, and the q18-side forbidden state `01232`.
5. Preserve the 7011-pair / 7008-cut checkpoint as evidence and structural data, not as unfinished search state.
6. Prefer proof-tree/certificate work or geometric bridge work over blindly increasing semantic support.
7. Continue documenting interesting mathematical/geometric structures with evidence level and conditional scope.
