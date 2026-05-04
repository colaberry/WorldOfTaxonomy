# Public-launch TODO

Items to land before the public HN/X push. **Not** required for soft
launch; the soft-launch gate is in
[launch-checklist.md](./launch-checklist.md). Each item links to its
detail location and lists the rough effort + the unblock condition.

| # | Item | Effort | Unblocked by |
|---|---|---:|---|
| 1 | [Pricing page with real numbers](#1-pricing-page-with-real-numbers) | 1d | Stripe Price IDs created in dashboard (pricing decisions LOCKED 2026-05-04) |
| 2 | [Stripe integration](#2-stripe-integration) | 2-3d | None (pricing LOCKED, see [stripe-integration.md](stripe-integration.md)) |
| 3 | [Press kit](#3-press-kit) | 0.5d | None |
| 4 | [Status page](#4-status-page) | 0.5d | Cloud Run alerts wired |
| 5 | [Demo video (~2 min)](#5-demo-video-2-min) | 1d | Pricing copy locked |
| 6 | [Phase 1-5 Zitadel + Permit.io migration](#6-phase-1-5-zitadel--permitio-migration) | ~1w | Soft-launch traffic patterns observed |
| 7 | [MCP server registration / discoverability](#7-mcp-server-registration--discoverability) | 1d | First PyPI release tag |
| 8 | [REST API registration / discoverability](#8-rest-api-registration--discoverability) | 1d | OpenAPI spec frozen at v1 |
| 9 | [Website outreach / discoverability](#9-website-outreach--discoverability) | 2d | Soft launch live + status page + press kit |

## 1. Pricing page with real numbers

A `/pricing` page exists with placeholder content. Pricing decisions
were locked 2026-05-04; the page now needs the actual numbers wired
plus "Subscribe" buttons that POST to `/api/v1/billing/checkout`.

**Locked tiers** (verbatim from
`.claude/.../memory/project_pricing_tiers.md`):

- **Free** ($0): 30/min anonymous, 200/min authenticated, 50K/day
  cap; 20 /classify calls/day; MCP stdio mode only.
- **Pro** ($49/month or $490/year, ~17% annual discount): 5,000/min
  unlimited daily; 200 /classify calls/day included with metered
  overage at **$0.05/call** above the bucket; MCP HTTP-mode included;
  bulk JSON export; webhook notifications; per-key analytics; 14-day
  free trial card-required.
- **Enterprise** (starts $499/month, sales-led, "Contact us"):
  50,000+/min; unlimited /classify; 99.9% SLA; private classification
  systems; dedicated support channel; annual contract.

The /pricing page should render two pricing cards (Pro, Enterprise)
plus a Free panel. Enterprise card says "Contact us", not a price.
See [stripe-integration.md](stripe-integration.md) Day 3 for the
frontend wiring.

## 2. Stripe integration

Provision a Stripe account, define products (free, pro, enterprise) +
price points, wire customer-portal handoff, write the webhook handler
that bumps `org.tier` + `org.stripe_customer_id` when the subscription
state changes.

Pricing was locked 2026-05-04 (see item 1 above). The full developer
handover is in [stripe-integration.md](stripe-integration.md): three-day
sequencing, migration SQL, endpoint contracts, webhook event handling,
and frontend changes. Read that doc first.

Org-tier is already in the schema (Phase 6); the gap is the Stripe
half. Hosted Stripe pages take care of the PCI surface; we never
touch card numbers.

## 3. Press kit

A single page (or `/press` route) with:

- Logo files (mark + lockup, light/dark, SVG + PNG @ 400/600/1200)
- One-paragraph description for journalists
- 3-5 hero screenshots
- Founder bios + headshots
- Stats line ("1,000 systems / 1.2M nodes / 321K edges")

Most assets already exist in `frontend/public/logo-*` and
`frontend/public/opengraph-image.tsx`. Collating them into one
authoritative location is the work.

## 4. Status page

Pick one of:

- **statuspage.io** (Atlassian, paid)
- **Better Stack** (free tier covers this)
- **Instatus** (free for one page)
- self-host on Cloudflare Pages with our own component-by-component status JSON

Cloud Run alerts already exist (PR #133). Wire them to the status page
of your choice. ~30 min for setup + ~2 hrs for the integration.

## 5. Demo video (~2 min)

Goal: someone scrolling the landing page should understand the product
in 90 seconds. Suggested script:

- 0-15s - the problem (5 different codes for "truck driver", show the
  matrix)
- 15-45s - browse the website, hit /classify with a real description,
  show the cross-system results
- 45-90s - same query through the API + MCP server (show Claude
  Desktop calling search_classifications)
- 90-120s - call to action (sign up, see /developers)

Tools: Loom for capture, ffmpeg for trim, host on YouTube + embed.

## 6. Phase 1-5 Zitadel + Permit.io migration

Current state: magic-link sign-in via `developers.py`, no central IdP,
no policy engine. Memory references for context:
`.claude/.../memory/project_auth_decision.md` and
`project_authz_decision.md`.

Phases per `auth-implementation.md`:

1. Provision Zitadel Cloud (free tier) at
   `<instance>.zitadel.cloud`
2. Wire Zitadel as the OIDC IdP for the `/login` page (replaces
   magic-link as the only path; magic-link stays as fallback)
3. Migrate `/auth/me` and `/auth/keys` to read Zitadel claims
4. Provision Permit.io (free tier), wire ABAC + ReBAC policy engine
5. Move `require_scope` and `require_tier` checks from in-process to
   Permit.io PDP

Trigger: when magic-link auth proves insufficient at scale, or when
the second product (WoO) needs the same identity layer. Until then,
magic-link + OAuth + slowapi is enough. Don't pre-build identity
infrastructure for traffic that may never arrive.

## 7. MCP server registration / discoverability

Once the package is on PyPI (a soft-launch checklist item, see
[launch-checklist.md L218](./launch-checklist.md)), submit / register
the MCP server in every directory and channel that AI agents,
developers, and AI-tool users browse for MCP servers. None of these
take more than a few minutes per submission; the bulk of the effort is
proofreading the listings.

### Official + canonical

- [ ] **Anthropic's official MCP servers list** -
      [github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers).
      Open a PR adding our entry to the "Community" section of the
      README. Keep the description short and link the PyPI package +
      our `/mcp` page. This is the most-cited list; getting accepted
      here is the highest-leverage single action.
- [ ] **awesome-mcp-servers** community lists. The two with the most
      stars at time of writing:
      [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)
      and
      [appcypher/awesome-mcp-servers](https://github.com/appcypher/awesome-mcp-servers).
      Both accept PRs. Submit to both.
- [ ] **GitHub topics** - tag our repo with `mcp`, `mcp-server`,
      `model-context-protocol`, `classification`, `taxonomy`,
      `knowledge-graph`. Topics surface in GitHub discovery.

### Public MCP marketplaces / directories

- [ ] **smithery.ai** - submit at
      [smithery.ai/new](https://smithery.ai/new). They auto-build a
      one-click install URL for Claude Desktop, Cursor, and Windsurf.
- [ ] **mcp.so** - submit at [mcp.so/submit](https://mcp.so/submit).
      Indexes by category; we land in "Knowledge / Reference".
- [ ] **glama.ai/mcp** - submit at
      [glama.ai/mcp](https://glama.ai/mcp/servers). Includes badge
      art we can embed in the README.
- [ ] **mcphub.io** - submit there too if active at launch time.

### Client-side discovery

- [ ] **Cursor Directory** - Cursor publishes a directory of MCP
      servers at [cursor.directory](https://cursor.directory). Submit
      via their PR template.
- [ ] **Claude Desktop** - the install snippet on our `/mcp` page
      should include the exact `mcp.json` block users paste into
      Claude Desktop config. Already done in PR #137; double-check
      the path remains correct after the PyPI release.
- [ ] **Continue.dev** (VS Code AI extension) - their docs link to
      MCP servers; submit a docs PR if they accept community entries.

### Package + binary distribution

- [ ] **PyPI** (the install path itself). Tag a `vX.Y.Z` release;
      Trusted Publishing is already wired (PR #136) so the GitHub
      Action publishes automatically.
- [ ] **npm** - if we ship the npm wrapper later, mirror
      `@worldoftaxonomy/mcp` there for Node-first users.
- [ ] **conda-forge** - lower priority; some research users prefer
      conda. Ship after the PyPI version has been stable for a month.

### Adjacent communities (not registries, but where AI-tool users live)

- [ ] **r/ClaudeAI**, **r/LocalLLaMA**, **r/MCP** subreddits -
      announcement post on launch day, link the GitHub repo + the
      `/mcp` page.
- [ ] **Hacker News** - "Show HN: WoT - REST + MCP for 1,000
      classification systems". Headline focuses on a concrete
      developer use case, not the abstract idea.
- [ ] **Anthropic Discord** - they have a `#community-projects`
      channel; post once with a one-paragraph description + GitHub
      link.
- [ ] **MCP-Tools community** - Slack / Discord channels listed in
      the official MCP repo's CONTRIBUTING.md.

### ChatGPT / GPT Store (separate from MCP)

- [ ] **Custom GPT** - we have an existing skill in the repo for
      Claude. A ChatGPT Custom GPT with the same skill (search +
      classify) reaches a different audience. Publish to the GPT
      Store; ~30 min if the skill is already written, more if not.

### Track + measure

After submitting, watch:

- GitHub repo stars + clones (build a weekly cron in
  `scripts/audit_*` style)
- PyPI install stats via [pepy.tech](https://pepy.tech)
- Referrer logs in Cloud Run for traffic from each registry domain
- MCP-server-init events at the protocol layer (already counted via
  the existing Prometheus counters)

This is the cheapest customer-acquisition channel we have - one good
listing on Anthropic's repo can outweigh a Hacker News post in
sustained traffic.

## 8. REST API registration / discoverability

The MCP audience overlaps with but does not equal the API audience.
Where MCP-side reach is mostly AI-tool users, the API-side reach is
classical developers who never touch an LLM. Different directories,
different communities. The unblock condition is a **stable, public
OpenAPI v3 spec** at `/api/v1/openapi.json` (FastAPI emits this for
free; verify it is reachable + clean before submitting anywhere).

### Official + canonical

- [ ] **APIs.guru / OpenAPI Directory** -
      [github.com/APIs-guru/openapi-directory](https://github.com/APIs-guru/openapi-directory).
      Single highest-leverage API submission. Postman, Stoplight,
      SwaggerHub, ReadMe, and dozens of devtools index this list. PR
      adds a `worldoftaxonomy.com.yaml` pointing at our hosted spec.
- [ ] **public-apis/public-apis** -
      [github.com/public-apis/public-apis](https://github.com/public-apis/public-apis).
      ~300k-star awesome list; submission is a one-line PR adding us
      under "Government" or "Open Data" (taxonomy data is closer to
      reference than government). Massive discoverability.
- [ ] **GitHub topics** - tag the repo with `rest-api`, `openapi`,
      `swagger`, `taxonomy`, `classification`, `naics`, `isic`,
      `nace`, `hs-codes`. Topics surface in GitHub's Explore page +
      its API consumers (e.g. SourceGraph code search).

### Public API marketplaces

- [ ] **RapidAPI Hub** - [rapidapi.com](https://rapidapi.com). The
      largest commercial API marketplace. Listing requires an
      OpenAPI spec + a pricing schedule. Set the free tier at our
      anonymous rate (30/min) so the listing remains true after the
      Stripe paid tier ships.
- [ ] **Postman Public API Network** - publish a Postman workspace
      with example collections. [postman.com/explore](https://postman.com/explore).
      Strong discoverability inside Postman's own product, and the
      collections double as quickstart docs.
- [ ] **SwaggerHub** (SmartBear) - host the spec there as a public
      project. SmartBear's directory indexes public APIs + the page
      auto-generates code samples in 10+ languages.
- [ ] **ReadMe.io** - if we want hosted API docs separate from our
      `/api` page. ReadMe-hosted docs come with built-in
      discoverability + a "try it" sandbox. Optional; skip if our
      `/api` page is good enough.
- [ ] **APIList.fun** / **AnyAPI** - smaller catalogs; one-line
      submissions, low effort.

### AI-developer surfaces (different audience than MCP)

- [ ] **OpenAI Plugin Manifest** - publish at
      `worldoftaxonomy.com/.well-known/ai-plugin.json` so
      ChatGPT Custom GPTs and other plugin-aware agents can install
      our API as a tool without an MCP client. Effort: 1 hour
      (manifest + matching OpenAPI spec at the well-known path).
- [ ] **Anthropic Tool Use** docs - we are not a tool ourselves,
      but if we appear in their public examples list (e.g. the
      "real-world tool examples" page), that drives adoption. Open
      a docs PR if their examples are community-sourced.

### Open-data + classification-domain channels

- [ ] **Awesome-Public-Datasets** -
      [github.com/awesomedata/awesome-public-datasets](https://github.com/awesomedata/awesome-public-datasets).
      We are reference data, not raw datasets, but several entries
      in the "Government" section are similar in spirit. Worth a
      submission.
- [ ] **datahub.io** / **OpenDataSoft** - if we ship periodic data
      dumps (post-Pro-launch), these aggregate open data with
      indexed search. Skip until dumps exist.
- [ ] **Hugging Face Datasets** - publish a snapshot of
      `classification_node` + `equivalence` tables as a
      versioned dataset. ML researchers find taxonomy data through
      HF, not through API directories. Effort: 0.5d for a first
      snapshot + a release script.
- [ ] **Awesome-X domain lists** - awesome-naics, awesome-trade,
      awesome-medical-coding, awesome-occupation-data exist as
      community repos. Submit to each that fits; ~5 min each.

### Adjacent communities (developer audience, not registries)

- [ ] **Hacker News Show HN** - post #1 was MCP-focused; post #2 is
      API-focused. "Show HN: A unified REST API for every industry
      classification (NAICS, ISIC, NACE, HS, SOC...)". Different
      hook, different audience.
- [ ] **r/webdev, r/programming, r/datasets, r/opendata** -
      announcement threads on launch day; one post per subreddit,
      personalized.
- [ ] **dev.to / Medium / Hashnode** - one technical blog post on
      launch ("Translating between 1,000 classification systems with
      a single API call"). Repost across all three; cross-link from
      our `/blog`.
- [ ] **Stack Overflow** - watch tags `naics`, `isic`, `industry-codes`,
      `classification`. Answer existing questions with a one-line
      mention of the API + a link to the relevant guide page. Don't
      spam new threads.

### Track + measure

After submitting, watch:

- API-key signup conversion per registry (referrer logs in Cloud
  Run, partitioned by source domain)
- OpenAPI spec hits (`/api/v1/openapi.json` request count)
- GitHub stars / clones from the public-apis listing landing
- RapidAPI usage report (their own dashboard) once listed
- Postman workspace forks + collection runs

The API directories are slower-burn than HN but the traffic
compounds. APIs.guru-derived traffic in particular tends to last
years because Postman et al. keep their indexes fresh from that
single source.

## 9. Website outreach / discoverability

The third audience: humans who arrive via search or social, not
through an API client or MCP tool. Different distribution channels,
different message ("explore 1,000 classification systems" instead of
"integrate with our API"). Three Hacker News posts total are warranted
across items 7, 8, 9 - each with a distinct hook and a distinct
audience - but the rest of this list does not overlap with the MCP or
API sections.

Unblock condition: the site needs the soft-launch fundamentals already
shipped in PRs #152, #154, plus a status page (item 4) and a press kit
(item 3). Without those, a launch post that sends a wave of traffic
risks looking unprofessional.

### Search engines (passive but essential)

- [ ] **Google Search Console** - verify the property at
      [search.google.com/search-console](https://search.google.com/search-console).
      Submit the sitemap (`worldoftaxonomy.com/sitemap.xml`). Watch
      for crawl errors and structured-data issues.
- [ ] **Bing Webmaster Tools** - same idea at
      [bing.com/webmasters](https://www.bing.com/webmasters). Bing
      indexes faster than Google for new sites and feeds DuckDuckGo +
      Yahoo.
- [ ] **IndexNow** - one POST per new URL pings Bing, Yandex, and
      Naver simultaneously. Wire this into the Next.js
      `/api/revalidate` handler so it fires whenever a wiki page
      republishes. ~1 hour of work.
- [ ] **Yandex Webmaster** + **Naver Search Advisor** - low-priority
      but free. Useful if Russian or Korean industry-classification
      queries are a real audience for us.

### AI search / answer engines (the AEO surface)

The Karpathy-wiki + llms-full.txt pattern is built for this audience.
Each engine has a different submission / ingestion path; most do not
have a public submit form yet, so the goal is to make the site
**impossible to miss** when their crawlers come through.

- [ ] **Perplexity** - no submit form. They follow `robots.txt`
      respect (PerplexityBot already allowed in our robots.ts) and
      pull from indexed sites. Make sure the `<head>`-linked
      `/llms-full.txt` is reachable; verify after launch by asking
      Perplexity a NAICS-vs-ISIC question and seeing if we appear in
      sources.
- [ ] **OpenAI / ChatGPT search** - GPTBot is allowed in our
      robots.ts. ChatGPT's "Search" feature pulls from indexed sites
      via Bing, so the Bing Webmaster submission above doubles as
      ChatGPT-search distribution.
- [ ] **Google AI Overviews / Gemini** - rides on Google's index +
      `Google-Extended` opt-in (already allowed). Submit + confirm
      Google Search Console verification.
- [ ] **You.com**, **Brave Search**, **Kagi** - smaller but
      AI-friendly. Brave has a free submit endpoint
      ([search.brave.com/help/submit-url](https://search.brave.com/help/submit-url)).
- [ ] **Wikipedia / Wikidata** - if the project becomes notable
      enough by community standards, a Wikipedia article on
      "WorldOfTaxonomy" or a Wikidata Q-item creates a permanent
      reference that AI engines disproportionately weight. Don't
      self-author; wait for an external editor or refer the project
      via Wikipedia's Articles for Creation. Lower-priority.

### Launch posts (one-time signals, time-limited spike)

- [ ] **Hacker News Show HN #3** - human-website hook, distinct from
      the MCP and API posts. Suggested title: "Show HN: Explore 1,000
      classification systems side by side (NAICS, HS, ICD-11, ISCO,
      and 996 more)". Lead with the visual `/explore` page, not the
      developer integration. Post on a Tuesday-Thursday morning ET.
- [ ] **Product Hunt** - launch on a Tuesday for the daily ranking
      window. Press kit assets (item 3) are mandatory here: Product
      Hunt without good screenshots underperforms by ~10x. Hunter
      handoff: have someone with > 500 followers on Product Hunt
      submit on our behalf.
- [ ] **Reddit** - one post per relevant subreddit on launch day,
      personalized to each: r/dataisbeautiful (lead with a
      crosswalk visualization), r/datasets (the data dump angle),
      r/InternationalBusiness (the trade/HS angle), r/MapPorn (the
      country-system map). One post, one community, no crossposting.
- [ ] **Mastodon / Bluesky / X** - one announcement thread per
      platform, video-first. The 90-second demo (item 5) is the
      asset. Pin the thread on each profile.
- [ ] **LinkedIn** - long-form post from Ram + a paragraph from
      Colaberry's company page. The audience here is enterprise
      buyers, not developers; lead with "we just open-sourced X"
      framing.

### Tech / tool directories (ongoing, slow-burn traffic)

- [ ] **AlternativeTo** - submit at
      [alternativeto.net/feedback](https://alternativeto.net/feedback).
      Position as an alternative to "looking up codes manually" or
      to expensive licensed crosswalk products. Slow-burn but
      durable.
- [ ] **futuretools.io** - free directory of AI tools. Submit at
      [futuretools.io/submit-a-tool](https://www.futuretools.io/submit-a-tool).
      The MCP server angle qualifies us here even though we are
      mostly classical infrastructure.
- [ ] **theresanaiforthat.com** - same shape; submit if MCP-tool
      framing is real for our use case.
- [ ] **OpenAlternative.co** - directory of OS alternatives to paid
      tools. Good fit because most existing crosswalk products are
      proprietary subscriptions.
- [ ] **G2** / **Capterra** / **GetApp** - paid placements; defer
      until paid plans exist (item 1+2).

### Domain-specific communities (highest engagement, smallest reach)

- [ ] **Federal data community** - GitHub repos like
      `usds/federalist`, `18F/`, gov.uk's
      open-data-network-of-networks, EU Open Data Portal forums.
      Listings here are slow but the audience is exactly our
      ideal-customer profile (data scientists at orgs that need
      cross-jurisdiction taxonomy reconciliation).
- [ ] **Trade / customs communities** - WCO discussion forum,
      ICC International Chamber of Commerce, customs broker
      LinkedIn groups. Lead with the HS + Schedule B + CN angle.
- [ ] **Healthcare informatics** - HL7 community lists, AMIA
      forums, HIMSS. Lead with the ICD-10/11 + LOINC + SNOMED
      angle. Be careful not to overpromise on clinical accuracy
      (legal exposure); link to the Disclaimer in the footer.
- [ ] **HR-tech communities** - SHRM forums, recruitership
      networks, OWASP-style ATS-developer Discords. Lead with
      ESCO + SOC + ISCO + O*NET.

### Earned media / newsletters

- [ ] **AI newsletters** - Ben's Bites, The Rundown AI, AI Tidbits,
      Bensbites's "Show & Tell" section. Pitch via their public tip
      lines.
- [ ] **Data engineering newsletters** - Data Engineering Weekly
      (Ananth Packkildurai), Seattle Data Guy newsletter, Andreessen
      Horowitz's data newsletter.
- [ ] **TechCrunch / VentureBeat tip lines** - low conversion but
      free. Pitch as "open-source alternative to Dun & Bradstreet's
      industry-classification tooling".
- [ ] **Hacker Newsletter** (curated weekly) - submit via tip jar;
      gets re-distributed if the HN post performed well.

### Encyclopedic / reference

- [ ] **Wikidata Q-item** - create
      `worldoftaxonomy.com` as a Wikidata entity, link from the
      Wikidata entries on NAICS, ISIC, etc. (the "described by URL"
      property). Permanent reference that AI engines weight heavily.
- [ ] **Open Knowledge Foundation / OKFN forums** - the project
      directly serves their mission. Get listed in Frictionless
      Data's catalog of taxonomy resources.
- [ ] **Awesome-Open-Source-Data** lists on GitHub - submit to the
      ones that are still maintained. Different list from the
      `awesome-public-apis` and `awesome-mcp-servers` from items 7
      and 8.

### Track + measure

After launch:

- Cloud Run referrer logs partitioned by `Referer` host
- Google Search Console weekly report (impressions, clicks, top queries)
- Bing Webmaster equivalent
- Posthog/Plausible if/when wired (currently deferred per launch checklist)
- Hacker News post score + top comments (qualitative signal)
- Product Hunt rank + upvote source

The website outreach is the slowest-burn of the three (MCP/API/web)
because each item compounds individually but takes weeks to register
in search. Start the search-engine submissions on day 1; the launch
posts can wait until item 3 (press kit) and item 5 (demo video) are
ready.

## How this list should evolve

Cross items off the matrix at the top as they ship. Every item should
move to the launch-checklist's "shipped" log when complete, with a PR
reference. The detailed sections here can then be deleted - the goal
is for this file to shrink to zero entries by public-launch day.
