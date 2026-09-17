-- stg_pharmacy_fills_hk.sql
-- Computes the Hub FK hash keys (member, drug, pharmacy), the two
-- non-transactional Link composite keys (lnk_pharmacy_drug,
-- lnk_member_pharmacy), and the T-Link hash key for
-- tlnk_pharmacy_fill_txn. Derives effective_from from the fill's own
-- fill_date, following the same pattern established for Payment
-- Integrity, Risk Adjustment, and Clinical Quality T-Links (a dedicated
-- derived column, not a raw payload column referenced directly).
{% set yaml_metadata %}
source_model: 'stg_pharmacy_fills'
hashed_columns:
  member_hk: member_bk
  drug_hk: drug_bk
  pharmacy_hk: pharmacy_bk
  pharmacy_drug_hk:
    - pharmacy_bk
    - drug_bk
  member_pharmacy_hk:
    - member_bk
    - pharmacy_bk
  pharmacy_fill_txn_hk:
    - member_bk
    - drug_bk
    - pharmacy_bk
    - fill_date
derived_columns:
  effective_from: fill_date
{% endset %}
{% set metadata_dict = fromyaml(yaml_metadata) %}
{{ automate_dv.stage(include_source_columns=true,
                      source_model=metadata_dict['source_model'],
                      hashed_columns=metadata_dict['hashed_columns'],
                      derived_columns=metadata_dict['derived_columns']) }}
