# WorldOfTaxonomy AI Skills

Four packaged integrations that let AI assistants use WorldOfTaxonomy's 1,000+ classification systems, 1.2M+ nodes, and 320K+ crosswalk edges.

All four surface the same underlying capability: query, translate, and reason across global taxonomies (NAICS, ISIC, NACE, HS, ICD, SOC, ISCO, and hundreds more).

| Skill | Audience | Transport | Location |
|-------|----------|-----------|----------|
| MCP Server | Claude Desktop, Claude Code, Cursor, Zed, any MCP-aware client | stdio JSON-RPC | `world_of_taxonomy/mcp/` |
| Claude Code Skill | Claude Code users | Markdown skill file | `skills/claude-code/` |
| Anthropic Claude Skill | Claude.ai agent skills | `SKILL.md` bundle | `skills/anthropic/` |
| ChatGPT Custom GPT | ChatGPT Plus/Team/Enterprise | OpenAPI Action | `skills/openapi/` |
| Portable LLM Instructions | Gemini, Llama, generic agents | Plain markdown | `skills/portable/` |

## Shared backend

- REST API base URL: `https://worldoftaxonomy.com/api/v1`
- OpenAPI spec: `https://worldoftaxonomy.com/api/v1/openapi.json`
- Interactive docs: `https://worldoftaxonomy.com/docs`
- LLM full context: `https://worldoftaxonomy.com/llms-full.txt`
- Auth: API key header `Authorization: Bearer wot_<32hex>` (get one at `/dashboard` after signing in)
- Rate limits: Anonymous 30/min, Free 1000/min, Pro 5000/min, Enterprise 50000/min

## When to use this

An AI should reach for WorldOfTaxonomy when a user asks to:
- Classify a business, product, occupation, disease, or document under a standard code (NAICS, HS, ICD, SOC, etc.)
- Translate a code from one country/system to another (NAICS -> ISIC, ICD-10-CM -> ICD-10-GM, SOC -> ISCO)
- Find equivalents or crosswalks between any two classification systems
- Browse the hierarchy of a taxonomy or find siblings/children/ancestors of a code
- Audit coverage or compare two systems structurally
