-- dim_member.sql
-- Conformed Member dimension, built from hub_member + sat_member_demographics.
-- Gold layer models are plain dbt SQL (not automate_dv macros) - by this
-- point we are past Data Vault mechanics and into presenting a
-- business-friendly star schema for BI tools and the Semantic Layer.

select
    h.member_hk,
    h.member_bk as member_id,
    s.birth_date,
    s.sex,
    s.race_code,
    s.state_code,
    s.source_system
from {{ ref('hub_member') }} h
left join {{ ref('sat_member_demographics') }} s
    on h.member_hk = s.member_hk
