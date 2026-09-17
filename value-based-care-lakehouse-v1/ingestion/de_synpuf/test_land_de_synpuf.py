"""
Unit tests for land_de_synpuf.py.

Runs against small synthetic DE-SynPUF-format fixtures (not real CMS data).
"""
import pandas as pd
import pytest

from land_de_synpuf import (
    land_beneficiary_summary,
    land_inpatient_claims,
    process_inpatient_chunk,
)
from make_sample import BENE_HEADER, BENE_ROWS, INPATIENT_HEADER, INPATIENT_ROWS


@pytest.fixture
def bene_csv(tmp_path):
    path = tmp_path / "bene.csv"
    pd.DataFrame(BENE_ROWS, columns=BENE_HEADER).to_csv(path, index=False)
    return path


@pytest.fixture
def inpatient_csv(tmp_path):
    path = tmp_path / "inpatient.csv"
    pd.DataFrame(INPATIENT_ROWS, columns=INPATIENT_HEADER).to_csv(path, index=False)
    return path


def test_beneficiary_summary_dedupes_and_renames(bene_csv, tmp_path):
    summary = land_beneficiary_summary(str(bene_csv), str(tmp_path / "out"), fmt="csv")
    assert summary["input_rows"] == 3
    assert summary["members_landed"] == 2  # de-duped on member_bk

    out = pd.read_csv(tmp_path / "out" / "beneficiary_summary.csv")
    assert "member_bk" in out.columns
    assert "DESYNPUF_ID" not in out.columns
    assert "flag_diabetes" in out.columns


def test_beneficiary_summary_raises_on_missing_columns(tmp_path):
    bad_path = tmp_path / "bad.csv"
    pd.DataFrame(BENE_ROWS, columns=BENE_HEADER).drop(columns=["DESYNPUF_ID"]).to_csv(bad_path, index=False)
    with pytest.raises(ValueError, match="missing expected DE-SynPUF columns"):
        land_beneficiary_summary(str(bad_path), str(tmp_path / "out"), fmt="csv")


def test_process_inpatient_chunk_unpivots_diagnoses():
    df = pd.DataFrame(INPATIENT_ROWS, columns=INPATIENT_HEADER)
    header, dgns, prcdr = process_inpatient_chunk(df)

    assert len(header) == 2
    # claim 1 has 3 diagnosis codes, claim 2 has 1 -> 4 total unpivoted rows
    assert len(dgns) == 4
    assert set(dgns.columns) == {"claim_line_bk", "diagnosis_bk"}
    assert set(dgns[dgns["claim_line_bk"] == "196201039265290"]["diagnosis_bk"]) == {
        "41401", "4280", "2720"
    }
    # only claim 1 has a procedure code
    assert len(prcdr) == 1
    assert prcdr.iloc[0]["procedure_bk"] == "3615"


def test_process_inpatient_chunk_drops_blank_codes():
    df = pd.DataFrame(INPATIENT_ROWS, columns=INPATIENT_HEADER)
    _, dgns, _ = process_inpatient_chunk(df)
    # no blank/NaN diagnosis codes should have survived the unpivot
    assert dgns["diagnosis_bk"].isna().sum() == 0
    assert (dgns["diagnosis_bk"].astype(str).str.strip() == "").sum() == 0


def test_land_inpatient_claims_end_to_end(inpatient_csv, tmp_path):
    summary = land_inpatient_claims(str(inpatient_csv), str(tmp_path / "out"), fmt="csv")
    assert summary["input_rows"] == 2
    assert summary["claims_landed"] == 2
    assert summary["diagnosis_rows_landed"] == 4
    assert summary["procedure_rows_landed"] == 1

    header = pd.read_csv(tmp_path / "out" / "inpatient_claim_header.csv")
    assert "paid_amount" in header.columns
    assert "record_source" in header.columns


def test_land_inpatient_claims_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        land_inpatient_claims(str(tmp_path / "nope.csv"), str(tmp_path / "out"))
