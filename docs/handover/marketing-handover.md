# Marketing Handover

> **Hi - if you're reading this, you've been asked to run the multi-channel
> launch for WorldOfTaxonomy. This doc is your onboarding in one read.
> It tells you what the product is, what's true today (so you don't
> overclaim), what assets exist, where to publish, in what order, and
> what decisions block you from Ram.**
>
> Read time: 25 minutes.
> Owner of this doc: Ram Katamaraja, Colaberry AI.
> Last refresh: 2026-05-03.
> Companion docs:
> - [public-launch-todo.md](public-launch-todo.md) - the master target
>   list (137 individual outreach surfaces). This handover is the
>   meta-plan; that doc is the per-target detail.
> - [launch/](../launch/) - first-draft posts for HN, LinkedIn,
>   Product Hunt, X. **Numbers in those drafts are stale; correct
>   per §3 below before sending.**
> - [launch-handover.md](launch-handover.md) - the deployment operator's
>   counterpart to this doc.

---

## 1. What you're launching, in 30 seconds

WorldOfTaxonomy is a unified knowledge graph of **1,000 global
classification systems** - NAICS, ISIC, NACE, HS, ICD-11, LOINC,
ESCO, ISCO, GICS, SOC, plus 990 more across industry, trade,
occupation, health, education, finance, and regulation. They all
describe overlapping economic reality but normally don't talk to
each other. WoT lets you translate any code in any system to
its equivalents in every other system, in one API call.

Three product surfaces, one knowledge graph behind them:

| Surface | Audience | URL |
|---|---|---|
| **Web app** | data scientists, journalists, students, curious humans | `worldoftaxonomy.com` |
| **REST API** | classical developers, integration teams | `wot.aixcelerator.ai/api/v1` |
| **MCP server** | AI agent builders (Claude Desktop, Cursor, custom GPTs) | distributed via PyPI |

---

## 2. The pitches you'll need

### 30-second pitch (cocktail)

"Every dataset uses a different classification system. US data uses
NAICS. EU data uses NACE. Health data uses ICD. Trade data uses HS
codes. They all describe the same world but none of them speak to
each other. WorldOfTaxonomy connects 1,000 of them in a single
queryable graph, so you can translate any code into any other system
with one API call. We also ship a Model Context Protocol server, so
AI agents can use the whole graph as structured tools."

### 90-second pitch (newsletter / podcast)

The 30-second version, then:

"Three surfaces. The web app at worldoftaxonomy.com is a free
visual explorer - 1.2 million codes, browseable by country, by
industry, by crosswalk. The REST API is for classical integrations -
30 requests per minute free, paid tiers for production volume. The
MCP server is the newest part: AI agents like Claude or Cursor can
call it directly to translate, classify, or look up codes inside a
conversation. The whole thing is open source under MIT - you can
self-host if you don't want to pay us. The reason we built it is we
kept paying $5K-50K per year for licensed crosswalk products and
they each only covered two or three system pairs. Ours covers
roughly 320,000 verified pairwise mappings across all 1,000
systems."

### 5-minute pitch (briefing)

Lead with the problem (data silos by jurisdiction), the size of
the unsolved gap (1,000 official classification standards exist
worldwide; commercial tools cover ~5 of them well), the technical
architecture (single Postgres graph + REST + MCP + Karpathy-style
LLM-readable wiki), and the distribution model (open-source MIT
core, paid hosted API for production load). Close with the
audience targets in §4.

---

## 3. Hard facts (use these numbers; don't paraphrase)

**Authoritative source: [CLAUDE.md](../../CLAUDE.md) header table.
If a number here disagrees with CLAUDE.md, trust CLAUDE.md.**

- **1,000** classification systems
- **1,212,173+** classification nodes (codes)
- **321,937+** verified crosswalk edges
- **249** countries with country-system profiles
- **3** product surfaces (web app, REST API, MCP server)
- **MIT** license (the free tier is genuinely free, including for
  commercial use)
- **26** MCP tools shipped at launch
- **`worldoftaxonomy.com`** for the web app
- **`wot.aixcelerator.ai`** for the API and MCP HTTP transport

### Things that look like facts but are NOT yet shipped

Don't promise these in any external copy until they ship:

- **Stripe / paid plans.** Pricing page exists but the integration
  isn't wired. If asked: "free tier today, paid tiers coming." Do
  not quote price points; they aren't decided yet.
- **PyPI release.** The MCP server isn't on PyPI yet. Once
  `v0.1.0` is tagged, this becomes a fact. Until then say "ship
  via clone + run."
- **Status page.** Not wired yet. If a journalist asks for one,
  link the GitHub repo's Issues page as the temporary
  transparency surface.
- **Cookie banner / EU consent.** Deferred. We have a privacy
  policy at `/privacy`; banner is not live.
- **Demo video.** Not made yet. The 90-second demo is in §6
  below as a script if you commission it.

### Stale numbers in existing draft posts (correct before sending)

[`docs/launch/`](../launch/) has four first-draft posts written when
the product had 279 systems and 570K codes. Every draft is **stale**.
Before sending any of them, find/replace:

| Stale | Replace with |
|---|---|
| 279 systems / 279 classification systems | 1,000 systems |
| 570,178 codes | 1,212,173+ nodes |
| 122,769 crosswalk edges | 321,937+ crosswalk edges |

The structure, headlines, and CTAs in those drafts are still good;
just the stat lines are outdated.

---

## 4. Audience segments (who you're actually selling to)

The launch is a one-product, four-audience pitch. Each audience
hears a different lead. **Do not collapse them into one message.**

| Segment | Where they live | Lead with | Avoid |
|---|---|---|---|
| **AI agent builders** (Claude/Cursor/custom GPTs) | r/ClaudeAI, r/MCP, Anthropic Discord, MCP directories | "WoT ships a Model Context Protocol server with 26 taxonomy tools, install in 30 seconds" | classical API framing |
| **Classical developers** | HN, RapidAPI, Postman, public-apis lists | "REST API with 30/min free tier, OpenAPI v3 spec, full crosswalk graph in one query" | MCP framing |
| **Data scientists / analysts** | r/datasets, dev.to, data eng newsletters, Kaggle | "Reconcile your NAICS-vs-ISIC join in 30 minutes instead of two days" | enterprise framing |
| **Enterprise buyers / RevOps** | LinkedIn, trade-association forums, customs brokerage groups | "Open-source alternative to D&B's classification tooling; self-host if you want, or use our hosted API" | playful / startup framing |
| **Journalists / editors** | TechCrunch, VentureBeat, Hacker Newsletter, newsletter editors | "Founder open-sourced a problem they solved at Colaberry; first unified taxonomy graph at this scale" | technical depth |

The product is the same. The headline is different. Don't write
one launch post and dump it everywhere.

---

## 5. Channel plan (the multi-channel sequence)

This is the launch sequence. Phase 0 is the soft launch (no public
push); Phase 1 is the public launch; Phases 2-3 are the slow-burn
distribution that compounds over weeks.

The exhaustive channel-by-channel target list is in
[public-launch-todo.md](public-launch-todo.md) (137 surfaces across
items 7, 8, 9). This section is the **prioritized plan** - what to
hit, in what order, owned by whom.

### Phase 0 - soft launch (no marketing, blocking on operations)

You wait. Do not push anything externally during Phase 0. The
soft-launch gate is in
[launch-checklist.md](launch-checklist.md) and is owned by the
deploy operator, not you. Three concrete blockers must clear:

1. **Cloud SQL DB seed** - production DB is empty until Ram restores
   his local dump. Without this, every link you send shows zero data.
2. **Resend API key** - magic-link emails don't deliver until this
   is provisioned. Anyone you invite to sign up gets nothing.
3. **Cloudflare** - in front of Cloud Run for DDoS / bot management.
   Without it, a successful launch post is a denial-of-service.

Use Phase 0 for **preparation work only**: assemble the press kit
(§7), commission the demo video (§6), correct the stale numbers in
[`docs/launch/`](../launch/), and pre-warm the search engines (§5,
"Search engines, day 1" below).

### Phase 1 - public launch day (all-hands, single Tuesday)

Pick a Tuesday. Avoid US public holidays and major tech-industry
release windows (Apple events, AWS re:Invent week, Google I/O).
Day-of sequence (Eastern Time):

| Time | Channel | Owner | Asset needed |
|---|---|---|---|
| 06:00 ET | Push live: status page, press kit, demo video on landing | Marketing | item 3, 4, 5 |
| 09:00 ET | **Hacker News Show HN #1** (MCP-focused) | Ram (account history matters) | corrected `hn_post.md` |
| 09:30 ET | First comment on HN with feedback questions | Ram | per `hn_post.md` template |
| 10:00 ET | Anthropic Discord `#community-projects` | Marketing | one-paragraph + GitHub link |
| 10:00 ET | r/ClaudeAI, r/MCP announcement | Marketing | personalized to each sub |
| 11:00 ET | Product Hunt submission | Hunter (>500 followers) | full press kit |
| 12:00 ET | LinkedIn long-form (Ram personal + Colaberry company page) | Ram + Marketing | corrected `linkedin_post.md` |
| 12:30 ET | X / Bluesky / Mastodon thread | Marketing | corrected `twitter_thread.md` |
| 14:00 ET | Reddit waves: r/dataisbeautiful, r/datasets, r/InternationalBusiness, r/MapPorn (one post each, personalized) | Marketing | per-sub copy |
| All day | Watch HN comments, respond within 15 min for first 4 hrs | Ram | - |

Hold these for Day 2-7, do **not** dump on Day 1:

- Newsletter pitches (Ben's Bites, Data Engineering Weekly, etc.)
- Blog cross-posts (dev.to / Medium / Hashnode)
- Domain-specific community posts (HL7, customs forums, etc.)

Day 1 is for top-of-funnel. Day 2-7 is for sustained discovery.

### Phase 2 - slow-burn distribution (weeks 1-4)

These are the channels where one good listing keeps sending traffic
for years. Owned by Marketing, no Ram involvement except sign-off
on copy. Pick 2-3 per week and complete them; do not batch all of
these into Day 1.

**Highest leverage (do these first):**

- [ ] PR to **modelcontextprotocol/servers** (Anthropic's official
      MCP list). Single most valuable submission for the MCP audience.
- [ ] PR to **APIs.guru / OpenAPI Directory**. Postman, Stoplight,
      SwaggerHub all index this; one PR distributes everywhere.
- [ ] PR to **public-apis/public-apis** (~300K stars).
- [ ] **Smithery.ai** submission for the MCP audience.
- [ ] **RapidAPI Hub** listing.

**Useful, lower priority:**

- [ ] mcp.so, glama.ai/mcp, mcphub.io
- [ ] Postman Public API Network (publish a Postman workspace)
- [ ] AlternativeTo, futuretools.io, theresanaiforthat.com
- [ ] Awesome-Public-Datasets, Awesome-Public-APIs, Awesome-MCP-Servers

The full enumeration is in
[public-launch-todo.md §7-9](public-launch-todo.md). Track each
submission in a spreadsheet (date submitted, status, accepted/rejected,
referrer-log evidence).

### Phase 3 - earned media + thought leadership (weeks 4-8)

- One technical blog post on launch ("Translating between 1,000
  classification systems with a single API call"). Cross-post to
  dev.to / Medium / Hashnode.
- Newsletter pitches: Ben's Bites, The Rundown AI, Data Engineering
  Weekly, Hacker Newsletter (curated).
- Domain-specific pitches: WCO trade community, HL7 informatics,
  SHRM HR-tech, federal data community on GitHub.
- Wikidata Q-item creation (permanent reference; AI engines weight
  this heavily).
- Conference CFPs if calendar permits: Strange Loop, MCP Conf
  (if/when), FOSDEM open-source data track, FedScoop summits.

### Search engines, day 1 (passive but essential)

Wire these on the soft-launch day, not the public-launch day. They
take days to start crawling.

- [ ] Google Search Console - verify property, submit sitemap
- [ ] Bing Webmaster Tools - same
- [ ] IndexNow - one POST per new URL pings Bing + Yandex + Naver
- [ ] (Optional) Yandex / Naver / Brave submit URLs

---

## 6. Demo video script (90 seconds)

You are commissioning this from a contractor or recording it
yourself. The script:

| Time | Visual | Voiceover |
|---|---|---|
| 0-15s | Show 5 windows, each with a different code for "truck driver" (NAICS 4841, NACE H494, ISCO 8332, SOC 53-3032, ANZSCO 7331). Zoom out, all 5 collide in confusion. | "Every dataset uses a different classification system. None of them talk to each other." |
| 15-30s | Cursor on `worldoftaxonomy.com` home page. Click `/explore`. Type "truck driver". | "WorldOfTaxonomy connects all 1,000 of them in one queryable graph." |
| 30-50s | Click into NAICS 4841. Show the crosswalk panel - all 5 systems' equivalents lit up. Click ISCO 8332, smooth transition to its detail page. | "Translate any code to any other system with one click - or one API call." |
| 50-70s | Switch to a terminal. `curl https://wot.aixcelerator.ai/api/v1/systems/naics_2022/nodes/4841/translations`. JSON streams in. | "Free for 30 requests per minute. Open source. MIT licensed." |
| 70-90s | Switch to Claude Desktop. Type "What's the ISCO equivalent of NAICS 4841?". Watch it call `translate_code` via MCP. | "And shipped as a Model Context Protocol server, so your AI agents speak the language of every classification system in the world." |

**Tools:** Loom or OBS for capture. ffmpeg for trim. Host on
YouTube; embed on landing page below the fold.

**Don'ts:** no music with lyrics (distracts from voiceover); no
talking-head shots (focus on the product); don't show admin
panels or any signed-in state with real email addresses.

---

## 7. Brand assets inventory

| Asset | Location | Format | Notes |
|---|---|---|---|
| Logo mark | `frontend/public/logo-mark.svg` | SVG | Primary mark |
| Logo lockup | `frontend/public/logo-lockup.svg` | SVG | Mark + wordmark |
| Mark mono | `frontend/public/logo-mark-mono-{black,white}.svg` | SVG | For one-color contexts |
| Lockup mono | `frontend/public/logo-lockup-mono-{black,white}.svg` | SVG | Same |
| Square 400/600 | `frontend/public/logo-square-{400,600}.png` | PNG | For PH, social, app icons |
| Favicon | `frontend/public/logo-favicon{,-light}.svg` | SVG | Browser tab |
| OpenGraph image | dynamic (Next.js `opengraph-image.tsx`) | PNG | Auto-generated social card |

**What's missing (you need to create these for the press kit):**

- 3-5 hero screenshots from the live site (`/`, `/explore`,
  `/system/naics_2022`, `/crosswalks`, `/classify`). 1920x1080 PNG.
  Take after the DB seed completes; until then, screenshots show
  zero rows.
- Founder photo (Ram). Headshot, 800x800 minimum.
- Colaberry logo (separate from WoT logo) at the same sizes as
  the WoT mark/lockup, for the "made by" attribution.
- 60-second silent product demo GIF for X / Bluesky (loops on
  hover; no audio because most platforms autoplay muted).

### Brand voice

- **Voice:** technically precise, plainspoken, no jargon. Optimize
  for "auditor satisfaction" - if a customer's compliance team
  asks where a number came from, the answer should already be in
  the prose, not in a follow-up email.
- **Tense:** present, declarative. ("WorldOfTaxonomy connects
  1,000 systems.") Not future ("will connect"), not aspirational
  ("aims to connect").
- **No em-dashes.** Project-wide style: use a hyphen `-`. CI
  enforces this on code; please mirror it in marketing copy too.
- **No exposing admin email publicly.** The site has a `/contact`
  form; route every "reach out" CTA through that. Do not put
  `ram@colaberry.com` or any individual address on a public asset.

---

## 8. Press kit checklist

A `/press` route does **not** exist yet. You can build it as a
single Markdown page rendered at `worldoftaxonomy.com/press`, or
host the assets in a public Notion/Drive folder and link from the
footer. Either is acceptable for soft launch.

Contents:

- [ ] Boilerplate: 50-word, 100-word, 200-word descriptions
- [ ] Stat block (1,000 / 1.2M / 321K / 26 MCP tools / MIT)
- [ ] 3-5 hero screenshots (see §7)
- [ ] Logo files (all 9 from §7)
- [ ] Founder bio + headshot (ask Ram for the bio he uses on
      LinkedIn; 100-word version is enough)
- [ ] Colaberry attribution: one paragraph on Colaberry AI, the
      parent company, and Ram's role
- [ ] Contact: link the `/contact` form, **not** an email address

---

## 9. KPIs

Track weekly. Do not aim at all of these on Day 1; the order
roughly matches when each becomes meaningful.

### Day-1 / launch-week metrics

- HN post score + duration on front page
- Product Hunt rank + total upvotes
- Cloud Run request rate + 5xx rate (Ops dashboard, not yours,
  but watch in case marketing traffic causes alerts)
- Sign-ups: API-key creates per hour
- Top-of-funnel: `worldoftaxonomy.com` unique visitors

### Week 1-4 metrics

- GitHub stars and clones (weekly delta)
- PyPI installs (`pepy.tech` once package is live)
- API-key conversion rate (visitors → signups → first API call)
- Referrer breakdown by source (Cloud Run logs partitioned by
  `Referer` host)
- MCP-server-init events at the protocol layer (Prometheus
  counter already exists)

### Month 1+ metrics

- Search Console: impressions, clicks, top queries
- Listings accepted vs rejected (per Phase 2 spreadsheet)
- Newsletter mention count (manual)
- Wikidata / Wikipedia references (manual)
- Customer-reported use cases (qualitative; ask in `/contact`
  thank-you reply)

### Reverse-funnel signals (the most important ones)

These tell you the product is finding fit, not just attention.

- **Repeat usage**: API keys with calls in week 2 that also had
  calls in week 1
- **Cross-system depth**: percentage of API calls hitting
  `/translations` (the unique-to-us endpoint) vs `/systems` (the
  generic browse one)
- **MCP retention**: number of `tools/call` per `initialize`
  (high ratio = sticky; low ratio = curiosity check-out)

---

## 10. Decisions only Ram can make

Don't move on these without his sign-off:

| Decision | Why blocked on Ram | Approximate when |
|---|---|---|
| Public-launch date | Soft launch must clear first; Ram + ops decide jointly | When Cloud SQL + Resend + Cloudflare are all green |
| Pricing tiers (free / pro / enterprise) | Affects every external claim about the product; can't be marketing-led | Before Phase 1 |
| Hunter for Product Hunt | Needs to be someone Ram trusts and who has > 500 followers | T-7 days from public launch |
| HN post timing + author | HN account history matters; Ram's account is the right one | Public-launch day |
| Quotes / testimonials | Anyone Ram is willing to attribute by name | Pre-press-kit |
| Negative-space restrictions | Anything Ram considers off-limits (clinical accuracy claims, legal advice, specific competitor positioning) | Before any external send |

---

## 11. Common pitfalls (read this twice)

1. **Don't promise paid tiers as live.** Stripe is not wired.
2. **Don't quote competitor pricing.** D&B / S&P / GICS-licensee
   numbers are confidential and quoting them creates legal risk.
3. **Don't claim clinical accuracy.** ICD-11, LOINC, SNOMED entries
   are reference data, not medical advice. The site footer has a
   Disclaimer; mirror that language in healthcare-targeted copy.
4. **Don't expose `ram@colaberry.com` or any admin address publicly.**
   Use the `/contact` form for every CTA.
5. **Don't post all four launch drafts the same day to the same
   audience.** They are the same person reading the same news four
   times. Stagger by audience (§4) and channel (§5).
6. **Don't use em-dashes.** Use a hyphen. Project-wide convention,
   reflected in code, docs, wiki, and (please) marketing.
7. **Don't ship the existing `docs/launch/*.md` drafts as-is.**
   Numbers are stale (§3). Update before sending.
8. **Don't crosspost on Reddit.** One post per subreddit,
   personalized. Crossposting is the fastest way to get
   shadowbanned.
9. **Don't dump every directory submission on Day 1.** Pace per
   §5 Phase 2; the goal is sustained traffic, not a single spike.
10. **Don't speak for Anthropic, OpenAI, Google, or Stripe in
    marketing copy.** "Works with Claude Desktop" is a fact;
    "endorsed by Anthropic" is not.

---

## 12. Quick links you'll use daily

- Live web app: https://worldoftaxonomy.com
- Live API: https://wot.aixcelerator.ai/api/v1
- API docs: https://wot.aixcelerator.ai/docs (FastAPI auto-gen)
- GitHub repo: https://github.com/colaberry/WorldOfTaxonomy
- llms-full.txt (LLM-readable site map): https://worldoftaxonomy.com/llms-full.txt
- Stat-line authoritative source: [CLAUDE.md](../../CLAUDE.md)
- Master target list (137 surfaces): [public-launch-todo.md](public-launch-todo.md)
- Existing draft posts (correct numbers first!): [`docs/launch/`](../launch/)
- Deploy operator's counterpart doc: [launch-handover.md](launch-handover.md)
- Soft-launch operational gate: [launch-checklist.md](launch-checklist.md)
- This doc: [marketing-handover.md](marketing-handover.md)

---

## 13. Day-zero checklist for you

Before you do anything externally:

- [ ] Read this doc end to end (~25 min)
- [ ] Read [public-launch-todo.md](public-launch-todo.md) §7-9 (~30 min)
- [ ] Skim [`docs/launch/*.md`](../launch/) (~10 min)
- [ ] Verify the stat line in [CLAUDE.md](../../CLAUDE.md) header
      against the numbers in §3 above; if they disagree, trust
      CLAUDE.md and update §3
- [ ] Confirm with Ram which audience leads the launch (§4) - in
      practice this is "all four, but staggered"; he may have a
      preference
- [ ] Confirm public-launch date with Ram (do not pick yourself)
- [ ] Get the hunter for Product Hunt lined up at least one week
      out
- [ ] Fix the stale numbers in `docs/launch/*.md` (one PR; takes
      15 minutes)
- [ ] Build the press kit (§8) - this is the only Phase 0
      deliverable that is on you, not on operations

After all of the above is done, you are ready to enter Phase 1 the
moment soft launch goes green.

Welcome aboard.
