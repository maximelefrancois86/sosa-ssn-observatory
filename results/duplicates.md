# Probable duplicates of the candidate corpus

Equal normalised titles (four words or more), years one apart at most; computed by `scripts/dedupe.py`, clusters in `corpus/duplicates.csv`. A proposal: nothing is removed from the corpus before the reference harvest is frozen.

- Clusters: **22**, 45 records; records that would be linked to another: **23**; candidates after the merge: 2281 (of 2304)
- After the merge, by stratum: A 877, B 623, C 781
- Clusters whose merged stratum differs from that of the kept record: 0

## Clusters by the types of their records

| types | clusters |
|---|---|
| book-chapter + book-chapter | 7 |
| article + preprint | 4 |
| article + book-chapter | 2 |
| conference-paper + preprint | 2 |
| preprint + preprint | 2 |
| data-paper + preprint | 1 |
| conference-abstract + preprint | 1 |
| book-chapter + preprint | 1 |
| article + article | 1 |
| article + book-chapter + book-chapter | 1 |

