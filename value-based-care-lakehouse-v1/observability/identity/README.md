# Identity Layer

This folder gives the agent its own Unity Catalog identity, distinct
from any human user - the missing piece ADR-006 and ADR-007 assumed but
never actually created. See ADR-013 in `docs/decisions/ADRs.md` for
full reasoning.

## Why this matters to a data architect specifically

Unity Catalog's row filters and column masks (`governance_policies.sql`,
ADR-007) enforce access based on *whichever identity is asking* - but
Unity Catalog doesn't invent that identity, something upstream has to
hand it one. Without this layer, an agent connecting through the
dbt-mcp server authenticates as whatever personal Databricks credential
a developer put in `.env`, so agent traffic and human traffic look
identical to Unity Catalog and to the audit log. That means a policy
meant to apply differently to agents than to humans literally cannot
be expressed, and `mcp_audit_logger.py`'s `caller_identity` field can
never actually distinguish agent activity from a person's own manual
queries. This layer is the upstream input the rest of the governance
stack already assumed existed.

## One-time setup this repo cannot script alone

Unity Catalog service principals are account-level objects, created
via the Databricks account console or Terraform - not via SQL. Before
`create_agent_service_principal.sql` means anything, a metastore admin
must:

1. Create a service principal in the account console, named
   `svc-agent-semantic-layer` (the name this project's docs use
   throughout).
2. Generate an OAuth client ID and client secret for it - never a
   long-lived personal access token repurposed for this identity.
3. Add that service principal to the workspace the metastore is
   attached to.

Only once that exists does `create_agent_service_principal.sql` have
something to grant permissions to.

## Files

- `create_agent_service_principal.sql` - grants `SELECT` on
  `gold.semantic` only to the service principal, once it exists -
  nothing on any other Gold schema, staging, or vault.
- `identity_policy.yaml` - the identity, its credential mechanism, and
  its exact allowed and explicitly denied scope, documented as
  reviewable data rather than scattered code comments.

## Wiring this into the MCP server

`.env.example` (repo root) and `.mcp/mcp.json.example` are both updated
to flag that `DBT_TOKEN` must be this service principal's OAuth
credential - never the developer's own personal Databricks token. The
agent's credential surface is meant to be entirely separate from any
human administrator's own login.

## What this doesn't cover

This is identity - proving who the agent is and what it's scoped to.
Orchestration - what happens when this agent delegates to a sub-agent,
and ensuring a sub-agent can only ever receive a strict subset of its
parent's privileges - is a related, distinct concern this project has
not yet built, since there is exactly one agent identity and no
sub-agent delegation today.
