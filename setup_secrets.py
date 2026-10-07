"""
One-time setup script: creates the Databricks secret scopes and stores all
API keys needed by the three app components.

Secrets created:
  - massive/api-key           -> Massive.com news API key (news_app + mcp_server)
  - database/lakebase-url     -> Lakebase Postgres connection URL (all components)
  - database/alpaca-key-id    -> Alpaca API key ID (mcp_server + dashboard)
  - database/alpaca-secret-key -> Alpaca API secret key (mcp_server + dashboard)

Run this locally (with the Databricks CLI configured) or from a notebook -
never commit the resulting secret values anywhere.

Usage:
    python setup_secrets.py
"""
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import workspace
import getpass

w = WorkspaceClient()

# --- Massive API key (news_app + mcp_server quote fetching) ---
w.secrets.create_scope(scope="massive")
w.secrets.put_secret(
    scope="massive",
    key="api-key",
    string_value=getpass.getpass("Paste your Massive API key: ")
)

# --- Database secrets (Lakebase + Alpaca) ---
w.secrets.create_scope(scope="database")

# Lakebase Postgres connection URL (base64-encoded postgresql:// URL)
w.secrets.put_secret(
    scope="database",
    key="lakebase-url",
    string_value=getpass.getpass("Paste your Lakebase URL: ")
)

# Alpaca API credentials (mcp_server + dashboard paper/live trading)
w.secrets.put_secret(
    scope="database",
    key="alpaca-key-id",
    string_value=getpass.getpass("Paste your Alpaca key ID: ")
)

w.secrets.put_secret(
    scope="database",
    key="alpaca-secret-key",
    string_value=getpass.getpass("Paste your Alpaca secret key: ")
)

# --- Grant read access to all users ---
w.secrets.put_acl(
    scope="database",
    principal="users",
    permission=workspace.AclPermission.READ,
)

w.secrets.put_acl(
    scope="massive",
    principal="users",
    permission=workspace.AclPermission.READ,
)
