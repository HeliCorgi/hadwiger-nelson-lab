# Arithmetic barrier and strategy reset

Date: 2026-09-16. This is an application of Madore's published reduction method,
not a new Hadwiger-Nelson lower bound. The mathematical argument is not Lean formalized.

## Certified obstruction for the old A-search language

Let E = Q(sqrt(3),sqrt(5),sqrt(11)) and R0 = Z[1/30,sqrt(3),sqrt(5),sqrt(11)].
The Cartesian coordinates of every vertex in the audited all1200, wide494 Gen1,
and wide494 Gen2 files belong to R0. This is checked from the coordinates, not
inferred from the larger K2 container. The complex coordinates lie in
Q(sqrt(5),sqrt(-3),sqrt(-11)).

There is a ring homomorphism R0 -> F11 given by sqrt(3)->5, sqrt(5)->4,
sqrt(11)->0, 1/30->7. The three independent square classes give the usual
multiquadratic basis presentation, and these substitutions respect its relations.
It preserves the equation (dx)^2+(dy)^2=1. Madore's explicit five-color table
for the norm graph on F11^2 therefore pulls back to a proper five-coloring of
ALL unit edges in R0^2. The standalone verifier checks all 121 table vertices
and 726 table edges, membership, point distinctness, and every supplied exact
unit norm, without SAT, floating point, or the old hn_exact implementation.
Missing saved edges do not invalidate this ring-wide coloring argument.

The stronger full-field statement also holds: chi(Gamma(E^2)) <= 5.
The simple roots 5 of X^2-3 and 4 of X^2-5 modulo 11 lift to Q11.
Thus E embeds in Q11(sqrt(11)), whose residue field is F11. Since -1 is not a
square modulo 11, X^2+Y^2 is anisotropic over that residue field. If a unit
vector had negative minimum valuation, division by a minimum-valuation
coordinate and reduction would produce a nonzero isotropic vector, impossible.
Every unit vector is therefore integral. Translate each coset of the valuation
ring squared and reduce; pull back the finite color table on each coset.
This is Madore Proposition 3.2 / Corollary 3.4 applied to this field.
Division by 11 does NOT evade the field-wide obstruction. The direct verifier
rejects such denominators rather than pretending there is a field map to F11.

## Independently repeated local audits

| input | vertices | exact saved edges | coloring conflicts |
|---|---:|---:|---:|
| all1200 | 10569 | 68754 | 0 |
| Gen1 | 11473 | 75705 | 0 |
| Gen2 | 12102 | 80678 | 0 |

All three inputs use all 121 residue classes. The verifier is
`tools/hn_mod11_barrier.py`. Input provenance:

- all1200: run 34887160185, artifact 10365397197;
- Gen1: run 34895797863, artifact 10368468620;
- Gen2: run 34957362184, artifact 10391403066.

Gen2 semantic {pts,edges} SHA256:
`b46ea400f8b8fdd536916aa7b1dbc5eadc7658fa269186091a9fdb90e32f559f`.
Generated Gen2 coloring text SHA256, including newline:
`ce44cfc739f7038193d38a0bc7512290d51847fb263a1892ea51b06001110fbd`.

## Follow-up: target B is also excluded in E

The [no-forced-equal result](../../results/mod11-no-forced-equal-2026-09-16/README.md)
strengthens the old-field obstruction. For every distinct a,b in E^2, there is
an at-most-five-coloring c of Gamma(E^2) with c(a) != c(b). Different pairs may
use different colorings. Thus neither A nor B can be realized entirely in E.

Madore's table has no nonzero translation period: its color-0 class has size
23, whereas a nonzero translation has only orbits of size 11. Therefore table
translations separate any pair of different residue images. If the images
coincide, translate them to (0,0), whose color is 3 and whose neighbor colors
are exactly {0,1,4}; recolor just one actual vertex to 2. This separates the
pair without a conflict. The argument applies to every graph mapping to
Gamma(F11^2); the valuation-coset construction above supplies that map for E.

The standalone follow-up verifies all 726 finite-table edges and 875 Gen2
five-colorings on all 80,678 saved edges. Distinct vertex signatures certify
separation of all 73,223,151 pairs. Code, proof, compressed witnesses, hashes,
and reproduction instructions are retained in the linked result directory.
The ten tests and full audit were rerun locally before integration. The written
general proof is not Lean formalized or independently peer reviewed. No new
six-color construction, H_phi gadget, or mixed-field exclusion is claimed.

## Consequences and corrections

Do not launch Gen3/Gen4 in the same 494-direction language as an A or B search.
All p+d candidates remain in R0 and are simultaneously five-colorable; the
follow-up also excludes any forced-equal pair in that field. This does not
rule out every ambient K2 construction or every real UDG. Earlier statements
leaving B open in E are superseded by the follow-up, not by the original
five-color upper-bound argument alone.

Counts 358->258 and 310->214 compare different chosen colorings. They are NOT
survival probabilities or universal recurrence, and do not support progress
toward a six-chromatic graph. Frozen-boundary local UNSAT only forbids a repair
within that exact region with that exact outside assignment; it is not a lower
bound on all possible recoloring supports.

## Prioritized next gates

1. Reproduce and preserve this audit. Stop identical-field A/B growth.
2. Reconstruct Haugland's sevenfold 740/1066/2131-vertex graphs exactly. Verify
   actual field escape, known four-color port statements, and ordinary colorings.
   A known four-color relation must never be assumed valid for five colors.
3. Probe genuine five-color terminal relations, keeping UNKNOWN states allowed.
   Prefer certified reusable boundary relations over covering sampled colorings.
4. Independently reconstruct Parts's two-distance six-chromatic scaffold.
   A unit-distance terminal gadget enforcing inequality at distance phi would
   realize its non-unit constraints, but no such gadget is currently known here.
5. Only synthesize modules using actual rigid placements and exact unit edges.
   An abstract six-chromatic graph or a numerical near-unit realization is not A.

## Primary sources

- D. A. Madore, https://arxiv.org/abs/1509.07023,
  Proposition 3.2, Corollary 3.4, Lemma 4.5. Table checked against PDF p.12.
- J. K. Haugland, https://arxiv.org/html/2608.04542v2,
  Sections 2-3 and Appendix A (CC BY 4.0).
- J. Parts, https://arxiv.org/abs/2010.12656,
  two-distance construction; not an ordinary unit-distance A witness.
