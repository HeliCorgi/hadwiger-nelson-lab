# Mixed-field phi-rhombus follow-up

Date: 2026-09-16 JST.

This records the first bounded mixed-field follow-up after the strategy reset. It does **not** improve the Hadwiger–Nelson lower bound.

## Construction tested

Workflow `hn-phi-rhombus-interface` at source commit `adee862ff0aae8453e678c00b0adf8983d4c11e2` assembled two exact variants (`same` and `alternating`) from the sevenfold field-escape geometry and pentagonal/phi structure. The workflow then exhausted all fifteen set partitions of four boundary ports for the relevant long/short separator sides with both CaDiCaL195 and Glucose4, retaining positive witnesses and proof-checking negative states where applicable.

Actions run: **35009411746**.

## Joined result

For both assembly variants, the joined graph has:

- **8,520 vertices**;
- **50,584 exact unit-distance edges**;
- status `SAT_WITNESSES_JOINED`;
- classification for target A: **NOT_A**;
- classification as the desired phi-inequality gadget: **NOT_H_PHI**;
- specified pair B check: **NOT_FORCED_EQUAL**.

For each variant, all four locally admissible four-port boundary states have full proper five-color witnesses:

- `[0,1,0,1]`;
- `[0,1,0,2]`;
- `[0,1,2,1]`;
- `[0,1,2,3]`.

Every joined witness was validated on all parent edges. In particular, both phi-terminal relations are witnessed, so this bounded rhombus assembly does **not** force the terminal inequality required for `H_phi`.

Parent graph SHA-256 values recorded by the joined artifacts:

- `same`: `88faa1aeae757a6123b06480766060d1afdf61ce281e1233b6ae17f50d019a82`;
- `alternating`: `9dab94a474e9af4c11b08a3a96c95a8039add1edb2f3e9ac59fb0c6d3ad22727`.

Joined artifact: `phi-rhombus-joined-35009411746`, artifact ID **10412649395**.

## Interpretation

This closes only these two bounded rhombus assemblies. It does not rule out other mixed-field `H_phi` gadgets or stronger multiport relations.

The useful design lesson is that field escape plus exact phi accessibility is still insufficient by itself. The next candidate should be required to have genuine multi-contact/interior cross-coupling and should be screened by its **complete five-color boundary relation** before any large composition is attempted.

Do not interpret solver runtime, missing sampled states, or geometric size as forcing evidence.
