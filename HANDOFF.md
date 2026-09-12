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

For each validated A/B fooling pair `(alpha,beta)`, define the difference graph

`{u,v} in D(alpha,beta)  <=>  [alpha(u)=alpha(v)] != [beta(u)=beta(v)]`.

A four-set can separate the A/B projected equality-state families only if one of its six internal pairs hits every difference graph.

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

This is conditional and non-geometric. It does not rule out support 5+, richer observables, or an unconditional unit-distance forcing gadget.

Historical Run-4 counter correction: run `34562068005` added **2705** sound cuts and made **2705** oracle calls, while its checkpoint `fast_candidates` counter is **2702**. Do not identify those counters.

## Verified structural backbone

### Critical quotient

For `Q = H*/C88`:

- 305 vertices / 1599 edges;
- `Q` is 5-colorable;
- `Q + pq` is not 5-colorable and is vertex-critical under single-vertex deletion;
- no articulation point or 2-vertex cut;
- `p`–`q` vertex connectivity in `Q` is 6.

Evidence: `results/quotient-critical/analysis.json`.

### Six-vertex color-symmetric separator

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

This remains the cleanest verified finite explanation of the conditional P2 relation.

### Independently checked SAT contradiction

The normalized `COMMON ∧ A-only ∧ B-only` CNF has 1965 variables and 13,203 clauses. Glucose4 DRUP was converted/trimmed with pinned `drat-trim` and accepted by independent `lrat-check`. The dependency cone remains global, so ordinary proof trimming does not expose a small explanation.

Evidence: `results/proof-lrat/PARTITION.json`, `results/proof-lrat/LRAT_CONE.json`.

## Active human-proof lane — compress the 261-qnode side

### Step 1: the 202-state table reduces to three equalities

**Evidence level: exact computational observation.**

Workflow run `34694157711` found that on

`{p=q5, q0, q6, q8, q9, q10, q266}`

the 267-qnode left bag forces

- `p = q6`;
- `q0 = q10`;
- `q8 = q9`.

After contracting those three equalities, ordinary graph edges give four classes

`A={p,q6}`, `B={q0,q10}`, `C={q8,q9}`, `D={q266}`

whose class graph is exactly **`K4` minus the edge `C-D`**. Therefore only two color-symmetric possibilities remain: `C=D` gives `012202`, while a distinct fourth color on `D` gives `012203`.

This is the first major human-readable compression:

> explaining the 261-node side reduces to explaining three forced equalities.

Evidence:

- `results/separator-left-compression/HUMAN_NOTE.md`;
- `results/separator-left-compression/analysis.json`.

### Step 2: no small induced forcing gadget was hiding inside

**Evidence level: exact computational observation with two-solver checks of the retained forcing properties.**

Two core-extraction routes were tried (`34694323751`, `34694642367`). The shared induced core preserving all three equalities is the entire **267-qnode / 1428-edge** left bag: every nontracked vertex is deletion-critical for at least one equality in that shared property.

Individual inclusion-minimal induced cores remain large:

- `p=q6`: **253 vertices / 1357 edges**;
- `q0=q10`: **260 / 1396**;
- `q8=q9`: **233 / 1251** in the best deletion order found (an assumption-core route found a different 234-vertex inclusion-minimal core).

The retained equality claims were checked with both CaDiCaL195 and Glucose4. These are inclusion-minimal cores for the chosen deletion orders, not minimum-size gadgets.

Interpretation: the three equalities are genuinely global in the induced-subgraph deletion sense; shrinking vertices alone is the wrong explanatory tool.

Evidence:

- `results/separator-left-forcing-cores/analysis.json`;
- `results/separator-left-unsat-cores/analysis.json`.

### Step 3: exact equality classes reveal a small overlapping K4 fabric, but it stalls

**Evidence level: exact computational observation; equality classes cross-checked by CaDiCaL195 and Glucose4.**

In the left bag the three target anchors belong to forced-equality classes of sizes 13, 8, and 13:

- class of q5: `[3,5,6,22,33,54,63,65,86,189,210,222,252]`;
- class of q0: `[0,10,39,62,98,105,214,251]`;
- class of q8: `[1,8,9,17,19,55,61,71,72,74,82,100,104]`.

Inside those classes, the simple common-neighborhood lemma finds exactly one local K4 equality in each:

- `q5=q22` via K4 `{q0,q4,q8,q21}`;
- `q0=q62` via K4 `{q4,q5,q8,q21}`;
- `q8=q17` via K4 `{q0,q4,q21,q22}`.

The witnesses strongly overlap, which is structurally notable. However iterating the same lemma after contracting newly proved equalities stops after this single round. It does **not** reach `q5=q6`, `q0=q10`, or `q8=q9`.

Evidence:

- `results/separator-left-equality-classes/analysis.json`;
- `results/separator-left-local-closure/analysis.json`;
- runs `34697174645`, `34697256661`.

### Step 4: one target equality factors through a five-vertex palette gate

**Evidence level: finite exact computation, independently solver-rechecked for the state table.**

Recursive minimum separators inside the 267-qnode left bag are:

- `q5=q6`: min cut **13**;
- `q0=q10`: min cut **5**;
- `q8=q9`: min cut **14**.

The size-5 case is the useful one. For `q0=q10`, a minimum separator is

`T = {q14, q18, q54, q55, q256}`.

Removing `T` isolates `q10` as a singleton. Moreover `q10` has degree exactly five in the left bag and `N(q10)=T`.

The large q0 side extends only three of the 52 canonical five-boundary states:

- `01230`, with q0 forced to color 4;
- `01233`, with q0 forced to color 4;
- `01234`, with q0 allowed colors 3 or 4.

The q10 singleton side extends 26 states. The intersection is exactly

`01230`, `01233`.

The excluded large-side state `01234` uses all five colors on `N(q10)`, so q10 has no available color. In each surviving state the neighborhood uses four colors and q10 is forced to the missing fifth color 4, exactly the color forced on q0. Hence `q0=q10`.

This turns one of the three global equalities into a simple two-stage explanation:

`261-node side -> three boundary states -> degree-5 palette gate removes the all-five-colors state -> both endpoints use the missing fifth color`.

CaDiCaL discovery (`34697314517`) was re-enumerated with Glucose4 (`34697626060`). The two runs share the repository quotient/min-cut construction, so call this **independently solver-rechecked**, not a fully independent graph reconstruction.

Important residual structure: neither the two globally viable separator states nor the four augmented `[q0]+T` states are characterizable by a conjunction of pairwise equality/disequality relations. A small disjunction / palette constraint is genuinely present at this recursive layer.

Human-readable note and evidence:

- `results/separator-left-q0-q10-compression/HUMAN_NOTE.md`;
- `results/separator-left-q0-q10-compression/analysis.json`;
- `results/separator-left-recursive-interfaces/analysis.json`.

## Current interpretation

The left-side proof is no longer a featureless 261-node SAT object. Its currently visible hierarchy is:

1. outer six-boundary table: `202 -> 2` states;
2. those two states are explained by three forced equalities plus a `K4-e` relation graph;
3. those equalities are not small induced-subgraph gadgets;
4. a simple overlapping K4 fabric explains one auxiliary equality in each target equality class, but local closure stalls;
5. one target equality, `q0=q10`, recursively factors through a minimum five-vertex separator and a degree-5 palette gate.

This is meaningful human-readable compression even though two target equalities remain global.

## Next work, in priority order

1. **Explain the q0-side three-state relation** `01230 / 01233 / 01234` on `{q14,q18,q54,q55,q256}` using a richer small relation than pairwise equality. The current data show that a disjunctive/palette observable is required. Look for another separator, a short finite clause system, or a reusable color-palette lemma.
2. **Look for analogous non-pairwise decompositions for `q5=q6` and `q8=q9`.** Their direct minimum cuts are 13 and 14, so do not blindly enumerate all color partitions. Search for intermediate forced-equality classes, nested separators, or palette gates first.
3. **Geometric bridge work.** Keep looking for a way to turn a conditional same-color relation into an unconditional unit-distance forcing pair, ideally at distance at least `1/2` so the rotation-doubling bridge applies.
4. **Richer semantic observables.** The support-4 equality-only language is exhausted; a richer observable may compress the relation differently.
5. **Support-5 equality search only with an explanatory reason.** Do not increase support merely because five is the next integer.

The eventual Hadwiger–Nelson objective remains geometric: an unconditional forced-mono pair at Euclidean distance at least `1/2`, or an equivalent finite 6-chromatic unit-distance construction.

## Evidence/checkpoint invariants

Preserve these rules:

- every A/B witness must validate against its defining formula;
- oracle UNKNOWN never creates a blocking cut;
- heuristic failure is never proof;
- terminal finite claims require independent reconstruction or certificate checking before theorem-level promotion;
- conditional quotient/SAT statements must never be presented as unconditional geometric results;
- proactively record mathematically interesting negative results and structural near-misses, not only wins.

## Resume checklist

1. Do **not** restart the support-4 equality CEGIS/master; that lane is closed and independently verified.
2. Read `results/separator-left-q0-q10-compression/HUMAN_NOTE.md` before continuing the human-proof lane.
3. Treat `q0=q10` as the currently best-understood of the three left-side equalities.
4. The active unresolved human-proof targets are the q0-side three-state relation, `q5=q6`, and `q8=q9`.
5. Preserve the 7011-pair / 7008-cut checkpoint as evidence and structural data, not as unfinished search state.
6. Continue documenting interesting mathematical/geometric structures with evidence level and conditional scope.
