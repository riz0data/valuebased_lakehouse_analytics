"""
synthea_schema.py

Field definitions for parsing MITRE Synthea synthetic patient data.

Synthea outputs synthetic patients as FHIR R4 Bundles (JSON), one bundle
per patient, each containing a mix of resource types: Patient, Encounter,
Condition, Observation, MedicationRequest, etc. This is structurally very
different from the flat CSV files CMS ships (DE-SynPUF, NPPES) - it's
nested JSON with a "resourceType" discriminator per entry.

This module defines which FHIR resource types this ingestion pulls out,
and the field paths used to flatten each one into a tabular row.

Source: https://github.com/synthetichealth/synthea (Apache License 2.0)
Synthea also ships a CSV export mode with flatter files, but the FHIR
Bundle format is used here since it's the canonical Synthea output and
better demonstrates handling semi-structured healthcare data.
"""

from __future__ import annotations

# FHIR resourceType values this ingestion extracts. Any other resource
# type present in a bundle (e.g. Claim, ExplanationOfBenefit, Provenance)
# is intentionally skipped for now - see README "Not yet covered".
SUPPORTED_RESOURCE_TYPES = ["Patient", "Encounter", "Condition"]

# Field paths (dot-notation into the FHIR resource JSON) extracted for
# each resource type, and the business-friendly column name they land as.
PATIENT_FIELDS: dict[str, str] = {
    "id": "member_bk",
    "birthDate": "birth_date",
    "gender": "sex",
    "deceasedDateTime": "death_date",
}

ENCOUNTER_FIELDS: dict[str, str] = {
    "id": "encounter_bk",
    "status": "encounter_status",
    "class.code": "encounter_class_code",
    "type.0.text": "encounter_type_text",
    "subject.reference": "member_reference",
    "period.start": "encounter_start",
    "period.end": "encounter_end",
    # Real FHIR R4 Encounter fields (see hl7.org/fhir/R4/encounter.html):
    # Encounter.participant.individual references the attending
    # Practitioner; Encounter.serviceProvider references the Organization
    # (facility) responsible for the encounter. Both are 0..1/0..* and
    # commonly absent - _get_path returns None gracefully when they are.
    "participant.0.individual.reference": "provider_reference",
    "serviceProvider.reference": "facility_reference",
}

CONDITION_FIELDS: dict[str, str] = {
    "id": "condition_bk",
    "clinicalStatus.coding.0.code": "clinical_status_code",
    "code.coding.0.code": "diagnosis_bk",
    "code.coding.0.display": "diagnosis_description",
    "subject.reference": "member_reference",
    "encounter.reference": "encounter_reference",
    "onsetDateTime": "onset_date",
}
