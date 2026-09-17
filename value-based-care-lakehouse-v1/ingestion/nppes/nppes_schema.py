"""
nppes_schema.py

Column selection and renaming for the NPPES NPI Registry bulk file.

The full NPPES bulk CSV ("npidata_pfile_<date>.csv") ships with 300+ columns
covering both Type 1 (individual providers) and Type 2 (organizations /
facilities). Most downstream Hub/Satellite models only need a subset of
those columns. This module defines that subset in one place so the
ingestion script and any downstream dbt staging model agree on names.

Source of truth for the full column list:
https://download.cms.gov/nppes/NPI_Files.html (NPPES Data Dissemination
Public File - see the accompanying data dictionary PDF).

License: NPPES data is published by CMS and is in the public domain.
"""

from __future__ import annotations

# Raw NPPES column name -> business-friendly staging column name.
# Kept explicit (rather than a blanket lowercase/replace) so the mapping is
# self-documenting and safe to extend without accidentally renaming a
# column that isn't actually being kept.
NPPES_COLUMN_MAP: dict[str, str] = {
    "NPI": "npi",
    "Entity Type Code": "entity_type_code",  # 1 = Individual, 2 = Organization
    "Provider Organization Name (Legal Business Name)": "organization_name",
    "Provider Last Name (Legal Name)": "provider_last_name",
    "Provider First Name": "provider_first_name",
    "Provider Middle Name": "provider_middle_name",
    "Provider Credential Text": "provider_credential",
    "Provider First Line Business Practice Location Address": "practice_address_line_1",
    "Provider Second Line Business Practice Location Address": "practice_address_line_2",
    "Provider Business Practice Location Address City Name": "practice_city",
    "Provider Business Practice Location Address State Name": "practice_state",
    "Provider Business Practice Location Address Postal Code": "practice_zip",
    "Healthcare Provider Taxonomy Code_1": "primary_taxonomy_code",
    "Healthcare Provider Primary Taxonomy Switch_1": "primary_taxonomy_flag",
    "Provider Enumeration Date": "enumeration_date",
    "Last Update Date": "last_update_date",
    "NPI Deactivation Date": "deactivation_date",
    "Is Sole Proprietor": "is_sole_proprietor",
}

# Entity Type Code values, per the NPPES data dictionary.
ENTITY_TYPE_INDIVIDUAL = "1"   # -> feeds hub_provider
ENTITY_TYPE_ORGANIZATION = "2"  # -> feeds hub_facility

REQUIRED_SOURCE_COLUMNS = list(NPPES_COLUMN_MAP.keys())
STAGING_COLUMNS = list(NPPES_COLUMN_MAP.values())
