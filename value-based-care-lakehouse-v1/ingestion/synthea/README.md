# Synthea Ingestion

**Status: Implemented and tested.**

Lands MITRE Synthea synthetic patient data into the Bronze layer. Synthea's
canonical output is one FHIR R4 Bundle (JSON) per patient, containing a mix
of resource types (Patient, Encounter, Condition, and others) nested inside
a `bundle.entry[]` array - structurally very different from the flat CSVs
used by the CMS sources (DE-SynPUF, NPPES), and the main reason this
ingestion looks different from the other two.

This script currently extracts three resource types - Patient, Encounter,
Condition - flattening each into its own tabular Bronze output using
dot-notation field paths (including array indexing, e.g. `type.0.text`)
defined in `synthea_schema.py`. Any other resource type present in a
bundle (Claim, Observation, MedicationRequest, etc.) is intentionally
skipped for now.

**Fixed during the Clinical Quality domain build:** the Encounter field
map originally omitted the attending provider and facility references
entirely. Real FHIR R4 Encounters carry these at
`Encounter.participant.individual` (a Practitioner reference) and
`Encounter.serviceProvider` (an Organization/facility reference) - see
hl7.org/fhir/R4/encounter.html. Both are now extracted as
`provider_reference` and `facility_reference`, cleaned the same way as
`member_reference`/`encounter_reference`, and covered by 2 new tests
(present + missing field cases). This was needed to build
`lnk_encounter_provider` and `lnk_encounter_facility` in the Clinical
Quality Vault layer - see `dbt/models/vault/links/README.md`.

Source: https://github.com/synthetichealth/synthea (Apache License 2.0)

## Files

- `land_synthea.py` - main ingestion script: walks bundle files, buckets
  entries by resourceType, flattens each into a row, cleans FHIR
  references (`urn:uuid:pat-001` -> `pat-001`)
- `synthea_schema.py` - supported resource types and their field-path maps
- `test_land_synthea.py` - pytest suite (10 tests, all passing) covering
  path resolution, resource flattening (including the provider/facility
  reference extraction and its missing-field case), unsupported-type
  skipping, reference cleaning (including the NaN edge case pandas
  introduces for missing references), and end-to-end landing
- `sample_bundles/` - two small fabricated FHIR bundles used as test fixtures

## Usage

```bash
pip install -r requirements.txt

python land_synthea.py --input-dir /path/to/synthea/output/fhir --output-dir ./bronze/synthea

# Quick smoke test against the included samples
python land_synthea.py --input-dir sample_bundles --output-dir ./bronze/synthea --format csv

pytest test_land_synthea.py -v
```

## Note on this repo's test data

Generating real Synthea output requires running the Synthea Java
application locally, which isn't available in every environment
(including the sandbox this repo was built in). `sample_bundles/`
contains small hand-built bundles in the exact real FHIR Bundle shape
Synthea produces, so the parsing and flattening logic - including the
nested-path resolution and reference cleaning - can be verified
end-to-end without that dependency. Point `--input-dir` at real Synthea
output to use this in production.

## Not yet covered

Observation, MedicationRequest, Procedure, and Claim resources follow
the same bundle-entry pattern but aren't extracted yet - extending
`SUPPORTED_RESOURCE_TYPES` and adding a field map is the way to add them.

**Fixed during the Payment Integrity / Risk Adjustment / Clinical
Quality metrics build-out:** `sample_bundles/patient-001.json` originally
had only one ambulatory encounter, so Readmission Rate would always
compute as zero with nothing to demonstrate. Added two inpatient (`IMP` -
a real FHIR R4 `Encounter.class` code) encounters to that same patient: an
admission/discharge (March 1-5, 2024) and a readmission 14 days after
discharge (March 20-23, 2024), following the same real FHIR Encounter
shape already established. This is a fixture edit to existing real
Synthea-shaped sample data, not a new synthetic data source - see
`dbt/models/gold/fact_readmission.sql` and
`dbt/models/semantic/README.md` for how this feeds Readmission Rate.
