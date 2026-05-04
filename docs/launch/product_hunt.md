# Product Hunt Launch

## Tagline (60 chars max)

The Rosetta Stone for global industry classification

(alternatives:)
- 279 classification systems. One API. Zero reconciliation pain.
- Translate any industry code to any other standard, instantly.
- The open-source taxonomy graph for every industry on Earth.

---

## Description (260 words target)

Every country, standards body, and industry organization has its own classification
system. A hospital in the US is NAICS 622, in Germany it's WZ 86.10, globally it's
ISIC 8610. The same building. Three different codes. Zero official translation.

World Of Taxonomy fixes this.

We've built the world's most comprehensive open taxonomy knowledge graph: 279
classification systems, 570,178 codes, and 122,769 verified crosswalk edges - all
in one queryable API.

**What you can do with it:**
- Translate any NAICS code to NACE, ISIC, SIC, and 50+ other systems in one call
- Identify which classification systems officially apply to any of 249 countries
- Search across all 279 systems simultaneously with full-text search
- Use it with Claude and other AI agents via our MCP server

**Who it's for:**
- Data engineers reconciling cross-jurisdictional datasets
- Compliance teams mapping products across customs and trade systems
- AI developers giving language models structured industry knowledge
- Financial analysts bridging GICS sectors to national industry codes
- Academic researchers studying comparative classification

**Free and open source forever.** Self-host with Docker in under 2 minutes. No
vendor lock-in, no usage fees, no rate-limited free tier that turns into a bill.

The MCP server is what makes it AI-native: give Claude access to 570K codes across
industry, occupation, health, trade, and regulatory taxonomies as structured tools.

Built on FastAPI + PostgreSQL + Next.js. MIT licensed.

---

## Topics / Tags

open-source, developer-tools, data, api, classification, taxonomy, productivity,
artificial-intelligence, compliance, data-engineering

## Gallery images needed (get these from the live app)

1. World map showing 249 countries with taxonomy coverage (home page)
2. Dashboard showing 10 category tabs with system counts
3. API response showing translation of NAICS -> all other systems
4. MCP conversation in Claude: "classify this company's activities"
5. System detail page showing crosswalk edges

## Maker comment (post this right after launch)

"Hi PH! I built World Of Taxonomy after spending too many hours manually reconciling
US supplier data (NAICS) with EU reporting requirements (NACE). Every time I thought
'there must be a better way' - but there wasn't, so I built one.

The thing I'm most excited about is the MCP server. Being able to ask Claude to
'map this product catalog to HS codes for UK customs' and get a structured answer
in seconds is genuinely useful.

Self-hosting takes 2 minutes with Docker Compose, or try the hosted demo at https://worldoftaxonomy.com.
PRs welcome - there are still ~50 national classification systems that belong in the
graph and I'd love help adding them."
