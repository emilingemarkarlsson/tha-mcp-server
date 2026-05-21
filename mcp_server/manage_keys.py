#!/usr/bin/env python3
"""THA MCP Server — API key management CLI.

Usage:
    python -m mcp_server.manage_keys add --name "Frisk Asker" --tier nor
    python -m mcp_server.manage_keys add --name "My Team" --dbs nhl,moneypuck
    python -m mcp_server.manage_keys list
    python -m mcp_server.manage_keys export          # prints CUSTOMER_KEYS JSON for env var
    python -m mcp_server.manage_keys remove tha-abc123
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys

from .schema_hints import ALL_DBS, TIER_PRESETS

KEYS_FILE = os.path.join(os.path.dirname(__file__), ".keys.json")


def _load() -> dict:
    if not os.path.exists(KEYS_FILE):
        return {}
    with open(KEYS_FILE) as f:
        return json.load(f)


def _save(keys: dict) -> None:
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=2)
    print(f"[saved → {KEYS_FILE}]")


def cmd_add(args: argparse.Namespace) -> None:
    if args.tier:
        dbs = TIER_PRESETS.get(args.tier, [])
        tier = args.tier
    elif args.dbs:
        raw = [d.strip() for d in args.dbs.split(",")]
        unknown = [d for d in raw if d not in ALL_DBS]
        if unknown:
            print(f"Unknown databases: {', '.join(unknown)}")
            print(f"Valid: {', '.join(ALL_DBS)}")
            sys.exit(1)
        dbs = raw
        tier = "custom"
    else:
        print("Provide --tier or --dbs")
        sys.exit(1)

    keys = _load()
    raw_key = f"tha-{secrets.token_hex(8)}"
    keys[raw_key] = {"name": args.name, "dbs": dbs, "tier": tier}
    _save(keys)

    print(f"\nKey created:")
    print(f"  key:  {raw_key}")
    print(f"  name: {args.name}")
    print(f"  tier: {tier}")
    print(f"  dbs:  {', '.join(dbs)}")
    print(f"\nClaude Desktop config snippet:")
    print(json.dumps({
        "mcpServers": {
            "tha-hockey": {
                "url": "https://mcp.thehockeyanalytics.com/mcp",
                "headers": {"X-API-Key": raw_key},
            }
        }
    }, indent=2))


def cmd_list(args: argparse.Namespace) -> None:
    keys = _load()
    if not keys:
        print("No keys configured. Use 'add' to create one.")
        return
    print(f"{'Key':<26}  {'Name':<30}  {'Tier':<12}  Databases")
    print("-" * 100)
    for k, v in keys.items():
        print(f"{k:<26}  {v['name']:<30}  {v.get('tier','?'):<12}  {', '.join(v.get('dbs',[]))}")


def cmd_export(args: argparse.Namespace) -> None:
    """Print the CUSTOMER_KEYS JSON blob for use as env var."""
    keys = _load()
    print(json.dumps(keys))


def cmd_remove(args: argparse.Namespace) -> None:
    keys = _load()
    if args.key not in keys:
        print(f"Key not found: {args.key}")
        sys.exit(1)
    name = keys.pop(args.key)["name"]
    _save(keys)
    print(f"Removed key for '{name}'")


def cmd_tiers(args: argparse.Namespace) -> None:
    """Show available tier presets."""
    print("Available tiers:")
    for tier, dbs in TIER_PRESETS.items():
        print(f"  {tier:<12} → {', '.join(dbs)}")


def main() -> None:
    p = argparse.ArgumentParser(
        prog="python -m mcp_server.manage_keys",
        description="THA MCP API key manager",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="Create a new API key")
    a.add_argument("--name", required=True, help="Customer / key description")
    a.add_argument("--tier", choices=list(TIER_PRESETS), help="Tier preset")
    a.add_argument("--dbs", help="Comma-separated DB list (alternative to --tier)")

    sub.add_parser("list", help="List all keys")
    sub.add_parser("export", help="Export CUSTOMER_KEYS JSON for env var")
    sub.add_parser("tiers", help="Show tier presets")

    r = sub.add_parser("remove", help="Remove a key")
    r.add_argument("key", help="Key to remove (e.g. tha-abc123)")

    args = p.parse_args()
    {
        "add": cmd_add,
        "list": cmd_list,
        "export": cmd_export,
        "remove": cmd_remove,
        "tiers": cmd_tiers,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
