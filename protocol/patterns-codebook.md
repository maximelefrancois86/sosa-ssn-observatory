# Codebook of the modelling patterns (version 1, 2026-11-14)

A second extraction form, for the works that use SOSA/SSN (engagement E3 to E5) or write
its names: **which modelling choice the work makes** where the specification leaves the
choice open (SOSA/SSN 2017, section 7 "Common Modeling Questions"; 2023 Edition, section
"Common Patterns"). It answers the question the first codebook leaves open: of the works
that reuse SOSA/SSN, how many take one approach and how many the other (generic or
feature-specific properties, systems as individuals or as types, simple literals or
quantity values…).

Coded from **excerpts** of the full text: the passages around the names of SOSA/SSN
(`scripts/pattern_coding.py prepare`), not the whole work. A choice the excerpts do not
show is `not-shown`: never infer it from what the work is likely to do. Code what the
**work's own data, ontology, examples, figures or queries** show; a sentence that only
paraphrases the specification ("SOSA allows simple results or result objects") shows
nothing about the work's choice.

Each answer gives its values, at most two quotations copied **exactly** from the
excerpts (5 to 40 words each; a script checks them against the text), and a note of at
most two sentences. Who codes it is recorded with each answer (a model; the readers check).

## P1. Property individuals: generic or feature-specific

`property_individuals`, one value. What the objects of `sosa:observedProperty`,
`sosa:actsOnProperty`, `ssn:hasProperty` / `sosa:hasProperty` stand for.

- `generic`: one individual per kind of property, shared by all the features of interest
  (`ex:Temperature`, `quantitykind:Temperature`, `saref:Temperature`, `:airTemperature`
  observed on many rooms or stations).
- `specific`: an individual bound to one feature of interest (`<office/1/temperature>`,
  `ex:room34LightStatus`, `:Sensor1_Humidity`, a property declared with `isPropertyOf` a
  single feature), whatever class types it.
- `both`: the work shows both, e.g. specific properties linked to a generic kind
  (`saref:hasPropertyKind`, a class and its instances).
- `class`: the property is an OWL class and nothing else: the work defines
  `ex:Temperature rdfs:subClassOf sosa:ObservableProperty` and its observations point to
  the class IRI, or never show an individual.
- `not-shown`: no property individual or class in the excerpts.

## P2. Where the properties come from

`property_source`, several values: `own-classes` (the work defines subclasses of
`sosa:ObservableProperty`, `sosa:ActuatableProperty`, `ssn:Property`), `own-individuals`
(the work names its own property individuals, no catalogue), `catalogue` (it takes them
from an external vocabulary: name it in the note: QUDT quantity kinds, SWEET, ENVO, OM,
I-ADOPT, SAREF, CF standard names, BODC, Wikidata…), `not-shown`.

## P3. Punning

`punning`, one value: `yes` when the same IRI is used both as a class (subclass of a
SOSA/SSN class, or `rdf:type` object) and as an individual (object of `observedProperty`,
`madeBySensor`…), which the specification says one SHOULD NOT do (2017, § 7.4–7.5); `no`
when classes and individuals are shown and are distinct; `not-shown`.

## P4. System individuals

`system_individuals`, one value. What instances of `sosa:Sensor`, `sosa:Actuator`,
`sosa:Sampler`, `ssn:System` / `sosa:System`, `sosa:Platform` stand for.

- `individual-devices`: each individual is one physical or software device
  (`<sensor/927>`, `:DHT22_kitchen`, a serial number).
- `generic-individuals`: an individual stands for a model or a kind of device and is
  shared by observations of many devices (`ex:TemperatureSensor` as an individual,
  `:DHT22` used as the sensor of every reading).
- `types-and-instances`: device models or kinds are classes (subclasses of `sosa:Sensor`
  or `ssn:System`), devices are their instances (the pattern the 2023 Edition recommends).
- `not-shown`.

## P5. Form of the results

`result_form`, several values: `simple-literal` (`sosa:hasSimpleResult`), `qudt`
(`qudt:QuantityValue`, `qudt:numericValue`), `om` (`om:Measure`, `om:Point`),
`schema-org` (`schema:QuantitativeValue`), `own-result-node` (a `sosa:Result` or a class
of the work, with the work's own value property), `own-value-property` (the value is
attached to the observation by a property of the work that is not `hasSimpleResult`, e.g.
`:hasValue`, `:temperatureValue`), `structured` (array, matrix, JSON or CSV literal, RDF
list, Data Cube), `by-reference` (file, image, stream given by IRI), `nested` (an
observation or collection as result), `not-shown`.

## P6. Where the unit is

`unit_placement`, several values: `in-literal` (a `cdt:ucum` or other custom datatype
literal, or a string with the unit, "22 °C"), `on-result-node` (`qudt:unit`,
`qudt:hasUnit`, `om:hasUnit`, `schema:unitCode` on the result), `on-observation` (a unit
property on the observation), `on-property` (the unit is attached to the observed
property or its class), `on-sensor-or-collection`, `none` (values are shown without any
unit), `not-shown`.

## P7. Time

`time`, several values: `resultTime-literal` (`sosa:resultTime` with an `xsd:dateTime`
literal), `phenomenonTime-owl-time` (`sosa:phenomenonTime` to a `time:Instant` or
`time:Interval`), `phenomenonTime-literal`, `own-time-property` (a timestamp property of
the work or another vocabulary), `forecast` (an observation whose phenomenon time is after
its result time, the forecast pattern of the specification), `none`, `not-shown`.

## P8. Hosting and deployment

`hosting`, several values: `platform` (`sosa:hosts` / `sosa:isHostedBy` between platforms
and systems), `deployment` (`ssn:Deployment`, `ssn:deployedSystem`, `ssn:deployedOnPlatform`),
`subsystem` (`ssn:hasSubSystem`), `none` (systems are described but never hosted),
`not-shown`.

## P9. Location

`location`, several values: what the location is attached to and how. Attachment:
`on-system` (sensor, actuator), `on-platform`, `on-feature`, `on-observation`; encoding:
`geosparql` (`geo:hasGeometry`, WKT), `wgs84` (`geo:lat`/`geo:long` of W3C Basic Geo),
`schema-org`, `own-property`, `not-shown`.

## P10. Groups of observations

`grouping`, several values: `one-by-one` (each reading is one observation),
`collection-ssn-ext` (`ssn-ext:ObservationCollection`), `collection-sosa`
(`sosa:ObservationCollection`), `own-collection` (a class or property of the work, a
named graph, a Data Cube slice), `series-literal` (a whole series as one literal or
file), `stream` (an RDF stream of observations), `not-shown`.

## P11. Features of interest

`feature_typing`, one value: `explicit` (individuals typed `sosa:FeatureOfInterest`),
`subclass` (domain classes declared subclasses of `sosa:FeatureOfInterest`), `domain-only`
(features typed only by domain classes, linked by `hasFeatureOfInterest`), `both`,
`not-shown`.

## P12. Other idioms

`other`, free text, at most three sentences: a notable way of using SOSA/SSN that P1 to
P11 do not catch (observations subclassed per quantity, an actuation whose result is a
command, sample chains, the ultimate feature of interest, procedures described with
P-Plan, rules over observations…), or `none`.

## Form of the answer

One JSON object per work, on one line:

```json
{"item": "openalex:W…", "answers": {
  "property_individuals": {"values": ["generic"], "quotes": ["…"], "note": "…"},
  "property_source": {"values": ["catalogue"], "quotes": ["…"], "note": "QUDT quantity kinds"},
  "punning": {"values": ["not-shown"], "quotes": [], "note": ""},
  "system_individuals": {…}, "result_form": {…}, "unit_placement": {…}, "time": {…},
  "hosting": {…}, "location": {…}, "grouping": {…}, "feature_typing": {…},
  "other": {"values": ["…free text…"], "quotes": [], "note": ""}},
 "uncertain": ["property_individuals"]}
```

`values` is always a list. `uncertain` lists the questions the coder hesitates on.
