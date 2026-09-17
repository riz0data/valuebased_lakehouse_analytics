"""
Unit tests for land_synthea.py.

Runs against small synthetic FHIR Bundle fixtures (not real Synthea output).
"""
import json

import pandas as pd
import pytest

from land_synthea import _clean_reference, _get_path, flatten_resource, land_synthea, parse_bundle
from synthea_schema import PATIENT_FIELDS, ENCOUNTER_FIELDS, CONDITION_FIELDS


BUNDLE_1 = {
    "resourceType": "Bundle",
    "entry": [
        {"resource": {"resourceType": "Patient", "id": "pat-001", "birthDate": "1975-03-14", "gender": "female"}},
        {"resource": {
            "resourceType": "Encounter", "id": "enc-001", "status": "finished",
            "class": {"code": "AMB"}, "type": [{"text": "General examination of patient"}],
            "subject": {"reference": "urn:uuid:pat-001"},
            "period": {"start": "2024-02-01T09:00:00Z", "end": "2024-02-01T09:30:00Z"},
            "participant": [{"individual": {"reference": "Practitioner/prov-001"}}],
            "serviceProvider": {"reference": "Organization/fac-001"},
        }},
        {"resource": {
            "resourceType": "Condition", "id": "cond-001",
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "code": {"coding": [{"code": "44054006", "display": "Diabetes mellitus type 2"}]},
            "subject": {"reference": "urn:uuid:pat-001"},
            "encounter": {"reference": "urn:uuid:enc-001"},
            "onsetDateTime": "2024-02-01",
        }},
        {"resource": {"resourceType": "Claim", "id": "claim-001"}},  # unsupported - must be skipped
    ],
}

BUNDLE_2 = {
    "resourceType": "Bundle",
    "entry": [
        {"resource": {"resourceType": "Patient", "id": "pat-002", "birthDate": "1990-11-02", "gender": "male"}},
        {"resource": {
            "resourceType": "Condition", "id": "cond-002",
            "clinicalStatus": {"coding": [{"code": "resolved"}]},
            "code": {"coding": [{"code": "195662009", "display": "Acute viral pharyngitis"}]},
            "subject": {"reference": "urn:uuid:pat-002"},
            "onsetDateTime": "2023-06-10",
        }},
    ],
}


def test_get_path_resolves_nested_and_array_paths():
    obj = {"type": [{"text": "well child visit"}], "period": {"start": "2024-01-01"}}
    assert _get_path(obj, "type.0.text") == "well child visit"
    assert _get_path(obj, "period.start") == "2024-01-01"


def test_get_path_returns_none_for_missing_field():
    obj = {"a": {"b": 1}}
    assert _get_path(obj, "a.c") is None
    assert _get_path(obj, "x.y.z") is None
    assert _get_path(obj, "type.5.text") is None  # index out of range


def test_flatten_resource_uses_field_map():
    resource = {"id": "pat-001", "birthDate": "1975-03-14", "gender": "female"}
    flat = flatten_resource(resource, PATIENT_FIELDS)
    assert flat == {
        "member_bk": "pat-001",
        "birth_date": "1975-03-14",
        "sex": "female",
        "death_date": None,
    }


def test_flatten_resource_extracts_encounter_provider_and_facility_references():
    """Real FHIR R4 fields: Encounter.participant.individual (Practitioner)
    and Encounter.serviceProvider (Organization/facility) - see
    hl7.org/fhir/R4/encounter.html."""
    resource = {
        "id": "enc-001",
        "status": "finished",
        "class": {"code": "AMB"},
        "type": [{"text": "General examination of patient"}],
        "subject": {"reference": "urn:uuid:pat-001"},
        "period": {"start": "2024-02-01T09:00:00Z", "end": "2024-02-01T09:30:00Z"},
        "participant": [{"individual": {"reference": "Practitioner/prov-001"}}],
        "serviceProvider": {"reference": "Organization/fac-001"},
    }
    flat = flatten_resource(resource, ENCOUNTER_FIELDS)
    assert flat["provider_reference"] == "Practitioner/prov-001"
    assert flat["facility_reference"] == "Organization/fac-001"


def test_flatten_resource_encounter_missing_participant_and_service_provider():
    """Both fields are optional in FHIR - a missing participant/serviceProvider
    must resolve to None, not raise."""
    resource = {"id": "enc-002", "status": "finished", "class": {"code": "AMB"}}
    flat = flatten_resource(resource, ENCOUNTER_FIELDS)
    assert flat["provider_reference"] is None
    assert flat["facility_reference"] is None


def test_parse_bundle_buckets_by_resource_type_and_skips_unsupported():
    buckets = parse_bundle(BUNDLE_1)
    assert len(buckets["Patient"]) == 1
    assert len(buckets["Encounter"]) == 1
    assert len(buckets["Condition"]) == 1
    assert "Claim" not in buckets  # unsupported type never enters the buckets dict


def test_clean_reference_strips_urn_and_slash_forms():
    assert _clean_reference("urn:uuid:pat-001") == "pat-001"
    assert _clean_reference("Patient/pat-001") == "pat-001"
    assert _clean_reference(None) is None
    assert _clean_reference(float("nan")) is None


def test_land_synthea_end_to_end(tmp_path):
    bundle_dir = tmp_path / "bundles"
    bundle_dir.mkdir()
    (bundle_dir / "p1.json").write_text(json.dumps(BUNDLE_1))
    (bundle_dir / "p2.json").write_text(json.dumps(BUNDLE_2))

    summary = land_synthea(str(bundle_dir), str(tmp_path / "out"), fmt="csv")

    assert summary["bundles_parsed"] == 2
    assert summary["patients"] == 2
    assert summary["encounters"] == 1
    assert summary["conditions"] == 2

    patients = pd.read_csv(tmp_path / "out" / "patients.csv")
    assert set(patients["member_bk"]) == {"pat-001", "pat-002"}

    conditions = pd.read_csv(tmp_path / "out" / "conditions.csv")
    cond2 = conditions[conditions["condition_bk"] == "cond-002"].iloc[0]
    assert pd.isna(cond2["encounter_reference"])  # bundle 2's condition has no encounter ref

    encounters = pd.read_csv(tmp_path / "out" / "encounters.csv")
    assert encounters.iloc[0]["member_reference"] == "pat-001"  # urn:uuid: prefix stripped
    assert encounters.iloc[0]["provider_reference"] == "prov-001"  # Practitioner/ prefix stripped
    assert encounters.iloc[0]["facility_reference"] == "fac-001"  # Organization/ prefix stripped


def test_land_synthea_raises_on_missing_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        land_synthea(str(tmp_path / "nope"), str(tmp_path / "out"))


def test_land_synthea_raises_on_empty_dir(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(ValueError, match="No .json bundle files found"):
        land_synthea(str(empty_dir), str(tmp_path / "out"))
