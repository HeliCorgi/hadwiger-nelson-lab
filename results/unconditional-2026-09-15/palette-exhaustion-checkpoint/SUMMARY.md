# Coupled palette-exhaustion checkpoint — 2026-09-15

This checkpoint records unconditional exact-geometry experiments built on the exact p1q7 commuting cube.  None of the results below is a Hadwiger–Nelson breakthrough: every completed construction listed here has a validated proper 5-coloring.

## Mechanism

For an added center `x`, its exact unit-neighborhood `N(x)` must omit the color assigned to `x`.  Thus an added center acts as an anti-rainbow constraint on `N(x)`.  Center-center unit edges couple the corresponding missing-color variables by inequality.  The combined construction can be viewed as a geometric missing-color/list-coloring system over the p1q7 base graph.

All candidate centers are exact K2 points.  Every center-to-base relation and every selected center-center pair is checked with exact `unit_modulus`.  The base p1q7 graph was already induced-complete.

## Initial palette CEGIS and six-center diagnosis

The first CEGIS run added six exact centers before its monolithic SAT step became slow.  Their base degrees were `26,16,15,14,16,15`.  The reconstructed six-center graph had:

- 9,375 vertices;
- 57,590 exact unit edges;
- no center-center unit edges;
- semantic `{pts,edges}` SHA-256 `316e56dc5d5be9a7b4f42a2408a5c818ebc0e41c08d86fc62086d5a641fbc0db`.

A validated proper 5-coloring was found by unrestricted seeded TabuCol, so this graph is `NOT_A`.  From the chosen near-coloring to the validated proper coloring, only 43 base vertices changed; the largest changed components had 22 and 16 vertices.  This established the first explicit local-repair escape mechanism.

## Coupled center geometry, top 160

The top-160 exact center library had:

- 160 center candidates;
- 61 center-center exact unit edges;
- maximum center degree 5;
- two center triangles;
- largest center-edge component: 16 centers / 17 edges.

Representative coupled layers were all 5-colorable:

| layer | centers | center edges | fixed-base exact optimum conflicts | unrestricted repair | result |
|---|---:|---:|---:|---:|---|
| largest component | 16 | 17 | 1 | 4 iterations | NOT_A |
| hybrid | 25 | 21 | 6 | 121,931 iterations | NOT_A |
| nonisolated | 87 | 61 | 7 | 6,802 iterations | NOT_A |
| all160 | 160 | 61 | 15 | 289,909 iterations | NOT_A |

The hybrid25 escape required recoloring 772 base vertices; its largest changed base component had 634 vertices.  The all160 escape recolored 977 base vertices; largest changed component 908.  Hence counterexample-guided coupling can turn a local repair into a large global recoloring, but this is not a chromatic obstruction.

## Counterexample-guided adaptive layers

`adaptive47` was formed from the hybrid25 layer plus exact centers that killed the validated hybrid25 escape coloring and their immediate center-edge partners.

- 47 centers / 29 center-center edges;
- exact fixed-base optimum 11 conflicts;
- unrestricted repair reached conflict 0 in 112,188 iterations;
- 1,211 base vertices changed; largest changed base component 1,121;
- semantic `{pts,edges}` SHA-256 `952b49687f6958da090cbd5116941e0fef062bb7a05c8ae36dec8781d26471dc`.

`adaptive95` repeated the construction in the top-400 center library using the validated adaptive47 escape coloring.

- 9,464 vertices / 58,416 exact unit edges;
- 95 centers / 56 center-center edges;
- 872 center-base incidences on 673 base vertices;
- exact fixed-base optimum 22 conflicts;
- unrestricted repair reached conflict 0 in 83,808 iterations;
- semantic `{pts,edges}` SHA-256 `4261b70d8fef82351f59b6bf2c12629251c3c4212b2f80057f47e68391a1354a`;
- result: `NOT_A`.

The adaptive95 escape coloring leaves 12 unused top-400 centers as exact rainbow killers.  Adding those 12 and their immediate center-edge partners yields a 119-center subset with 72 center-center edges.  This subset is diagnostically useful but is already known to be `NOT_A` as an A-search target because the full all400 supergraph below is 5-colorable.

## Top-400 coupled layer

The top-400 exact center library had:

- 400 center candidates;
- 400 center-center exact unit edges;
- maximum center degree 9;
- 29 center triangles;
- 308 center-center-base triangles;
- largest center component: 283 centers / 359 edges.

The 283-center largest component was `NOT_A`:

- 9,652 vertices / 60,339 exact edges;
- 359 center-center edges;
- 2,492 center-base incidences on 1,082 base vertices;
- fixed-base optimum 15 conflicts;
- unrestricted repair reached conflict 0 in 108,983 iterations.

The full all400 layer was also `NOT_A`:

- **9,769 vertices**;
- **61,404 exact unit edges**;
- 400 center-center edges;
- 3,516 center-base incidences on 1,449 base vertices;
- semantic `{pts,edges}` SHA-256 `29764f22d532dbe110630065455f979d936613a5e8bd66f98318e5e3ca18cc7a`;
- best fixed-base exact optimum: 24 conflicts;
- unrestricted repair reached conflict 0 at restart 0 / **774,067 iterations**;
- final coloring validated on all 61,404 edges.

In the validated all400 escape coloring, the 400 center neighborhoods use colors as follows:

- 212 centers see exactly four colors, so their missing-color list has size 1;
- 176 centers see three colors, list size 2;
- 12 centers see two colors, list size 3.

The 212 forced-list centers induce 91 center-center edges, and none of those 91 edges has the same forced missing color at both ends.  The base coloring has therefore reorganized itself so that the forced missing colors form a proper coloring of the tight-center subgraph.  From the fixed-base optimum seed to the validated all400 coloring, 935 base vertices changed; the largest changed base component had 807 vertices.

## Current mainline

Do **not** continue searching subsets of the same top-400 library for an A witness: all such graphs are subgraphs of the validated 5-colorable all400 graph.

The active nonredundant next step is to expand the exact center language beyond the old 400 candidates.  Workflow `hn-palette-center-geometry-1200` was launched with the validated adaptive95 and all400 escape projections included in the witness ranking.  A coordinate-based `tools/hn_palette_escape_frontier.py` was added so larger libraries can match old centers exactly and identify genuinely fresh rainbow killers and their center-center coupling without relying on unstable candidate indices.

The next construction should use fresh centers outside the old all400 point set, preferably selecting a small list-coloring/coupling obstruction rather than merely increasing center count.

## Evidence discipline

- A proper validated coloring is sufficient for `NOT_A`.
- A failed or slow repair is never evidence for A.
- Positive fixed-base MaxSAT optimum is only a seed-hardness diagnostic.
- Any future SAT UNSAT result must be independently confirmed before an A claim.
- Exact point/edge completion and semantic hashes must be retained for any selected construction.
