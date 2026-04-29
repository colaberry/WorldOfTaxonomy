import Link from 'next/link'
import { ContactSalesForm } from './ContactSalesForm'
import { GitFork, Terminal, Braces, ArrowRight, Zap, BookOpen, ChevronRight, Star, PlusCircle, Network, Sparkles, Bot } from 'lucide-react'

async function fetchGithubStars(): Promise<number | null> {
  try {
    const res = await fetch('https://api.github.com/repos/colaberry/WorldOfTaxonomy', {
      headers: { Accept: 'application/vnd.github.v3+json' },
      next: { revalidate: 3600 },
    })
    if (!res.ok) return null
    const data = await res.json()
    return data.stargazers_count ?? null
  } catch {
    return null
  }
}

const API_ENDPOINT_COUNT = 50
const MCP_TOOL_COUNT = 22

const API_HIGHLIGHTS = [
  { method: 'GET',  path: '/api/v1/search?q={term}',                        desc: 'Full-text search across 1.2M+ nodes' },
  { method: 'GET',  path: '/api/v1/systems/{id}/nodes/{code}/equivalences', desc: 'Crosswalk mappings to other systems' },
  { method: 'POST', path: '/api/v1/classify',                               desc: 'Classify free-text against all systems (Pro+)' },
  { method: 'GET',  path: '/api/v1/countries/{code}',                       desc: 'Country taxonomy profile' },
]

const MCP_HIGHLIGHTS = [
  { name: 'search_classifications',        desc: 'Full-text search across all nodes' },
  { name: 'translate_code',               desc: 'Convert a code from one system to another' },
  { name: 'classify_business',             desc: 'Classify free-text against taxonomy systems' },
  { name: 'explore_industry_tree',         desc: 'Interactive hierarchy exploration' },
  { name: 'get_country_taxonomy_profile',  desc: 'Full taxonomy profile for a country' },
]

const METHOD_COLORS: Record<string, string> = {
  GET:  'text-emerald-500 bg-emerald-500/10',
  POST: 'text-blue-500 bg-blue-500/10',
}

export default async function BuildersPage() {
  const githubStars = await fetchGithubStars()
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 space-y-16">

      {/* ── Hero ── */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium">
          <Zap className="h-3.5 w-3.5 text-primary" />
          Builders
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Build on the world&apos;s most comprehensive classification graph
        </h1>
        <p className="text-muted-foreground text-base max-w-2xl leading-relaxed">
          1,000+ classification systems, 1.2M+ nodes, and 321K+ crosswalk edges - available via
          REST API, MCP server, packaged AI skills (Claude Code, Anthropic, ChatGPT Custom GPT,
          portable), or directly from the open-source repo.
        </p>
        <div className="flex flex-wrap gap-3 pt-2">
          <Link
            href="https://github.com/colaberry/WorldOfTaxonomy"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary text-secondary-foreground text-sm font-medium hover:bg-secondary/80 transition-colors"
          >
            <GitFork className="h-4 w-4" />
            View on GitHub
          </Link>
          <Link
            href="https://github.com/colaberry/WorldOfTaxonomy/stargazers"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border/50 bg-card text-sm font-medium hover:bg-secondary/50 transition-colors"
          >
            <Star className="h-4 w-4 text-yellow-500" />
            Star{githubStars != null ? ` (${githubStars.toLocaleString()})` : ''}
          </Link>
          <Link
            href="/explore"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <BookOpen className="h-4 w-4" />
            Explore the data
          </Link>
        </div>
      </div>

      {/* ── Quick-glance cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <a
          href="#github"
          className="group flex flex-col gap-3 p-5 rounded-xl border border-border/50 bg-card hover:border-border hover:shadow-sm transition-all"
        >
          <div className="flex items-center justify-between">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
              <GitFork className="h-5 w-5" />
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div>
            <p className="font-semibold text-sm">Open Source</p>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              Fork, self-host, or contribute. Full source for the API, ingesters, and frontend.
            </p>
          </div>
          <code className="text-[11px] font-mono text-muted-foreground bg-secondary/60 px-2.5 py-1.5 rounded-md w-fit">
            colaberry/WorldOfTaxonomy
          </code>
        </a>

        <Link
          href="/api"
          className="group flex flex-col gap-3 p-5 rounded-xl border border-border/50 bg-card hover:border-border hover:shadow-sm transition-all"
        >
          <div className="flex items-center justify-between">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
              <Braces className="h-5 w-5" />
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div>
            <p className="font-semibold text-sm">REST API</p>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              {API_ENDPOINT_COUNT} endpoints - search, browse, translate codes, and explore crosswalks. No SDK needed.
            </p>
          </div>
          <code className="text-[11px] font-mono text-muted-foreground bg-secondary/60 px-2.5 py-1.5 rounded-md w-fit">
            GET /api/v1/search?q=physician
          </code>
        </Link>

        <Link
          href="/mcp"
          className="group flex flex-col gap-3 p-5 rounded-xl border border-border/50 bg-card hover:border-border hover:shadow-sm transition-all"
        >
          <div className="flex items-center justify-between">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
              <Terminal className="h-5 w-5" />
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div>
            <p className="font-semibold text-sm">MCP Server</p>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              Connect Claude, Cursor, VS Code, or any MCP client. {MCP_TOOL_COUNT} tools for search, translation, and hierarchy navigation.
            </p>
          </div>
          <code className="text-[11px] font-mono text-muted-foreground bg-secondary/60 px-2.5 py-1.5 rounded-md w-fit">
            python3 -m world_of_taxonomy mcp
          </code>
        </Link>

        <a
          href="#skills"
          className="group flex flex-col gap-3 p-5 rounded-xl border border-border/50 bg-card hover:border-border hover:shadow-sm transition-all"
        >
          <div className="flex items-center justify-between">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
              <Sparkles className="h-5 w-5" />
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div>
            <p className="font-semibold text-sm">AI Skills</p>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              Drop-in skills for Claude Code, Anthropic, ChatGPT, and any LLM agent. Four bundles, same backend.
            </p>
          </div>
          <code className="text-[11px] font-mono text-muted-foreground bg-secondary/60 px-2.5 py-1.5 rounded-md w-fit">
            skills/
          </code>
        </a>

        <a
          href="#add-system"
          className="group flex flex-col gap-3 p-5 rounded-xl border border-border/50 bg-card hover:border-border hover:shadow-sm transition-all"
        >
          <div className="flex items-center justify-between">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
              <PlusCircle className="h-5 w-5" />
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div>
            <p className="font-semibold text-sm">Add a System</p>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              Contribute a classification system using our TDD guide. Three paths: NACE-derived, ISIC-derived, or standalone.
            </p>
          </div>
          <code className="text-[11px] font-mono text-muted-foreground bg-secondary/60 px-2.5 py-1.5 rounded-md w-fit">
            ingest/my_system.py
          </code>
        </a>
      </div>

      {/* ── GitHub ── */}
      <section id="github" className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
            <GitFork className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">GitHub</h2>
            <p className="text-sm text-muted-foreground">Open source - fork, contribute, or self-host</p>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
          <div className="grid sm:grid-cols-4 gap-4 text-sm">
            {[
              { label: 'Repository', value: 'colaberry/WorldOfTaxonomy' },
              { label: 'License',    value: 'Open Source' },
              { label: 'Stack',      value: 'Python + Next.js + PostgreSQL' },
              { label: 'GitHub Stars', value: githubStars != null ? githubStars.toLocaleString() : '-' },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">{label}</p>
                <p className="font-mono text-sm">{value}</p>
              </div>
            ))}
          </div>

          <div className="border-t border-border/50 pt-4 space-y-2">
            <p className="text-sm font-medium">Quick start</p>
            <pre className="rounded-lg bg-secondary/60 px-4 py-3 text-xs font-mono overflow-x-auto text-foreground/90 leading-relaxed">
{`git clone https://github.com/colaberry/WorldOfTaxonomy.git
cd WorldOfTaxonomy

# Install backend dependencies
pip install -r requirements.txt

# Configure database (copy .env.example and fill in DATABASE_URL)
cp .env.example .env

# Run the API
python3 -m uvicorn world_of_taxonomy.api.app:create_app --factory --port 8000

# Run the frontend (separate terminal)
cd frontend && npm install && npm run dev`}
            </pre>
          </div>

          <Link
            href="https://github.com/colaberry/WorldOfTaxonomy"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
          >
            Open repository <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </section>

      {/* ── Crosswalk Explorer ── */}
      <section id="crosswalks" className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
            <Network className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">Crosswalk Explorer</h2>
            <p className="text-sm text-muted-foreground">Interactive graph visualization of crosswalk relationships</p>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
          <p className="text-sm leading-relaxed text-muted-foreground">
            Explore how classification systems connect through 321K+ crosswalk edges.
            The system-level graph shows all connected systems grouped by category.
            Click any edge to drill into the code-level view with individual mappings.
          </p>
          <div className="grid sm:grid-cols-3 gap-4 text-sm">
            {[
              { label: 'System view', value: 'Systems grouped by category, edges = crosswalks' },
              { label: 'Code view',   value: 'Individual codes with exact/partial/broad edges' },
              { label: 'Powered by',  value: 'Cytoscape.js graph library' },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">{label}</p>
                <p className="text-xs text-foreground/80">{value}</p>
              </div>
            ))}
          </div>
          <Link
            href="/crosswalks"
            className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline"
          >
            Open Crosswalk Explorer <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </section>

      {/* ── REST API (summary - full reference at /api) ── */}
      <section id="api" className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
            <Braces className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">REST API</h2>
            <p className="text-sm text-muted-foreground">HTTP JSON API - {API_ENDPOINT_COUNT} endpoints, no SDK needed</p>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card divide-y divide-border/50">
          <div className="p-6 space-y-4">
            <div className="grid sm:grid-cols-3 gap-4 text-sm">
              {[
                { label: 'Base URL',    value: '/api/v1' },
                { label: 'Auth',        value: 'Bearer token or API key' },
                { label: 'Rate limits', value: '30/min anon, 1,000/min auth' },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">{label}</p>
                  <p className="font-mono text-xs text-foreground/80">{value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="p-6 space-y-3">
            <p className="text-sm font-medium">Popular endpoints</p>
            <div className="space-y-1">
              {API_HIGHLIGHTS.map(({ method, path, desc }) => (
                <div key={path} className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 py-2 border-b border-border/30 last:border-0 text-sm">
                  <span className={`inline-flex items-center rounded px-2 py-0.5 text-[11px] font-mono font-semibold w-fit shrink-0 ${METHOD_COLORS[method] ?? ''}`}>
                    {method}
                  </span>
                  <code className="font-mono text-xs text-foreground/80 flex-1 truncate">{path}</code>
                  <span className="text-xs text-muted-foreground sm:text-right shrink-0 max-w-xs">{desc}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4">
            <Link
              href="/api"
              className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline font-medium"
            >
              View full API reference ({API_ENDPOINT_COUNT} endpoints) <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Guides ── */}
      <section id="guides" className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">Guides</h2>
            <p className="text-sm text-muted-foreground">Curated knowledge to use the data effectively</p>
          </div>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          {[
            { slug: 'getting-started', title: 'Getting Started', desc: 'API + MCP quickstart, auth, rate limits' },
            { slug: 'crosswalk-map', title: 'Crosswalk Map', desc: 'How 321K+ edges connect classification systems' },
            { slug: 'industry-classification', title: 'Industry Classification', desc: 'Which system to use by country and purpose' },
            { slug: 'medical-coding', title: 'Medical Coding', desc: 'ICD-10 vs ICD-11 vs MeSH vs LOINC compared' },
            { slug: 'trade-codes', title: 'Trade Codes', desc: 'How HS, CPC, UNSPSC, and SITC relate' },
            { slug: 'architecture', title: 'Architecture', desc: 'System design, data flows, and diagrams' },
          ].map((guide) => (
            <Link
              key={guide.slug}
              href={`/guide/${guide.slug}`}
              className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-card hover:bg-secondary/30 transition-colors group"
            >
              <div>
                <span className="text-sm font-medium group-hover:text-primary transition-colors">{guide.title}</span>
                <p className="text-xs text-muted-foreground mt-0.5">{guide.desc}</p>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
            </Link>
          ))}
        </div>
        <Link href="/guide" className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline">
          View all guides <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </section>

      {/* ── MCP Server (summary - full reference at /mcp) ── */}
      <section id="mcp" className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
            <Terminal className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">MCP Server</h2>
            <p className="text-sm text-muted-foreground">Works with Claude, Cursor, VS Code, Windsurf, and any MCP client</p>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card divide-y divide-border/50">
          <div className="p-6 space-y-3">
            <p className="text-sm leading-relaxed text-muted-foreground">
              The MCP (Model Context Protocol) server lets AI assistants like Claude query the
              taxonomy graph directly - searching codes, translating between systems, navigating
              hierarchies, and exploring country profiles - all from within a conversation.
            </p>
            <div className="grid sm:grid-cols-3 gap-4 text-sm pt-2">
              {[
                { label: 'Protocol',   value: 'JSON-RPC over stdio' },
                { label: 'Transport',  value: 'stdin / stdout' },
                { label: 'Tools',      value: `${MCP_TOOL_COUNT} available` },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">{label}</p>
                  <p className="font-mono text-sm">{value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="p-6 space-y-2">
            <p className="text-sm font-medium">Quick start</p>
            <pre className="rounded-lg bg-secondary/60 px-4 py-3 text-xs font-mono overflow-x-auto text-foreground/90 leading-relaxed">
{`# From the repo root (requires DATABASE_URL in environment)
python3 -m world_of_taxonomy mcp`}
            </pre>
          </div>

          <div className="p-6 space-y-3">
            <p className="text-sm font-medium">Popular tools</p>
            <div className="grid sm:grid-cols-2 gap-x-8 gap-y-2">
              {MCP_HIGHLIGHTS.map(({ name, desc }) => (
                <div key={name} className="flex items-start gap-2 py-1 border-b border-border/20 last:border-0">
                  <ChevronRight className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <code className="text-[11px] font-mono text-foreground/90">{name}</code>
                    <p className="text-[11px] text-muted-foreground mt-0.5">{desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="p-4">
            <Link
              href="/mcp"
              className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline font-medium"
            >
              View full MCP reference ({MCP_TOOL_COUNT} tools) <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── AI Skills ── */}
      <section id="skills" className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">AI Skills</h2>
            <p className="text-sm text-muted-foreground">Drop-in skill bundles for Claude, ChatGPT, and any LLM agent</p>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card divide-y divide-border/50">
          <div className="p-6 space-y-3">
            <p className="text-sm leading-relaxed text-muted-foreground">
              Four packaged integrations, all backed by the same REST API and MCP server. Pick the
              one that matches your agent runtime. Source lives in the{' '}
              <code className="font-mono text-xs">/skills</code> directory of the repo.
            </p>
          </div>

          <div className="p-6 grid sm:grid-cols-2 gap-4">
            {[
              {
                icon: Bot,
                title: 'Claude Code Skill',
                path: 'skills/claude-code/worldoftaxonomy.md',
                desc: 'Markdown skill file with frontmatter. Drop into ~/.claude/skills/ or reference from the repo. Auto-activates on classification, translation, and hierarchy queries.',
              },
              {
                icon: Sparkles,
                title: 'Anthropic Claude Skill',
                path: 'skills/anthropic/SKILL.md',
                desc: 'Self-contained SKILL.md bundle for claude.ai agent skills. Includes auth, endpoints, response guidance, and invocation triggers.',
              },
              {
                icon: Braces,
                title: 'ChatGPT Custom GPT',
                path: 'skills/openapi/',
                desc: 'OpenAPI Action schema + system prompt for ChatGPT. Includes an export script that trims the spec to the 10 endpoints a Custom GPT needs.',
              },
              {
                icon: Terminal,
                title: 'Portable LLM Skill',
                path: 'skills/portable/',
                desc: 'Plain markdown system prompt + JSON tool schemas. Works with Gemini, Llama, LangChain, LlamaIndex, or any function-calling agent.',
              },
            ].map(({ icon: Icon, title, path, desc }) => (
              <div key={title} className="rounded-lg border border-border/50 bg-secondary/30 p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-primary shrink-0" />
                  <p className="text-sm font-semibold">{title}</p>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">{desc}</p>
                <code className="text-[10px] font-mono text-primary/80 block">{path}</code>
              </div>
            ))}
          </div>

          <div className="p-6 space-y-2">
            <p className="text-sm font-medium">Shared capabilities</p>
            <ul className="space-y-1.5 text-xs text-muted-foreground">
              <li className="flex items-start gap-2">
                <ChevronRight className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                <span>Classify free text (business, product, occupation, document) under standard codes across all systems</span>
              </li>
              <li className="flex items-start gap-2">
                <ChevronRight className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                <span>Translate codes between systems (NAICS -&gt; ISIC, ICD-10-CM -&gt; ICD-10-GM, SOC -&gt; ISCO, HS -&gt; CPC)</span>
              </li>
              <li className="flex items-start gap-2">
                <ChevronRight className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                <span>Walk hierarchies (children, ancestors, siblings) and audit crosswalk coverage between any two systems</span>
              </li>
            </ul>
          </div>

          <div className="p-4">
            <Link
              href="https://github.com/colaberry/WorldOfTaxonomy/tree/main/skills"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline font-medium"
            >
              Browse all four skills on GitHub <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ── Adding a New System ── */}
      <section id="add-system" className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
            <PlusCircle className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">Adding a New System</h2>
            <p className="text-sm text-muted-foreground">Contribute a classification system in ~10 steps using TDD</p>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card divide-y divide-border/50">

          {/* Overview */}
          <div className="p-6 space-y-3">
            <p className="text-sm leading-relaxed text-muted-foreground">
              Every system follows the same TDD cycle: write a failing test first, implement the
              ingester to make it green, wire it into the CLI, then run the full suite to confirm
              no regressions. The detailed SOP lives in{' '}
              <code className="font-mono text-xs">docs/adding-a-new-system.md</code>.
            </p>
            <div className="grid sm:grid-cols-3 gap-4 text-sm pt-1">
              {[
                { label: 'New file',     value: 'world_of_taxonomy/ingest/<system>.py' },
                { label: 'Test file',    value: 'tests/test_ingest_<system>.py' },
                { label: 'Wire up',      value: 'world_of_taxonomy/__main__.py' },
              ].map(({ label, value }) => (
                <div key={label}>
                  <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">{label}</p>
                  <p className="font-mono text-xs text-foreground/80">{value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 10-step checklist */}
          <div className="p-6 space-y-3">
            <p className="text-sm font-medium">10-step checklist</p>
            <ol className="space-y-2 text-sm text-muted-foreground list-none">
              {[
                'Write a failing test (test_ingest_<system>.py) - confirm it is red before continuing',
                'Create the ingester (ingest/<system>.py) - parse source data, build SYSTEM + NODES dicts',
                'Set is_leaf correctly - use codes_with_children = {parent for ... if parent} pattern',
                'Implement ingest(conn) - upsert system row, upsert nodes in dependency order',
                'Run the test green - minimum code to pass, nothing more',
                'Add crosswalk edges if a concordance table exists (ingest/crosswalk_<system>.py)',
                'Write a test for equivalences - confirm bidirectional edges are created',
                'Wire into __main__.py ingest command (add system id to the dispatch table)',
                'Run the full test suite - python3 -m pytest tests/ -v - all green before committing',
                'Update CLAUDE.md system table with name, region, and node count',
              ].map((step, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-secondary text-xs font-medium text-foreground">
                    {i + 1}
                  </span>
                  <span className="text-xs text-foreground/80 pt-0.5">{step}</span>
                </li>
              ))}
            </ol>
          </div>

          {/* Three implementation paths */}
          <div className="p-6 space-y-4">
            <p className="text-sm font-medium">Three implementation paths</p>
            <div className="grid sm:grid-cols-3 gap-4">
              {[
                {
                  label: 'Path A - NACE-derived',
                  desc: 'System shares all NACE Rev 2 codes (WZ, ONACE, NOGA, ATECO, NAF, PKD, SBI, etc.). Copy nodes from NACE and create 1:1 equivalence edges. ~15 lines of code.',
                  example: 'nace_derived.py',
                },
                {
                  label: 'Path B - ISIC-derived',
                  desc: 'System is a national adaptation of ISIC Rev 4 (CIIU, VSIC, BSIC, etc.). Copy ISIC nodes and create equivalences. Add country-specific codes if the source deviates.',
                  example: 'isic_derived.py',
                },
                {
                  label: 'Path C - Standalone',
                  desc: 'System has its own source file (CSV, XLSX, JSON, XML, PDF). Parse source, build hierarchy from parent codes, detect leaves via codes_with_children, upsert independently.',
                  example: 'naics.py, loinc.py',
                },
              ].map(({ label, desc, example }) => (
                <div key={label} className="rounded-lg border border-border/50 bg-secondary/30 p-4 space-y-2">
                  <p className="text-xs font-semibold text-foreground">{label}</p>
                  <p className="text-[11px] text-muted-foreground leading-relaxed">{desc}</p>
                  <code className="text-[10px] font-mono text-primary/80">see: {example}</code>
                </div>
              ))}
            </div>
          </div>

          {/* Minimal standalone template */}
          <div className="p-6 space-y-2">
            <p className="text-sm font-medium">Minimal standalone ingester template</p>
            <pre className="rounded-lg bg-secondary/60 px-4 py-3 text-xs font-mono overflow-x-auto text-foreground/90 leading-relaxed">
{`# world_of_taxonomy/ingest/my_system.py
SYSTEM = {
    "id": "my_system_2024",
    "name": "My Classification System 2024",
    "authority": "Issuing Body",
    "region": "Global",
    "version": "2024",
    "description": "...",
}

# (code, title, description, parent_code)
NODES = [
    ("A", "Section A", "Agriculture", None),
    ("A01", "Crop production", "...", "A"),
    ...
]

async def ingest(conn) -> None:
    await conn.execute("""
        INSERT INTO classification_system (...) VALUES (...)
        ON CONFLICT (id) DO UPDATE SET ...
    """, *SYSTEM.values())

    # Compute leaf flags dynamically - never hard-code level == N
    codes_with_children = {parent for (_, _, _, parent) in NODES if parent is not None}

    for code, title, desc, parent in NODES:
        is_leaf = code not in codes_with_children
        await conn.execute("""
            INSERT INTO classification_node (...) VALUES (...)
            ON CONFLICT (system_id, code) DO UPDATE SET ...
        """, SYSTEM["id"], code, title, desc, parent, is_leaf)`}
            </pre>
          </div>

        </div>
      </section>

      {/* ── Pricing ── */}
      <section id="pricing" className="space-y-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
            <Zap className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">Pricing</h2>
            <p className="text-sm text-muted-foreground">Free, Pro, and Enterprise plans available</p>
          </div>
        </div>

        <div className="rounded-xl border border-border/50 bg-card p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              The full knowledge graph is available on every plan. Paid tiers add higher limits,
              bulk export, classification API, and dedicated support.
            </p>
          </div>
          <Link
            href="/pricing"
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shrink-0"
          >
            View pricing <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* ── Contact Sales ── */}
      <section id="contact" className="space-y-5">
        <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
          <h2 className="text-xl font-semibold">Contact Sales</h2>
          <p className="text-sm text-muted-foreground">
            Interested in Enterprise? Tell us about your use case and we&apos;ll get back to you.
          </p>
          <ContactSalesForm />
        </div>
      </section>

      {/* ── Footer CTA ── */}
      <div className="rounded-xl border border-border/50 bg-card p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="font-semibold">Questions or contributions?</p>
          <p className="text-sm text-muted-foreground mt-0.5">
            Open an issue or pull request on GitHub - all feedback welcome.
          </p>
        </div>
        <Link
          href="https://github.com/colaberry/WorldOfTaxonomy/issues"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-secondary text-secondary-foreground text-sm font-medium hover:bg-secondary/80 transition-colors shrink-0"
        >
          <GitFork className="h-4 w-4" />
          Open an issue
        </Link>
      </div>

    </div>
  )
}
