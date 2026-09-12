# Human-readable p-side compression

**Evidence level:** exact computational observation for the pinned quotient system; the boundary-state enumeration is exact, but the three equality implications below have not yet been reduced to purely local graph-theoretic proofs.

The six separator qnodes are ordered as

`[q0, q6, q8, q9, q10, q266]`.

The 261-qnode `p` component plus the six boundary nodes admits exactly two canonical boundary equality states:

- `012202`
- `012203`

The same exact scan also shows that the port `p=q5` is forced to the color of `q6` in both states. Equivalently, every proper 5-coloring of the 267-qnode left bag satisfies the three equalities

`p = q6`, `q0 = q10`, `q8 = q9`.

These three equalities give a much simpler explanation of the two-state table. Contract the tracked nodes into four classes

- `A = {p,q6}`
- `B = {q0,q10}`
- `C = {q8,q9}`
- `D = {q266}`.

Ordinary quotient edges already give every edge among `A,B,C,D` **except `C-D`**. In other words, the tracked relation graph after the three forced equalities is `K4` minus one edge.

Therefore a proper 5-coloring has only two color-symmetric possibilities on these four classes:

1. `C` and `D` use the same color; this is boundary state `012202`.
2. `D` uses a new fourth color; this is boundary state `012203`.

So the large p-side's collapse

`202 boundary partitions -> 2`

can be reformulated as a substantially smaller proof target:

> prove the three forced equalities `p=q6`, `q0=q10`, and `q8=q9` inside the left bag.

No further mysterious 202-state interaction is needed once those equalities are known; the remaining inequalities are ordinary graph edges and their consequences.

A minimum pairwise relation description on the six boundary vertices alone has size 7. One such basis is

- direct edges: `q0!=q6`, `q0!=q8`, `q0!=q266`;
- forced equalities: `q0=q10`, `q8=q9`;
- additional disequalities: `q6!=q8`, `q6!=q266`.

The last two disequalities become ordinary edge consequences after using `p=q6`, because `p` is adjacent to `q8` and `q266`. This is why including the port exposes the cleaner `K4-e` picture.

The simple common-neighborhood lemma is **not** enough for these three equalities: their common-neighborhood sizes inside the left bag are respectively 3, 2, and 1, and all three common-neighborhood graphs are 3-colorable. Thus the remaining proof compression must use a less local forcing mechanism.

Evidence:

- `results/separator-left-compression/analysis.json`
- `results/separator-left-compression/SUMMARY.md`
- `tools/separator_left_compression.py`
- workflow run `34694157711`

Scope warning: this is a conditional quotient-level observation under `C88`. It is not an unconditional unit-distance forcing gadget and does not change the Hadwiger-Nelson bound.
