"""
Unit tests for land_nppes.py.

Runs against a small synthetic NPPES-format CSV fixture (not real NPPES
data) so the test suite doesn't depend on network access to CMS's
download servers.
"""
import shutil
from pathlib import Path

import pandas as pd
import pytest

from land_nppes import land_nppes, process_chunk
from make_sample import HEADER, INDIVIDUAL_ROWS, ORG_ROWS


@pytest.fixture
def sample_csv(tmp_path) -> Path:
    csv_path = tmp_path / "sample_nppes.csv"
    df = pd.DataFrame(INDIVIDUAL_ROWS + ORG_ROWS, columns=HEADER)
    df.to_csv(csv_path, index=False)
    return csv_path


def test_process_chunk_splits_providers_and_facilities():
    df = pd.DataFrame(INDIVIDUAL_ROWS + ORG_ROWS, columns=HEADER)
    providers, facilities = process_chunk(df)

    assert len(providers) == 3
    assert len(facilities) == 3  # includes the un-deduped raw duplicate
    assert set(providers["entity_type_code"]) == {"1"}
    assert set(facilities["entity_type_code"]) == {"2"}


def test_process_chunk_renames_columns():
    df = pd.DataFrame(INDIVIDUAL_ROWS, columns=HEADER)
    providers, _ = process_chunk(df)
    assert "npi" in providers.columns
    assert "provider_last_name" in providers.columns
    # original raw NPPES column names should not survive
    assert "NPI" not in providers.columns


def test_process_chunk_raises_on_missing_columns():
    df = pd.DataFrame(INDIVIDUAL_ROWS, columns=HEADER).drop(columns=["NPI"])
    with pytest.raises(ValueError, match="missing expected NPPES columns"):
        process_chunk(df)


def test_land_nppes_end_to_end_dedupes_and_writes_csv(sample_csv, tmp_path):
    out_dir = tmp_path / "bronze" / "nppes"
    summary = land_nppes(str(sample_csv), str(out_dir), fmt="csv")

    assert summary["input_rows"] == 6
    assert summary["providers_landed"] == 3
    assert summary["facilities_landed"] == 2  # de-duped from 3 raw rows

    providers_df = pd.read_csv(out_dir / "providers.csv")
    facilities_df = pd.read_csv(out_dir / "facilities.csv")

    assert len(providers_df) == 3
    assert len(facilities_df) == 2
    assert "record_source" in providers_df.columns
    assert "load_dts" in providers_df.columns
    assert (providers_df["record_source"] == "nppes_npi_registry").all()

    # the duplicated NPI should keep the row with the LATER last_update_date
    dup_row = facilities_df[facilities_df["npi"] == 4567890123]
    assert len(dup_row) == 1
    assert dup_row.iloc[0]["last_update_date"] == "09/01/2024"


def test_land_nppes_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        land_nppes(str(tmp_path / "does_not_exist.csv"), str(tmp_path / "out"))
