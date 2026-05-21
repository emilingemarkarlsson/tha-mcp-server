"""THA Hockey Analytics — MCP Server (HTTP production mode).

Exposes MotherDuck hockey databases via Model Context Protocol.
Auth via X-API-Key header; per-key database access control.

Run (production):
    uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000

Run (local stdio — use stdio_server.py instead):
    MCP_LOCAL_MODE=1 python -m mcp_server.server
"""
from __future__ import annotations

import json
import os
import re
import threading
from contextvars import ContextVar
from typing import Any

import duckdb
from fastapi import FastAPI, Request, Response
from fastmcp import FastMCP

from .schema_hints import ALL_DBS, DB_DESCRIPTIONS, SQL_HINTS, TIER_PRESETS

# ── Config ────────────────────────────────────────────────────────────────────

MD_TOKEN: str = os.environ.get("MOTHERDUCK_TOKEN", "")

# CUSTOMER_KEYS = JSON blob: {"tha-abc123": {"name": "X", "dbs": ["nhl"], "tier": "nhl"}}
CUSTOMER_KEYS: dict[str, dict] = json.loads(os.environ.get("CUSTOMER_KEYS", "{}"))

# Local/stdio mode bypasses all auth — set via MCP_LOCAL_MODE=1 or stdio_server.py
LOCAL_MODE: bool = os.environ.get("MCP_LOCAL_MODE", "0") == "1"
_LOCAL_CUSTOMER: dict = {"name": "local-dev", "dbs": list(ALL_DBS), "tier": "internal"}

# Per-request customer context — asyncio-safe ContextVar
_customer: ContextVar[dict | None] = ContextVar("customer", default=None)

# Per-thread DuckDB connections (reused across tool calls on same thread)
_tls = threading.local()


# ── DuckDB connection pool ────────────────────────────────────────────────────

def _conn(db: str) -> duckdb.DuckDBPyConnection:
    if not hasattr(_tls, "conns"):
        _tls.conns: dict[str, duckdb.DuckDBPyConnection] = {}
    if db not in _tls.conns:
        _tls.conns[db] = duckdb.connect(f"md:{db}?motherduck_token={MD_TOKEN}")
    return _tls.conns[db]


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _get_customer() -> dict | None:
    if LOCAL_MODE:
        return _LOCAL_CUSTOMER
    return _customer.get()


def _check_db(database: str) -> str | None:
    """Return error string if access denied, None if allowed."""
    c = _get_customer()
    if c is None:
        return "Unauthorized — provide X-API-Key header"
    allowed = c.get("dbs", [])
    if database not in allowed:
        return f"No access to '{database}'. Your tier ({c.get('tier','?')}) grants: {', '.join(allowed)}"
    return None


# ── FastMCP instance ──────────────────────────────────────────────────────────

mcp = FastMCP(
    "THA Hockey Analytics",
    instructions=(
        "You have access to hockey analytics databases via MotherDuck (DuckDB). "
        "Databases: nhl, swe (all Swedish leagues), shl_analytics (SHL.se detailed), "
        "nor (Norwegian), sui (Swiss), liiga (Finnish), met (Danish), "
        "moneypuck (NHL xG/advanced), hockey_ref (IIHF/contracts). "
        "ALWAYS call get_schema_overview() first to understand available tables. "
        "ALWAYS qualify table names: database.schema.table (e.g. nhl.main.games). "
        "Use run_sql() for all data retrieval. DuckDB SQL syntax."
    ),
)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_databases() -> str:
    """List all hockey databases this API key grants access to, with descriptions."""
    c = _get_customer()
    if not c:
        return "Error: Unauthorized"
    lines = [f"# Accessible Databases\nCustomer: {c.get('name','?')} | Tier: {c.get('tier','?')}\n"]
    for db in c.get("dbs", []):
        info = DB_DESCRIPTIONS.get(db, {})
        lines.append(f"**{db}**")
        lines.append(f"  {info.get('description', '')}\n")
    return "\n".join(lines)


@mcp.tool()
def get_schema_overview() -> str:
    """Comprehensive overview of all accessible databases with key tables and what they contain.

    Call this first — it gives you everything needed to write accurate queries without
    having to enumerate tables manually.
    """
    c = _get_customer()
    if not c:
        return "Error: Unauthorized"

    lines = ["# THA Hockey Analytics — Full Schema Overview\n"]
    for db in c.get("dbs", []):
        info = DB_DESCRIPTIONS.get(db, {})
        lines.append(f"## {db}")
        lines.append(info.get("description", ""))
        for tbl, desc in info.get("key_tables", {}).items():
            lines.append(f"  • {tbl}: {desc}")
        lines.append("")

    lines.append(SQL_HINTS)
    return "\n".join(lines)


@mcp.tool()
def list_tables(database: str) -> str:
    """List all tables in a database with live row counts and descriptions.

    Args:
        database: Database name, e.g. 'nhl', 'swe', 'shl_analytics'
    """
    err = _check_db(database)
    if err:
        return f"Error: {err}"
    try:
        con = _conn(database)
        rows = con.execute("SHOW ALL TABLES").fetchall()
        user_tables = [(r[1], r[2]) for r in rows if r[0] == database]

        hints = DB_DESCRIPTIONS.get(database, {}).get("key_tables", {})

        # Group by schema
        by_schema: dict[str, list[str]] = {}
        for schema, tbl in sorted(user_tables):
            by_schema.setdefault(schema, []).append(tbl)

        lines = [f"# {database} ({len(user_tables)} tables)\n"]
        for schema, tbls in by_schema.items():
            lines.append(f"## Schema: {schema}")
            for tbl in tbls:
                key = f"{schema}.{tbl}" if schema != "main" else tbl
                hint = hints.get(key, hints.get(tbl, ""))
                try:
                    cnt = con.execute(
                        f'SELECT COUNT(*) FROM "{database}"."{schema}"."{tbl}"'
                    ).fetchone()[0]
                    lines.append(f"  {key}: {cnt:,} rows{' — ' + hint if hint else ''}")
                except Exception:
                    lines.append(f"  {key}: —{' — ' + hint if hint else ''}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def describe_table(database: str, table: str) -> str:
    """Show column names, types, row count and a sample row for a table.

    Args:
        database: Database name, e.g. 'nhl'
        table: Table name. Use schema.table for non-main schemas,
               e.g. 'raw.players_per_game' for shl_analytics.
    """
    err = _check_db(database)
    if err:
        return f"Error: {err}"
    try:
        con = _conn(database)
        schema, tbl = table.split(".", 1) if "." in table else ("main", table)

        cols = con.execute(f'DESCRIBE "{database}"."{schema}"."{tbl}"').fetchall()

        try:
            cnt = con.execute(
                f'SELECT COUNT(*) FROM "{database}"."{schema}"."{tbl}"'
            ).fetchone()[0]
            header = f"# {database}.{schema}.{tbl}  ({cnt:,} rows)\n"
        except Exception:
            header = f"# {database}.{schema}.{tbl}\n"

        col_lines = ["## Columns"]
        for col in cols:
            nullable = "" if col[2] == "YES" else " NOT NULL"
            col_lines.append(f"  {col[0]:<30} {col[1]}{nullable}")

        sample_lines = []
        try:
            sample = con.execute(
                f'SELECT * FROM "{database}"."{schema}"."{tbl}" LIMIT 1'
            ).fetchdf()
            if not sample.empty:
                sample_lines = ["\n## Sample row"]
                for k, v in sample.iloc[0].items():
                    sample_lines.append(f"  {k}: {repr(v)}")
        except Exception:
            pass

        return header + "\n".join(col_lines) + "\n".join(sample_lines)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def run_sql(database: str, sql: str) -> str:
    """Execute a SELECT query against a hockey database. Returns up to 1,000 rows as TSV.

    DuckDB SQL syntax. Always qualify table names: database.schema.table

    Args:
        database: Connection context database (must match your access tier)
        sql: SELECT or WITH...SELECT query in DuckDB syntax

    Examples:
        run_sql("nhl", "SELECT lastName, goals, assists, points FROM nhl.main.skater_stats WHERE season=20242025 ORDER BY points DESC LIMIT 20")
        run_sql("swe", "SELECT league, COUNT(*) games FROM swe.main.games WHERE season='2024' GROUP BY 1 ORDER BY 2 DESC")
        run_sql("shl_analytics", "SELECT spelare, lag, mal, assist, poang FROM shl_analytics.raw.player_totals ORDER BY poang DESC LIMIT 20")
        run_sql("moneypuck", "SELECT name, team, xGoalsFor/(xGoalsFor+xGoalsAgainst) xgf_pct FROM moneypuck.main.skater_summaries WHERE season='2024' AND situation='5on5' AND games_played::INT>=40 ORDER BY xgf_pct DESC LIMIT 20")
        run_sql("nor", "SELECT p.first_name||' '||p.last_name name, s.goals, s.assists FROM nor.main.skater_summaries s JOIN nor.main.players p ON p.player_id=s.player_id ORDER BY s.goals+s.assists DESC LIMIT 20")
    """
    err = _check_db(database)
    if err:
        return f"Error: {err}"

    sql_stripped = sql.strip().rstrip(";")
    if not re.match(r"^\s*(SELECT|WITH)\b", sql_stripped, re.IGNORECASE):
        return "Error: only SELECT or WITH … SELECT queries are allowed"

    try:
        con = _conn(database)
        # Wrap in row cap — user can use LIMIT in their query for finer control
        capped = f"SELECT * FROM ({sql_stripped}) __tha_result LIMIT 1000"
        df = con.execute(capped).fetchdf()

        if df.empty:
            return "Query returned 0 rows."

        tsv = df.to_csv(sep="\t", index=False)
        if len(df) >= 1000:
            tsv += "\n[Result capped at 1,000 rows — add LIMIT to your query for finer control]"
        return tsv
    except Exception as e:
        return f"Query error: {e}"


# ── FastAPI wrapper with auth middleware ──────────────────────────────────────

app = FastAPI(
    title="THA MCP Server",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "tha-mcp-server", "mode": "local" if LOCAL_MODE else "http"}


@app.middleware("http")
async def auth_middleware(request: Request, call_next: Any) -> Response:
    if request.url.path in ("/health", "/"):
        return await call_next(request)

    api_key = (
        request.headers.get("X-API-Key")
        or request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    )

    if not api_key or api_key not in CUSTOMER_KEYS:
        return Response(
            content='{"error":"Unauthorized. Set X-API-Key header."}',
            status_code=401,
            media_type="application/json",
        )

    token = _customer.set(CUSTOMER_KEYS[api_key])
    try:
        response = await call_next(request)
    finally:
        _customer.reset(token)
    return response


# Mount MCP ASGI app at /mcp
# fastmcp 2.x exposes the ASGI app via http_app() or get_asgi_app()
try:
    _mcp_asgi = mcp.http_app()
except AttributeError:
    _mcp_asgi = mcp.get_asgi_app()  # older fastmcp API

app.mount("/mcp", _mcp_asgi)
