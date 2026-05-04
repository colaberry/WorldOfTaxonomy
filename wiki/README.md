## Wiki - Curated Classification Guides

This directory contains curated markdown files that serve as the single source of truth for World Of Taxonomy's guide content. Each file is distributed through four channels automatically:

1. **Web pages** at `/guide/[slug]` (server-rendered HTML for SEO)
2. **MCP instructions** (injected into the AI agent context at session start)
3. **llms-full.txt** (concatenated plain text for AI crawlers)
4. **Wiki API** at `GET /api/v1/wiki` (for developers and RAG pipelines)

## How to Add a New Wiki Page

1. Create a new `.md` file in this directory
2. Add an entry to `_meta.json` with slug, file, title, description, and order
3. Run `python scripts/build_llms_txt.py` to regenerate llms-full.txt
4. The new page automatically appears in all four channels

## How to Edit Existing Content

1. Edit the `.md` file directly
2. Run `python scripts/build_llms_txt.py` to update llms-full.txt
3. Changes propagate to all channels on next build/deploy

## Content Guidelines

- **No em-dashes** (U+2014) - use hyphens `-` instead. CI enforces this.
- **H2/H3 structure** - every page must have at least one `##` heading
- **Self-contained** - each page should make sense on its own (for LLM context injection)
- **3-8K tokens per page** - keep pages focused; no single page should exceed 10K tokens
- **Total budget** - all pages combined should stay under 80K tokens
- **Mermaid diagrams** - use fenced code blocks with `mermaid` language for diagrams (renders on GitHub and in the web app)
- **No speculative content** - only document what exists in the system

## File Structure

```
wiki/
  _meta.json              # Page metadata (slug, title, description, order)
  getting-started.md      # API + MCP quickstart
  systems-catalog.md      # All 1,000+ systems listed
  crosswalk-map.md        # How systems connect
  industry-classification.md  # Which system to use
  medical-coding.md       # Health systems compared
  trade-codes.md          # Trade code relationships
  occupation-systems.md   # Occupation systems compared
  categories-and-sectors.md   # Categories and sectors
  data-quality.md         # Provenance and quality
  architecture.md         # System architecture diagrams
  README.md               # This file
```

## Testing

```bash
python3 -m pytest tests/test_wiki.py tests/test_api_wiki.py tests/test_mcp_wiki.py -v
```

## When to Update Wiki Pages

- Adding a new classification system that changes category counts or crosswalk topology
- Adding a new crosswalk - update `crosswalk-map.md`
- Expanding a major system - update the relevant comparison guide
- Changing the API surface - update `getting-started.md`
- Changing the architecture - update `architecture.md`
