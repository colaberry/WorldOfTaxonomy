# Hacker News - "Show HN" Post

## Title

Show HN: World Of Taxonomy - 279 global classification systems in one open-source API

---

## Body

(Paste this as the description text. Edit the [BRACKETS] before posting.)

---

I built World Of Taxonomy because I kept running into the same problem: every dataset uses
a different classification system. US data uses NAICS. EU data uses NACE. ILO uses ISCO.
WHO uses ICD. They all describe the same economic reality but none of them talk to each
other. Reconciling them manually was costing me days.

World Of Taxonomy connects 279 classification systems - industry, trade, occupation, health,
education, finance, regulatory - into a single queryable knowledge graph with 570,178 codes
and 122,769 crosswalk edges.

The core idea: translate any code to any other system in one API call.

  GET /api/v1/systems/naics_2022/nodes/4841/translations

Returns equivalents in NACE, ISIC, ISCO, SOC, SIC, and every other system that has a
crosswalk to NAICS 4841 (general freight trucking).

What I think is genuinely novel:

1. Scope - I don't know of any other open-source project that federates this many
classification systems. Most "crosswalk" tools cover 2-3 system pairs. This covers
all pairwise combinations with a formal equivalence.

2. Country profiles - the API knows which systems apply to which countries. Ask for
Germany and you get WZ 2008 (official), NACE Rev 2 (regional), ISIC (recommended).
Ask for Japan and you get JSIC (official) + ISIC (recommended). 249 countries covered.

3. MCP server - it ships with a Model Context Protocol server so Claude and other AI
agents can use the entire taxonomy graph as structured tools. I've been using this to
auto-classify product descriptions and map supplier data across jurisdictions.

Demo: https://worldoftaxonomy.com
GitHub: https://github.com/colaberry/WorldOfTaxonomy
Docker: git clone + docker compose up (data ingestion takes ~5 minutes for core systems)

The main limitation: some systems require manual data download because their license
prohibits automated access (I document which ones in DATA_SOURCES.md). The free
systems (NAICS, ISIC, NACE, HS, ISCO, ICD, LOINC) ingest automatically.

Happy to answer questions about the architecture, the crosswalk methodology, or how
to add a new classification system. PRs welcome - there are still ~50 national
industry classification standards that belong in the graph.

---

## Posting tips

- Post on a Tuesday or Wednesday morning (9-10am ET) for best HN traction
- Have the demo URL live and fast before posting - HN traffic is immediate
- Watch the comments for the first 2 hours and respond to every question
- "Show HN" posts do best with honest limitations (included above)
- Don't edit the title after posting

## Follow-up comment to post early

Post this as the first comment right after submitting:

"A few things I'd especially love feedback on:

1. Is the API design intuitive? The /translations endpoint returns all equivalences
at once, but I'm unsure whether that should be paginated for systems with thousands
of leaf codes.

2. Are there classification systems you regularly work with that I've missed?
(Open issues are the best place to request them)

3. The MCP server is the newest part - has anyone used similar taxonomy MCP tools
in their AI workflows?"
