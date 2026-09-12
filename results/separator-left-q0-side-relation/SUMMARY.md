# q0-side three-state relation

- q0-side states: `['01230', '01233', '01234']`
- minimum pairwise disequality basis size: **8**
- separator equality-class sizes: `{'14': 5, '18': 7, '54': 12, '55': 1, '256': 1}`
- all required disequalities explained by equality classes plus an ordinary edge: **False**

- `14 != 18`: direct=False; class-edge witnesses `[[14, 7], [14, 13], [80, 18], [80, 58], [80, 68], [92, 58]]`
- `14 != 54`: direct=True; class-edge witnesses `[[14, 5], [14, 54], [14, 210], [14, 222], [80, 5], [92, 6]]`
- `14 != 55`: direct=False; class-edge witnesses `[[80, 55], [92, 55]]`
- `18 != 54`: direct=False; class-edge witnesses `[[7, 5], [7, 6], [7, 65], [7, 189], [13, 5], [13, 33]]`
- `18 != 55`: direct=True; class-edge witnesses `[[7, 55], [18, 55]]`
- `18 != 256`: direct=False; class-edge witnesses `[]`
- `54 != 55`: direct=False; class-edge witnesses `[[86, 55], [189, 55]]`
- `54 != 256`: direct=False; class-edge witnesses `[[86, 256]]`
