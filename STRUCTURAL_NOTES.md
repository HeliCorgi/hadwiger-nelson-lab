# Structural notes — mathematically interesting observations

This file records structures that appear mathematically or geometrically interesting even when they are not, by themselves, new Hadwiger–Nelson bounds.

The goal is **human-readable compression**: whenever a computation reveals a rigid or repeated pattern, preserve a concise statement of what the pattern is, why it may matter, and what evidence supports it. Solver output alone is not considered an adequate explanation.

Evidence levels used below:

- **Verified finite statement** — exact exhaustive computation and independently rechecked when stated.
- **Exact computational observation** — exact for the stated finite system, but not necessarily independently reimplemented.
- **Empirical pattern** — observed in a sampled family of colorings/search trajectories.
- **Conjectural interpretation** — a proposed explanation or possible geometric significance.

All observations here are conditional on the finite P2 system inherited from upstream commit `d1e80998bda337d9fa721f2e96d203ae54e97fc8` unless explicitly stated otherwise. They do not by themselves produce an unconditional unit-distance 6-chromatic graph.

## 1. Six vertices carry the conditional P2 forcing across a global cut

**Evidence level: Verified finite statement.**

Let `Q = H*/C88`, with quotient ports `p` and `q` containing original vertices 217 and 490. A minimum `p`-`q` vertex separator is

`S = {0, 6, 8, 9, 10, 266}`.

Deleting `S` separates `Q` into a 261-vertex `p` side and a 38-vertex `q` side.

The six boundary vertices have 202 canonical equality partitions using at most five colors. Solving the two sides independently gives:

- `p` side: only `012202` and `012203` extend;
- `q` side: 81 states extend;
- intersection: exactly `012203`.

In the unique common state, both side solvers force their respective port to the same singleton boundary color. Thus the entire 305-vertex conditional forcing relation factors through a six-vertex color-symmetric interface.

Why this is interesting: the original forcing statement is global and the direct common neighborhood of the two ports is empty, yet a minimum separator of size six compresses the compatibility information to one equality-partition state. This is much closer to a graph-theoretic explanation than a raw SAT contradiction.

Evidence:

- `results/separator-interface/analysis.json`
- `results/separator-verify/analysis.json`
- `tools/separator_interface.py`
- independent Glucose4 verification workflow

## 2. The large side is dramatically more rigid than the small side

**Evidence level: Verified finite statement.**

The 261-vertex `p` side of the separator accepts only two of 202 boundary states, while the 38-vertex `q` side accepts 81.

So the asymmetry is not merely in component size; the large side acts almost like a boundary-state filter:

`202 possible states -> 2 states`.

The final global compatibility then removes one of those two.

Why this is interesting: this suggests that a human-readable proof may be obtainable by understanding why the large side enforces the small relation distinguishing `012202` from all but `012203`, rather than by analyzing all 305 quotient vertices simultaneously.

A promising structural subproblem is therefore:

> explain, with a small collection of graph-theoretic lemmas, why the `p` side permits only `012202` and `012203`.

This could be more informative than further shrinking a generic SAT core.

## 3. Twenty quotient classes are globally forced to the port color

**Evidence level: Exact computational observation.**

With the port class `p` fixed to one color, exact SAT scans over all 305 quotient nodes found:

- 20 qnodes forced equal to `p`;
- 155 forced different from `p`;
- 130 flexible relative to `p`.

The forced-equal set includes both target-side port classes containing original vertices 489 and 490, as well as qnode 267 (`{378,403,502}`), which also appears prominently in the Kempe-path data below.

Why this is interesting: the forcing relation is not isolated to the target pair. There is a larger same-color backbone distributed through the quotient. Understanding that backbone may expose a reusable forcing mechanism or a smaller description of the color constraints.

Evidence: `results/port-relation-scan/analysis.json`.

## 4. A clean local K4 forcing lemma exists inside the global structure

**Evidence level: Verified graph-theoretic lemma on the checked quotient.**

General rule in any proper 5-coloring:

> If the common-neighborhood graph of vertices `u,v` is not 3-colorable, then `u` and `v` must have the same color.

Reason: if `u` and `v` had distinct colors, every common neighbor would be restricted to the other three colors.

In `Q`, the port class `p` and qnode 22 (original component `{36}`) have exactly four common neighbors, and those four form a `K4`. Hence `p` and qnode 22 are forced equal by a short local argument.

The four witness qnodes are

`{0, 4, 8, 21}`.

This local rule does **not** chain all the way from `p` to `q`; among the 20 globally forced-equal classes, this was the only pair found by this particular common-neighborhood criterion.

Why this is interesting: it is a rare genuinely local human-readable forcing mechanism embedded in an otherwise global obstruction. It may be useful as a building block in a larger proof decomposition.

Evidence: `results/local-equality-chain/analysis.json`.

## 5. Kempe connectivity repeatedly uses the same four path skeletons

**Evidence level: Empirical pattern over 300 sampled color partitions.**

For a critical edge `pq` in a 6-critical graph, every 5-coloring of `Q = G-pq` must connect `p` and `q` in each relevant two-color Kempe subgraph; otherwise a Kempe swap would separate their colors.

Across 300 sampled color partitions, 1200 required Kempe channels were checked. The shortest paths always fell into the same four qnode skeletons, with lengths 4, 8, 4, and 6:

1. `5-266-274-268-270`
2. `5-4-33-92-6-271-267-289-270`
3. `5-0-267-295-270`
4. `5-8-267-272-274-277-270`

qnode 267 occurred in 75% of sampled shortest channels; qnode 274 occurred in 50%.

Why this is interesting: a 305-vertex critical graph could in principle realize the mandatory Kempe connections in many unrelated ways. Repeated use of the same small collection of route skeletons suggests a narrower structural backbone.

Caution: this is not yet a theorem. The sample demonstrates stability over the enumerated color partitions, not exhaustion of all 5-colorings.

Evidence: `results/kempe-probe/analysis.json`.

## 6. Proof-guided supports repeatedly come within one partition state of separation

**Evidence level: Exact computation on a non-exhaustive proof-guided sample.**

The DRUP proof was mined for candidate supports of sizes 4, 5, and 6. For 180 supports at each size, A and B were projected exactly to canonical equality partitions.

No sampled support was a separator, but the minimum overlap at every size was exactly one state.

One size-4 example is original vertices

`{27, 74, 96, 272}`,

for which A has only state `0123`, while B has two states including the same `0123`. So this support misses separation by one surviving common state.

Why this is interesting: independently of the six-vertex quotient separator, the proof itself repeatedly points toward small supports with near-disjoint color-symmetric projections. This may indicate that the forcing relation has several low-complexity descriptions that are obscured by one residual state.

Caution: these 540 supports were sampled from proof-guided candidates; this is not an exhaustive support-5 or support-6 theorem.

Evidence: `results/proof-interpolant-deep/DEEP_SUMMARY.json`.

## 7. The added-edge quotient obstruction is globally critical, not a tiny hidden bad core

**Evidence level: Exact computational observation.**

For `G = Q + pq`:

- `G` is not 5-colorable;
- every one-vertex deletion is 5-colorable;
- there is no articulation point;
- there is no 2-vertex cut;
- `p`-`q` vertex connectivity in `Q` is 6.

Why this is interesting: a short explanation cannot simply be “there is a much smaller non-5-colorable subgraph hiding inside.” The obstruction is vertex-global at the quotient level. This helps explain why proof-core trimming remains large and why separator/interface descriptions are more promising than ordinary subgraph minimization.

Evidence: `results/quotient-critical/analysis.json`.

## What to look for next

When future computations produce new data, actively check for human-readable structure in at least these directions:

- can a large SAT implication be factored through a small separator or boundary state table?
- do many forced-equal vertices admit a small family of local forcing rules?
- do Kempe paths, shortest paths, or cutsets repeatedly reuse the same vertices?
- do coordinates reveal exact rotations/reflections, lattice cosets, repeated distances, or recognizable unit-distance motifs?
- is a candidate only one state, one edge, or one equality away from becoming an unconditional forcing gadget?
- can an empirical pattern be upgraded to an exhaustive finite lemma with a small checker?

The preferred end product is not merely `UNSAT`, but a statement a human can explain without replaying the full search.
