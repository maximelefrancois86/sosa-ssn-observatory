# Coding by the language model

Recommendations of claude-opus-5-5, then claude-sonnet-5-5 (the strongest that coded each work; protocol/model.toml, prompt protocol/model-prompt.md), runs 2026-11-13T1830, 2026-11-13T1837, 2026-11-13T1857, 2026-11-13T1907, 2026-11-13T1916, 2026-11-14T1241, 2026-11-14T1356, 2026-11-13T1830b, 2026-11-13T1837b; computed by `scripts/model_code.py ingest`. **Recommendations, not results**: a reader decides (protocol § 5, pilotage review/105).

- Works coded: 1493; failed requests: {'refusal': 1}; texts that are not the work (`no` or `unsure`): 9
- Values outside the codebook, dropped: {'extensions.how: value outside the codebook': 7, 'question missing': 1, 'domain: value outside the codebook': 1}
- Quotations found verbatim in the body (whitespace, case and hyphenation aside): 10516 of 10674 (98.5 %)
- Tokens: 35,232,533 input, 19,508,055 read from the cache, 59,295 written to it, 2,138,071 output; cost at the prices of protocol/model.toml: 56.99 dollars

## Engagement recommended, by stratum

| stratum | E0 | E1 | E2 | E3 | E4 | E5 | unknown |
|---|---|---|---|---|---|---|---|
| A | 136 | 192 | 129 | 121 | 240 | 4 | 0 |
| B | 146 | 193 | 88 | 40 | 83 | 1 | 0 |
| D | 22 | 12 | 10 | 37 | 39 | 0 | 0 |

## Against the script's rules

Rows: the script's recommendation; columns: the model's. The script's E0 means no occurrence of SOSA/SSN in the body; E1, named only in background sections.

| script | E0 | E1 | E2 | E3 | E4 | E5 | unknown |
|---|---|---|---|---|---|---|---|
| E0 | 126 | 7 | 0 | 1 | 1 | 0 | 0 |
| E1 | 1 | 34 | 6 | 0 | 2 | 0 | 0 |

## Texts the model does not take for the work

To check (wrong PDF, front matter, proceedings):

- `openalex:W2945277624` (unsure): Applying Evaluation Criteria to Ontology Modules.
- `openalex:W3162839248` (unsure): End-User Development in the Internet of Things
- `openalex:W4206701980` (no): Russian Supercomputing Days: Proceedings of the International Conference. September 21–22, 2020
- `openalex:W4212764240` (no): State-of-the-Art Sensors Technology in Spain 2017
- `openalex:W4226148669` (unsure): Process Mining Workshops
- `openalex:W4254403118` (no): Communication Papers of the 2019 Federated Conference on Computer Science and Information Systems
- `openalex:W4383499536` (no): Short Papers of the 11th Conference on Cloud Computing Conference, Big Data & Emerging Topics (JCC-BD&ET 2023)
- `openalex:W4396874574` (unsure): 
- `s2orc:208086021` (unsure): Manual of Digital Earth
