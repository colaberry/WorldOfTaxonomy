# MCP setup guide

> **TL;DR:** Get an API key at [worldoftaxonomy.com/developers](https://worldoftaxonomy.com/developers),
> paste it into your AI client's MCP config, and ask the assistant
> taxonomy questions in plain English. Five minutes start to finish.

The WorldOfTaxonomy MCP server gives AI assistants (Claude Desktop,
Cursor, Zed, VS Code Continue, and any other MCP client) direct
access to 1,000+ classification systems, 1.2M+ codes, and 321K+
crosswalk edges. Once installed, you can ask things like
"convert NAICS 5415 to NACE" or "find ICD-10 codes related to type 2
diabetes" and get authoritative answers without leaving the editor.

## Step 1: Get your API key

1. Visit [worldoftaxonomy.com/developers](https://worldoftaxonomy.com/developers).
2. Enter your email and click **Send me a sign-in link**.
3. Open the email and click the link. The dashboard loads.
4. Click **Generate new key**. Name it after where you'll use it
   (e.g., `MCP on laptop`).
5. Copy the key shown on screen. **It's shown only once.**

The key looks like `wot_a3f2c5d9b8e7f6c4d2a1b0c9d8e7f6a5` (free-tier
keys start with `wot_`; restricted or cross-product keys may use
`rwot_` or `aix_`).

Free tier gives you **1,000 requests per minute** shared across your
team. No credit card. See
[API key management](./api-keys.md) for rotation, revocation, and
scoping.

## Step 2: Install for your AI client

Pick the client you use. Each has its own config file location.

### Claude Desktop

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this to the `mcpServers` block (create the block if it doesn't
exist):

```json
{
  "mcpServers": {
    "worldoftaxonomy": {
      "command": "uvx",
      "args": ["worldoftaxonomy-mcp"],
      "env": {
        "WOT_API_KEY": "wot_a3f2c5d9b8e7f6c4d2a1b0c9d8e7f6a5"
      }
    }
  }
}
```

Restart Claude Desktop (Cmd-Q, relaunch). You'll see a small hammer
icon at the bottom of the chat input - that's MCP. Click it to
confirm `worldoftaxonomy` appears in the tool list.

If you don't have `uvx` installed, replace `command` with `npx` and
`args` with `["-y", "@worldoftaxonomy/mcp"]`. Either works.

### Cursor

Cursor uses MCP via Settings -> Features -> Model Context Protocol.

1. Open **Settings** -> **Features** -> **Model Context Protocol**.
2. Click **Add new MCP server**.
3. Enter:
   - **Name**: `worldoftaxonomy`
   - **Type**: `stdio`
   - **Command**: `uvx worldoftaxonomy-mcp`
4. Add an environment variable: `WOT_API_KEY` = your key.
5. Save and restart Cursor.

### Zed

Zed uses `~/.config/zed/settings.json`. Add to `context_servers`:

```json
{
  "context_servers": {
    "worldoftaxonomy": {
      "command": {
        "path": "uvx",
        "args": ["worldoftaxonomy-mcp"],
        "env": {
          "WOT_API_KEY": "wot_a3f2c5d9b8e7f6c4d2a1b0c9d8e7f6a5"
        }
      }
    }
  }
}
```

Restart Zed.

### VS Code (with Continue extension)

Continue's MCP support lives in `~/.continue/config.json`:

```json
{
  "experimental": {
    "modelContextProtocolServers": [
      {
        "transport": {
          "type": "stdio",
          "command": "uvx",
          "args": ["worldoftaxonomy-mcp"],
          "env": {
            "WOT_API_KEY": "wot_a3f2c5d9b8e7f6c4d2a1b0c9d8e7f6a5"
          }
        }
      }
    ]
  }
}
```

Restart the Continue extension (Cmd-Shift-P -> "Continue: Restart").

### Windsurf

Windsurf uses `~/.codeium/windsurf/mcp_config.json` with the same
schema as Claude Desktop:

```json
{
  "mcpServers": {
    "worldoftaxonomy": {
      "command": "uvx",
      "args": ["worldoftaxonomy-mcp"],
      "env": {
        "WOT_API_KEY": "wot_a3f2c5d9b8e7f6c4d2a1b0c9d8e7f6a5"
      }
    }
  }
}
```

Restart Windsurf.

### Generic MCP client

If your client is a generic MCP host:

- **Transport**: stdio
- **Command**: `uvx worldoftaxonomy-mcp` (or `npx -y @worldoftaxonomy/mcp`)
- **Required env var**: `WOT_API_KEY`
- **Protocol version**: MCP 2024-11-05 or later

## Step 3: Verify it works

Open a chat with your AI client and try one of these prompts:

> "Look up NAICS 2022 code 5417 and tell me what NACE Rev 2 code it
> maps to."

> "Find ICD-10-CM codes related to type 2 diabetes mellitus."

> "Translate ISIC Rev 4 division 84 to its equivalent in the German
> WZ 2008 classification."

> "What classification systems are commonly used in Brazil?"

The assistant should call MCP tools (you'll see something like
`get_industry`, `translate_code`, or `get_equivalences` in the tool
log) and answer with specific codes and titles, not generic AI
reasoning.

## Available tools

The MCP server exposes ~26 tools. The most commonly used:

| Tool | Use it for |
|---|---|
| `list_classification_systems` | "What systems are available?" |
| `search_classifications` | Full-text search across all codes |
| `get_industry` | Look up a specific code |
| `browse_children` | Drill into a category |
| `get_equivalences` | Get all crosswalk mappings for a code |
| `translate_code` | Convert between two specific systems |
| `translate_across_all_systems` | Convert to every connected system |
| `classify_business` | Free text -> taxonomy codes |
| `get_country_taxonomy_profile` | Systems applicable in a country |

The full list with arguments and return types is in the API reference
at [worldoftaxonomy.com/api](https://worldoftaxonomy.com/api).

## Troubleshooting

### "WOT_API_KEY not set" on startup

The MCP server requires the key as an environment variable. Re-check
the `env` block in your client's config. Mac/Linux users can verify by
running the server directly:

```bash
WOT_API_KEY=wot_a3f2c5d9... uvx worldoftaxonomy-mcp
```

If this prints `Server ready (stdio)` and waits, your key is fine and
the issue is in your client's config file location.

### "Authentication failed" / 401 errors

Your key may be revoked or expired. Sign in at
[worldoftaxonomy.com/developers](https://worldoftaxonomy.com/developers),
check the key's status in the dashboard. Generate a new one if
needed; both old and new work simultaneously, so update your
`mcp.json` first, then revoke the old.

### "Rate limit exceeded" / 429 errors

You or your team has hit the free-tier 1,000 req/min ceiling.
Options:

- Wait 60 seconds and retry. The bucket refills.
- If you're on a corporate domain with multiple developers sharing
  the pool, ask the org admin who's burning the budget.
- Upgrade to the Pro tier (10,000 req/min pool) at
  [worldoftaxonomy.com/pricing](https://worldoftaxonomy.com/pricing).

### Tools don't appear in the AI client

1. Restart the client fully (quit and relaunch, not just close
   the window).
2. Verify the config file is valid JSON. A trailing comma or
   missing brace silently disables MCP.
3. Check the client's MCP log:
   - **Claude Desktop**: View -> Developer -> View Logs from MCP servers.
   - **Cursor**: Cmd-Shift-P -> "Cursor: Show Logs" -> filter for `mcp`.
   - **Zed**: Cmd-Shift-P -> "zed: open log" -> search for `worldoftaxonomy`.

### "Command not found: uvx" or "npx"

Install the runner:

- **uvx**: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Mac/Linux)
  or `irm https://astral.sh/uv/install.ps1 | iex` (Windows).
- **npx**: ships with Node.js. Install Node.js 18+ from
  [nodejs.org](https://nodejs.org).

Either runner works; pick whichever you already have.

### Server crashes when answering certain questions

Capture the error from the client's MCP log and report it via the
**Report incorrect description** link on the relevant node detail
page, or open an issue on the [GitHub repo](https://github.com/colaberry/WorldOfTaxonomy).
Include the exact prompt and the MCP log excerpt.

## What's next

- [API quickstart](./getting-started.md) for direct REST access
- [Crosswalk map](./crosswalk-map.md) to understand which systems
  connect to which
- [Industry classification guide](./industry-classification.md) for
  picking the right industrial system for your use case
- [Medical coding](./medical-coding.md) for ICD-10, ICD-11, MeSH,
  LOINC, ATC comparison
- [Trade codes](./trade-codes.md) for HS, CPC, UNSPSC, SITC
