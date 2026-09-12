# Exact CEGIS status

- Lab fooling pairs: **6139**
- Total sound fooling pairs/cuts before dedup: **7011**
- Checkpoint status: `RUNNING-AFTER-EXACT-MASTER-CUT`
- Exact-master state: `EXACT-MASTER-EXHAUSTED-REQUIRES-INDEPENDENT-VERIFY`
- State version: **2**
- Resume mode: `resume-same-library-v2`
- Unique cuts: **7008**
- Duplicate cuts: **3**
- Root rank: **23440 / 23440** (rank count only; not a runtime-completion percentage)
- Pivot source: `checkpoint:5191`
- Root-order SHA256: `f72cdbf49f6a06929ebae1efe58b795b466c1ef4bd5bfa2f923ee6b3029532a7`
- Cut-library SHA256: `a58cb579f1fa725107ef10a776b290c089a8ff0cfc12dc4d75fa1fe82ba5ccfa`
- Terminal event: **exact-master exhaustion (requires independent verification)**

Monotone-resume invariant: when the ordered unique-cut library is a verified prefix extension, completed roots remain impossible because added cuts only strengthen the hitting constraints. The candidate root itself is retried.
