# Twitter / X Launch Thread

Post these as a thread from @ramdhanyk. Tweet 1 is the hook - it needs to stand
alone if people only see that one. All URLs and handles are filled in; ready to post.

---

## Tweet 1 - The hook (lead tweet, must grab attention)

I spent 2 years reconciling industry codes across datasets.
NAICS in the US. NACE in Europe. ISIC globally. ISCO for occupations.
None of them talk to each other.

So I built the Rosetta Stone for all of them.

1,000 classification systems. 1.2M+ codes. One open-source API.

[demo screenshot or GIF of the world map]

---

## Tweet 2 - The problem

The classification mismatch problem is everywhere:

- Your suppliers report in NAICS. Your EU partners use NACE.
- Your HR system uses SOC codes. The job board uses ISCO.
- Your drugs table uses ATC. Claims use ICD-10. Research uses ICD-11.

Every team that touches cross-border data hits this wall.

---

## Tweet 3 - The solution (show, don't tell)

One API call translates any code to every equivalent:

GET /systems/naics_2022/nodes/4841/translations

Returns NACE 49.4, ISIC 4923, SIC 4213, ISCO 8332...

And it works in reverse. And across all 1,000 systems.
Not a lookup table - a knowledge graph.

[screenshot of API response]

---

## Tweet 4 - The MCP angle (this is the unique hook for AI developers)

The part I'm most excited about:

It ships with an MCP server.

Add it to Claude Desktop and your AI gets 26 tools for taxonomy lookups.
"Classify this product description in HS codes"
"What NACE code corresponds to NAICS 5415?"
"Which systems officially apply to companies in Brazil?"

AI-native from day one.

[screenshot of Claude using the MCP tool]

---

## Tweet 5 - The numbers

The scale:

- 1,000 classification systems
- 1,212,173+ codes across all systems
- 321,937+ crosswalk edges linking them
- 249 countries with official taxonomy profiles
- 16 categories: industry, health, trade, occupational, regulatory...
- 400+ domain deep-dives for emerging sectors

Self-hosted with Docker in 2 minutes.

---

## Tweet 6 - Open source CTA

It's fully open source. MIT license. PRs welcome.

There are still ~50 national industry codes that belong in the graph.
If you work with a classification system we're missing, the contributing
guide makes adding one take about 2 hours.

GitHub: https://github.com/colaberry/WorldOfTaxonomy
Demo: https://worldoftaxonomy.com

---

## Timing notes

- Post Tuesday-Thursday, 9-11am ET (peak developer Twitter hours)
- Reply to every response in the first 2 hours - thread engagement drives reach
- Tag relevant accounts: @AnthropicAI (MCP server angle), @HuggingFace (dataset angle)
- Post the HN link as a follow-up tweet once the HN post gets traction

## Hashtags (add to the last tweet only, not all of them)

#OpenSource #DataEngineering #API #BuildInPublic #MCP #AI
