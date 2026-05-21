"""THA MCP Server — stdio mode for local Claude Code / Claude Desktop usage.

Läser .env automatiskt. Full tillgång till alla databaser, ingen auth-nyckel krävs.

Konfigurера i Claude Code (~/.claude.json) eller Claude Desktop (claude_desktop_config.json):

    {
      "mcpServers": {
        "tha-hockey": {
          "command": "python",
          "args": ["/path/to/tha-mcp-server/stdio_server.py"],
          "env": {
            "MOTHERDUCK_TOKEN": "your_token_here"
          }
        }
      }
    }

Eller med uv (rekommenderas):
    {
      "mcpServers": {
        "tha-hockey": {
          "command": "uv",
          "args": ["run", "--project", "/path/to/tha-mcp-server", "python", "stdio_server.py"]
        }
      }
    }
"""
import os

# Must be set before importing server module
os.environ["MCP_LOCAL_MODE"] = "1"

from dotenv import load_dotenv
load_dotenv()

from mcp_server.server import mcp

if __name__ == "__main__":
    mcp.run()  # stdio transport (default)
