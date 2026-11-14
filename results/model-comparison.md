# The models against each other

Computed by `scripts/model_code.py compare` from the runs of `raw/`: each model of protocol/model.toml on the works it coded from the full text, against each stronger model on the works they share. Agreement between models, not accuracy: the readers' blind codes are the reference (pilotage review/105).

Models: sonnet (claude-sonnet-5-5, 1345 works), opus (claude-opus-5-5, 338 works).


## sonnet against opus (338 works)

- Engagement: kappa 0.82, agreement 86 %, within one level 95 %; use (E3-E5) or not: kappa 0.85; of the 168 works opus codes E3-E5, sonnet codes 8 E0 or E1

| question | works | agreement | kappa [95 % CI] | Jaccard |
|---|---|---|---|---|
| study_type | 338 | 100 % | 0.98 [0.94, 1.00] |  |
| engagement | 338 | 86 % | 0.82 [0.77, 0.87] |  |
| engagement_also | 338 |  |  | 0.78 |
| version_used | 145 | 84 % | 0.74 [0.64, 0.83] |  |
| modules | 145 |  |  | 0.80 |
| terms | 145 |  |  | 0.91 |
| extensions | 94 |  |  | 0.74 |
| result_pattern | 145 |  |  | 0.79 |
| value_properties | 145 |  |  | 0.67 |
| errors | 145 |  |  | 0.70 |
| domain | 205 | 94 % | 0.93 [0.89, 0.96] |  |
| artefacts | 145 |  |  | 0.92 |

Engagement: rows opus, columns sonnet.

| | E0 | E1 | E2 | E3 | E4 | E5 | unknown |
|---|---|---|---|---|---|---|---|
| E0 | 12 | 1 | 0 | 0 | 0 | 0 | 0 |
| E1 | 0 | 97 | 7 | 0 | 1 | 0 | 0 |
| E2 | 0 | 4 | 46 | 1 | 1 | 0 | 0 |
| E3 | 0 | 1 | 7 | 43 | 1 | 0 | 0 |
| E4 | 0 | 7 | 8 | 7 | 93 | 0 | 0 |
| E5 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
