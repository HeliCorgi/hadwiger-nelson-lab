# Independent support-4 verification

- Reconstruction: `INDEPENDENT-CUT-RECONSTRUCTION-OK`
- Full validated pairs: **7011**
- Unique cuts: **7008**
- Reconstructed cut SHA256: `a58cb579f1fa725107ef10a776b290c089a8ff0cfc12dc4d75fa1fe82ba5ccfa`
- Exhaustive verifier: **INDEPENDENT-EXHAUSTION-VERIFIED**
- Triples checked: **9810580** / **9810580**

The verifier enumerates each four-set uniquely as `a<b<c<d` via its first triple and intersects the legal fourth vertices over every cut not already hit inside the triple. It does not use the producing master root order, canonical-root pruning, monotone checkpoint, or pivot recursion.

**Finite conclusion:** the independently reconstructed final difference-cut library has no four-set hitting every cut. Combined with independent validation of every A/B fooling pair, this independently verifies the pinned system has no port-free equality semantic interface of support `<=4`.

This remains conditional on the pinned P2/C88 system and does not imply a new Hadwiger–Nelson bound.
