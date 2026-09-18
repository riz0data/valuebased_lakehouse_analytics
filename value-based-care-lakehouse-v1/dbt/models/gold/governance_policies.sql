-- governance_policies.sql
--
-- Unity Catalog row filters and column masks for the Gold layer.
--
-- This file is NOT a dbt model - it is not selected by `dbt build` and
-- produces no table. It is a plain SQL script, run once (or via a
-- one-off `dbt run-operation` / post-hook, see below) against a real
-- Databricks workspace, that registers the governance functions
-- described in ADR-007 and binds them to the Gold tables below.
--
-- It lives here, next to the Gold models it governs, rather than in a
-- separate top-level "governance" folder, because a row filter or
-- column mask is meaningless without the specific table it's applied
-- to - keeping them side by side makes it obvious which Gold tables
-- have governance applied and which don't yet.
--
-- Requires: EXECUTE on the function, USE SCHEMA on gold, USE CATALOG on
-- the parent catalog (table owner by default already has this).
--
-- ============================================================
-- ROW FILTER: regional access to provider and claim data
-- ============================================================
--
-- Scenario: a regional operations manager should only see providers
-- (and, by extension, claims) in their own practice state. Someone in
-- the `regional_manager_northeast` Unity Catalog group sees only
-- Northeast providers; anyone not in a recognized regional group (for
-- example, national analysts, or the function's own owner) sees every
-- row. This mirrors the real access pattern named in ADR-005 and
-- ADR-007: "restricting which providers a regional manager can see
-- cost data for."

CREATE OR REPLACE FUNCTION gold.governance.provider_region_filter(practice_state STRING)
RETURNS BOOLEAN
RETURN
  CASE
    WHEN is_member('regional_manager_northeast') THEN practice_state IN ('NY', 'NJ', 'PA', 'MA', 'CT', 'RI', 'NH', 'VT', 'ME')
    WHEN is_member('regional_manager_south')     THEN practice_state IN ('TX', 'FL', 'GA', 'NC', 'SC', 'VA', 'TN', 'AL', 'MS', 'LA', 'AR', 'KY', 'WV', 'OK')
    WHEN is_member('regional_manager_midwest')   THEN practice_state IN ('IL', 'OH', 'MI', 'IN', 'WI', 'MN', 'IA', 'MO', 'KS', 'NE', 'SD', 'ND')
    WHEN is_member('regional_manager_west')      THEN practice_state IN ('CA', 'WA', 'OR', 'AZ', 'NV', 'CO', 'UT', 'NM', 'ID', 'MT', 'WY', 'AK', 'HI')
    ELSE true -- national analysts, data platform owners, and any
              -- identity not in a regional group see every row -
              -- Unity Catalog row filters are deny-by-exception here,
              -- not deny-by-default, matching the real org chart: most
              -- roles on this team are cross-regional.
  END;

ALTER TABLE gold.gold.dim_provider
  SET ROW FILTER gold.governance.provider_region_filter ON (practice_state);

-- fact_claim_payment has no practice_state column of its own - it only
-- carries provider_hk - so it cannot take this exact row filter
-- function directly (Unity Catalog row filters evaluate columns on the
-- table they are bound to, they do not follow joins). Restricting
-- fact_claim_payment by region requires either denormalizing
-- practice_state onto the fact table so the same filter can bind
-- there, or moving to an ABAC policy with a join-aware predicate. This
-- repo takes the simpler denormalization path conceptually but does
-- not implement it, to keep dim_provider as the one clearly-governed
-- example rather than silently implying every Gold table is covered -
-- see the "Known Gaps" note in dbt/models/gold/README.md.

-- ============================================================
-- COLUMN MASKS: member demographic and provider identity fields
-- ============================================================
--
-- Scenario: birth_date and race_code on dim_member are the kind of
-- demographic fields that are useful in aggregate (age-banded cohort
-- analysis, disparity reporting) but shouldn't be visible at the
-- individual level to every consumer of the Gold layer. Members of
-- `phi_reviewers` see real values; everyone else sees a masked version
-- that still supports aggregate analysis (year of birth instead of
-- exact date; a generalized "withheld" marker instead of race_code).

CREATE OR REPLACE FUNCTION gold.governance.mask_birth_date(birth_date DATE)
RETURNS DATE
RETURN
  CASE
    WHEN is_member('phi_reviewers') THEN birth_date
    ELSE DATE_TRUNC('YEAR', birth_date) -- keeps birth year for
                                         -- age-banding, drops month/day
  END;

CREATE OR REPLACE FUNCTION gold.governance.mask_race_code(race_code STRING)
RETURNS STRING
RETURN
  CASE
    WHEN is_member('phi_reviewers') THEN race_code
    ELSE 'WITHHELD'
  END;

ALTER TABLE gold.gold.dim_member
  ALTER COLUMN birth_date SET MASK gold.governance.mask_birth_date;

ALTER TABLE gold.gold.dim_member
  ALTER COLUMN race_code SET MASK gold.governance.mask_race_code;

-- Provider identity: first/last name masked to initials for anyone
-- outside the credentialing team, since NPI + practice_state + specialty
-- is already enough for almost every metric in this repo (leakage by
-- provider, DRG variance, and so on all group by provider_hk / NPI, not
-- by name).

CREATE OR REPLACE FUNCTION gold.governance.mask_provider_name(provider_name STRING)
RETURNS STRING
RETURN
  CASE
    WHEN is_member('credentialing_team') THEN provider_name
    ELSE CONCAT(LEFT(provider_name, 1), '.')
  END;

ALTER TABLE gold.gold.dim_provider
  ALTER COLUMN provider_first_name SET MASK gold.governance.mask_provider_name;

ALTER TABLE gold.gold.dim_provider
  ALTER COLUMN provider_last_name SET MASK gold.governance.mask_provider_name;
