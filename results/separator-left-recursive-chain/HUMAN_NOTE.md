# Human note — recursive palette structure on the large separator side

## Scope

Everything in this note is a finite statement about the pinned quotient/P2 system inherited from upstream commit `d1e80998bda337d9fa721f2e96d203ae54e97fc8`. It is conditional and non-geometric. It does **not** change the Hadwiger–Nelson bound.

The purpose of this note is human-readable compression: explain what the successive SAT tables are actually saying.

## 1. The outer six-boundary table reduces to three equalities

For the large side of the minimum six-vertex separator

`[q0,q6,q8,q9,q10,q266]`,

only `012202` and `012203` extend. Including the port `p=q5`, the large side forces

- `q5=q6`,
- `q0=q10`,
- `q8=q9`.

After contracting those three equalities, ordinary graph edges among the tracked classes form `K4` minus one edge. The missing edge is between the `{q8,q9}` class and `q266`, so exactly two color-symmetric states remain.

Thus the main human-proof task is to understand those three equalities rather than a 202-row boundary table.

## 2. Direct induced-core shrinking is not the explanation

The three equalities are global in the induced-subgraph sense. The best shared deletion-minimal core is the entire 267-qnode left bag. Individually, deletion-minimal induced cores still have 253, 260, and 233 vertices (the assumption-core route gives 253, 260, and 234 respectively).

A one-step common-neighborhood equality closure also stalls. It finds only the local K4 equalities

- `q5=q22`,
- `q0=q62`,
- `q8=q17`,

and does not reach `q5=q6`, `q0=q10`, or `q8=q9`.

So the useful compression is by **interfaces/palette states**, not by simply deleting most vertices.

## 3. `q0=q10` factors through a five-vertex palette interface

Inside the 267-qnode left bag, a minimum `q0`–`q10` vertex cut is

`T1 = [q14,q18,q54,q55,q256]`.

The `q10` side is a singleton: `q10` has degree 5 in the left bag and its neighborhood is exactly `T1`.

The large `q0` side allows only three canonical states on `T1`:

- `01230`, with `q0` forced to color 4;
- `01233`, with `q0` forced to color 4;
- `01234`, with `q0` allowed colors 3 or 4.

The singleton `q10` side rejects `01234`, because all five colors occur on its five neighbors and no color remains for `q10`. In the two surviving states, exactly four colors occur on the neighborhood, so `q10` is forced to the unique missing fifth color, which is also the forced color of `q0`.

This is the first clean palette mechanism:

> a degree-5 singleton filters out the all-five-colors boundary state; the surviving states force the endpoint to the missing color.

The two surviving states and endpoint colors were independently reconstructed with Glucose4 after the original separator analysis.

## 4. The three-state `q0`-side language is almost an ordinary quotient graph

The `q0`-side states `01230`, `01233`, `01234` are exactly described by eight pairwise disequalities on `T1`:

- the first four boundary positions form a color `K4`;
- `q256` must additionally differ from `q18` and `q54`.

Exact forced-equality classes for the five separator vertices were reconstructed identically with CaDiCaL195 and Glucose4. Seven of those eight disequalities are explained by an ordinary graph edge between the corresponding forced-equality classes.

Only one is not:

`q18 != q256`.

Thus almost the entire three-state SAT table is an ordinary edge relation after equality contraction; all remaining complexity is concentrated in one forced-disequality relation.

Evidence: `results/separator-left-q0-side-relation/`.

## 5. `q18!=q256` repeats the same degree-5 palette mechanism

The residual relation `q18!=q256` itself has a minimum five-vertex separator

`T2 = [q23,q35,q57,q86,q159]`.

Again one side is a singleton: `q256` has degree 5 in the `q0`-side bag and its neighborhood is exactly `T2`.

The `q18` side allows eight canonical boundary states:

`00121, 00123, 01121, 01123, 01212, 01213, 01231, 01234`.

The singleton `q256` side removes exactly the all-five-colors state `01234`. Seven states remain.

For every one of those seven states, exact independent enumerations by CaDiCaL195 and Glucose4 agree on the following palette statement:

- every color available to `q18` is already **used** on the five boundary vertices;
- the colors available to `q256` are exactly the colors **missing** from those five boundary vertices.

The two endpoint option sets are therefore disjoint, proving `q18!=q256`.

This is the second occurrence of the same recognizable mechanism: a degree-5 singleton takes a missing palette color while the opposite side constrains its endpoint to used palette colors.

Evidence: `results/separator-left-q18-q256-compression/`.

## 6. The remaining higher-order information is one forbidden partition

The eight `q18`-side states have five pairwise disequalities in common:

`q23!=q57`, `q23!=q86`, `q23!=q159`, `q57!=q86`, `q86!=q159`.

Those five pairwise conditions alone permit nine canonical states. The only extra state is

`01232`,

and that state is exactly the one rejected by the full `q18` side.

Equivalently, since `01232` means `q57=q159` while `q23,q35,q57,q86` use four distinct colors, the unique non-pairwise rule can be written as the palette-containment implication

> **if `q57=q159`, then `c(q35)` must belong to `{c(q23), c(q57), c(q86)}`.**

This is a useful richer observable: one conditional palette-membership rule replaces the final difference between the exact eight-state language and its pairwise approximation.

A direct induced-core explanation is still global. Fixing boundary state `01232` gives UNSAT in both CaDiCaL195 and Glucose4, while nearby state `01231` is SAT in both. The raw assumption core has 251 vertices; the best of four deletion orders gives an inclusion-minimal core of 236 vertices / 1263 edges. Thus the important compression is the **one forbidden state / one palette implication**, not a tiny hidden subgraph.

Evidence: `results/separator-left-q18-forbidden-state-core/`.

## 7. Current target

The most promising local target is now the palette-containment implication above. One possible short proof shape is:

1. assume `q57=q159` and `q23,q35,q57,q86` use four distinct colors;
2. find vertices constrained to avoid all four color classes, hence forced to the fifth color;
3. if two such forced-fifth-color vertices are adjacent, contradiction.

`tools/separator_left_q18_palette_witness.py` tests this both on the raw tracked vertices and after replacing each anchor by its exact forced-equality class.

If this local witness fails, the finite structure is still substantially clearer than before: the 202-state outer table has been reduced to three equalities, one of those equalities has been decomposed into two repeated degree-5 palette filters, and the remaining non-pairwise content is a single explicit forbidden partition.
