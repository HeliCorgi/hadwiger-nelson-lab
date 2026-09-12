# q0=q10 recursive interface compression

- separator: `[14, 18, 54, 55, 256]` (minimum cut 5)
- q0-side extendable states: **3**: `[('01230', [4]), ('01233', [4]), ('01234', [3, 4])]`
- q10-side extendable states: **26**
- intersection: **2** states: `['01230', '01233']`
- all intersection states force q0=q10: **True**
- q10 degree in left bag: **5**, neighborhood exactly separator: **True**
- separator induced edges: `[[14, 54], [18, 55]]`
- pairwise basis for the two globally viable separator states: **None**
- q0-side augmented states on `[q0]+separator`: `[[0, 1, 2, 3, 0, 4], [0, 1, 2, 3, 4, 0], [0, 1, 2, 3, 4, 1], [0, 1, 2, 3, 4, 4]]`
- pairwise basis for those q0-side augmented states: **None**
