# Frontend Drill-Down

Next.js 16 App Router + Turbopack + Tailwind v4 + shadcn/ui. Read [HANDOVER.md](../../HANDOVER.md) first for the overall picture.

---

## Next.js 16 gotchas

From [frontend/AGENTS.md](../../frontend/AGENTS.md): "This is NOT the Next.js you know." Breaking changes vs. older guides:

- **Async `params` and `searchParams`** in dynamic routes. All `[slug]`/`[id]`/`[code]` routes receive `params: Promise<{...}>`. You must `await params` before destructuring. Example: [frontend/src/app/dashboard/page.tsx](../../frontend/src/app/dashboard/page.tsx).
- **ISR is time-based only.** Tag-based revalidation is deprecated. Use `next: { revalidate: seconds }` in `fetch` options. See [frontend/src/lib/server-api.ts](../../frontend/src/lib/server-api.ts).
- **Turbopack by default** for `next dev` and `next build`. Faster HMR; occasional stale-cache moments - restart the dev server if you edit something and see ghost output.
- **`useSearchParams` requires Suspense.** Any client component that reads it must be wrapped in `<Suspense>` or Next.js will hard-error on build. Pattern: SSR page -> client wrapper that provides Suspense -> inner component that reads params.
- **Memory**: dev script bumps `NODE_OPTIONS='--max-old-space-size=4096'` because Turbopack holds more graph state than Webpack.
- **Install path**: `cd frontend && npx next dev --port 3000`. Requires `nvm` if system Node is too old.

When in doubt, read the docs shipped with the installed version: `node_modules/next/dist/docs/`.

---

## App Router inventory

[frontend/src/app/](../../frontend/src/app/):

| Route | File | Kind | Purpose |
|-------|------|------|---------|
| `/` | `page.tsx` + `HomeContent.tsx` | SSR shell + client | Galaxy view, stats pills, IndustryMap, world map |
| `/explore` | `explore/page.tsx` + `ExploreContent.tsx` | SSR shell + client | Unified search + browse. Empty query -> browse view with category/sector filters and systems table. Non-empty query -> grouped search results. Reads `?q=`, `?cat=`, `?sector=` |
| `/system/[id]` | `system/[id]/page.tsx` | SSR dynamic | System detail with hierarchy tree and crosswalks. `generateMetadata()` produces per-system OG tags |
| `/system/[id]/node/[code]` | nested dynamic | SSR dynamic | Node detail with breadcrumb ancestors, children, cross-system equivalences |
| `/crosswalks` + `/crosswalks/[systemA]/to/[systemB]` | `crosswalks/page.tsx` + `CrosswalkExplorerClient.tsx` | SSR shell + client | Cytoscape.js graph with major-pair directory. Reads `?source=&target=` to deep-link a preselected pair. Lazy-loads the 300KB graph component |
| `/country/[code]` | dynamic | SSR | Country profile: systems ranked by relevance (official/regional/historical) |
| `/guide` + `/guide/[slug]` | wiki index + dynamic | SSR | Renders [wiki/*.md](../../wiki/) via remark + remark-gfm + remark-html |
| `/blog` + `/blog/[slug]` | SSR | SSR | Same, for [blog/](../../blog/) |
| `/about`, `/pricing`, `/developers`, `/api`, `/mcp` | static | SSR | Long-form pages |
| `/login` | client | Client | OAuth buttons (GitHub, Google, LinkedIn). Bounces logged-in users home |
| `/auth/callback` | SSR | SSR | OAuth callback; stashes JWT + user in `localStorage`, redirects home |
| `/dashboard` | `page.tsx` | Server | 308 permanent redirect to `/explore` (preserves query string) |
| `/api/revalidate` | route handler | Server | ISR webhook; `x-revalidate-secret` header required (constant-time compared) |
| `/api/crosswalk/[source]/[target]/graph` | route handler | Server | Falls back to backend when a pair isn't bundled |
| `/api/crosswalk/[source]/[target]/sections` | route handler | Server | Section summary for a crosswalk pair |
| `sitemap.ts` | static | Static | Generates sitemap from wiki + blog slugs + `GET /api/v1/systems` |
| `robots.ts` | static | Static | Allows GPTBot, ClaudeBot, PerplexityBot + sitemap |
| `feed.xml/route.ts` | route handler | Server | RSS feed |

---

## Component layout

[frontend/src/components/](../../frontend/src/components/):

| Component | Notes |
|-----------|-------|
| `layout/Header.tsx` | Client. Sticky nav: Galaxy, Crosswalks, Explore, Guide, Blog, Builders, About, Pricing. Auth dropdown, theme toggle |
| `layout/Footer.tsx` | Server. Brand + links |
| `IndustryMap.tsx` | Client. 44 sector buttons that link to `/explore?q=<term>` |
| `visualizations/GalaxyView.tsx` | Client, D3 force simulation, theme-aware via `useTheme()` |
| `visualizations/RadialDendrogram.tsx` | Client, D3 radial cluster layout |
| `WorldMap.tsx` | Client. Reads `public/world-110m.json` TopoJSON |
| `NodeTree.tsx` | Client. Interactive hierarchy tree for system + node detail pages |
| `CrosswalkGraph.tsx` + `CrosswalkNetwork.tsx` | Client. Cytoscape.js, lazy-loaded |
| `MermaidBlock.tsx` | Client-only. Renders ```mermaid blocks in markdown |
| `WikiArticle.tsx`, `BlogArticle.tsx` | Server. Markdown templates |
| `Providers.tsx` | Client. React Query (`staleTime: 60s`) + `next-themes` (dark default, system support) |
| `ThemeToggle.tsx` | Client. Lucide icons, class-based theme switch |
| `ui/*` | shadcn/ui primitives: avatar, badge, button, card, command, dialog, dropdown-menu, input, input-group, label, separator, textarea |

---

## Data layer

[frontend/src/lib/](../../frontend/src/lib/):

| Module | Exports |
|--------|---------|
| `api.ts` | Client-side fetchers for every API surface: `getSystems`, `getSystem`, `getNode`, `getChildren`, `getAncestors`, `getEquivalences`, `search`, `getStats`, `getCrosswalkGraph`, `getCrosswalkSections`, `getCountriesStats`, `getCountryProfile`, auth (`register`, `login`, `getMe`, `createApiKey`, `listApiKeys`, `revokeApiKey`), `getGithubStars`, `generateTaxonomy`, `acceptGeneratedTaxonomy`. Relative paths (`/api/v1/*`), routed through Next's rewrite |
| `server-api.ts` | SSR mirrors: `serverGetSystems`, `serverGetStats`, `serverFetch` wrapper with `next: { revalidate: 3600 }` default, 5s timeout. Used from server components only |
| `types.ts` | Mirrors backend Pydantic models: `ClassificationSystem`, `SystemDetail`, `ClassificationNode`, `Equivalence` (now carries `edge_kind`, `source_category`, `target_category`), `CrosswalkStat`, `CrosswalkGraphResponse`, `User`, `ApiKey`, `AuthTokens`, etc. Keep in sync with `world_of_taxonomy/api/schemas.py` |
| `categories.ts` | `SYSTEM_CATEGORIES` (16 top-level groups with `systemIds`, `accent`, `bg`), `DOMAIN_SECTORS` (~50 domain deep-dives with prefix matching + explicit `extraIds`), `LIFE_SCIENCES_SECTORS`. Helpers: `getCategoryForSystem`, `getDomainSector`, `getLifeSciencesSector`, `groupSystemsByCategory` |
| `colors.ts` | `SYSTEM_TINTS` per system, `SECTOR_COLORS` for NAICS sectors, helpers |
| `auth.ts` | `localStorage` helpers: `getToken`, `setAuth`, `clearAuth`, `getStoredUser`, `isLoggedIn`. No cookies, no server session |
| `wiki.ts`, `blog.ts` | Server-side markdown loaders. Sort by `_meta.json` order / date |
| `crosswalk-data.ts` | Filesystem loader: `getStaticSystems`, `getStaticStats`, `getStaticAllSections`, `getPairData` (tries both directional filenames) |
| `tree-data.ts` | Per-system static tree loader |

**SSR + React Query hydration pattern** (used in `/explore`, `/`, system detail):

1. Server page calls `serverGetSystems()` / `serverGetStats()`, catches errors (backend down => `null`).
2. Server page renders a client wrapper with `initialSystems` / `initialStats` props.
3. Client wrapper seeds React Query with `initialData` and `staleTime: 0`, so background refetch refreshes without blocking first paint.

This gives fast TTFB (SSR renders with real data), SEO (crawlers see real content), and client UX (subsequent navigations feel instant via React Query cache).

---

## Authentication on the frontend

- Tokens + user blob live in `localStorage` under `wot_token` and `wot_user`.
- `getToken()` returns `null` on SSR (guards with `typeof window !== 'undefined'`), so server components must treat auth-required state as absent and let the client re-hydrate.
- OAuth flow: click a button on `/login` -> `window.location.href` to `/api/v1/auth/oauth/{provider}/authorize` -> backend redirects to provider -> provider redirects back to `/auth/callback` -> callback page writes token + user to `localStorage` and bounces to `/`.
- Logout is client-side only. Expiry is enforced by the backend; the frontend doesn't track it proactively.

OAuth provider setup (client IDs, secrets, redirect URIs per environment) is documented in [OAUTH_PRODUCTION_SETUP.md](../../OAUTH_PRODUCTION_SETUP.md).

---

## Configuration

- [frontend/next.config.ts](../../frontend/next.config.ts) - rewrites `/api/v1/*` to `${BACKEND_URL}/api/v1/*`. `serverExternalPackages` excludes remark/remark-gfm/remark-html from the client bundle. Applies baseline security headers (HSTS, nosniff, frame-deny, Referrer-Policy, Permissions-Policy) and a Content-Security-Policy Report-Only header that posts violations to `/api/v1/csp-report`. `poweredByHeader: false` drops the `X-Powered-By` fingerprint.
- Typed API surface generated from the live FastAPI OpenAPI spec via `openapi-typescript`; output under `frontend/src/lib/openapi-types.ts`. Wrapper clients in `lib/api.ts` / `lib/server-api.ts` consume those types. Regenerate when the backend schemas change.
- [frontend/tsconfig.json](../../frontend/tsconfig.json) - strict mode, `@/*` alias for `src/*`, `jsx: react-jsx`.
- [frontend/package.json](../../frontend/package.json) - notable scripts: `predev`/`prebuild` copy `wiki/`, `blog/`, `crosswalk-data/`, `tree-data/` into `src/content/` before each run; `dev` bumps Node heap; `build`, `start`, `lint` are standard.
- [frontend/src/app/globals.css](../../frontend/src/app/globals.css) - Tailwind v4 imports, shadcn theme tokens in `oklch()`, separate light/dark CSS variable sets, custom radius scales.

Key runtime dependencies: `next@16`, `react@19`, `@tanstack/react-query`, `cytoscape`, `d3`, `mermaid`, `next-themes`, `remark` + `remark-gfm` + `remark-html`, `lucide-react`, `tailwindcss@4`.

---

## Crosswalk data bundling

The frontend is aggressive about static bundling to eliminate client-side network calls (the "Karpathy wiki" pattern applied to structured data).

1. Backend writes JSON via [scripts/export_crosswalk_data.py](../../scripts/export_crosswalk_data.py): one `pair__<a>___<b>.json` per pair, plus `all-sections.json`, into [crosswalk-data/](../../crosswalk-data/). Filenames use alphabetically sorted system IDs so there's one canonical name per pair.
2. Tree data is exported similarly via [scripts/export_tree_data.py](../../scripts/export_tree_data.py) into [tree-data/](../../tree-data/).
3. `npm run predev` / `npm run prebuild` copies both into `frontend/src/content/crosswalk/` and `frontend/src/content/tree/`.
4. `getPairData()` in `lib/crosswalk-data.ts` tries both directional names so callers don't care which side is "source."
5. If a pair isn't bundled, the route handler at `frontend/src/app/api/crosswalk/[source]/[target]/graph/route.ts` proxies the live backend.

Cytoscape graph loads on demand (dynamic `import()` inside the crosswalk explorer client component) so the 300KB library never hits the initial bundle.

---

## Styling system

- **Tailwind v4** via `@tailwindcss/postcss`. No separate `tailwind.config.ts`; directives live in `globals.css`.
- **Color tokens in oklch** (lightness, chroma, hue). Two variants: `:root` (light) and `.dark` (dark). shadcn primitives read from these tokens so swapping themes doesn't require component edits.
- **Dark mode via `next-themes`**. Default is dark with system support. The `<ThemeProvider>` lives in `Providers.tsx`. The `useTheme()` hook is used in D3 visualizations that need theme-aware fill/stroke colors with SVG shadow filters for contrast.
- **`tw-animate-css`** provides shadcn-compatible animations.
- **No em-dashes anywhere** (CI enforces on `.ts`/`.tsx` too).

---

## Static assets and SEO

- [frontend/public/llms-full.txt](../../frontend/public/llms-full.txt) - regenerated by [scripts/build_llms_txt.py](../../scripts/build_llms_txt.py) from [wiki/](../../wiki/).
- [frontend/public/world-110m.json](../../frontend/public/world-110m.json) - TopoJSON for the world map.
- `layout.tsx` registers Schema.org `DataCatalog` JSON-LD; individual pages add `generateMetadata()` for OG / Twitter cards.
- `sitemap.ts` fetches `GET /api/v1/systems` at build time to emit one URL per system alongside static pages.
- `robots.ts` allow-lists GPTBot, ClaudeBot, PerplexityBot.

---

## Non-obvious rules

1. **No em-dashes** in any `.ts`/`.tsx`/`.md` file - CI fails on U+2014.
2. **Types mirror backend**: [frontend/src/lib/types.ts](../../frontend/src/lib/types.ts) must stay in sync with [world_of_taxonomy/api/schemas.py](../../world_of_taxonomy/api/schemas.py). Backend is the source of truth.
3. **Always wrap `useSearchParams` in Suspense** in client components.
4. **Default to SSR** for new pages. Only add `'use client'` when you need React hooks, browser APIs, or event handlers.
5. **React Query seeding**: when a server page pre-fetches, pass the result as `initialData` and use `staleTime: 0` so the client can refetch in the background without blocking.
6. **Turbopack cache glitches**: if something looks stale after an edit, kill and restart `npx next dev` rather than debugging phantom behavior.
7. **Verify UI in a browser** before calling a task done. Typecheck and tests confirm code correctness, not feature correctness.
