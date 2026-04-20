# Portable LLM Skill

Drop-in instructions for any LLM agent framework (Gemini, Llama, local models, LangChain, LlamaIndex, custom pipelines) that can call HTTP APIs.

## Quick start

1. Copy `system_prompt.md` into your agent's system prompt.
2. Give the agent an HTTP tool pointing at `https://worldoftaxonomy.com/api/v1`.
3. Supply an API key header: `Authorization: Bearer wot_<32hex>` (get one at https://worldoftaxonomy.com/dashboard).

## Alternative: feed the full LLM context

For retrieval-free setups, include `https://worldoftaxonomy.com/llms-full.txt` as a pre-loaded document. It contains every endpoint, MCP tool, schema, example, and error code in ~650 lines of plain text designed for LLM ingestion.

## Why portable

The four AI integration surfaces we publish (MCP, Claude Code skill, Anthropic Claude Skill, ChatGPT Custom GPT) are all thin wrappers around the same REST API. This directory is the lowest-common-denominator version: plain markdown + HTTP. It works anywhere.

## Files

- `system_prompt.md` - paste this into any LLM's system prompt
- `tool_schemas.json` - JSON Schema for the 10 most useful endpoints, suitable for function-calling agents
