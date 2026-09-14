# Commuting-square lifted-color checkpoint — 2026-09-14

Four copies of the exact 1,192-vertex / 7,008-edge closed order-3 ring are placed by two exactly commuting affine unit rotations. `T1` uses `r(1/3)=(-1+3*sqrt(-11))/10` and the established `(dst,src)=(0,911)` shift. `T2` uses `r(1/5)=(7+5*sqrt(-11))/18` about the same exact rotation center, so `T1*T2 = T2*T1` exactly.

Completed exact graph:

- vertices: **4,742**
- exact induced unit edges: **28,459**
- all unordered pairs checked exactly: **11,240,911**
- exact completion added **0** edges
- graph SHA-256: `dca9ae7bc33b535afb41bd2be8b1a0b7049eefbbe168ef9263a33826a146d385`

Structured coloring test:

- source: all **119** validated compressed proper 5-colorings of the completed A+B two-orbit control;
- C+D is the exact `T2` image of A+B;
- for each source coloring, all **120** global permutations of the five colors were tried on C+D;
- total assignments tested: **14,280**;
- each complete assignment was checked against all 28,459 exact edges;
- successful lifted proper coloring: **0**.

Classification boundary: `NO_LIFTED_WITNESS` is **not** an UNSAT proof. It only shows that this entire finite product-style witness family fails to color the commuting square. General 5-colorability remains unresolved until an unrestricted SAT/local-color result completes.

Actions run: `34825370811`, artifact `10340086919`.
