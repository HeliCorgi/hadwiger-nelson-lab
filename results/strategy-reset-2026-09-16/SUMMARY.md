# Ordered strategy reset: completed results

Date: 2026-09-16 JST. **No new HN lower bound, ordinary unit-distance
6-chromatic witness, or five-color phi-inequality gadget was found.**
This checkpoint distinguishes mathematical obstructions, complete finite tests,
known-result reproduction, and unfinished jobs.

## 1. Old arithmetic lane: closed for A by an upper-bound argument

The independent mod-11 verifier ran successfully locally and in Actions on:

| graph | vertices | exact saved edges | generated coloring conflicts |
|---|---:|---:|---:|
| all1200 | 10,569 | 68,754 | 0 |
| wide494 Gen1 | 11,473 | 75,705 | 0 |
| wide494 Gen2 | 12,102 | 80,678 | 0 |

Every point was checked to belong to Z[1/30,sqrt3,sqrt5,sqrt11]. The finite
121-point/726-edge norm-graph five-color table was verified exhaustively.
The ring map preserves every true unit pair, including unsaved ones. The
valuation argument extends the five-color upper bound to the entire real field
Q(sqrt3,sqrt5,sqrt11). Thus the old same-field p+d generator cannot produce A,
regardless of the number of further generations. This argument does not decide B.

Proof, scope, attribution and reproduction: see
`research/strategy-reset-2026-09-16/ARITHMETIC_BARRIER.md` and
`tools/hn_mod11_barrier.py`. Geometry/audit Actions run: **35003232409**.

## 2. Sevenfold alternative: exact geometry reproduced outside the old field

Haugland arXiv:2608.04542v2 was reconstructed from its attributed 231 path rows.

| graph | vertices | all-pairs induced unit edges | unordered pairs covered |
|---|---:|---:|---:|
| H21 | 21 | 42 | 210 |
| G1 | 740 | 3,985 | 273,430 |
| G2 | 1,066 | 6,264 | 567,645 |
| G3 | 2,131 | 12,530 | 2,269,515 |

The arithmetic is exact in Q(zeta42,sqrt5). Every pair is covered by sound
necessary modular norm filters followed by exact arithmetic for survivors;
no floating-point cutoff is used. The local and Actions point/edge sets agree.
G1 actually contains zeta42. Its real coordinate cos(pi/21) has irreducible
degree 6, which does not divide the old field degree 8: this is actual field
escape, not merely use of a larger coordinate container.

This reproduces known geometry. A separate bounded four-color calibration is
running; its full set of four-color assertions is NOT claimed reproduced here.
Positive five-color witnesses for G1/G2/G3 are already independently validated.

## 3. Five-color interface test: complete, but no useful extra relation

Run **35003816730** completed. Unlike sample-based color families, this test
covers every terminal partition modulo global color permutations.

| graph | selected terminals | partitions | local-edge exclusions | SAT extensions | nonlocal exclusions | UNKNOWN |
|---|---:|---:|---:|---:|---:|---:|
| G1 | 2 | 2 | 0 | 2 | 0 | 0 |
| G2 | 5 | 52 | 47 | 5 | 0 | 0 |
| G3 | 6 | 202 | 183 | 19 | 0 | 0 |

All 26 saved SAT models were revalidated locally against every exact edge and
the specified terminal partition. Therefore each selected interface is EXACTLY
the relation imposed by its own terminal edges. There is no hidden additional
five-color restriction from the interior. G1 permits both equality and inequality
at its pair; G2 permits inequality at the pair used for four-color equality.

Consequently, splicing these unchanged modules only at these interfaces, with
disjoint interiors and no additional interior cross edges, cannot add new
five-color restrictions to a five-colorable terminal skeleton. This is a scoped
extension lemma, not a statement about all interfaces or all sevenfold graphs.
Do not scale up that already-refuted terminal-only mechanism.

## 4. Six-color scaffold: built and certified, but TWO-distance

Parts arXiv:2010.12656v2 G16 and G31 were reconstructed with exact real algebraic
coordinates. Run **35003956571** completed.

- G16: 16 vertices, 28 unit edges and 28 phi edges. Exhaustive enumeration under
  a sound K5 color normalization yields 12 canonical five-colorings; all force
  its two designated terminals equal.
- G31: two isometric G16 copies sharing their origin, plus a unit edge between
  their other terminals. The complete two-distance graph has 31 vertices,
  **57 unit edges + 56 phi edges = 113 edges**.
- Exhaustive five-color search has zero solutions (26,502 recursive nodes).
- Glucose4 five-color UNSAT proof verified by pinned drat-trim.
- A six-color witness is validated, so the TWO-distance graph has chromatic
  number exactly 6.
- Remove the 56 phi edges: the remaining unit graph is exactly three-chromatic,
  certified by a proper three-coloring and an odd five-cycle.

The G16 terminal-inequality UNSAT proof from Glucose4 also passed drat-trim.
CaDiCaL returned UNSAT on both negative tests, but its exported proofs failed
checking with `no conflict`; the exports lack a final empty clause. The cause is
not established and these failed proofs are NOT used as certificates. The
conclusion rests on the independently verified Glucose proofs, exhaustive small
graph enumeration, and checked positive colorings. A successful workflow is not
by itself a mathematical result.

G31 semantic SHA256:
`047da2a6c8b8d3d25cfb65b632c7bcd6be448e03edb4174a8d48a76b25ec35e2`.

## 5. Next synthesis gate, now sharply specified

The missing component is H_phi: a genuine unit-distance gadget at terminal
distance phi=(1+sqrt5)/2 that is five-colorable but forbids equal terminal colors
in every five-coloring. It would realize the scaffold's long-edge constraints.
No such gadget is assumed or currently available.

An additional elementary obstruction is now recorded: even H_phi cannot lie
entirely in the old real field. Phi reduces to 8, and translating the finite
color table by (1,2) gives both terminals color 1 because T[1][2]=T[9][2]=1.

A target-accessible candidate language is Q(zeta210), combining zeta42 with
pentagonal directions zeta10. The identity zeta10+conj(zeta10)=phi supplies an
exact two-unit-edge path to the target. Its algebraic identities were checked
locally, but a path alone does NOT force terminal inequality. There is no newly
built mixed-field forcing graph or asserted absence of other arithmetic barriers.

See `research/strategy-reset-2026-09-16/PHI_TARGET_AND_INTERFACE_GATES.md` for
proofs, limitations, and what counts as an acceptable next experiment.

## Reproduction and durable data

Generators and the attributed path input are in main. Compact quantitative
results, semantic hashes, proof hashes, and artifact IDs are in `SUMMARY.json`.
The 90-day Actions artifacts retain exact graph files, DIMACS instances,
colorings, proofs, and checker logs:

- geometry/audits: run 35003232409, artifact 10410248491;
- terminal G1/G2/G3: run 35003816730, artifacts 10410428673 / 10410583251 / 10411010758;
- two-distance scaffold: run 35003956571, artifact 10410023793.

At this checkpoint the remaining active computation is the bounded Haugland
four-color calibration in run 35003232409 (two solver jobs; each case has a
600-second limit). Its unresolved results do not affect the already complete
five-color interface census or the verified two-distance scaffold.
