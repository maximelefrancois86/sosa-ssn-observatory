# Modelling patterns of the works that use SOSA/SSN

Written by `scripts/pattern_coding.py ingest` from run `2026-11-14T1117` (codebook `protocol/patterns-codebook.md`, coder: claude-opus-5-5 (Claude Code agents)). Recommendations, not decisions of the readers.

Works prepared: 481; coded: 481; quotations found in the excerpts: 1539 of 1539 (100.0 %).

## Agreement of a second, independent coder

60 works drawn by a seeded hash (raw/2026-11-14T1117-patterns-coded-R1.jsonl).

| Question | Works | Same set of values | Cohen's kappa | Mean Jaccard |
|---|---|---|---|---|
| property_individuals | 60 | 56 | 0.83 | 0.93 |
| property_source | 60 | 57 | 0.87 | 0.96 |
| punning | 60 | 59 | 0.79 | 0.98 |
| system_individuals | 60 | 54 | 0.76 | 0.90 |
| result_form | 60 | 53 | 0.81 | 0.92 |
| unit_placement | 60 | 59 | 0.96 | 0.98 |
| time | 60 | 59 | 0.96 | 0.98 |
| hosting | 60 | 55 | 0.70 | 0.92 |
| location | 60 | 58 | 0.91 | 0.97 |
| grouping | 60 | 56 | 0.83 | 0.93 |
| feature_typing | 60 | 59 | 0.94 | 0.98 |

## property_individuals

Shown in 157 of the 481 works coded; the coder hesitated on 80.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 324 |  |
| generic | 91 | 58 % |
| specific | 33 | 21 % |
| class | 25 | 16 % |
| both | 8 | 5 % |

## property_source

Shown in 163 of the 481 works coded; the coder hesitated on 9.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 318 |  |
| own-individuals | 93 | 57 % |
| own-classes | 62 | 38 % |
| catalogue | 31 | 19 % |

## punning

Shown in 16 of the 481 works coded; the coder hesitated on 2.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 465 |  |
| yes | 8 | 50 % |
| no | 8 | 50 % |

## system_individuals

Shown in 149 of the 481 works coded; the coder hesitated on 51.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 332 |  |
| individual-devices | 80 | 54 % |
| types-and-instances | 56 | 38 % |
| generic-individuals | 13 | 9 % |

## result_form

Shown in 197 of the 481 works coded; the coder hesitated on 41.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 284 |  |
| simple-literal | 78 | 40 % |
| own-result-node | 69 | 35 % |
| own-value-property | 29 | 15 % |
| qudt | 26 | 13 % |
| om | 9 | 5 % |
| by-reference | 5 | 3 % |
| structured | 5 | 3 % |
| nested | 1 | 1 % |
| schema-org | 1 | 1 % |

## unit_placement

Shown in 106 of the 481 works coded; the coder hesitated on 15.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 375 |  |
| on-result-node | 42 | 40 % |
| none | 22 | 21 % |
| on-sensor-or-collection | 12 | 11 % |
| on-property | 12 | 11 % |
| in-literal | 11 | 10 % |
| on-observation | 8 | 8 % |

## time

Shown in 145 of the 481 works coded; the coder hesitated on 31.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 336 |  |
| resultTime-literal | 81 | 56 % |
| own-time-property | 48 | 33 % |
| phenomenonTime-owl-time | 20 | 14 % |
| phenomenonTime-literal | 4 | 3 % |
| forecast | 2 | 1 % |
| none | 1 | 1 % |

## hosting

Shown in 97 of the 481 works coded; the coder hesitated on 12.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 384 |  |
| platform | 81 | 84 % |
| subsystem | 16 | 16 % |
| deployment | 12 | 12 % |

## location

Shown in 109 of the 481 works coded; the coder hesitated on 27.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 372 |  |
| own-property | 55 | 50 % |
| on-system | 46 | 42 % |
| geosparql | 38 | 35 % |
| on-feature | 30 | 28 % |
| on-platform | 23 | 21 % |
| wgs84 | 21 | 19 % |
| on-observation | 18 | 17 % |
| schema-org | 1 | 1 % |

## grouping

Shown in 111 of the 481 works coded; the coder hesitated on 8.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 370 |  |
| one-by-one | 51 | 46 % |
| stream | 27 | 24 % |
| own-collection | 22 | 20 % |
| collection-sosa | 15 | 14 % |
| collection-ssn-ext | 2 | 2 % |
| series-literal | 2 | 2 % |

## feature_typing

Shown in 89 of the 481 works coded; the coder hesitated on 23.

| Value | Works | Share of the works where it is shown |
|---|---|---|
| not-shown | 392 |  |
| subclass | 42 | 47 % |
| explicit | 26 | 29 % |
| domain-only | 20 | 22 % |
| both | 1 | 1 % |

## other (free text)

- `openalex:W1806356160`: Observations are observedBy the weather station; observation IRIs encode timestamp, station and property; a quality value per observation.
- `openalex:W2062032918`: Jena rules propagate the location of a platform to the subsystems of its deployed system, and shortcut the result chain into an own hasObservationValue.
- `openalex:W2082670328`: 2011 SSN with measurement capabilities (accuracy, sensitivity as rdf:value) per device; dynamic properties such as the last measure attached directly to the sensor resource.
- `openalex:W2212276110`: Observations are also typed void:Dataset; collections are aggregated recursively along spatial, temporal and property dimensions.
- `openalex:W2258400580`: Uses SSN 2011 with equivalence axioms to PROV-O (ssn:Observation as prov:Entity, ssn:Process as prov:Activity) so a reasoner materialises provenance.
- `openalex:W2309209207`: Track_Section declared a subclass of ssn:Platform and signalling elements subclasses of ssn:SensingDevice, composed through DUL:hasComponent restrictions in a railway layout ontology.
- `openalex:W2555963176`: Old SSN (ssnx) with CF properties; sensors point to a per-plot feature with ssn:ofFeature, and plots link to crop treatments for filtering.
- `openalex:W2598816345`: Observation and sensor output subclasses per quantity (em:PolyphaseVoltageObservation); stream queries construct alert events typed with DUL.
- `openalex:W2758824304`: SOSA terms re-declared as a PROV extension (prov-sw:) so that observations are prov:Activity associated with the sensor and generating the result.
- `openalex:W2787184475`: Built on the 2011 SSN: sbms:Observation is tied to a BMS data point and key classes carry IDs with owl:hasKey; observed properties split into physical quantity and property domain.
- `openalex:W2791815748`: Multimedia results (sosa:Result subclass) decomposed into temporal and spatial segments carrying MPEG-7-style descriptors, aligned with the Media Resource ontology.
- `openalex:W2797965711`: Factorized observations: identical readings at different timestamps are represented once, to shrink the knowledge graph built on demand from a stream.
- `openalex:W2800790195`: Quality-of-observation attributes and effects are attached to SSN 2011 measurement capabilities.
- `openalex:W2807592530`: Signal classes carry OWL restrictions on their sensor and unit; sensors and actuators are classes linked by sosa:isObservedBy/isActedBy restrictions.
- `openalex:W2810902628`: Uses the 2009 SSN (observationResultTime, SensorOutput) with DUL; property values are also stored on entity properties (hasValue) with the observation time.
- `openalex:W2886849005`: A DUL-aligned pattern network: observations express states (se-situ:State) and situations; a configuration procedure (subclass of sosa:Procedure) per sensor; TBox only, no instance data shown.
- `openalex:W2886925707`: Uses SSN 2011: one observation has several results typed by the quantity (CloudCover, AtmosphPress) instead of an observed property.
- `openalex:W2890066672`: IoT-Lite over SSN 2011 terms (ssn:Sensor, ssn:Device): no observation is modelled, sensors carry quantity kind, unit, location and service; the patient is an iot-lite:Entity.
- `openalex:W2890115906`: The stream is an ssn:Output of a sensing; the observation is also a vsd:TimeVaryingGraph and event:Event. Example built on the 2011 SSN with SAO.
- `openalex:W2894572834`: A sosa:Result may be an RDF graph description presented with lifting, lowering and validation rules; WoT TD terms are aligned as subclasses and subproperties of SSN system and procedure terms.
- `openalex:W2896965969`: Informal SSN-like triples with own property names (:observedBy, :observationValue, :time); the user's location is an observation value used by SWRL context rules.
- `openalex:W2897559405`: SHACL SPARQL rules built from automatic alignments rewrite oneM2M and OCF data into SOSA observations.
- `openalex:W2898839322`: Micro-controllers are subclasses of ssn:System implementing sosa:Procedures (algorithms); WoT TD aligned with td:Thing subclass of ssn:System and td:InteractionPattern subclass of sosa:Procedure.
- `openalex:W2899566284`: Observable features are DUL roles that physical objects play according to sensor deployment; events (LowTemperature) derived by rules over observations, built on the 2011 SSN.
- `openalex:W2900245446`: The work mints its own terms in the ssn: namespace (ssn:isMotedBy, ssn:Kitchen, ssn:Mum, ssn:On) and refines ssn:isObservedBy into ssn:isSensedBy and ssn:isMotedBy per sensor kind.
- `openalex:W2906464847`: Observations are the data source of KPI calculations; sensors are left out of the model.
- `openalex:W2907996754`: Sensor results linked to inputs of control logic through SEAS communication connections; checking observations against the measurement range of the sensor model.
- `openalex:W2908120732`: SSN terms are re-declared in an own ex: namespace (ex:Sensor, ex:observedProperty, ex:onPlatform), with observedProperty on the sensor.
- `openalex:W2909376481`: Actuations with a feature of interest (light, window) and stream rules deriving user events (closeTo, stoppedFrom) from observations.
- `openalex:W2945125411`: New sensor types are added as ssn:Sensor subclasses to an IoT dictionary built by knowledge extraction.
- `openalex:W2951278088`: Edge devices are sosa:Platform (written <http://www.w3.org/ns/sosa#Platform>), and ssn:Property is used for hardware resources and data volume/velocity/variety capabilities matched against task requirements.
- `openalex:W2961974912`: The ontology evolves from the sensor data stream, under a consistency model for updates and new concepts.
- `openalex:W2963438881`: Lightweight stream ontology: StreamObservation (sosa:Observation subclass) carries only values and timestamps, metadata (sensor, unit, quantity kind, location, service) sit on the IotStream.
- `openalex:W2964006647`: Numerical values are kept out of the ontology (time-series store); the ontology describes only measures, features and properties.
- `openalex:W2966249670`: Logical sensors/actuators (subclasses of sosa:Sensor/Actuator) run software procedures whose executions take observations as ssn:hasInput and produce observations as ssn:hasOutput.
- `openalex:W2969014756`: Sensor-centred triples (sensor hasUnit, hasQuantityKind, hasResult) in the work's MIoT-Ont namespace, without observation individuals.
- `openalex:W2970064150`: The result of a web service call (a Yelp search) is wrapped as a sosa observation blank node by a JavaScript accessor.
- `openalex:W2972992288`: The feature of interest is used to hold the sensor and actuator limits and faulty patterns against which observations are compared; Sampling stores observations over a period.
- `openalex:W2974197489`: Own relations (:isObservationFor, :isObservedPropertyFor, :isDataSourceFor) link hazards, observations, observed properties and data sources.
- `openalex:W2979435185`: The kind of measurement is given by the type of the result node (HeartRateObservationValue) rather than an observed property.
- `openalex:W2980451194`: Reuses a non-existent sosa:ObservationValue; actuations are HTTP requests with OWL-S preconditions and effects for AI planning.
- `openalex:W2985339799`: Properties carry the expected value type (semic:observationType / actionType) and static properties hold literal values; sosa:Sensor is split into physical and virtual (software) sensors.
- `openalex:W2985807578`: IoT devices modelled as a subclass of sosa:Platform inside a privacy preference ontology, with no observations.
- `openalex:W2987452795`: Built on the 2011 SSN with DUL: indicators are ssn:SensorOutput and scoring processes are ssn:Sensing with inputs and outputs. Observations satisfy goals expressed by benchmarks.
- `openalex:W2989739206`: Rules as SPARQL CONSTRUCT stored in RDF (SPIN-like rso:) classify observations (health:Healthy); misspelled ssn:observerBy.
- `openalex:W2995271153`: The feature of interest of fault-detection observations is a sensor itself; actuations produce system states with own timespans, inserted by SPARQL Update rules.
- `openalex:W2999380148`: A bridge cross-section is declared a sosa:Platform hosting the sensors installed on it. Observations produced by R2RML mappings and stored in HBase.
- `openalex:W3001254279`: Multi-typing: a musical instrument individual is at once an iot:Thing, mo:Instrument, prov:Entity and sosa:Platform.
- `openalex:W3003347746`: The hall is at once a sample of the building, a feature of interest and a platform hosting the sensor board.
- `openalex:W3003933818`: IoT sensors themselves are said to act as features of interest for observation and actuation.
- `openalex:W3016754381`: Sample chain in the case study: a sampling of room air gives the sample air, which is then the feature of interest of the observation. Adds own DeviceId and hasSubDevice to the SSN classes.
- `openalex:W3032968634`: Own System, Sensor and Actuator classes subclass the SOSA ones, with system components, states, and operating conditions declared subclasses of a sosa:Condition class that SOSA does not define.
- `openalex:W3035029867`: Observations of virtual and cognitive sensors carry inferred results (activity levels, disease names) about an apartment, chained by stream reasoning.
- `openalex:W3035839863`: sosa:observes on the sensor used to determine the sensor type; SOSA/IoTStream entities stored in an NGSI-LD broker.
- `openalex:W3041094324`: Calibration models (OM plus Content MathML) attached to sensors through a new calibratedSensor class; measures with metrological uncertainty.
- `openalex:W3046424363`: Logical sensors/actuators (subclasses of sosa:Sensor/Actuator) run SPARQL software procedures whose executions take observations as ssn:hasInput and produce observations as ssn:hasOutput; the door is both feature of interest and platform.
- `openalex:W3083324460`: Knowledge base overlays merge a building knowledge base (SSN observations) with smartphone knowledge bases so that logical actuators use users' observations and preferences.
- `openalex:W3088317607`: 2011 SSN with iot-lite: ssn:Device subdivided into sensing and actuating devices; medical objects contain devices and carry own has-location and has-time properties.
- `openalex:W3092442218`: A capability ontology (C4I) is aligned with SSN through a separate bridging module (C4I2SSN).
- `openalex:W3093138486`: Smart musical instruments are platforms hosting sensors and also expose services.
- `openalex:W3094146027`: Observations produced by RML mappings from JSON outputs of ML anomaly-detection modules.
- `openalex:W3094822300`: Tutorial example: oven temperature observations about a pizza (feature of interest by UUID) with no sensor, property or time triple; the time is in the stream element IRI.
- `openalex:W3113081138`: Sensors and actuators are linked to AADL device components, and SWRL rules characterise them.
- `openalex:W3119640639`: veo:Device is declared a subclass of both sosa:ObservableProperty and sosa:Sampler, and sosa:Sensor is said to represent a feature measured by the network; sosa:Platform specialised as a seismic network.
- `openalex:W3120914367`: The work mints its own individuals in the ssn: namespace (ssn:AoxMercury, ssn:TVOC).
- `openalex:W3126873643`: Each sensor reading is an LDP RDF source typed ssn:SensorOutput served over CoAP, with no observation node.
- `openalex:W3166314457`: A holdsState data property on the dynamic vehicle property gives the current value without instantiating a sosa:Observation.
- `openalex:W3166368427`: Alignment only: weather station deployment details aligned with ssn:Deployment, co-iot entities with ssn:Platform; m3-lite quantity kinds reused.
- `openalex:W3166728768`: SOSA terms are used as NGSI-LD relationships in JSON-LD entities alongside SAREF4EE and M3-lite properties.
- `openalex:W3172699908`: RDF-star detection and tracking triples annotated with sosa:resultTime (frame index) and a score, without sosa:Observation individuals.
- `openalex:W3177319477`: Observations subclassed per meaning and rule outcome (ExhibitProximityObservation, ObservationToHighLevelEnergy) with SWRL rules deciding lamp brightness.
- `openalex:W3180800754`: Mobile sensors whose observations are coordinates (m2ssn:MobileSensor); complex event detection over multimedia sensor observations.
- `openalex:W3184451757`: Calibrated sensors carry a dynamic transfer model whose parameters have units and uncertainties, with covariance matrices encoded in MathML.
- `openalex:W3200558953`: The feature of interest is a node per property and location (tempFOI/location/001); about 80 to 90 triples per observation.
- `openalex:W3201971413`: The patient wearing a sensor is modelled as the platform that hosts it; situations detected by C-SPARQL aggregates over windows.
- `openalex:W3203151633`: Queries use 2011 SSN terms (observedBy, observationResultTime, hasValue) under the 2017 ssn: namespace, with iot-lite for quantity kinds and devices.
- `openalex:W3205282433`: The ontology invents SOSA names (sosa:Observable, sosa:hasmadeBySensor, sosa:Longitude) and makes Observation a subclass of feature of interest; procedures subclassed into Actuation, Sampling, Publishing, Composing.
- `openalex:W3211466183`: ssn:hasSubSystem is reused as a generic part-whole relation between industrial entities and concepts generated from data-lake labels (385 links extracted).
- `openalex:W3212446860`: Cyber-twin ontology: machine automation programs and data translators are subclasses of sosa:Procedure, machines link to sensors, actuators and platforms by own properties.
- `openalex:W3212945135`: System capabilities (operating power range, response time, measurement range) describe the sensors.
- `openalex:W3214742825`: The work mints its sensor, property, feature and observation IRIs in the sosa: namespace (sosa:se-0004). Rules over observations in LARS compiled to Flink.
- `openalex:W3214988970`: Observations and observation collections aligned with an event ontology: collection members as sub-events, wasOriginatedBy as cause event.
- `openalex:W3215556764`: Observations carry a trust score (ts) and a description target; JSON-LD messages per spatial entity.
- `openalex:W3216349317`: Instrument interfaces are platforms that host sensors and actuators, while the instrument links its components by an own property.
- `openalex:W4200036868`: A GraphQL interface navigates platform, hosts, madeObservation; the room itself is the platform.
- `openalex:W4200131824`: Sensor capabilities with ssn-system:Accuracy, Resolution and Condition using schema:unitCode; thresholds attached to carrier properties and SPARQL rules annotating exceedances.
- `openalex:W4200424421`: SOSA classes referenced from OpenAPI schemas by an x-refersTo annotation (a smart door as sosa:Actuator).
- `openalex:W4205494988`: madeLastObservation is a subproperty of sosa:madeObservation for the latest result; sosa:hosts relates appliances to ingredients they contain; SWRL rules pick the actuator for a cooking step.
- `openalex:W4205929117`: Own terms are minted in the sosa: and owl: namespaces (sosa:hasOccuredAt, owl:hasObservationValue); rooms are platforms; results are activity labels used in SWRL/SQWRL rules.
- `openalex:W4206760768`: Only class alignments between ontologies (SSN/SOSA Sensor, Procedure and FeatureOfInterest made equivalent to OEMA, OntoWind and SAREF classes); no instance data shown.
- `openalex:W4210288813`: Features of interest are locations (station site, hypocentre); a data point has one to three axis components; collections of collections (matrix of arrays).
- `openalex:W4210623388`: Neural networks and CEP rules are described as s3n:Algorithm procedures with ssn:hasInput/ssn:hasOutput subclasses and memory requirements as ssn-system conditions, inside WoT Thing Descriptions.
- `openalex:W4212982773`: Observations subclassed per kind (TargetPosition, QualityObservation); quality observations take another observation as feature of interest. Procedures are individuals of a sosa:Procedure taxonomy.
- `openalex:W4220838552`: Each observable property declares the observation type it takes as value (semic:observationType), observations are subclassed per type (occupancy observations), and static properties hold literal values.
- `openalex:W4226190403`: Models written in YAML and converted to N-Quads to generate edge deployments.
- `openalex:W4226271820`: SOSA classes used only as qb:concept of Data Cube dimensions and measures, combined with SKOS concepts.
- `openalex:W4229018183`: Data-quality assessments are attached per observation through idqa:qualityOfObservation, a subproperty of ssn-system:qualityOfObservation, after SHACL validation; the IoT device collecting data is called a sosa:Sampler.
- `openalex:W4229052159`: Process steps and transformation processes are subclasses of sosa:Actuation, performed by sosa:Actuator (PO2:Material) with sosa:Procedure (PO2:Method); observations are attached to steps.
- `openalex:W4237246775`: Alignment axioms only (SOSA to PROV-O, OBOE, BCO/OBI/BFO), no instance data. oboe:Measurement is made equivalent to sosa:Observation and an OBOE observation groups measurements through rdfs:member; ssn:Property is aligned to bfo:Quality.
- `openalex:W4242054492`: Proposes to treat sosa:Observation, sosa:Actuation and sosa:Sampling as subclasses of dcat:Dataset to attach DUV user feedback for a GEO label.
- `openalex:W4283319002`: Weather stations are subclasses of both geosparql:Feature and sosa:Platform; duration-specific interval classes reused for all observations.
- `openalex:W4283753507`: A data acquisition system class (DAS) implements the procedure and is connected to sensors.
- `openalex:W4285112131`: Observations attached to stations by wep:madeByStation rather than to sensors; interval classes by duration reused for all observations. Qualitative values as SKOS collections of WMO codes.
- `openalex:W4285328224`: Maps its SensorObservationValue concept to sosa:SensorOutput, a term SOSA does not define.
- `openalex:W4293149060`: Collection-level metadata: properties set on an ObservationCollection (result, feature of interest) are shared by its members; the feature of interest comes from an external vocabulary (OIEAU).
- `openalex:W4296913163`: sosa:Platform is made equivalent to WoR:Environment, and devices and platforms expose Web resources through an own Exposes relation; no observation data shown.
- `openalex:W4297042567`: Invents ssn:-prefixed data properties for weather variables (ssn:Temperature, ssn:WindSpeed, ssn:relativehumidity) and object properties (ssn:area).
- `openalex:W4297147174`: The work proposes its own BOP ontology (bop:Executor, bop:Execution, bop:Property, bop:FeatureOfInterest) generalising the SOSA pattern, with bop:hasSimpleResult and property levels, rather than instantiating SOSA.
- `openalex:W4302773371`: MCSO aligns to SSN mostly by equivalent classes (loose coupling); observations are grouped by DL-defined subclasses using usedProcedure to a campaign; sensor specifications (resolution, range) carry UO units.
- `openalex:W4303183291`: Observations linked to executed process tasks by a CONSTRUCT rule (meta:observedOn) comparing resultTime with task start and end on the hosting platform.
- `openalex:W4312327889`: A processing step loosely linked to sosa:Observation and sosa:Sample, Procedure being judged broader.
- `openalex:W4312390026`: Neural network models described as S3N procedures with ssn:hasInput/hasOutput and procedure features whose conditions (RAM, Flash) carry schema:value and schema:unitCode with OM units; matching models to devices by system capabilities.
- `openalex:W4313400144`: SOSA properties are borrowed onto own classes bfp:Observation and bfp:Record (a device status), with no sosa:Observation or sosa:Sensor; devices link to their observations by own bfp:hasObservation / bfp:hasRecord.
- `openalex:W4316659945`: Quality-of-context criteria and min/max interpretation thresholds are attached to observable properties.
- `openalex:W4320488768`: Virtual sensors and actuators (vhbieo:VirtualSensor) for immersive virtual environments next to in-situ ssn:Sensor; survey answers treated alongside observations as data of an occupant.
- `openalex:W4320802684`: SSN classes (ObservableProperty, Sensor) are reimplemented as Python graph-object classes stored in Neo4j, with methods named after SSN properties.
- `openalex:W4321107447`: In the generated Jena rules sosa:Sensor is used as a predicate whose value is a sensor kind literal ('Pressure', 'PIR').
- `openalex:W4322766180`: Context attributes (user activity, location, emotion) are made equivalent to sosa:Observation.
- `openalex:W4323338757`: The manufacturer's normal output range is an ssn-system:MeasurementRange capability; a robot path is a procedure linked to the sensor by ssn:implements, used to choose a fallback sensor.
- `openalex:W4323361161`: A storm track is a collection of tracklet collections, each tracklet a sample point with time, location and observed attributes; damage types are observed properties of storm events.
- `openalex:W4361802507`: SOSA, QUDT and D-SI terms used as keys of JSON metadata attached to HDF5-style data groups, with madeBySensor pointing to a string.
- `openalex:W4362474450`: sosa:madeBySensor is attached to a qudt:Quantity data set in JSON metadata of an HDF5 file, with no sosa:Observation; uncertainty given by qudt:standardUncertainty.
- `openalex:W4367319156`: Observations link to the weather station by an own property wep:madeByStation instead of a sensor, and are subclassed (weo:MeteorologicalObservation).
- `openalex:W4377098706`: Observations are also EWE events and actuations EWE actions (vlctas:ObservedEvent, vlctas:TriggeredAction) for rule-based automation; the property class is both observable and actuatable.
- `openalex:W4378574480`: No observedProperty: the quantity is encoded in the observation IRI (urn:dev:mac:…/current, …/voltage), and a sosa:hasUnit term not in SOSA is invented; the JSON-LD serves as a baseline for CBOR templates.
- `openalex:W4379800884`: sosa:Procedure used for the steps of actuations; locations of physical entities through a geo:Location class that GeoSPARQL does not define.
- `openalex:W4381786701`: A hardware device is one wot:Thing typed both sosa:Sensor and sosa:Actuator; user preferences on WebThings properties are matched to actuators.
- `openalex:W4382358393`: Actuations target an ActuatableProperty such as Email and are triggered by ContextAwareRules over observations; an actuator executes only one actuation. Gateways and Groups modelled as sosa:Platform.
- `openalex:W4383681962`: Sensor capabilities with SSN systems module (ssn-system:Range, ssn-system:Frequency) whose values use bop:hasSimpleResult; custom ranges inserted by SPARQL for outlier detection.
- `openalex:W4383682001`: One observation node per sensor acts as a template (no result value, no time) holding the real-time data key and topic; time series stay outside the graph.
- `openalex:W4384695933`: Queries mint terms in the sosa: namespace (sosa:PointID, sosa:Temperature, sosa:MuseumPoint) and attach sosa:hasResult directly to properties (udeo:availableBikeNumber sosa:hasResult ?x).
- `openalex:W4385164309`: SOSA is mapped into a city information model by SWRL rules (sosa:Sensor(?x) -> cim:Sensor(?x)), and Brick points are linked to sosa:Observation.
- `openalex:W4385492113`: Social media posts are modelled as observations made by users as sensors.
- `openalex:W4386420804`: An extra PO2:hasObjectOfInterest names the object observed within the feature; sensors and actuators may be human agents (a tasting panel).
- `openalex:W4387819602`: Each dataset record (soil sample, image, GPS fix) becomes an observation individual (Soil_ID, Image_ID); taxonomy classes used for animal features.
- `openalex:W4388144214`: Observations (user inputs or meter readings) feed a PROV chain of emission calculation steps; the quantity kind sits on the result rather than an observed property.
- `openalex:W4388540746`: sosa:isObservedBy links observations to gateways (the property is meant for observable properties); observations are presence intervals derived from image interpretation.
- `openalex:W4388720837`: Lists ssn:PowerConsumption among SSN core entities, a term that SSN does not define, with legacy ssn:ObservationValue and ssn:SensorOutput.
- `openalex:W4390098492`: In a MERODE domain model, a Device class generalises Sensor and Actuator and a Device Usage class generalises Observation, Actuation and Sampling; an own Platform Deployment ties a platform to one feature of interest.
- `openalex:W4391093128`: Uses non-existent SOSA terms (sosa:madeObservation, sosa:hasObservableProperty, sosa:isObservedBy) and ssn:Device as a subclass of ssn:System; a controller regulates observable properties (priv:controls).
- `openalex:W4391684103`: The patient is the feature of interest of the observations, queried through sosa:isFeatureOfInterestOf.
- `openalex:W4391713859`: The observation module is centred on FeatureOfInterest and ObservationValue (an SSN 2011 class) mixed with SOSA, OWL-Time and OM/QUDT terms.
- `openalex:W4393067627`: An ssn:Deployment stands for a building and is linked to beacons by an own namespace property rather than ssn:deployedSystem.
- `openalex:W4393237783`: Instance IRIs are written under SOSA-like prefixes (sosa:Observation/…, sosa:Sensor/DHT11); each observation carries a blockchain hash and a trustability score, and SHACL shapes check observation quality.
- `openalex:W4394000017`: Inspections as sosa:Procedure (eurotl:InspectionActivity) used by condition observations; an agent takes the sensor role.
- `openalex:W4396874565`: Observations subclassed per quantity (TempValue, HumidityValue, CO2level); sensors linked to observations by own per-quantity properties (:hasSmokeValue); SWRL rules over results raise fire risk.
- `openalex:W4399602188`: Monitored entities such as machines and patients are typed ssn:System and their sensors are subsystems. Properties are the items of a dashboard recommender.
- `openalex:W4400484626`: An RL agent annotates environment streams with SSN observations of process properties (waiting time of an order).
- `openalex:W4403524913`: Individual animals (southern elephant seals) are modelled as sosa:Platform hosting satellite tags; time, space and units are said to use OWL-Time, GeoSPARQL and QUDT but are not shown in data.
- `openalex:W4404116920`: Ground motion represented as sampled time steps with a quantity kind and a direction (NS, EW, V).
- `openalex:W4404238720`: A SWRL rule types the sensor itself as the observation (Observation(?sensor)); SSN/SAN terms are reimported with own properties (hasSpot, hasState, hasValue) and converted to Drools rules.
- `openalex:W4404611367`: Sensors and algorithms point to OBOE characteristics (orka:observesCharacteristic) rather than sosa:observes; a SWRL rule makes the hosting robot the feature of interest of proprioceptor observations.
- `openalex:W4404838075`: The monitored battery cell is a host of its sensors rather than a feature of interest; no hasFeatureOfInterest shown. Anomaly causes derived by rules over pairs of observations.
- `openalex:W4405283898`: Observations subclassed per theme (VulnerabilityObservation); survey and census data modelled as observations on regions or S2 cells. Integration relies on the spatiotemporal features rather than shared observable properties.
- `openalex:W4405306282`: Knowledge graph stored as a Neo4j property graph; observation subclassed per property kind (SpatialPositionObservation).
- `openalex:W4405733766`: Measurement samples (DICMeasurementSample, a subclass of sosa:Sample) are the entry point from which observations and results are reached; calibration outputs are linked to procedures with prov:wasGeneratedBy.
- `openalex:W4405785718`: Time granularity terms invented in the ssn namespace (ssn:Day, ssn:Hour).
- `openalex:W4405889325`: Sensor functions are sosa:Procedures with ssn:Input/ssn:Output arguments; SHACL metadata profiles validate every node; system parameters are ssn:Property of components.
- `openalex:W4406062764`: Static design properties carry value and unit directly (brick:value, brick:hasUnit) instead of observations; sensors point to external time series by ID (Brick ref:hasTimeseriesID). SHACL shapes validate sosa:Actuator descriptions.
- `openalex:W4406396774`: Own foo: copies of SOSA classes aligned by owl:equivalentClass; observable properties double as datatype properties carrying values; trail-camera images given by a path URI.
- `openalex:W4406810616`: Observations and results subclassed per quantity (TemperatureObservation, TemperatureResult); qudt:QuantityValue and geo:Geometry declared subclasses of sosa:Result; stored in Neo4j.
- `openalex:W4406834793`: Features of a cyber-threat ontology are mapped to SOSA classes (Observation, Actuation, Procedure, Platform).
- `openalex:W4406853000`: Assets of a production chain described as accomplishing procedures whose results trigger events; no SOSA instance data shown.
- `openalex:W4407272113`: sosa:isHostedBy combined with an own hasComponent hierarchy to trace anomalous data streams back to components and failure modes.
- `openalex:W4407366854`: A virtual sensor implements a detection query; events and states derived from observations with causal knowledge between state types and topological relations through hosting.
- `openalex:W4407919415`: Process-mining event log entries are modelled as a subclass of sosa:Result with case, activity and timestamp attributes.
- `openalex:W4407919831`: Observation IRIs minted from the OPC UA nodeId and the timestamp; RML stream mapping from OPC UA.
- `openalex:W4408472960`: dcat:Dataset declared a subclass of sosa:Result to point to files and external databases (dcat:DataService) from observations.
- `openalex:W4409191336`: The work models IoT measurements with SAREF (saref:Measurement, saref:hasValue, saref:isMeasuredIn), not SOSA/SSN; SOSA is only compared and declared as a prefix.
- `openalex:W4410794932`: Indoor-positioning observations of workers have locations as their values and are chained by dicp:hasNextObservation; observedProperty points to saref:Property in the SAREF alignment.
- `openalex:W4411369836`: Observations are satellite images (sors:SatelliteImage equivalent to sosa:Observation) subclassed per satellite (LandsatImage, SentinelImage, MODISImage); results are subclassed per land-cover percentage.
- `openalex:W4411440164`: sosa:Observation and saref:Measurement are mapped to the work's own observation and measurement classes for construction quality inspection.
- `openalex:W4412430508`: Sensed data are drone:MissionSensorData mission event elements rather than sosa:Observation.
- `openalex:W4413049290`: Smart-building algorithms (forecasting, MPC) are subclasses of sosa:Procedure, with their inputs and outputs as subclasses of ssn:Input and ssn:Output linked to Brick sensors.
- `openalex:W4413796311`: Signals (time series kept outside the graph) are attached to hosted devices by properties such as ev:ActivePower and queried with a SPARQL extension instead of observations.
- `openalex:W4414433193`: Only sosa:Procedure and ssn:System are reused, as concepts of a civil complaint ontology for digital-twin government.
- `openalex:W4414448776`: Dataset-level metadata model: dcat:Dataset linked to sosa:ObservationCollection, with FeatureTheme and PropertyTheme SKOS concepts as thematic abstractions beside FeatureOfInterest and ObservableProperty.
- `openalex:W4414930035`: Design choices from an alignment exercise: ssn:Property used in place of sosa:ObservableProperty, sosa:isHostedBy linking a sensor to the room it is installed in.
- `openalex:W4415050885`: Observation classes per property kind, restricted with owl:allValuesFrom on sosa:observedProperty; static property values attached directly to the property (osph:hasPropertySimpleValue).
- `openalex:W4415398083`: Only SOSA properties are imported, not its classes; observations are subclassed into NumericObservation and StatusObservation, and sensors are linked by own correlation and influence properties for diagnosis.
- `openalex:W4415507007`: The fused value and its standard deviation go on the result (qudt:standardUncertainty); observations are then translated into logical facts for regulation checking.
- `openalex:W4415974463`: Observations subclassed per quantity (ex:TemperatureObservation); the C-SPARQL queries re-mint SOSA properties in the work's anomaly: namespace (anomaly:hosts, anomaly:madeObservation, anomaly:hasSimpleResult).
- `openalex:W7116695360`: Observations kept as rows of a time-series database with sosa:madeBySensor, quantity, unit, value and timestamp columns, federated with Brick/BOT graphs.
- `openalex:W7117991961`: sosa:hasSimpleResult used with a structured QUDT node instead of a literal.
- `openalex:W7118161186`: Names an own class in the sosa namespace (sosa:ObservableVehicleProperty) and own relations observesVehicleProperty; ADAS as ssn:System subclass for forensic investigation.
- `openalex:W7125215157`: Measurement and Instrument subclass sosa:Observation and sosa:Sensor; diagnoses as prov:Activity over measurements; designed for relational databases.
- `openalex:W7126047962`: AI models are sosa:Procedure instances with ssn:hasInput/ssn:hasOutput and REST endpoints; controllers typed with invented terms in the sosa namespace (sosa:MachineAutomation, sosa:MachineSetting).
- `openalex:W7126368824`: Observation and its OM measure merged into one instance typed sosa:Observation and om:Measure.
- `openalex:W7127082105`: Actors and human-centricity factors are linked directly to sensors by isObservedBy, and sensors send outputs to an own Data class, without sosa:Observation.
- `openalex:W7127571839`: A material sample (sosa:Sample) is the centre of the schema, with a sampling event, a sampling site for the spatial context, curation activities and relations to other resources; a LinkML schema, no RDF instance shown.
- `openalex:W7128318862`: SensorThings API entities mapped to SOSA with OWL functional and inverse-functional constraints to detect inconsistencies; result and unit arrays of MultiDatastreams lose their pairing when flattened.
- `openalex:W7128925937`: hasSimpleResult mapped as subproperty of domain quantity properties (Length, Volume); SWRL rules over observations infer hazards.
- `openalex:W7134970444`: Measurements hang off asset states (AssetState → Measurement) with an uncertainty value; measurement IRIs embed probe and timestamp.
- `openalex:W7139934035`: Observations carry key-value tags (<hasTags>, <keyTag>, <keyValue>) used to select time series for AI services.
- `openalex:W7143478328`: Observation classes defined by a value restriction on hasSimpleResult (ex:HighTempObservation) for anomaly classification; sosa:observes points to a unit.
- `openalex:W7147154016`: A textbook example in which the device is a platform hosting its sensing element; the observation shown has no sensor or property link.
- `openalex:W7148571504`: Quality of Observation attributes (qoo:hasQoO) attached to observation values; virtual sensors described with SSN capabilities.
- `openalex:W7148666581`: Sensor subclasses for mobility (hssn:MobileSensor, hssn:StaticSensor) and a coverage area per sensor, tracked over time with past coverage areas and OWL-Time entities.
- `openalex:W7148860605`: SWRL privacy rules over observations, which are matched to terms of service by an own string observation_name and given data categories and privacy rules.
- `openalex:W7148864503`: Old SSN sensors in a process-model knowledge base carry energy-cost attributes as literals containing the unit name, queried with a regex on "milliwatt".
- `openalex:W7149001482`: Each VSS signal becomes a property class with matching sensor/actuator classes; vehicle branches are features of interest. Contextual driving facts (traffic flow, visibility) are modelled as observations.
- `openalex:W7149348416`: Observations subclassed per property instance (irrig:Soil30cmDepthMoistureObservation…). caso:Observation marks aggregations with prov:wasInformedBy to its inputs, caso:Deduction gives a caso:State as result.
- `openalex:W7149550705`: SSN/SOSA classes re-classified under BFO/CCO (sosa:FeatureOfInterest under an information content entity, ObservableProperty under bfo:quality); sensor kinds defined as subclasses (temperature sensor, pressure sensor).
- `openalex:W7149554352`: SWRL rules over observations detect abnormal situations; C-SPARQL stream reasoning over observations; alignment of SOSA to DUL.
- `openalex:W7151002360`: Own classes declared equivalent to SOSA ones (ucsn:DataValue to sosa:Observation, ucsn:SensedInformation to sosa:ObservableProperty), with a sensing status per property recording sharing with data consumers; past locations of mobile sensors.
- `openalex:W7151043122`: A human observer (foaf:Person) is the sosa:Sensor; the procedure forest_mensuration is a sosa:Procedure. Experimental plots are seen as sosa:Sample.
- `openalex:W7151608427`: The work's ContextAttribute class is declared equivalent to sosa:Observation.
- `openalex:W7152004493`: SHACL rules compute derived values and aggregates over observations with automatic unit conversion; features are platform parts linked by hasPart.
- `openalex:W7152014930`: Per-quantity object properties (hasTemperature, hasPressure, hasWindForce, belongsObservation) and value data properties replace the generic observedProperty pattern.
- `openalex:W7152083400`: ssn:Observation is aligned as a subclass of prov:Entity and orbac:Object, and sosa:hasResult as a subproperty of prov:generated, for usage-control policies on observations.
- `openalex:W7152090635`: Controllers and predictors implement procedures (pep:implements) and optimise properties of HVAC spaces as features of interest.
- `openalex:W7152396788`: Zones and devices are subclasses of a platform and nest through sosa:hosts; quality indicators are attached to observations or sensors.
- `openalex:W7153352983`: ssn:observedProperty given on raster scientific field layers (ex:BaseLayer with rows, cols, WKT bbox) rather than on observations.
- `openalex:W7160320950`: ssn:observes links a service or its telemetry to a seas:Process rather than a sensor to a property.
- `openalex:W7161559072`: Observations subclassed per feature type (RoadObservation, IncidentObservation, ActivityObservation); a shortcut property from road to length besides the observation.
- `openalex:W7163808232`: Observation events carry sensor and timestamp so that precise measurements are fetched from a time-series database on demand.
- `openalex:W7165866707`: Observation subclasses per quantity (EnvironmentTemperatureObservation) and a local aal:madeBySensor subproperty used in place of sosa:madeBySensor.
- `openalex:W7167743913`: TBox only: SEAS energy forms beside sosa:ObservableProperty, ethic modes attached to ssn:System, devices linked to sensors by ioto:hasSensor.
- `openalex:W7171320046`: Actuator modules linked to agricultural properties by ssn:forProperty; observations named by kind (NDVIObservation) as individuals.
- `openalex:W7202089242`: Observations subclassed by epistemic level (EvidenceObservation, PerceivedHazardObservation, PropertyEstimation); reliability attached to results; revisable estimated event states with OWL-Time.
- `openalex:W7204787473`: Services are mapped to sosa:Sensor and sosa:Actuator and compute-continuum nodes to sosa:Platform in the base TBox.
- `openalex:W7214725585`: Results linked to evidence resources (photos, videos, reports) and data segments; crack states model the temporal evolution of the feature.
- `openalex:W7214739339`: Spatial relations link sensors, observable properties and bridge components, with space types from SPOT.
- `openalex:W7221564856`: Observations carry no feature of interest; they reach the machine through the sensor and the own property am:isAttachedToMachine. sosa:Sensor and sosa:Actuator are declared subclasses of an own am:Device class to keep OWL 2 RL.
- `openalex:W7225094972`: Observations are evidence (EvidenceObservation) clustered into maintained hazard events; one feature of interest per incoming bundle.
- `openalex:W7225115631`: Observations subclassed per modality (TimeSeriesObservation, ImageObservation, ComputedObservation derivedFrom sources); SWRL rules compare simple results with specification limits bound to the same observable property; DetectionMethod subclasses sosa:Procedure.
- `s2orc:116374294`: Property IRIs invented in the ssn namespace; IFC devices linked to sensors by ssn:observedBy.
- `s2orc:12551620`: Old SSN data published from a relational database with D2RQ mappings that generate both the sensor-type classes and the sensor instances.
- `s2orc:129943213`: SOSA is aligned by mapping: sosa:Observation made equivalent to lhr:EnvSSNResource, sosa:madeObservation to a subproperty of lhr:hasResource, sosa:resultTime to lhr:hasObservationDateTime.
- `s2orc:13791319`: Observations are typed per quantity with a class minted in the sosa: namespace (sosa:HeartRateObservation); no observedProperty is given.
- `s2orc:13793673`: Signals not produced by any sensor get a vss:VirtualSensor to fit the SOSA pattern; observations are abstracted into step:Episode instances of semantic trajectories by rules.
- `s2orc:149455273`: Legacy SSN extended with a wearable sensor platform subclass placed on body parts, aligned with BFO and HL7 FHIR.
- `s2orc:153315088`: Quality-of-context indicators (precision, freshness) attached to observation results.
- `s2orc:158938101`: Observations link to their monitoring station by an own property (MonitoringStation) rather than through a sensor or feature of interest; SQWRL rules raise pollution alerts over observations.
- `s2orc:15910378`: Capability attributes take instances or classes as domain and range (unioned with rdfs:Class), revising SSN 2011 measurement capabilities with conditional accuracy.
- `s2orc:195791381`: Rules over observations derive new facts (off-limit areas); an observation result can be a person IRI.
- `s2orc:198930586`: Data-quality tags attached to observations (hasObservationTag) and a CorrectedValue subclass of ssn:ObservationValue linked by hasCorrectedValue; SWRL rules classify suspect data.
- `s2orc:202764762`: One property individual is typed both sosa:ObservableProperty and sosa:ActuatableProperty; Web Things are typed sosa:Sensor or sosa:Actuator to support discovery queries.
- `s2orc:202767588`: Procedures described as plans: EP-Plan plans extend ssn:Procedure (P-Plan lineage) and are aligned with the device (ssn:System) that follows them.
- `s2orc:202781247`: Rules over observations infer domain facts (an area with high CO becomes :OffLimitArea); SHACL schemas over SOSA triple patterns.
- `s2orc:204242377`: Observations are indexed into a time-series store by declared predicate patterns (value, time, sensor, reading type).
- `s2orc:204754912`: Device descriptions as ontology templates whose subsystems (ssn:hasSubSystem) and producible observations are declared by class restrictions.
- `s2orc:204984908`: Old SSN (ssnx) with observation subclasses per event type (?ob rdfs:subClassOf ssn:Observation); sensors are event services discovered by observed property and feature; location values are observation results.
- `s2orc:20807723`: Uses SSN 2011: a measurement (control point) observation has per-phenomenon observations as parts via dul:hasPart.
- `s2orc:209073179`: Built on SSN 2011 (ssnx namespace); the observation IRI embeds the indicator and the month (ex:NoiseSensorObservation_LdInterval201704) for a monthly average.
- `s2orc:209353621`: SAREF and SOSA combined: measurements subclassed per quantity (IndoorTemperatureMeasurement) carry sosa:hasSimpleResult; SWRL rules compare them with occupants' comfort settings to set actuators.
- `s2orc:209382758`: Stream services (enrich, aggregation, join) modelled as auxiliary ssn:SensingDevice instances cloned from input sensors; time granularity via ssn:ResponseTime measurement property with a unit.
- `s2orc:211024141`: Observations as time-annotated named graphs in RDF streams consumed by real-time agents; misspelled sosa:simpleResult.
- `s2orc:211044727`: Security metadata (access control, authentication provider) attached to IoT-Stream streams generated by SOSA sensors.
- `s2orc:211113477`: The IotStream is the root node that carries sensor, quantity kind, unit, location and quality, so stream observations stay minimal; observations can be outputs of an analytics process.
- `s2orc:211475699`: Aggregators typed dashb:AggregatedObservableProperty; units and data types on a separate metric node; sensor annotations on a Web Thing gateway drive dashboards.
- `s2orc:212850498`: GEO label facets are computed from SOSA/SSN graphs, e.g. user feedback attached to a sosa:Observation with duv:hasUserFeedback.
- `s2orc:212930909`: Measurements stored as (feature, property, time, value) tuples in a time-series database and mapped to SOSA observations on demand (Linked Time Series Data).
- `s2orc:216215748`: Observation subclasses per property and feature defined by necessary and sufficient conditions (irrig:Soil30cmDepthMoistureObservation); deductions as caso:Observation subclasses linked to inputs with prov:wasInformedBy; software computing averages typed sosa:Sensor.
- `s2orc:218690779`: The feature of interest is a location node (location/001); about 80 to 90 triples per observation.
- `s2orc:218901255`: Alignment of the W3C Thing Description with SSN: things may be systems, platforms or features of interest, connected devices are modelled as features of interest, and property affordances relate to ssn:Property through ssn:forProperty, inferred from @type tags by rules.
- `s2orc:218910879`: A merged vehicle observation carries several values (speed, acceleration) through subproperties of hasSimpleResult; road sections are a subclass of sosa:Sample linked by a subproperty of sosa:hasSample.
- `s2orc:219404877`: The motor is both platform and feature of interest of its consumption sensor; sensor thresholds (sn4e:maxValue) are stored on the sensor.
- `s2orc:219741281`: sosa:Sensor is declared a subclass of bot:Element so rooms contain sensors; evolving room properties use OPM property states.
- `s2orc:219878952`: An AnonymizationProcedure subclass of sosa:Procedure records how personal information was removed; observations are mapped to access-control Resources.
- `s2orc:220042800`: SWRL rules over observation results flag abnormal vital signs; a vital sign is linked to its observations by an own VitalSignhasObservation property.
- `s2orc:221207926`: Stations are subclasses of both sosa:Platform and geo:Feature; an interpolator ssn:System is hosted on grid-cell platforms; the graph is virtual (Ontop mappings over SQL).
- `s2orc:221911457`: Feature, phenomenon time and provenance (raster file) sit on the collection, members carry only property and result; collections are also dcat:Dataset and prov:Entity; feature is a version of a territorial parcel.
- `s2orc:224949022`: Deployments stand for areas of a laboratory (ssn:WestSideMaldiTof), and the work mints its own individuals in the ssn: namespace (ssn:SN_22, ssn:DHT22_22).
- `s2orc:225300711`: 2011 SSN output/value pattern (SensorOutput, ObservationValue, isProducedBy) specialised per quantity (TrafficIntensity...).
- `s2orc:226355839`: Readings below the threshold are not stored, so the collection carries aggregate statistics (average, count); constraint evaluations (EP-Plan) are based on the collection; observations are also prov:Activity.
- `s2orc:226599725`: Observable properties modelled as a DUL:Role that an object property plays given the sensing capabilities, not as an intrinsic quality.
- `s2orc:227129720`: A whole observing campaign (EHT VLBI) is one sosa:Observation linked to an observatory and to observational data.
- `s2orc:229152318`: The query links sensors to observations with sosa:observes instead of madeObservation; unit heterogeneity (bar, hectopascal) resolved at query time.
- `s2orc:229331992`: Access permissions are attached to observable and actuatable properties rather than to observations; ssn-system property subclasses carry values via dul:hasDataValue; observation quality as subclasses (Poor, Fair, Good).
- `s2orc:229484088`: Rules infer a characteristic index (NDVI, NDWI) of an image from the bands it observes; CharacteristicIndex is an ssn:Property that is not observable.
- `s2orc:232131679`: The IoT-Stream extension adds stream entities between sensors and observations for search and indexing.
- `s2orc:232288965`: sosa:phenomenonTime used on features of interest to date planting and presence; experimental plots as sosa:Sample; Jena rules derived from properties.
- `s2orc:232385659`: Calibrated-sensor classes combine SOSA with the digital SI model (D-SI) for measurement uncertainty and calibration models.
- `s2orc:234142797`: An animal (southern elephant seal) is the sosa:Platform; location is itself observed, with a WKT geometry as the result.
- `s2orc:234838325`: Observations are subclassed by value type (BooleanObservation, DoubleValueObservation), and sensor classes carry axioms fixing what they observe and which observations they make.
- `s2orc:235357145`: Station classes are subclasses of both sosa:Platform and geo:Feature, populated through a virtual knowledge graph over relational data.
- `s2orc:235359168`: Observation, Sensor and Result each subclassed per climate factor (ca:[?]Observation). The work lists sosa:isMadeBySensor, a term that does not exist.
- `s2orc:235546428`: Dataset metadata distinguish the feature of interest (the sample) from the ultimate feature of interest (the sampled real-world phenomenon) of ssn-ext, to support domain-neutral search.
- `s2orc:237489732`: Mobility stations, vehicles and charging columns are themselves sensors; their sensor records bundle a state (SKOS concept), a timestamp and a series of sosa:Observation.
- `s2orc:237937868`: Observation subclasses (HeartObservation, MovementObservation, WalkingFeature) defined by OWL equivalent-class restrictions on observedProperty and feature, so DL reasoning classifies observations; features are abstract individuals (movement, heart) and observations are interpreted through DUL situations.
- `s2orc:238639946`: Quality-of-data indicators are a subclass of ssn:SystemProperty, each with metrics and interpretations, in JSON-LD.
- `s2orc:239029884`: Gateways and LoRa nodes modelled as platforms for connectivity management; hardware vs software sensors.
- `s2orc:239617085`: Machines of a digital twin ontology composed of SOSA sensors, actuators and platforms, with events as machine outputs.
- `s2orc:240576023`: sosa:Observation and saref:Measurement are both aligned to an own Observation class; observations are checked against indoor-condition constraints of construction activities.
- `s2orc:243806774`: Detected anomaly events carry the detector as sosa:usedProcedure and point with ssn:wasOriginatedBy to the sensor properties whose time series triggered them; sensor metadata drive dashboard widget selection.
- `s2orc:244147698`: Automatic ontology alignment maps aras:Sensor to sosa:Sensor.
- `s2orc:244549237`: A bus stop in a route is modelled as a sosa:Sensor, and expected arrival times as observations whose feature of interest is the stop.
- `s2orc:244799183`: Attributes of geographic entities in a narrative map are modelled as observations grouped per entity in a collection whose feature is the map content item.
- `s2orc:244865838`: OM classes are declared subtypes of sosa:Result.
- `s2orc:245054521`: SWRL-style rules classify observations into derived classes (TrustedObservations, ObservationToHighLevelEnergy) and attach trust values to entities.
- `s2orc:245225276`: Observation IRIs minted from the device metric path plus a timestamp by RML streaming mappings.
- `s2orc:245838541`: Raster analysis outputs turned into per-territory observations, with provenance to the source raster through prov:wasDerivedFrom.
- `s2orc:246189192`: Observations are also ewe:Events, actuations ewe:Actions and results ewe:Parameters (task automation); one property class is a subclass of both ObservableProperty and ActuatableProperty; actuators use sosa:forProperty.
- `s2orc:246241572`: Environmental monitoring stations are modelled as sosa:Sampler and their time series as sosa:Sampling, rather than sensors and observations, with per-pollutant value properties.
- `s2orc:246241789`: Attributes of grid-cell features modelled as observations in an ontology design pattern, with RCC8 spatial relations between features.
- `s2orc:246241930`: Observations subclassed per domain (EarthquakeObservation, AQObservation); SHACL shapes validate SOSA data, e.g. one sensor per observation collection.
- `s2orc:246996565`: System capabilities from S3N and the SSN systems module, with RAM and Flash as system properties carrying schema:value and schema:unitCode om:kilobyte; ML model inputs and outputs as subclasses of ssn:Input and ssn:Output.
- `s2orc:247120879`: qb:Observation is declared equivalent to sosa:Observation, merging Data Cube and SOSA; O&M sampling points are subclasses of geosparql:Point.
- `s2orc:247157978`: sosa:resultTime drives window membership of LDP stream containers.
- `s2orc:247158231`: Detected bounding boxes linked to tracked objects with sosa:isSampleOf, asserted by soft ASP rules for video stream fusion.
- `s2orc:247358657`: Instance IRIs are minted under the specification URL (https://www.w3.org/TR/vocab-ssn/Sensor{col3}); a toy weather example for table-to-graph mapping.
- `s2orc:248006013`: Terms are invented in the ssn namespace: ssn:Temperature, ssn:WindSpeed, ssn:relativehumidity as datatype properties.
- `s2orc:248368566`: Cameras are the features of interest of aggregated count observations, the aggregation tool being the sensor; aggregation function given by cot:usingFunction.
- `s2orc:248790886`: sosa:hasSimpleResult applied to the result node rather than the observation; Jena rules over observations for fault detection and control, with Brick points.
- `s2orc:249442873`: Observations are stream events whose materialised inferences are cached by structure; sensors and properties are static background knowledge.
- `s2orc:249586261`: Forecast models are virtual sensors; quantile predictions use 24 sub-properties of sosa:hasSimpleResult (covid-so:point, covid-so:quantile-N).
- `s2orc:249953724`: SOSA/SSN names reused as annotation values in an XES event-log extension (system type, interaction type), with sosa:Sampling read as a set of subsequent observations.
- `s2orc:250305863`: Own ofo: copy of the sensor pattern (Wearable, Feedback, Property, FeatureOfInterest) aligned to SOSA; results may attach to feedback, property or feature; time series stay in InfluxDB behind data points.
- `s2orc:251484894`: An own property (p:sourceStation) links an observation to the weather station it comes from instead of madeBySensor.
- `s2orc:252631393`: ObservableProperty carries the data type of the observed value; each sensor observes one property and each actuator acts on one. Thing extends sosa:Platform; context-awareness rules trigger actuations.
- `s2orc:252976593`: Social media users treated as social sensors (sosa:Sensor) and tweets annotated with sosa:resultTime and the property they report on.
- `s2orc:254754915`: Observations are deliberately kept out of the knowledge graph (BIM-IoTDI) to avoid growth; only sensors, properties and rooms are described semantically, with BOT, IFC and Brick.
- `s2orc:255799616`: The record subject <sosa/sensor/86338> is typed sosa:Weather_Station (a term not in SOSA) yet carries observedProperty and hasSimpleResult; all IRIs minted in the sosa namespace. Tweets modelled as social sensors observing a property.
- `s2orc:256061953`: Quality-of-context indicators (precision, freshness) are attached to the sensor output of each observation.
- `s2orc:256589646`: Datasets are modelled as collections of virtual entities whose primary source is a sensor, linked with PROV-O activities such as measurement campaigns.
- `s2orc:258059842`: An own class of collections of EV registrations (ev-ont:ElectricVehicleRegistrationCollection) modelled on sosa:ObservationCollection, without SOSA observations.
- `s2orc:258140669`: A hosts property relates a welding machine to the part it welds; whether it is sosa:hosts is not shown.
- `s2orc:258357266`: Feature of interest is a point IRI with lat/long query parameters; spatio-temporal values kept in a time-series database linked through madeBySensor.
- `s2orc:258377590`: Old SSN ssn:SensingDevice linked by own properties (mmkg:outputs to data, mmkg:hasMeasuringProperty to an own MeasurementProperty class) in a multimodal scene graph; no sosa:Observation.
- `s2orc:258755803`: sosa:Sensor and sosa:Platform used only as prov:Agent of the activity that generated a dataset (DCAT, Data Cube), with no observations.
- `s2orc:258934357`: A Part-Observation-Property design pattern; farm operations with input and output products via ssn:hasInput/ssn:hasOutput.
- `s2orc:259287114`: Per-observation quality assessment results (IDQA vocabulary) attached to sosa:Observation as data properties after SHACL validation.
- `s2orc:259316580`: ssn:Property is used for design parameters of HVAC components (nominal power, nominal efficiency), alongside BOT, PROPS and FSO.
- `s2orc:259443960`: Reuses sosa:madeObservation and sosa:observes in a manufacturing ontology; machines 'host' tools in the prose.
- `s2orc:259588429`: Restricts the range of sosa:resultTime and sosa:phenomenonTime to own transaction-time and valid-time classes; humans and social media are treated as sensors.
- `s2orc:259951234`: Properties are dereferenceable time-varying resources holding the current value; instances of sosa:ActuatableProperty are writable by agents. Brick aligned with SOSA/SSN.
- `s2orc:261011479`: Entity-level alignment of a property-graph model: a SensorProperty entity is aligned with ssn:Observation, and an IoT platform with ssn:System.
- `s2orc:261049310`: RDF-star quoted triples are typed as observations (a frame image, detections, tracklets), each with sosa:usedProcedure pointing to the DNN or tracking algorithm (:Yolo, :KalmanFilter).
- `s2orc:265068586`: The observation pattern is collapsed into one predicate per property and result time (averageHeatingDegreeDaysPerMonthAug2021) pointing directly to the simple result.
- `s2orc:266977430`: ioe:System subclasses ssn:System; agents' preferences are defined on an ssn:Property measured in a site, with a preferred value.
- `s2orc:267419831`: Sensor kinds of the pilot (fibre-optic, acceleration) defined as subclasses of sosa:Sensor.
- `s2orc:267587296`: Observations are subclassed per type of sensor that generated them (four subclasses) and linked to recognised activities.
- `s2orc:268643358`: sosa:hosts/isHostedBy inside WoT Thing Descriptions drive the URI hierarchy of Solid pod containers.
- `s2orc:268681279`: Observation types are subclasses of sosa:Observation with OWL restrictions on result, observed property and usedProcedure; laboratory procedures are both sosa:Procedure and skos:Concept; alignments with ISO 19156.
- `s2orc:269000855`: Each observation identified by a 32-character id; the observation carries value and date as data properties.
- `s2orc:269250307`: Own ontology inspired by SOSA: devices point to observations by hasObservation, and the result (people count) is also copied onto the space entity.
- `s2orc:269315388`: An own ca:MeasurementCode (e.g. ca:TMAX-d combining quantity, aggregation and sampling interval) plays the role of sosa:ObservableProperty, without using SOSA.
- `s2orc:269449040`: A meta-context model mixing old SSN (ssn:Device, ssn:SensingDevice), IoT-Lite and an own iot-context vocabulary is populated by an LLM mapping table columns to concepts, to derive functional dependencies for data cleaning.
- `s2orc:269605375`: ssn:hasProperty links objects of video scenes (scene ontology) to their characteristics in a causal knowledge graph used for link prediction.
- `s2orc:270661728`: IRIs built from relational primary keys of the WoSIS database; SPARQL queries over SOSA graphs used to generate a SensorThings API.
- `s2orc:270888894`: Extends IoT-Stream (StreamObservation, IotStream with sosa:Sensor, QU quantity kind and unit, geo:Point) with patient and health-condition classes.
- `s2orc:271489653`: RDF-star annotates a sensor's hasSimpleResult statement with a certainty value (ex:probability), aggregated by weighted average.
- `s2orc:271710251`: Observable properties carry the file locations of acceptance limits and results; observations link to test reports by an own property.
- `s2orc:272085822`: Observations are event detections whose results are events, with the detection rule as sosa:Procedure; raw readings stay in InfluxDB and the model links each sensor to its InfluxDB instance.
- `s2orc:272260384`: Reuses SSN 2011 through the Global City Indicator Pollution ontology: concentrations link directly to the weather station by ssn:isProducedBy, keeping raw and calibrated values side by side.
- `s2orc:273482761`: Observations subclassed per theme (kwg-ont:VulnerabilityObservation); census and survey statistics modelled as observations of regions and S2 cells; integration through the spatial feature rather than shared properties.
- `s2orc:273501528`: ssn:hasProperty links objects of video scenes to their characteristics in a causal knowledge graph, outside any sensing context.
- `s2orc:273501606`: ssn:hasProperty links objects of video scenes to their characteristics in a causal knowledge graph.
- `s2orc:273502244`: Property chains compose sosa:hasFeatureOfInterest with spatial relations to S2 grid cells, which act as features for gridded data.
- `s2orc:274166430`: The PLC is both a platform hosting sensors and actuators and a system implementing the control procedure, whose input is an observation; attacks compromise features of interest and violate own SafetyProperty nodes.
- `s2orc:275089319`: Observations are subclassed per kind (SpatialPositionObservation, SafetyDistanceObservation from 3D simulation, CVPeopleNumObservation from video AI) and sosa:Observation is itself a subclass of ctx:ExternalContext; quantities are separate qudt:Quantity nodes with unit:KiloGM.
- `s2orc:276449905`: Sensors are omitted when no data layer describes them; observations are validated with generic SOSA-SHACL shapes.
- `s2orc:278697593`: ssn:System given an ethics mode (:hasEthicMode) and privacy attributes from ColPri; SEAS connections between systems.
- `s2orc:279301474`: Test messages use non-standard SSN terms (ssn:hasID, ssn:hasUnit with qu:DegreeCelsius) as inputs to an automatic mapping system.
- `s2orc:280017575`: A knowledge graph merging 2011 SSN and SOSA terms, choosing ssn:Property over sosa:ObservableProperty as the property class.
- `s2orc:281134834`: Laptop hardware components (temperature, pressure, humidity sensors) reuse sosa:Sensor subclasses in a digital product passport ontology.
- `s2orc:281653562`: Replaces sosa:actsOnProperty with an own 'actsOn' relation between Actuator and ActuableProperty after its reasoner inferred Actuation and Actuator equivalent.
- `s2orc:281825082`: Sensors are linked to their observations through a hasResult relation, and threshold readings are tied to building components by an own ContainedIn relation; SOSA is aligned rather than reused directly.
- `s2orc:282443533`: New relations are minted in the sosa namespace (sosa:close, sosa:hasSpatial, sosa:hasTemporal) and inferred by SWRL rules; reconstructed values are a subclass of sosa:Observation.
- `s2orc:283447010`: Metadata nodes attached to observations (mmo:hasMetadata, mmo:Frequency); a SWRL rule infers ssn:isProxyFor from a stimulus; SOSA terms written in the ssn namespace.
- `s2orc:285345129`: An elephant's GPS position is modelled as the result of an observation of an invented sosa:Location property.
- `s2orc:285974086`: Stream payload fields are linked to a sosa:Property (a term SOSA does not define) to tie stream schemas to system capabilities.
- `s2orc:286377782`: SOSA/SSN reduced to a flat event-log schema: observable and actuatable properties merged into one Property, Platform and Deployment merged into a Location concept, feature of interest replaced by the business object of the OCEL log.
- `s2orc:286420799`: Provenance (prov:wasGeneratedBy) held at the observation-collection level; flow paths between subsystems by downstreamOf.
- `s2orc:286634853`: giri:System is a subclass of sosa:System grouping ICT devices, power and cooling subsystems; observations feed sustainability metric instances, and capacities use qudt:QuantityValue.
- `s2orc:286675088`: Planning agents aligned with sosa:Platform, with location and time on agent states.
- `s2orc:287190130`: Observations are subclassed per sensing modality and per satellite product (GIFAPAR_S3_Observation); sosa:Platform declared a subclass of geosparql:Feature.
- `s2orc:287479978`: The feature of interest is a location node whose IRI encodes the coordinates (oim-feat:loc_70.41_0.0).
- `s2orc:287774152`: Observations as blank nodes scoped per message; sosa:resultTime proposed as the version order of a message profile.
- `s2orc:289217324`: Continuous sensing and actuation activities (ado:SensingActivity) are linked by own properties instead of sosa:observedProperty / madeBySensor, to avoid being inferred as observations; sensors and actuators are aligned as ep-plan:Agent.
- `s2orc:289331172`: SSN/SOSA device instances are combined with GDPRtEXT privacy-by-design concepts.
- `s2orc:289604411`: MQTT packets mapped to SOSA terms: grip position and correction points as properties, actuation signals with correction offsets as simple results.
- `s2orc:289720113`: An own observation-like class pdto:AtomicInformation links a product (pdto:hasFeatureOfInterest) and an ssn:Property (pdto:clarifiedProperty) to a value, instead of sosa:Observation.
- `s2orc:290321672`: Symbols of a learned timed automaton are typed sosa:Observation or sosa:Actuation; the work writes sosa:ActuableProperty, a term that does not exist.
- `s2orc:290690911`: Observations are workflow activity instances (vpd:SensorActivityInstance subclass of sosa:Observation and wild:ActivityInstance), sensor and machine activities are subclasses of sosa:Procedure, and DCAT datasets link to observations through prov:wasGeneratedBy.
- `s2orc:290852569`: Domain classes are placed under BFO, QUDT, SOSA and MASON parents; process parameters are QUDT quantity kinds while measured quantities are observable properties.
- `s2orc:290956322`: SOSA and QUDT terms appear as key-value pairs in Avahi (mDNS) service advertisements so that oneM2M devices discover each other without a controller.
- `s2orc:291217620`: Devices are ssn:System individuals whose continuous behaviour is given by ODE records; variables carry an ssn:symbol property that SSN does not define.
- `s2orc:292116675`: Observations declare neither unit nor observed property; both are factored on the sosa:ObservationCollection they belong to.
- `s2orc:292193946`: Satellite subsystems are subclasses of sosa:Platform, generated automatically from channel lists.
- `s2orc:292733266`: Actuators are linked to ssn:Properties through :PropertyChange and :Effect individuals, optimal conditions are OWL class expressions over properties, and Jena rules generate :Actions from actuator states; property values sit on property individuals.
- `s2orc:4343299`: N3 rules generate sensor queries; uses a non-SOSA sosa:hasObservation linking a sensor to observations that carry symptoms.
- `s2orc:46937953`: SSN 2011-based observation capability ontology: sensors subclassed into remote and in-situ sensors, linked to tasks and ssn:Stimulus as DUL events.
- `s2orc:51906672`: Feature-of-interest subclasses are used to derive a category tree of marketplace offerings.
- `s2orc:52171330`: Discusses aligning SAREF with SOSA, e.g. saref:BuildingSpace as a subclass of sosa:Platform.
- `s2orc:52204861`: Observation subclasses defined by OWL class expressions (NursePresentObservation, SoundAboveThresholdFault) so that reasoning classifies observations into faults and nurse calls.
- `s2orc:52235652`: Alternative observation designs: mssn:AltObservationDesign subclass of ssn:Observation, with refined altFeatureOfInterest, altObservedProperty and altObservedBy to flag multiple mappings of one dataset.
- `s2orc:52832898`: Shortcut roles (speed, pos, acceleration) defined by role chains hosts • madeObservation • hasResult from a platform to measured values.
- `s2orc:53020082`: SWRL rules over observations assign alarm levels from alarm ranges attached to observable properties, and combine nearby alarms with custom geo built-ins.
- `s2orc:53094706`: The measurement capability of the sensor is linked to the feature of interest of the observation.
- `s2orc:53241582`: SSN 2011 terms are paraphrased; features of interest are equated with agricultural conditions (weather, water, soil).
- `s2orc:53247320`: Observation classes defined in DL (HighTrafficObservation, ∃observedProperty.CongestionLevel) and inferred by cascading stream reasoning.
- `s2orc:58668262`: Mapping of the FIESTA-IoT ontology (old SSN) to OMA NGSI context entities.
- `s2orc:5887317`: CSV on the Web metadata maps middleware CSV rows to legacy SSN observations, minting IRIs from sensor and time columns.
- `s2orc:73499497`: Observations and sensor descriptions are stored in two graphs of an IoT registry, joined through the identifier of the sensor (legacy SSN).
- `s2orc:9740727`: Machine perception by abduction: ssn:isPropertyOf between properties and features (diseases) is encoded as a bit matrix to explain observed properties.
