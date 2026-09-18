-- lakehouse_cost_attribution.sql
--
-- Reference implementation for lakehouse compute cost attribution,
-- sourced entirely from Databricks' own system tables - no invented
-- pricing model, no estimated DBU-to-dollar conversion done by hand.
--
-- Mechanism, in plain terms:
--   1. system.billing.usage records real, actual consumption (DBUs)
--      for every cluster, SQL warehouse, and job run in the account,
--      already broken out by the custom tags attached to that compute
--      resource (for example: project, team, environment).
--   2. system.billing.list_prices holds the dollar rate per DBU for
--      each SKU (job compute, all-purpose compute, SQL warehouse,
--      serverless, etc.) at the time that usage occurred.
--   3. Joining the two on sku_name and effective date range converts
--      raw DBU consumption into real dollar cost - not an estimate.
--
-- This mirrors the same real, current Databricks-documented pattern as
-- observability/mcp_audit_logger.py: no invented APIs, only tables and
-- columns Databricks actually publishes. See README.md in this folder
-- for the tagging convention this assumes upstream (set on cluster and
-- job creation, not applied retroactively).
--
-- Not runnable against a live account from this repo (no workspace is
-- attached to this portfolio project) - this is written to be dropped
-- into a real Databricks SQL warehouse as-is. See
-- example_lakehouse_cost_output.txt for what a result set looks like.

WITH priced_usage AS (
    SELECT
        u.usage_date,
        u.sku_name,
        u.usage_quantity                                   AS dbus_consumed,
        p.pricing.effective_list.default                    AS price_per_dbu,
        u.usage_quantity * p.pricing.effective_list.default AS dollar_cost,
        u.custom_tags['project']                            AS project_tag,
        u.custom_tags['team']                                AS team_tag,
        u.custom_tags['environment']                         AS environment_tag,
        u.workspace_id,
        u.usage_metadata.cluster_id                          AS cluster_id,
        u.usage_metadata.job_id                              AS job_id
    FROM system.billing.usage u
    JOIN system.billing.list_prices p
        ON u.sku_name = p.sku_name
        AND u.usage_date >= p.price_start_time
        AND (p.price_end_time IS NULL OR u.usage_date < p.price_end_time)
    WHERE u.usage_date >= current_date() - INTERVAL 30 DAYS
)

-- Chargeback view: real dollar spend per project per day, the
-- attribution granularity most FinOps reviews actually ask for.
SELECT
    usage_date,
    COALESCE(project_tag, 'untagged')     AS project,
    COALESCE(team_tag, 'untagged')        AS team,
    COALESCE(environment_tag, 'untagged') AS environment,
    sku_name,
    ROUND(SUM(dbus_consumed), 2)          AS total_dbus,
    ROUND(SUM(dollar_cost), 2)            AS total_cost_dollars
FROM priced_usage
GROUP BY usage_date, project, team, environment, sku_name
ORDER BY usage_date DESC, total_cost_dollars DESC;

-- A second, narrower query worth calling out separately: untagged
-- spend. If this project were live, this is the query a FinOps review
-- would run first, since untagged compute cannot be charged back to
-- anyone, and Databricks' own guidance is to catch that as early as
-- possible rather than after months of drift.
--
-- SELECT usage_date, sku_name, ROUND(SUM(dollar_cost), 2) AS untagged_cost_dollars
-- FROM priced_usage
-- WHERE project_tag IS NULL
-- GROUP BY usage_date, sku_name
-- ORDER BY untagged_cost_dollars DESC;
