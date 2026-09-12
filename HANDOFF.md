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

The user should not have to decide which computational observations are mathematically interesting. Future work must proactively preserve structures that look non-generic, concise, symmetric, extremal, unexpectedly rigid, or recurrent.

Examples include:

- small separators, interfaces, critical substructures, and forcing witnesses;
- color-symmetric state descriptions;
- repeated Kempe/path skeletons;
- forced-equality backbones;
- unexpectedly small projection spaces;
- local graph-theoretic forcing lemmas;
- exact geometric symmetries, distances, rotations, reflections, lattice structure, or repeated unit-distance motifs;
- near-misses one state/edge/constraint from separation;
- exact exhaustion results that delimit what a chosen explanatory language can express.

Use these evidence labels:

1. **proved / independently verified finite statement**;
2. **exact computational observation** not yet independently reimplemented;
3. **empirical pattern** over a sample;
4. **conjectural interpretation**.

For each important observation record the precise claim, why it matters, generating code/results, solver/checker and exhaustive/sample scope, independent-verification status, and all conditionality. Prefer a human explanation over a raw SAT/UNSAT verdict whenever possible.

For geometric observations, record exact coordinates/distances when practical and say explicitly whether the object is genuinely unit-distance or only abstract/conditional.

## Current headline result — support `<=4` port-free equality interfaces do not exist

**Evidence level: independently verified finite statement.**

Consider only non-port vertices and observe, on a support `S`, the equality partition of the five colors. There are 391 non-port vertices and 76,245 unordered pair-atoms.

For every validated A/B fooling pair `(alpha,beta)`, define a difference graph by

`{u,v} in D(alpha,beta)  <=>  [alpha(u)=alpha(v)] != [beta(u)=beta(v)]`.

A four-set can separate the A and B projected equality-state families only if one of its six internal pairs lies in every accumulated difference graph. Conversely, if a four-set misses one validated difference graph, that fooling pair explicitly witnesses that A and B agree on the complete equality pattern of the four-set.

Searching exactly four vertices is complete for support `<=4`: any separator on fewer vertices remains a separator after adding arbitrary non-port vertices.

### Producing computation

Workflow run `34683854626` (`exact-cegis-loop-v2`) terminated with:

- upstream seed fooling pairs: **872**;
- lab-generated fooling pairs: **6139**;
- full validated A/B pair records: **7011**;
- unique difference cuts: **7008**;
- exact duplicate cuts: **3**;
- non-port vertices: **391**;
- pair-atoms: **76,245**;
- fixed pivot root count: **23,440**;
- completed roots: **23,440 / 23,440**;
- producing status: `EXACT-MASTER-EXHAUSTED-REQUIRES-INDEPENDENT-VERIFY`.

Final cut-library SHA-256:

`a58cb579f1fa725107ef10a776b290c089a8ff0cfc12dc4d75fa1fe82ba5ccfa`

Evidence:

- `results/exact-cegis-loop/MASTER_FINAL.json`;
- `results/exact-cegis-loop/STATUS.md`;
- `results/exact-cegis-loop/master-current/STATE.json`;
- `results/exact-cegis-loop/master-current/ROOT_ORDER.json`;
- `checkpoints/semantic_portfree_s4.json.gz`.

Producing artifact `10298170797`, ZIP SHA-256 `33be9aa4456a8fb293811c39b5a4bf58574d9a34c9f8bbc812b5091a7fb96d29`. The user-supplied artifact copy was checked against this digest and matched.

### Independent reconstruction and exhaustive checker

Workflow run `34693564501` independently rechecked the finite statement using code that does **not** import the producing master and a search decomposition that does **not** use its pivot/root-order/canonicalization logic.

`tools/reconstruct_fourset_cuts_independent.py`:

- reloads pinned H*/C88 source data;
- validates every alpha model directly against `A`;
- validates every beta model directly against `B`;
- reconstructs all non-port equality-difference masks;
- independently deduplicates the masks.

It reproduced exactly:

- full pair count **7011**;
- lab pair count **6139**;
- unique cuts **7008**;
- duplicates **3**;
- the same cut-library SHA-256 `a58cb579f1fa725107ef10a776b290c089a8ff0cfc12dc4d75fa1fe82ba5ccfa`.

`tools/verify_fourset_exhaustion_independent.cpp` uses a different exhaustive decomposition. Every four-set has a unique increasing representation `a<b<c<d`. For each first triple `a<b<c`, the checker starts with all `d>c`; for every cut not already hit by `ab`, `ac`, or `bc`, it intersects the candidate set with

`N_t(a) ∪ N_t(b) ∪ N_t(c)`.

A surviving `d` would be a four-set hitting every cut. The checker exhausted

**9,810,580 / 9,810,580**

possible increasing first triples with no survivor. Before the full run, the implementation matched literal four-set brute force on **600 randomized toy instances**.

Independent evidence:

- `results/independent-fourset-verify/RECONSTRUCTION.json`;
- `results/independent-fourset-verify/VERIFICATION.json`;
- `results/independent-fourset-verify/SUMMARY.md`;
- `.github/workflows/verify-fourset-exhaustion-independent.yml`.

Independent artifact:

- id `10297481903`;
- SHA-256 `b546962ed743046fe8d55008e019efaaf52ba6a8772b0aed0b3afaa65f45e344`.

### Finite conclusion

The independently verified statement is:

> **For the pinned A/B system, no port-free equality semantic interface supported on at most four vertices exists.**

Equivalently, this particular port-free equality-observable language requires support at least five if it is to separate A from B.

This conclusion is conditional and non-geometric. It does not rule out:

- support-5 or larger equality interfaces;
- the six-vertex quotient separator below;
- smaller interfaces using richer observables;
- an unconditional unit-distance forcing gadget.

It does not imply `χ(R²) >= 6`.

## Why this negative result is structurally interesting

The earlier proof-guided search repeatedly found four-vertex supports whose A/B projected state sets overlap in only one state. So support 4 looked close to sufficient.

P3 now shows that the residual obstruction is not merely a search failure: **no four non-port vertices can carry the entire conditional forcing relation when only equality pattern is observed**.

This gives a meaningful lower bound on the complexity of that explanatory language. It also makes the verified six-vertex quotient separator more significant: the current clean human-readable explanation genuinely lives above the exhausted four-vertex port-free equality regime.

## Other verified structural results

### Quotient criticality

For `Q = H*/C88`:

- `Q` has 305 vertices and 1599 edges;
- `Q` is 5-colorable;
- adding the edge between the quotient classes containing 217 and 490 makes it non-5-colorable;
- every one-vertex deletion restores 5-colorability;
- there is no articulation point and no 2-vertex cut;
- `p`-to-`q` vertex connectivity in `Q` is 6.

Evidence: `results/quotient-critical/analysis.json`, `tools/quotient_critical.py`.

### Six-vertex color-symmetric separator proof

A minimum `p`-`q` separator in quotient-node numbering is

`S = {0, 6, 8, 9, 10, 266}`.

Deleting it leaves a 261-vertex `p` side and a 38-vertex `q` side. Of all 202 canonical equality partitions of the six boundary vertices using at most five colors:

- 2 extend to the `p` side: `012202`, `012203`;
- 81 extend to the `q` side;
- exactly one extends to both: `012203`.

For that unique state both sides force their port to the same singleton boundary color, hence every proper 5-coloring of Q satisfies `c(217)=c(490)`.

Discovery used CaDiCaL; an independent Glucose4 implementation enumerated all 202 states on both sides and confirmed the unique intersection and port color.

Evidence:

- `results/separator-interface/analysis.json`;
- `results/separator-verify/analysis.json`.

This remains the cleanest verified finite explanation of the conditional P2 relation.

### Independently checked SAT-level contradiction

The normalized `COMMON ∧ A-only ∧ B-only` CNF has 1965 variables and 13,203 clauses. Glucose4 generated a DRUP proof; pinned `drat-trim` converted/trimmed it to LRAT; independent `lrat-check` accepted the proof.

Evidence: `results/proof-lrat/PARTITION.json`, `results/proof-lrat/LRAT_CONE.json`, `tools/lrat_export.py`.

## Interesting observations to preserve

See `STRUCTURAL_NOTES.md` for full explanations. Current highlights:

- the 261-vertex side of the six-separator allows only 2/202 boundary states, while the 38-vertex side allows 81;
- 20 quotient classes are globally forced to the port color;
- one of those equalities has a short local K4 common-neighborhood proof;
- 300 sampled quotient colorings repeatedly route mandatory Kempe connectivity through the same four path skeletons;
- proof-guided small supports often miss separation by exactly one state;
- support `<=4` port-free equality separation is now independently ruled out, converting a long near-miss search into a precise complexity lower bound for that observable language.

## Terminal CEGIS engineering note

The producing v2 master used a sound monotone-resume optimization. Adding a fooling-pair cut only strengthens the hitting problem, so roots already exhaustively rejected stay rejected. The implementation fixes and hashes the pivot/root order and checks that the new ordered cut library extends the old one before reusing completed roots.

The terminal run exercised this twice:

- upgraded legacy state resumed at root **4833**, not 0;
- support `{318,394,399,444}` appeared at root **10484**, was SAT in both CaDiCaL195 and Glucose4, added lab pair 6138, and search resumed at **10484**;
- support `{4,301,402,464}` appeared at root **21442**, was SAT in both solvers, added lab pair 6139, and search resumed at **21442**;
- the final library then exhausted through root **23440**.

This engineering result is no longer part of the mathematical trust boundary because the final finite claim was independently reconstructed and re-exhausted by the triple-extension verifier.

## Historical Run-4 counter correction

Run `34562068005` added **2705** sound cuts and made **2705** exact-oracle calls, with zero oracle UNKNOWNs. Its checkpoint counter `fast_candidates` is **2702**, not 2705. Keep these numbers separate; the three-call difference was not traced to the fast layer.

Run-4 artifact id `10187878072`, SHA-256 `f32e432c7f4cc8b30ce9ddbc449e9e8b23d863ad0d83772c745ed73cb1be8bcd`.

## Current direction

The support-`<=4` port-free equality lane is finished for the pinned system. **Do not rerun that master as if it were unfinished.**

High-value next directions, in approximate preference order:

1. **Human proof compression of the six-boundary interface.** Explain graph-theoretically why the 261-vertex `p` side allows only `012202` and `012203`. A small family of local forcing lemmas would improve understanding more than another generic core shrink.
2. **Geometric bridge work.** Search for ways to turn a conditional same-color relation into an unconditional unit-distance forcing pair, ideally at Euclidean distance at least `1/2` so the rotation-doubling bridge applies.
3. **Richer semantic observables.** A four-vertex equality interface is impossible, but another observable language might compress the relation differently.
4. **Support 5 equality search**, only if there is a clear explanatory or geometric reason; avoid increasing support merely because it is the next integer.

The eventual Hadwiger–Nelson objective remains geometric: an unconditional forced-mono pair at Euclidean distance at least `1/2`, or an equivalent finite 6-chromatic unit-distance construction.

## Checkpoint / evidence invariants

Preserve these rules in future computation:

- `iterations == len(new_pairs)` for generated semantic witnesses;
- every A/B witness must be validated against its defining formula;
- oracle UNKNOWN never generates a blocking cut;
- heuristic failure is never proof;
- atomic checkpoint writes and gzip integrity checks remain mandatory;
- terminal finite claims should be independently reconstructed or certificate-checked before README promotion;
- conditional quotient/SAT statements must never be presented as unconditional geometric results.

## Resume checklist

1. Read README P3 and `results/independent-fourset-verify/SUMMARY.md`; support `<=4` equality nonexistence is already independently verified.
2. Do not restart `exact-cegis-loop-v2` to continue support 4.
3. Preserve the 7011-pair / 7008-cut checkpoint as evidence and as a possible source of structural information, not as an unfinished search state.
4. Prefer human-readable analysis of the six-separator or direct geometric work before mechanically moving to larger support.
5. If a new semantic language or support-5 search is started, state beforehand what mathematical explanation or geometric bridge it is intended to expose.
6. Continue proactively documenting interesting structures and near-misses with their evidence level and scope.