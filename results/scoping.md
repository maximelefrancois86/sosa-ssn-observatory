# Scoping figures of the candidate corpus

Harvest `2026-11-07T1337` (OpenAlex, forward citations of the seeds in `protocol/seeds.toml`). No screening yet: these are **candidates**, not included studies.

- Distinct candidate works: **2304**
- By seed group: lineage only 1418 (61.5 %), 2017+ only 672 (29.2 %), lineage and 2017+ 214 (9.3 %)
- With an abstract in OpenAlex: 1716 (74.5 %)
- With a DOI: 2190 (95.1 %)
- Retracted: 1
- Naming SOSA or SSN in the title: 20 (0.9 %); in the title or abstract: 137 (5.9 %)
- Likely secondary studies (survey, review, state of the art, systematic, mapping study, bibliometric in the title): 114 (4.9 %)
- Records sharing a normalised title with another record (likely versions of one work): 40

## Strata (review/101; stratum D, found by full-text search, is not harvested yet)

| stratum | works | diamond | gold | hybrid | green | bronze | closed | unknown | open access |
|---|---|---|---|---|---|---|---|---|---|
| A: cites a 2017+ seed | 886 | 57 | 177 | 140 | 191 | 34 | 287 | 0 | 67.6 % |
| B: lineage seeds only, 2018+ | 626 | 39 | 113 | 63 | 106 | 20 | 285 | 0 | 54.5 % |
| C: lineage seeds only, before 2018 | 792 | 20 | 79 | 22 | 183 | 39 | 449 | 0 | 43.3 % |

## Per seed

| seed | role | citing works | citing this seed only |
|---|---|---|---|
| ssn-xg-report-2011 | lineage | 142 | 81 |
| sso-2010 | lineage | 131 | 60 |
| compton-2012 | lineage | 1447 | 1143 |
| cox-2017-oosf | lineage | 45 | 23 |
| w3c-rec-2017 | core | 147 | 95 |
| w3c-rec-2017-hal | variant | 0 | 0 |
| janowicz-2019 | core | 550 | 321 |
| janowicz-2018-ssrn | variant | 37 | 14 |
| haller-2019 | core | 282 | 148 |
| taylor-2019-revamped | core | 10 | 4 |

## By year and seed group

| year | lineage only | lineage and 2017+ | 2017+ only | total |
|---|---|---|---|---|
| 2011 | 16 | 0 | 0 | 16 |
| 2012 | 56 | 0 | 0 | 56 |
| 2013 | 77 | 2 | 0 | 79 |
| 2014 | 122 | 1 | 1 | 124 |
| 2015 | 160 | 0 | 2 | 162 |
| 2016 | 180 | 1 | 4 | 185 |
| 2017 | 181 | 3 | 5 | 189 |
| 2018 | 150 | 7 | 23 | 180 |
| 2019 | 100 | 23 | 45 | 168 |
| 2020 | 79 | 32 | 65 | 176 |
| 2021 | 79 | 32 | 92 | 203 |
| 2022 | 53 | 27 | 82 | 162 |
| 2023 | 48 | 24 | 84 | 156 |
| 2024 | 44 | 26 | 95 | 165 |
| 2025 | 46 | 21 | 82 | 149 |
| 2026 | 27 | 15 | 90 | 132 |

## By OpenAlex type

| type | works | share |
|---|---|---|
| article | 1050 | 45.6 % |
| conference-paper | 887 | 38.5 % |
| book-chapter | 151 | 6.6 % |
| dissertation | 104 | 4.5 % |
| preprint | 49 | 2.1 % |
| review | 25 | 1.1 % |
| book | 14 | 0.6 % |
| other | 6 | 0.3 % |
| data-paper | 5 | 0.2 % |
| conference-abstract | 3 | 0.1 % |
| reference-entry | 3 | 0.1 % |
| editorial | 2 | 0.1 % |

## By language

| language | works | share |
|---|---|---|
| en | 2205 | 95.7 % |
| fr | 63 | 2.7 % |
| de | 11 | 0.5 % |
| es | 8 | 0.3 % |
| pt | 6 | 0.3 % |
| ru | 3 | 0.1 % |
| uk | 2 | 0.1 % |
| ng | 2 | 0.1 % |

## By OpenAlex domain (primary topic)

| domain | works | share |
|---|---|---|
| Physical Sciences | 2060 | 89.4 % |
| Social Sciences | 151 | 6.6 % |
| Health Sciences | 49 | 2.1 % |
| Life Sciences | 43 | 1.9 % |
| (none) | 1 | 0.0 % |

## By OpenAlex field (primary topic)

| field | works | share |
|---|---|---|
| Computer Science | 1642 | 71.3 % |
| Engineering | 335 | 14.5 % |
| Social Sciences | 92 | 4.0 % |
| Environmental Science | 62 | 2.7 % |
| Agricultural and Biological Sciences | 38 | 1.6 % |
| Health Professions | 33 | 1.4 % |
| Business, Management and Accounting | 33 | 1.4 % |
| Medicine | 16 | 0.7 % |
| Decision Sciences | 11 | 0.5 % |
| Arts and Humanities | 10 | 0.4 % |
| Mathematics | 5 | 0.2 % |
| Neuroscience | 5 | 0.2 % |
| Earth and Planetary Sciences | 5 | 0.2 % |
| Psychology | 4 | 0.2 % |
| Chemistry | 3 | 0.1 % |

## By OpenAlex subfield (primary topic)

| subfield | works | share |
|---|---|---|
| Artificial Intelligence | 1064 | 46.2 % |
| Information Systems | 216 | 9.4 % |
| Computer Networks and Communications | 201 | 8.7 % |
| Computer Vision and Pattern Recognition | 101 | 4.4 % |
| Industrial and Manufacturing Engineering | 101 | 4.4 % |
| Building and Construction | 77 | 3.3 % |
| Electrical and Electronic Engineering | 66 | 2.9 % |
| Control and Systems Engineering | 55 | 2.4 % |
| Urban Studies | 37 | 1.6 % |
| Management, Monitoring, Policy and Law | 36 | 1.6 % |
| Health Information Management | 32 | 1.4 % |
| Software | 30 | 1.3 % |
| Plant Science | 29 | 1.3 % |
| Geography, Planning and Development | 26 | 1.1 % |
| Management Information Systems | 25 | 1.1 % |
| Sociology and Political Science | 13 | 0.6 % |
| Environmental Engineering | 12 | 0.5 % |
| Civil and Structural Engineering | 12 | 0.5 % |
| Computer Science Applications | 11 | 0.5 % |
| Information Systems and Management | 9 | 0.4 % |

## Top venues

| venue | works | share |
|---|---|---|
| Lecture notes in computer science | 157 | 6.8 % |
| (none) | 86 | 3.7 % |
| Sensors | 74 | 3.2 % |
| theses.fr (ABES) | 54 | 2.3 % |
| Springer eBooks | 37 | 1.6 % |
| Semantic Web | 35 | 1.5 % |
| Communications in computer and information science | 33 | 1.4 % |
| Procedia Computer Science | 28 | 1.2 % |
| IEEE Access | 26 | 1.1 % |
| IEEE Internet of Things Journal | 24 | 1.0 % |
| Future Generation Computer Systems | 23 | 1.0 % |
| arXiv (Cornell University) | 21 | 0.9 % |
| Journal of Web Semantics | 20 | 0.9 % |
| Advances in intelligent systems and computing | 19 | 0.8 % |
| Journal of Ambient Intelligence and Humanized Computing | 19 | 0.8 % |
| IEEE World Forum on Internet of Things (WF-IoT) | 16 | 0.7 % |
| Automation in Construction | 16 | 0.7 % |
| Elsevier eBooks | 16 | 0.7 % |
| Applied Sciences | 16 | 0.7 % |
| International Journal of Distributed Sensor Networks | 15 | 0.7 % |
| IFIP advances in information and communication technology | 15 | 0.7 % |
| Sensors and Materials | 15 | 0.7 % |
| Internet of Things | 15 | 0.7 % |
| SSRN Electronic Journal | 14 | 0.6 % |
| IEEE International Conference on Emerging Technologies and Factory Automation (ETFA) | 14 | 0.6 % |

## Top publishers (host organisation)

| publisher | works | share |
|---|---|---|
| (none) | 683 | 29.6 % |
| Elsevier BV | 305 | 13.2 % |
| Springer Science+Business Media | 304 | 13.2 % |
| Multidisciplinary Digital Publishing Institute | 179 | 7.8 % |
| Institute of Electrical and Electronics Engineers | 142 | 6.2 % |
| Springer Nature | 92 | 4.0 % |
| IOS Press | 63 | 2.7 % |
| IGI Global | 51 | 2.2 % |
| Association for Computing Machinery | 35 | 1.5 % |
| Springer International Publishing | 32 | 1.4 % |
| Taylor & Francis | 30 | 1.3 % |
| Wiley | 30 | 1.3 % |
| Hindawi Publishing Corporation | 26 | 1.1 % |
| Cornell University | 21 | 0.9 % |
| MYU K.K. | 15 | 0.7 % |

## Publishers on the risk list (DOI prefix)

| publisher | works | share |
|---|---|---|
| MDPI | 182 | 7.9 % |

## Author countries (a work counts once per country)

| country | works | share |
|---|---|---|
| DE | 301 | 13.1 % |
| FR | 277 | 12.0 % |
| US | 241 | 10.5 % |
| IT | 232 | 10.1 % |
| GB | 185 | 8.0 % |
| CN | 168 | 7.3 % |
| ES | 161 | 7.0 % |
| AU | 125 | 5.4 % |
| IN | 92 | 4.0 % |
| IE | 88 | 3.8 % |
| GR | 82 | 3.6 % |
| NL | 76 | 3.3 % |
| BE | 63 | 2.7 % |
| KR | 58 | 2.5 % |
| AT | 56 | 2.4 % |

## Changes since the previous harvest (`2026-11-07T0956`)

- Distinct works: 2227 then 2304: 77 added, 0 gone
- Seeds added: cox-2017-oosf; works added that cite only added seeds: 23; the others (54) come from changes in the index between the two harvests

| seed | citing works, 2026-11-07T0956 | citing works, 2026-11-07T1337 |
|---|---|---|
| ssn-xg-report-2011 | 142 | 142 |
| sso-2010 | 131 | 131 |
| compton-2012 | 1421 | 1447 |
| cox-2017-oosf | — | 45 |
| w3c-rec-2017 | 147 | 147 |
| w3c-rec-2017-hal | 0 | 0 |
| janowicz-2019 | 527 | 550 |
| janowicz-2018-ssrn | 36 | 37 |
| haller-2019 | 268 | 282 |
| taylor-2019-revamped | 10 | 10 |

