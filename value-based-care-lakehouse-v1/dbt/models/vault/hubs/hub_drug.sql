-- hub_drug.sql
-- Hub for drugs, keyed on the real NDC. Real FDA NDC Directory data -
-- see ingestion/pharmacy/README.md.

{{
    automate_dv.hub(
        src_pk='drug_hk',
        src_nk='drug_bk',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_drugs_hk'
    )
}}
