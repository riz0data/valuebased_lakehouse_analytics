-- tlnk_pharmacy_fill_txn.sql
-- Transactional Link for prescription fill events - each fill (member +
-- drug + pharmacy on a given fill_date) is an immutable, point-in-time
-- fact. SYNTHETIC - see ingestion/pharmacy/README.md; there is no
-- public dataset of individual fill events.

{{
    automate_dv.t_link(
        src_pk='pharmacy_fill_txn_hk',
        src_fk=['member_hk', 'drug_hk', 'pharmacy_hk'],
        src_payload=['days_supply', 'fill_date'],
        src_eff='effective_from',
        src_ldts='load_dts',
        src_source='record_source',
        source_model='stg_pharmacy_fills_hk'
    )
}}
