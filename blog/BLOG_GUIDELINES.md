# Blog Writing Guidelines

Quality checklist for every World Of Taxonomy blog post. Follow these standards before publishing.

## Structure

- [ ] **TL;DR callout** at the top: `> **TL;DR:** One-sentence summary with key stats.`
- [ ] **Horizontal rule** (`---`) after the TL;DR to separate it from the body
- [ ] **Clear section headers** using `##` (no single `#` - the post title is the `#`)
- [ ] **Short paragraphs** - max 3-4 sentences per paragraph. Walls of text are not acceptable.
- [ ] **No orphan sections** - every `##` section must have content below it

## Visual elements (at least 2 per post)

- [ ] **Mermaid diagram** - at least one per post. Use `graph`, `sequenceDiagram`, `erDiagram`, or `flowchart` as appropriate.
- [ ] **Structured table** - at least one per post. Use tables for comparisons, system lists, feature matrices, and data summaries.
- [ ] **Blockquote callouts** (`>`) for key insights, important warnings, or memorable takeaways
- [ ] **Code blocks** with language tags for API examples (`bash`, `python`, `json`, `sql`)

## Content quality

- [ ] **No jargon without context** - if a term is domain-specific, explain it briefly on first use
- [ ] **Concrete examples** - every concept must be illustrated with a real system, real code, or real use case
- [ ] **API examples** - include at least one `curl` command showing the relevant API endpoint
- [ ] **Use cases section** - who benefits and how. Use a table: `| Who | What | Systems |`

## Formatting rules

- [ ] **No em-dashes** (U+2014) anywhere. Use hyphens `-` instead. CI enforces this.
- [ ] **No trailing whitespace**
- [ ] **File name format**: `kebab-case.md` matching the slug in `_meta.json`
- [ ] **Author**: Use full name (Ram Katamaraja), not shortened forms

## Mermaid diagram guidelines

- Use `graph TD` or `graph LR` for hierarchy/flow diagrams
- Use `sequenceDiagram` for API call flows
- Use `erDiagram` for data model illustrations
- Keep node labels short (2-4 words + optional `\n` line break for stats)
- Use `style` directives sparingly - only to highlight the focal node
- Use `-.->` for approximate/crosswalk relationships, `-->` for definite/hierarchical ones
- Use subgraphs to group related nodes by category

## _meta.json entry

Every post must have a corresponding entry in `blog/_meta.json`:

```json
{
  "slug": "kebab-case-title",
  "file": "kebab-case-title.md",
  "title": "Human-Readable Title",
  "description": "One sentence, under 160 chars, for SEO and RSS feed.",
  "date": "YYYY-MM-DD",
  "author": "Ram Katamaraja",
  "tags": ["tag1", "tag2"]
}
```

## Before publishing

1. Run `npm run blog:copy` in `frontend/` to sync content
2. Check the post renders at `http://localhost:3000/blog/{slug}`
3. Verify Mermaid diagrams render correctly (not just raw code blocks)
4. Check `/feed.xml` includes the new post
5. Grep for em-dashes: `grep -rP '\x{2014}' blog/` should return nothing
