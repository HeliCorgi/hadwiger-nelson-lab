# q8/q9 large-side relation CNF

- separator: `[4, 5, 33, 62, 68, 78, 226]`
- exact large-side states: **12**
- common pairwise relations: **13**
- pairwise closure states: **21** (extras 9)
- valid width-2 clauses: **5**
- minimum width-2 clause cover: **4 clauses**
- number of minimum covers: **1**
- exact formula verified: **True**

Chosen residual clauses:
- `(q4!=q226) OR (q33!=q68)`
- `(q4!=q226) OR (q62!=q78)`
- `(q4!=q226) OR (q68!=q78)`
- `(q5=q33) OR (q78!=q226)`

Together with the 13 common pairwise disequalities, these four color-name-invariant clauses select exactly the 12 large-side states. Pairwise relations alone allow 21 states, so these clauses encode exactly the residual higher-order information. The minimum four-clause cover is unique among the enumerated valid width-2 clauses.

Workflow run: `34699746189`. Artifact id: `10299634171`. Artifact SHA-256: `4bfe925df0d7700e6fa0eb8a3245e1c6ae54817f10d9423abe3fec45c1711e27`.
