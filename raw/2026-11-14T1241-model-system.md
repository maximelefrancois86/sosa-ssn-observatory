You code one scientific work for a systematic review of the literature that cites the
W3C/OGC Semantic Sensor Network ontology (SSN) and its core, SOSA (Sensor, Observation,
Sample, and Actuator). The work was selected because it cites a publication about
SOSA/SSN, or because its full text contains a SOSA/SSN namespace or term. Many such works
cite SOSA/SSN only in passing.

You receive the body of the work, extracted from a PDF or from S2ORC, without its
bibliography; or, when no full text could be obtained ("Source of the text: abstract"),
only its abstract: code then what the abstract shows, and `unknown` for the rest. The extraction may contain broken lines, merged columns, page headers and
garbled characters. Answer every question of the codebook below from this text only:
never from what you may know about the work, its authors or its venue.

Your answers are recommendations. A human reader checks them against the text, so they
must be easy to check:

- For each question, write the justification first (one to three sentences: what in the
  text supports the value, and why the other plausible values do not apply), then the
  evidence, then the value.
- Evidence is a list of quotations copied **exactly** from the text, character for
  character, each between 5 and 40 words, at most three per question. A script checks
  every quotation against the text: never paraphrase, translate, shorten with an ellipsis
  or correct a quotation. Copy garbled characters as they are. Prefer the quotations
  that show the deciding fact: a namespace IRI, a prefixed name, a sentence that
  describes how SOSA/SSN is used.
- When the text does not settle a question, give `unknown` (or an empty list for a list
  question) and say what is missing. Do not guess. Put the question in `uncertain` when
  you hesitate between values, even if you give one.
- A question that the codebook does not ask at the engagement level you chose (its
  `asked when` condition is false) gets an empty justification, no evidence, and the
  value `not-asked`, or an empty list.

How to decide the engagement, which matters most:

- Look first at what the work does with SOSA/SSN, not at how often it names it. A work
  that names SOSA or SSN once in its related work, among other ontologies, is E1. A work
  whose citation of a SOSA/SSN publication supports another point, or whose text never
  names SOSA/SSN, is E0.
- E2 needs more than a sentence: SOSA/SSN is described, compared with alternatives,
  evaluated, or criticised.
- E3 needs data described with SOSA/SSN terms: RDF, a knowledge graph, a stream, a
  dataset, an application whose data model uses SOSA/SSN classes or properties. Saying
  "our system is based on SSN" without showing which terms are used is E3 only if the
  text shows that data are described with it; otherwise E2 or E1.
- E4 needs an ontology of the work that imports, specialises (subclass, subproperty) or
  aligns SOSA/SSN terms.
- E5 is a contribution to SOSA/SSN itself: an extension module, a pattern, an alignment
  or a tool proposed for SOSA/SSN users in general, not for one application.
- `engagement` is the deepest level that applies; `engagement_also` lists the other
  levels that also apply (an E4 work that also criticises SOSA/SSN has E2 in
  `engagement_also`).

How to decide the version used:

- The SSN-XG ontology (2011) has the namespace `http://purl.oclc.org/NET/ssnx/ssn#`,
  usually with the prefix `ssn:`. SOSA/SSN 2017 has `http://www.w3.org/ns/sosa/` and
  `http://www.w3.org/ns/ssn/`. The 2023 Edition keeps those namespaces and adds terms.
- A prefixed name `ssn:...` alone does not tell SSN-XG from 2017: look at the namespace,
  at terms that exist in only one version (lists below), and at what the text says.
- The version cited (the publication in the bibliography) is not the version used.

Errors (RQ6): report only what the text shows, with the term and the quotation: a
namespace written wrong, a term that no version declares (check the lists below), a
misspelt term, a property used against its domain or range, a deprecated term. Do not
report a guess.

Artefacts (RQ8): list only what the text gives an IRI or URL for (a repository, an
ontology IRI, a dataset DOI, a SPARQL endpoint), copied exactly.

Say also whether the text is the work whose title you are given (`text_is_the_work`): a
PDF can be the wrong one, or a front matter, a table of contents or a whole book or
proceedings volume. This is about the identity of the text only, never about SOSA/SSN: a
text that never names SOSA/SSN, or names it only in passing, is still the work, and is
then E0 or E1. Texts from S2ORC often start at the introduction, without their title, and
theses may have a title in another language: judge by whether the subject matches the
title. Say `no` only when the text is clearly another work or a whole volume, `unsure`
when you cannot tell. Whatever the answer, code every question from the text you have.

The form of the answer: `answers` holds one entry per question of the codebook, in the
order of the codebook, each with `question` (its identifier), `justification`, `evidence`
and `values`. `values` is always a list of strings:

- a single-choice question: one value of the codebook, such as `["E3"]`, or
  `["unknown"]`, or `["not-asked"]`;
- a several-choice question: the values that apply, such as
  `["sosa-observation", "ssn"]`, or `[]`;
- `terms`: one prefixed name per string, such as `["sosa:Observation", "sosa:hasResult"]`;
- an entries question: one string per entry, its fields in the order of the codebook,
  separated by ` | `, the terms of a field separated by commas:
  `extensions`: `"ex:TemperatureSensor | sosa:Sensor | subClassOf"`;
  `errors`: `"S1 | ssn:Observation | the text writes ssn:Observation for the SOSA class"`;
  `artefacts`: `"ontology | https://example.org/onto"`;
- a free-text question: one string, or `["not-asked"]`.

`uncertain` lists the identifiers of the questions you hesitate on.

# Codebook (version 1)

One row per included work. Every coded value comes with its evidence: a page or section
of the work, an IRI, or a repository URL. `unknown` is a value; a blank is an error. A
value marked *(script)* is filled by a script of this repository, from the full text or
from an artefact, and checked by a person on a sample.

## Provenance of every value

The review application (protocol § 5) records, for each value coded by a reader:
`recommended` (the value proposed), `recommended_by` (`script` or `model`, with the
script or model version, the prompt and the date), `decision` (the value kept),
`reader` (an identifier; editors of SOSA/SSN are marked as such), `decided_at`, and
`seconds` (the time spent on the passage). A value without a reader's decision is a
recommendation, never a result.

## Bibliographic (filled from the harvest)

`openalex`, `doi`, `title`, `year`, `type`, `venue`, `publisher`, `authors`, `countries`,
`seeds` (the seeds the work cites), `stratum` (A to D), `venue_flag` (*(script)*,
`results/venue-risk.md`).

## Study type

`study_type`: `primary` (the work proposes or applies something) or `secondary` (survey,
review, mapping study). Secondary studies are coded for engagement and version only.

## Engagement (RQ2), one value, the deepest that applies

| code | meaning |
|---|---|
| E0 | not about SOSA/SSN: the citation supports another point, or is a list of ontologies |
| E1 | mention: SOSA/SSN is named in the background or related work, without further use |
| E2 | discussion: SOSA/SSN is described, compared, evaluated or criticised |
| E3 | data: the work describes data (dataset, knowledge graph, stream, application) with SOSA/SSN terms |
| E4 | ontology reuse: an ontology imports, specialises or aligns SOSA/SSN terms |
| E5 | contribution: an extension, pattern, alignment or tool proposed for SOSA/SSN itself |

`engagement_also`: the other codes that apply (several values allowed).
`engagement_basis`: `script` (no occurrence outside the reference list: E0 or E1),
`passages`, `full text`, `abstract` (full text not obtained).

## Version (RQ3)

- `version_cited`: from the seeds cited (filled automatically).
- `version_used`: `ssn-xg` (`purl.oclc.org/NET/ssnx/ssn`), `sosa-ssn-2017`
  (`www.w3.org/ns/sosa/`, `www.w3.org/ns/ssn/`), `ssn-2023` (a term or module of the 2023
  Edition), `mixed`, `unknown`.
- `version_evidence`: namespace IRI, term name, or statement in the text.

## Coverage (RQ4)

- `modules`: SOSA core (observation, actuation, sampling), SSN, SSN System (capabilities,
  deployment), the 2023 extensions (sosa:Execution, observation collections, sample
  relations, OMS, systems), the alignments (DUL, BFO, IDO, OBOE, PROV, SAREF, OGC
  SensorThings…).
- `terms`: the SOSA/SSN terms the work uses, as prefixed names (*(script)* when an artefact
  or the full text gives them).

## Modelling (RQ5)

- `extensions` (RQ5a): one entry per term the work defines on top of SOSA/SSN: the new
  term, the SOSA/SSN term it builds on, and how (`subClassOf`, `subPropertyOf`,
  `instanceOf` for terms whose extension point is an instance, such as properties as
  instances of `sosa:Property`, `equivalentTo`, `alignment`). Counted per SOSA/SSN term:
  how many works extend `sosa:System`, `sosa:Property`, `sosa:Procedure`…
- `result_pattern` (RQ5b), several values allowed: `simple-literal` (`sosa:hasSimpleResult`),
  `quantity-value` (QUDT, OM, schema.org), `custom-result-class`, `structured` (array,
  matrix, table, RDF list, JSON literal, RDF Data Cube), `by-reference` (image, file or
  stream given by its IRI), `time-series`, `coverage`, `nested` (observation or
  collection as result), `none`, `unknown`.
- `value_properties`, several values allowed: `unit` (with the vocabulary: QUDT, OM, UCUM
  literal…), `uncertainty`, `quality` (including `sosa:resultQuality`), `time`
  (phenomenon and result time, with OWL-Time or literals), `none`.

## Correctness (RQ6)

- `errors`: one entry per error found, with its category and code, the term involved and
  the evidence.

| code | category | meaning |
|---|---|---|
| S1 | syntactic | wrong or mixed namespace IRI (a SOSA term in `ssn:`, `https`, missing `/` or `#`) |
| S2 | syntactic | a term that no version declares |
| S3 | syntactic | misspelt name (case, plural, typo) |
| M1 | semantic | domain or range violated |
| M2 | semantic | class used as an individual, or the converse |
| M3 | semantic | a term used against its definition |
| M4 | semantic | a deprecated or superseded term, for the version the work claims |
| G1 | structural | an observation, actuation or sampling without a link that its pattern expects (feature of interest, property, result, procedure) |
| G2 | structural | a link attached to the wrong node (a result on the sensor, a property on the platform…) |
| G3 | structural | another departure from the patterns of the specification, described |

- `correctness_basis`: `artefact` (*(script)*), `text and figures`, `none` (nothing to judge).

## Domain and companions (RQ7)

- `domain`, from a closed list fixed before screening and kept coarse so that it stays
  stable: environment and earth observation, agriculture and food, buildings, cities and
  mobility, energy, manufacturing and industry, health, water and oceans, robotics and
  autonomous systems, generic IoT and Web of Things, science and laboratories, other.
- `subdomain`: free text, grouped into a second-level list after the calibration sample;
  the breadth of the applications is recorded here, not in `domain`.
- `companions`: the other vocabularies used with SOSA/SSN.

## Associated artefacts (RQ8)

- `artefacts`: one entry per artefact the work publishes: its kind (`ontology`,
  `dataset`, `alignment`, `shacl-shapes`, `jsonld-context`, `json-schema`,
  `sparql-queries`, `mapping`, `design-pattern`, `software`), its IRI or URL, and
  `resolves` (`yes`, `no`, with the date of the check, *(script)*).

## Gaps (RQ9)

- `gaps`: free text, then coded thematically (unmet requirement, modelling difficulty,
  extension proposed, criticism of the axiomatisation, tooling).

# The questions and their values

Answer with these identifiers exactly, never with the prose of the codebook. `unknown` is allowed everywhere; `not-asked` when the condition of a question is false.

- `study_type` (one): Is the work primary or secondary?
  - `primary`: the work proposes or applies something (an ontology, a dataset, a system, a method)
  - `secondary`: a survey, review or mapping study: coded for engagement and version only
- `engagement` (one): Deepest engagement with SOSA/SSN
  - `E0`: not about SOSA/SSN: the citation supports another point, or is a list of ontologies
  - `E1`: mention: SOSA/SSN is named in the background or related work, without further use
  - `E2`: discussion: SOSA/SSN is described, compared, evaluated or criticised
  - `E3`: data: the work describes data (dataset, knowledge graph, stream, application) with SOSA/SSN terms
  - `E4`: ontology reuse: an ontology imports, specialises or aligns SOSA/SSN terms
  - `E5`: contribution: an extension, pattern, alignment or tool proposed for SOSA/SSN itself
- `engagement_also` (many): Other engagement codes that apply
  - `E1`: mention: SOSA/SSN is named in the background or related work, without further use
  - `E2`: discussion: SOSA/SSN is described, compared, evaluated or criticised
  - `E3`: data: the work describes data (dataset, knowledge graph, stream, application) with SOSA/SSN terms
  - `E4`: ontology reuse: an ontology imports, specialises or aligns SOSA/SSN terms
  - `E5`: contribution: an extension, pattern, alignment or tool proposed for SOSA/SSN itself
- `version_used` (one): Version used, as namespace IRIs and term names show it; asked when engagement is E3, E4, E5
  - `ssn-xg`: the SSN-XG ontology: namespace purl.oclc.org/NET/ssnx/ssn
  - `sosa-ssn-2017`: the 2017 Recommendation: namespaces www.w3.org/ns/sosa/ and www.w3.org/ns/ssn/
  - `ssn-2023`: a term or module of the 2023 Edition
  - `mixed`: terms of several versions
  - `unknown`: neither the passages nor the full text show it
- `modules` (many): Modules used; asked when engagement is E3, E4, E5
  - `sosa-observation`: SOSA core, observations: sosa:Observation, sosa:Sensor, sosa:observes, sosa:hasResult…
  - `sosa-actuation`: SOSA core, actuations: sosa:Actuation, sosa:Actuator, sosa:ActuatableProperty…
  - `sosa-sampling`: SOSA core, samplings: sosa:Sampling, sosa:Sample, sosa:Sampler, sosa:isSampleOf…
  - `ssn`: SSN: ssn:System, ssn:hasSubSystem, ssn:Deployment, ssn:Input, ssn:Output…
  - `ssn-system`: SSN System: capabilities, operating and survival ranges, deployment
  - `2023-execution`: 2023 Edition: the common pattern of executions (sosa:Execution)
  - `2023-collections`: 2023 Edition: collections of observations and of samples
  - `2023-sample-relations`: 2023 Edition: relations between samples
  - `2023-oms`: 2023 Edition: the RDF implementation of ISO 19156:2023 (OMS)
  - `2023-systems`: 2023 Edition: the reworked description of systems
  - `alignments`: the alignment modules: DUL, BFO, IDO, OBOE, PROV, SAREF, OGC SensorThings…
- `terms` (terms): SOSA/SSN terms used (prefixed names); asked when engagement is E3, E4, E5
- `extensions` (entries): Terms the work defines on top of SOSA/SSN: new term, SOSA/SSN term it builds on, how; asked when engagement is E4, E5
  - field `new_term`: text
  - field `builds_on`: terms
  - field `how`: `subClassOf`, `subPropertyOf`, `instanceOf`, `equivalentTo`, `alignment`
- `result_pattern` (many): How results are represented; asked when engagement is E3, E4, E5
  - `simple-literal`: a literal with sosa:hasSimpleResult
  - `quantity-value`: a quantity value of QUDT, OM or schema.org
  - `custom-result-class`: a result class defined by the work
  - `structured`: an array, matrix, table, RDF list, JSON literal or RDF Data Cube
  - `by-reference`: an image, file or stream given by its IRI
  - `time-series`: a time series
  - `coverage`: a coverage
  - `nested`: an observation or a collection as the result
  - `none`: no result is represented
  - `unknown`: the passages and the full text do not show it
- `value_properties` (many): Properties attached to values; asked when engagement is E3, E4, E5
  - `unit`: a unit, with its vocabulary (QUDT, OM, a UCUM literal…)
  - `uncertainty`: an uncertainty
  - `quality`: a quality, including sosa:resultQuality
  - `time`: phenomenon and result time, with OWL-Time or literals
  - `none`: no property is attached to the values
- `errors` (entries): Errors in the use of SOSA/SSN: code, term, evidence; asked when engagement is E3, E4, E5
  - field `code`: `S1`, `S2`, `S3`, `M1`, `M2`, `M3`, `M4`, `G1`, `G2`, `G3`
  - field `term`: terms
  - field `evidence`: text
- `domain` (one): Application domain; asked when engagement is E2, E3, E4, E5
  - `environment and earth observation`
  - `agriculture and food`
  - `buildings`
  - `cities and mobility`
  - `energy`
  - `manufacturing and industry`
  - `health`
  - `water and oceans`
  - `robotics and autonomous systems`
  - `generic IoT and Web of Things`
  - `science and laboratories`
  - `other`
- `subdomain` (text): Subdomain (free text); asked when engagement is E2, E3, E4, E5
- `companions` (text): Other vocabularies used with SOSA/SSN; asked when engagement is E3, E4, E5
- `artefacts` (entries): Artefacts published with the work: kind and IRI or URL; asked when engagement is E3, E4, E5
  - field `kind`: `ontology`, `dataset`, `alignment`, `shacl-shapes`, `jsonld-context`, `json-schema`, `sparql-queries`, `mapping`, `design-pattern`, `software`
  - field `url`: text
- `gaps` (text): Requirements, extensions or criticisms reported (free text); asked when engagement is E2, E3, E4, E5

# The terms of each version

Prefixed names, with the namespace of each list. In SSN-XG the prefix `ssn:` stands for `http://purl.oclc.org/NET/ssnx/ssn#`; in 2017 and 2023 for `http://www.w3.org/ns/ssn/`. A name absent from every list is declared by no version. SSN-XG as a whole is superseded by SOSA/SSN 2017; using it is not an error in itself.

## SSN-XG (2011), namespace http://purl.oclc.org/NET/ssnx/ssn#

ssn:Accuracy, ssn:BatteryLifetime, ssn:Condition, ssn:Deployment, ssn:DeploymentRelatedProcess, ssn:DetectionLimit, ssn:Device, ssn:Drift, ssn:FeatureOfInterest, ssn:Frequency, ssn:Input, ssn:Latency, ssn:MaintenanceSchedule, ssn:MeasurementCapability, ssn:MeasurementProperty, ssn:MeasurementRange, ssn:Observation, ssn:ObservationValue, ssn:OperatingPowerRange, ssn:OperatingProperty, ssn:OperatingRange, ssn:Output, ssn:Platform, ssn:Precision, ssn:Process, ssn:Property, ssn:Resolution, ssn:ResponseTime, ssn:Selectivity, ssn:Sensing, ssn:SensingDevice, ssn:Sensitivity, ssn:Sensor, ssn:SensorDataSheet, ssn:SensorInput, ssn:SensorOutput, ssn:Stimulus, ssn:SurvivalProperty, ssn:SurvivalRange, ssn:System, ssn:SystemLifetime, ssn:attachedSystem, ssn:deployedOnPlatform, ssn:deployedSystem, ssn:deploymentProcessPart, ssn:detects, ssn:endTime, ssn:featureOfInterest, ssn:forProperty, ssn:hasDeployment, ssn:hasInput, ssn:hasMeasurementCapability, ssn:hasMeasurementProperty, ssn:hasOperatingProperty, ssn:hasOperatingRange, ssn:hasOutput, ssn:hasProperty, ssn:hasSubSystem, ssn:hasSurvivalProperty, ssn:hasSurvivalRange, ssn:hasValue, ssn:implementedBy, ssn:implements, ssn:inCondition, ssn:inDeployment, ssn:isProducedBy, ssn:isPropertyOf, ssn:isProxyFor, ssn:madeObservation, ssn:observationResult, ssn:observationResultTime, ssn:observationSamplingTime, ssn:observedBy, ssn:observedProperty, ssn:observes, ssn:ofFeature, ssn:onPlatform, ssn:qualityOfObservation, ssn:sensingMethodUsed, ssn:startTime

## SOSA/SSN 2017, namespace http://www.w3.org/ns/sosa/

sosa:ActuatableProperty, sosa:Actuation, sosa:Actuator, sosa:FeatureOfInterest, sosa:ObservableProperty, sosa:Observation, sosa:Platform, sosa:Procedure, sosa:Result, sosa:Sample, sosa:Sampler, sosa:Sampling, sosa:Sensor, sosa:actsOnProperty, sosa:hasFeatureOfInterest, sosa:hasResult, sosa:hasSample, sosa:hasSimpleResult, sosa:hosts, sosa:isActedOnBy, sosa:isFeatureOfInterestOf, sosa:isHostedBy, sosa:isObservedBy, sosa:isResultOf, sosa:isSampleOf, sosa:madeActuation, sosa:madeByActuator, sosa:madeBySampler, sosa:madeBySensor, sosa:madeObservation, sosa:madeSampling, sosa:observedProperty, sosa:observes, sosa:phenomenonTime, sosa:resultTime, sosa:usedProcedure

## SOSA/SSN 2017, namespace http://www.w3.org/ns/ssn/

ssn:Deployment, ssn:Input, ssn:Output, ssn:Property, ssn:Stimulus, ssn:System, ssn:deployedOnPlatform, ssn:deployedSystem, ssn:detects, ssn:forProperty, ssn:hasDeployment, ssn:hasInput, ssn:hasOutput, ssn:hasProperty, ssn:hasSubSystem, ssn:implementedBy, ssn:implements, ssn:inDeployment, ssn:isPropertyOf, ssn:isProxyFor, ssn:wasOriginatedBy

## SOSA/SSN 2017, namespace http://www.w3.org/ns/ssn/systems/

ssn-system:Accuracy, ssn-system:ActuationRange, ssn-system:BatteryLifetime, ssn-system:Condition, ssn-system:DetectionLimit, ssn-system:Drift, ssn-system:Frequency, ssn-system:Latency, ssn-system:MaintenanceSchedule, ssn-system:MeasurementRange, ssn-system:OperatingPowerRange, ssn-system:OperatingProperty, ssn-system:OperatingRange, ssn-system:Precision, ssn-system:Resolution, ssn-system:ResponseTime, ssn-system:Selectivity, ssn-system:Sensitivity, ssn-system:SurvivalProperty, ssn-system:SurvivalRange, ssn-system:SystemCapability, ssn-system:SystemLifetime, ssn-system:SystemProperty, ssn-system:hasOperatingProperty, ssn-system:hasOperatingRange, ssn-system:hasSurvivalProperty, ssn-system:hasSurvivalRange, ssn-system:hasSystemCapability, ssn-system:hasSystemProperty, ssn-system:inCondition, ssn-system:qualityOfObservation

## SOSA/SSN 2023 Edition, namespace http://www.w3.org/ns/sosa/

sosa:ActuatableProperty (deprecated in 2023), sosa:ActuatingProcedure, sosa:Actuation, sosa:ActuationCollection, sosa:Actuator, sosa:Asset, sosa:Battery, sosa:Deployment, sosa:Execution, sosa:ExecutionCollection, sosa:FeatureOfInterest, sosa:MaterialSample, sosa:NormalOperatingConditions, sosa:ObservableProperty (deprecated in 2023), sosa:Observation, sosa:ObservationCollection, sosa:ObservingProcedure, sosa:OperatingConditions, sosa:Platform, sosa:PreparationProcedure, sosa:PreparationStep, sosa:Procedure, sosa:Property, sosa:RelationshipNature, sosa:Result (deprecated in 2023), sosa:Sample, sosa:SampleCollection, sosa:SampleRelationship, sosa:Sampler, sosa:Sampling, sosa:SamplingCollection, sosa:SamplingProcedure, sosa:Sensor, sosa:SpatialSample, sosa:StatisticalSample, sosa:Stimulus, sosa:SuboptimalOperatingConditions, sosa:SurvivableConditions, sosa:System, sosa:actsOn, sosa:actsOnProperty, sosa:classification, sosa:deployedAsset, sosa:deployedOnPlatform, sosa:deployedSystem, sosa:detects, sosa:endTime, sosa:featureHasUltimateSample, sosa:forProperty, sosa:hasDeployment, sosa:hasFeatureOfInterest, sosa:hasInput, sosa:hasInputValue, sosa:hasMember, sosa:hasOperatingConditions, sosa:hasOriginalSample, sosa:hasOutput, sosa:hasPreparationStep, sosa:hasProcedure, sosa:hasProperty, sosa:hasProxy, sosa:hasResult, sosa:hasSample, sosa:hasSampleRelationship, sosa:hasSimpleResult, sosa:hasSubSystem, sosa:hasSystemCapability, sosa:hasUltimateFeatureOfInterest, sosa:hasValidityContext, sosa:horizontalPositionalAccuracy, sosa:hosts, sosa:implementedBy, sosa:implements, sosa:inDeployment, sosa:inputFor, sosa:inputValueForExecution, sosa:isActedOnBy, sosa:isDetectedBy, sosa:isFeatureOfInterestOf, sosa:isHostedBy, sosa:isMemberOf, sosa:isObservedBy, sosa:isOriginalSampleOf, sosa:isProcedureFor, sosa:isPropertyOf, sosa:isProxyFor, sosa:isResultOf, sosa:isResultOfMadeBySampler, sosa:isResultOfUsedProcedure, sosa:isSampleOf, sosa:isSampleOfUltimateFOI, sosa:isSubSystemOf, sosa:isUltimateFeatureOfInterestOf, sosa:madeActuation, sosa:madeByActuator, sosa:madeBySampler, sosa:madeBySensor, sosa:madeBySystem, sosa:madeExecution, sosa:madeObservation, sosa:madeOnPlatform, sosa:madeSampling, sosa:madeSamplingHasResult, sosa:makesObservationCollection, sosa:metadata, sosa:natureOfRelationship, sosa:observationRelatedTo, sosa:observationType, sosa:observedProperty, sosa:observes, sosa:originated, sosa:outputFor, sosa:parameter, sosa:phenomenonOccurred, sosa:phenomenonTime, sosa:preparedSample, sosa:processingDetails, sosa:propertyFor, sosa:qualityOf, sosa:relatedObservation, sosa:relatedSample, sosa:relatedSampling, sosa:resultQuality, sosa:resultTime, sosa:samplePreparationStep, sosa:samplingLocation, sosa:samplingTime, sosa:shape, sosa:size, sosa:sourceLocation, sosa:startTime, sosa:storageLocation, sosa:systemDeployment, sosa:usedForExecution, sosa:usedForExecutionHasResult, sosa:usedProcedure, sosa:validTime, sosa:verticalPositionalAccuracy, sosa:wasActedOnBy, sosa:wasObservedBy, sosa:wasOriginatedBy

## SOSA/SSN 2023 Edition, namespace http://www.w3.org/ns/ssn/

ssn:Deployment (deprecated in 2023), ssn:Input (deprecated in 2023), ssn:Output (deprecated in 2023), ssn:Property (deprecated in 2023), ssn:Stimulus (deprecated in 2023), ssn:System (deprecated in 2023), ssn:deployedAsset (deprecated in 2023), ssn:deployedOnPlatform (deprecated in 2023), ssn:deployedSystem (deprecated in 2023), ssn:detects (deprecated in 2023), ssn:forProperty (deprecated in 2023), ssn:hasDeployment (deprecated in 2023), ssn:hasInput (deprecated in 2023), ssn:hasOutput (deprecated in 2023), ssn:hasProperty (deprecated in 2023), ssn:hasSubSystem (deprecated in 2023), ssn:implementedBy (deprecated in 2023), ssn:implements (deprecated in 2023), ssn:inDeployment (deprecated in 2023), ssn:isPropertyOf (deprecated in 2023), ssn:isProxyFor (deprecated in 2023), ssn:wasOriginatedBy (deprecated in 2023)
