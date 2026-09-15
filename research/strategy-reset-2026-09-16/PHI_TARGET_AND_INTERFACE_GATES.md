# Gates for the next synthesis attempt

Date: 2026-09-16. No new HN lower bound is claimed.

## 1. Exact interface-extension obstruction, not sampled flexibility

For the reconstructed Haugland graphs, a complete five-color partition census
was performed on the following actual terminals. Color names are factored out
by global permutations; all nonlocal accepted states have a full validated model.

| graph | terminals | partitions | excluded by terminal edges | SAT extensions | other exclusions | UNKNOWN |
|---|---|---:|---:|---:|---:|---:|
| G1 | A,B | 2 | 0 | 2 | 0 | 0 |
| G2 | left,middle,right,upper_left,upper_right | 52 | 47 | 5 | 0 | 0 |
| G3 | previous five plus rotated_right | 202 | 183 | 19 | 0 | 0 |

Each tested interface is therefore exactly the proper-coloring relation of its
own induced terminal graph. It imposes NO extra five-color restriction through
its interior. This includes equality and inequality both being possible at the
G1 pair, and inequality being possible at the G2 pair that the paper constrains
in four colors. The four-color statements must not be imported into five colors.

Extension lemma: take any number of copies of such modules. Suppose their
interiors are mutually disjoint, intersections are only at declared terminals,
and there are no additional edges incident to module interiors. Any proper
five-coloring of the combined terminal skeleton extends to each module
independently, and hence to the union. Proof: the restricted terminal assignment
belongs to the fully enumerated relation; choose its saved extension and rename
colors globally within that module. Interior disjointness and the absence of
extra cross edges make these choices compatible.

Scope is essential. This does not exclude different terminal selections,
interior identifications, geometric cross edges, or mixed-field replacements.
The skeleton itself might already be non-five-colorable; the lemma says that
these modules do not add any further restriction to that skeleton.

Evidence: Actions 35003816730, all 26 retained models independently revalidated
locally against the exact reconstructed graphs. Do not rerun this exact census
unchanged, or try to obtain new five-color forcing by terminal-only splicing of
these particular interfaces.

## 2. The precise missing component for the two-distance scaffold

The Parts G31 scaffold has 57 unit edges and 56 edges of length phi=(1+sqrt5)/2.
It is six-chromatic as a TWO-distance graph. Its unit-edge-only subgraph is
three-chromatic (an explicit 3-coloring and an odd 5-cycle were verified).
The 56 long edges are real missing constraints, not numerical tolerances.

Target: a finite unit-distance graph H_phi with distinct actual terminals a,b,
|a-b|=phi, a proper five-coloring, and an independently certified UNSAT result
for five colors with a=b in color. Replacing all 56 phi edges by isometric
copies then forces every scaffold edge to be bichromatic in any hypothetical
five-coloring, contradicting the verified scaffold. Extra geometric edges only
strengthen this contradiction. Coincident vertices must be handled explicitly;
no loop or false unit edge may be silently introduced.

Such a gadget has NOT been found here. It is a research target, not an assumed
construction. A two-edge unit path between the terminals does not enforce this
relation.

## 3. H_phi cannot be realized entirely in the OLD real coordinate field

This is a direct corollary of the mod-11 coloring, with explicit counterexample
colors, stronger for this target than merely saying that E is five-colorable.
Let E=Q(sqrt3,sqrt5,sqrt11). Normalize terminals to (0,0) and (phi,0).
An E-valued pair at that distance can be so normalized by an E-valued rigid
motion: divide the displacement components by phi to obtain its unit rotation.

Under the established residue map, phi maps to 8 in F11. Let T be the finite
five-color table in tools/hn_mod11_barrier.py. It has

    T[1][2] = T[9][2] = 1.

Translate the table by (1,2): C(x,y)=T[(red(x)+1) mod 11][(red(y)+2) mod 11].
This is a proper unit-distance five-coloring and assigns BOTH terminals color 1.
For the full field rather than just integral coordinates, use the valuation
coset construction from ARITHMETIC_BARRIER.md, choosing the integral coset's
representative as zero. The two normalized terminals belong to that coset.
Therefore no E-contained H_phi can force terminal inequality. This argument
concerns a forced-DIFFERENT phi gadget, not the repository's arbitrary-distance
forced-EQUAL target B.

The table identity was evaluated directly; it is not a solver observation.

## 4. A constructive target-accessibility gate for a new direction language

Use the standard complex root z=zeta210 and its conjugate z^-1. Then

    zeta42 = z^5,
    zeta10 = z^21,
    phi = z^21 + z^189,
    sqrt5 = 2*phi - 1.

Thus the Haugland arithmetic Q(zeta42,sqrt5) embeds into Q(zeta210), and the
pentagonal directions provide a genuine unit path

    0 -> zeta10 -> phi.

Both displacements have exact norm 1. Phi210 has degree 48. This is complex
coordinate arithmetic; one must not confuse it with the real Cartesian field.

The identities phi^2=phi+1, (2*phi-1)^2=5, Phi42(z^5)=0, and the embedded
Haugland u1 norm were checked locally by exact SymPy 1.14.0 polynomial remainders
modulo Phi210. They establish representability of the desired terminal distance,
NOT any color forcing and NOT the absence of other arithmetic upper bounds.

A separate all-pairs exact local census found zero phi-distance pairs in the
current finite G3 (all 2,269,515 pairs covered by necessary modular filters plus
exact norms). That is a property of this G3 point set only. It is not a field-wide
impossibility statement.

Next experiments should first check field/terminal accessibility, then construct
small genuinely cross-coupled modules in this mixed language, and evaluate the
specific terminal relation. Do not proceed just because a heuristic struggles,
a sampled coloring is killed, or the coordinate degree has increased.

## Sources and attribution

Haugland: https://arxiv.org/html/2608.04542v2 (known graph construction).
Parts: https://arxiv.org/abs/2010.12656v2 (known two-distance scaffold).
Madore: https://arxiv.org/abs/1509.07023 (finite-field coloring and valuation method).
The extension lemma and the translated-table phi obstruction above are elementary
derivations for the present research program, not claims of literature novelty.
