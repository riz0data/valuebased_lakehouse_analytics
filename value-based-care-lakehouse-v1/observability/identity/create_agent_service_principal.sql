-- create_agent_service_principal.sql
--
-- Reference implementation for giving the agent its own Unity Catalog
-- identity, distinct from any human user. See ADR-013 in
-- docs/decisions/ADRs.md for full reasoning, and ADR-006 for the
-- original decision this extends (agents only access data through the
-- governed semantic layer - this is the identity that decision assumed
-- but never actually created).
--
-- Mechanism, in plain terms: a Databricks service principal is a
-- non-human identity with its own client ID and short-lived OAuth
-- token, created and managed inside the account/workspace admin
-- console or the Databricks CLI/Terraform, then referenced here by
-- application_id once it exists. This file assumes the service
-- principal has already been created via the account console (Unity
-- Catalog service principals are account-level objects, not created
-- via SQL) - see README.md in this folder for that one-time setup
-- step. Everything below is the data-architecture side: granting that
-- identity exactly the access it needs, once it exists.
--
-- Not runnable against a live account from this repo (no workspace or
-- Unity Catalog metastore is attached to this portfolio project) -
-- written to be run as-is by whoever administers the real metastore.

-- Replace with the actual application_id assigned when the service
-- principal is created in the account console.
-- Convention used throughout this project's docs: svc-agent-semantic-layer

-- Grant USE on the catalog and schema, but nothing broader - this
-- identity should never see staging or vault schemas at all.
GRANT USE CATALOG ON CATALOG gold TO `svc-agent-semantic-layer`;
GRANT USE SCHEMA ON SCHEMA gold.semantic TO `svc-agent-semantic-layer`;

-- SELECT only on the semantic layer views this agent is meant to
-- query - not on gold's other schemas, and never on staging or vault.
GRANT SELECT ON SCHEMA gold.semantic TO `svc-agent-semantic-layer`;

-- Explicitly confirm no broader grants exist. This is a documentation
-- statement, not executable SQL - a real review should run
-- SHOW GRANTS ON CATALOG gold TO `svc-agent-semantic-layer`; and
-- confirm the output contains only the two grants above, nothing else.

-- The existing row filters and column masks in governance_policies.sql
-- (ADR-007) already apply to whichever identity is asking - creating
-- this service principal is what makes those policies actually mean
-- something specific for agent traffic, rather than being
-- indistinguishable from a human's own query.
