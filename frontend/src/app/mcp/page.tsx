import Link from 'next/link'
import { Terminal, ArrowLeft, ArrowRight, ChevronRight, Globe, Search, GitFork, FlaskConical, MapPin, ClipboardCheck, Zap } from 'lucide-react'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'MCP Tools - World Of Taxonomy',
  description: 'Connect Claude, Cursor, VS Code, or any MCP client to the World Of Taxonomy knowledge graph for search, translation, hierarchy navigation, and classification.',
  openGraph: {
    title: 'MCP Tools - World Of Taxonomy',
    description: 'MCP tools for AI assistants to search, translate, and navigate 1,000+ classification systems.',
    type: 'website',
    url: 'https://worldoftaxonomy.com/mcp',
  },
  alternates: { canonical: 'https://worldoftaxonomy.com/mcp' },
}

/* ── Tool data ── */

interface ToolParam {
  name: string
  type: string
  required: boolean
  description: string
  default?: string
}

interface McpTool {
  name: string
  description: string
  params: ToolParam[]
}

interface ToolGroup {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  tools: McpTool[]
}

const TOOL_GROUPS: ToolGroup[] = [
  {
    id: 'browse',
    title: 'Browse & Lookup',
    description: 'Navigate classification hierarchies and retrieve specific codes',
    icon: <Globe className="h-5 w-5" />,
    tools: [
      {
        name: 'list_classification_systems',
        description: 'List all available classification systems with node counts and metadata.',
        params: [],
      },
      {
        name: 'get_industry',
        description: 'Get details for a specific industry code including title, level, and hierarchy position.',
        params: [
          { name: 'system_id', type: 'string', required: true, description: 'System ID (e.g. naics_2022, isic_rev4)' },
          { name: 'code', type: 'string', required: true, description: 'Industry code (e.g. 6211, A01)' },
        ],
      },
      {
        name: 'browse_children',
        description: 'Get direct children of an industry code to navigate the hierarchy downward.',
        params: [
          { name: 'system_id', type: 'string', required: true, description: 'Classification system ID' },
          { name: 'parent_code', type: 'string', required: true, description: 'Parent code to list children of' },
        ],
      },
      {
        name: 'get_ancestors',
        description: 'Get the full path from root to a specific industry code.',
        params: [
          { name: 'system_id', type: 'string', required: true, description: 'Classification system ID' },
          { name: 'code', type: 'string', required: true, description: 'Industry code to trace ancestry for' },
        ],
      },
      {
        name: 'get_siblings',
        description: 'Get other industry codes at the same level under the same parent.',
        params: [
          { name: 'system_id', type: 'string', required: true, description: 'Classification system ID' },
          { name: 'code', type: 'string', required: true, description: 'Industry code to find siblings for' },
        ],
      },
      {
        name: 'get_sector_overview',
        description: 'Get top-level sectors/sections for a classification system.',
        params: [
          { name: 'system_id', type: 'string', required: true, description: 'Classification system ID' },
        ],
      },
      {
        name: 'get_subtree_summary',
        description: 'Summarize all codes under a given node: total count, leaf count, max depth.',
        params: [
          { name: 'system_id', type: 'string', required: true, description: 'Classification system ID' },
          { name: 'code', type: 'string', required: true, description: 'Root code of the subtree' },
        ],
      },
      {
        name: 'get_leaf_count',
        description: 'Compare granularity across systems: total nodes and leaf (most-specific) node counts.',
        params: [
          { name: 'system_id', type: 'string', required: false, description: 'Optional: filter to one system' },
        ],
      },
    ],
  },
  {
    id: 'search',
    title: 'Search & Discovery',
    description: 'Find codes across 1.2M+ nodes using keywords, codes, or free text',
    icon: <Search className="h-5 w-5" />,
    tools: [
      {
        name: 'search_classifications',
        description: 'Full-text search across industry classification systems. Searches titles and codes.',
        params: [
          { name: 'query', type: 'string', required: true, description: 'Search query (e.g. "hospital", "farming", "6211")' },
          { name: 'system_id', type: 'string', required: false, description: 'Optional: filter results to a specific system' },
          { name: 'limit', type: 'integer', required: false, description: 'Max results to return', default: '20' },
        ],
      },
      {
        name: 'find_by_keyword_all_systems',
        description: 'Search a keyword across all systems, returning results grouped by system.',
        params: [
          { name: 'query', type: 'string', required: true, description: 'Search keyword' },
          { name: 'limit_per_system', type: 'integer', required: false, description: 'Max results per system', default: '10' },
        ],
      },
      {
        name: 'resolve_ambiguous_code',
        description: 'Find all classification systems that contain a given code (e.g. "0111" exists in ISIC, SIC, and NIC).',
        params: [
          { name: 'code', type: 'string', required: true, description: 'Industry code to look up across all systems' },
        ],
      },
      {
        name: 'explore_industry_tree',
        description: 'Search by keyword and return each matching node with its full ancestor path and immediate children.',
        params: [
          { name: 'query', type: 'string', required: true, description: 'Keyword to search (e.g. "pharmaceutical", "fintech")' },
          { name: 'system_id', type: 'string', required: false, description: 'Optional: restrict to one system' },
          { name: 'limit', type: 'integer', required: false, description: 'Max matches to return', default: '10' },
        ],
      },
      {
        name: 'classify_business',
        description: 'Classify a business, product, occupation, or activity description against global taxonomy systems. Returns matching codes with relevance scores.',
        params: [
          { name: 'text', type: 'string', required: true, description: 'Free-text description to classify' },
          { name: 'systems', type: 'string[]', required: false, description: 'Optional list of system IDs to search (default: all major systems)' },
          { name: 'limit', type: 'integer', required: false, description: 'Max matches per system', default: '5' },
        ],
      },
    ],
  },
  {
    id: 'translation',
    title: 'Translation & Crosswalks',
    description: 'Convert codes between systems and explore 321K+ equivalence edges',
    icon: <GitFork className="h-5 w-5" />,
    tools: [
      {
        name: 'get_equivalences',
        description: 'Get cross-system equivalences for an industry code (e.g. NAICS to ISIC mappings).',
        params: [
          { name: 'system_id', type: 'string', required: true, description: 'Source classification system ID' },
          { name: 'code', type: 'string', required: true, description: 'Source industry code' },
        ],
      },
      {
        name: 'translate_code',
        description: 'Translate an industry code from one system to another (e.g. NAICS 6211 to ISIC).',
        params: [
          { name: 'source_system', type: 'string', required: true, description: 'Source system ID (e.g. naics_2022)' },
          { name: 'source_code', type: 'string', required: true, description: 'Source industry code' },
          { name: 'target_system', type: 'string', required: true, description: 'Target system ID (e.g. isic_rev4)' },
        ],
      },
      {
        name: 'translate_across_all_systems',
        description: 'Translate an industry code to every other system in one call. Returns all known equivalences.',
        params: [
          { name: 'system_id', type: 'string', required: true, description: 'Source system ID' },
          { name: 'code', type: 'string', required: true, description: 'Source industry code' },
        ],
      },
      {
        name: 'get_crosswalk_coverage',
        description: 'Show how many equivalence edges exist between each pair of classification systems.',
        params: [
          { name: 'system_id', type: 'string', required: false, description: 'Optional: filter to a specific system' },
        ],
      },
      {
        name: 'get_system_diff',
        description: 'Find codes in system A that have no equivalence mapping to system B.',
        params: [
          { name: 'system_id_a', type: 'string', required: true, description: 'System to check codes from' },
          { name: 'system_id_b', type: 'string', required: true, description: 'System to check coverage against' },
        ],
      },
      {
        name: 'describe_match_types',
        description: 'Explain what exact, partial, and broad equivalence match types mean.',
        params: [],
      },
    ],
  },
  {
    id: 'geography',
    title: 'Geography & Countries',
    description: 'Map countries to their applicable classification systems',
    icon: <MapPin className="h-5 w-5" />,
    tools: [
      {
        name: 'get_region_mapping',
        description: 'List classification systems grouped by geographic region.',
        params: [],
      },
      {
        name: 'get_country_taxonomy_profile',
        description: 'Get the classification systems applicable to a country, plus its known sector strengths. Returns official national system, regional standard, and globally recommended ISIC Rev 4.',
        params: [
          { name: 'country_code', type: 'string', required: true, description: 'ISO 3166-1 alpha-2 country code (e.g. DE, US, IN)' },
        ],
      },
    ],
  },
  {
    id: 'analysis',
    title: 'Comparison & Analysis',
    description: 'Compare systems, audit data quality, and analyze structure',
    icon: <FlaskConical className="h-5 w-5" />,
    tools: [
      {
        name: 'compare_sector',
        description: 'Compare top-level sectors of two classification systems side by side.',
        params: [
          { name: 'system_id_a', type: 'string', required: true, description: 'First system ID' },
          { name: 'system_id_b', type: 'string', required: true, description: 'Second system ID' },
        ],
      },
      {
        name: 'get_audit_report',
        description: 'Generate an aggregate audit report for data trustworthiness review. Returns provenance tier breakdown, missing file hashes, structural derivation accounting, and skeleton system detection.',
        params: [],
      },
    ],
  },
]

function ToolCard({ tool }: { tool: McpTool }) {
  return (
    <div className="border-b border-border/30 last:border-0 py-4 first:pt-0 last:pb-0">
      <div className="flex items-start gap-2">
        <ChevronRight className="h-3.5 w-3.5 text-primary shrink-0 mt-1" />
        <div className="flex-1 min-w-0">
          <code className="text-sm font-mono font-medium text-foreground/90">{tool.name}</code>
          <p className="text-xs text-muted-foreground mt-1">{tool.description}</p>

          {tool.params.length > 0 && (
            <div className="mt-3 rounded-lg bg-secondary/30 p-3">
              <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide mb-2">Parameters</p>
              <div className="space-y-1.5">
                {tool.params.map((p) => (
                  <div key={p.name} className="flex items-start gap-2 text-xs">
                    <code className="font-mono text-foreground/80 shrink-0">
                      {p.name}
                      {p.required && <span className="text-red-400">*</span>}
                    </code>
                    <span className="text-muted-foreground/60 font-mono shrink-0">{p.type}</span>
                    <span className="text-muted-foreground">
                      {p.description}
                      {p.default && <span className="text-foreground/50 ml-1">(default: {p.default})</span>}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function McpToolsPage() {
  const totalTools = TOOL_GROUPS.reduce((sum, g) => sum + g.tools.length, 0)

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 space-y-12">

      {/* Hero */}
      <div className="space-y-3">
        <Link
          href="/developers"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-3 w-3" /> Developers
        </Link>
        <div className="flex items-center gap-2 text-xs text-muted-foreground font-medium">
          <Terminal className="h-3.5 w-3.5 text-primary" />
          MCP Server
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          MCP Tools Reference
        </h1>
        <p className="text-muted-foreground text-base max-w-2xl leading-relaxed">
          {totalTools} tools for AI assistants to search, translate, and navigate the taxonomy
          knowledge graph. Works with Claude, Cursor, VS Code, Windsurf, and any MCP client.
        </p>
      </div>

      {/* Overview cards */}
      <div className="grid sm:grid-cols-3 gap-4">
        {[
          { label: 'Protocol', value: 'JSON-RPC over stdio' },
          { label: 'Transport', value: 'stdin / stdout' },
          { label: 'Tools', value: `${totalTools} available` },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-lg border border-border/50 bg-card p-4">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">{label}</p>
            <p className="font-mono text-sm text-foreground/80">{value}</p>
          </div>
        ))}
      </div>

      {/* Setup instructions */}
      <div className="rounded-xl border border-border/50 bg-card divide-y divide-border/50">
        <div className="p-6 space-y-3">
          <p className="text-sm font-medium flex items-center gap-2">
            <Zap className="h-4 w-4 text-primary" />
            Connect to Claude Desktop
          </p>
          <p className="text-xs text-muted-foreground">
            Add to your{' '}
            <code className="font-mono">claude_desktop_config.json</code>
            {' '}(macOS: <code className="font-mono">~/Library/Application Support/Claude/claude_desktop_config.json</code>):
          </p>
          <pre className="rounded-lg bg-secondary/60 px-4 py-3 text-xs font-mono overflow-x-auto text-foreground/90 leading-relaxed">
{`{
  "mcpServers": {
    "world-of-taxonomy": {
      "command": "/usr/bin/python3",
      "args": ["-m", "world_of_taxonomy", "mcp"],
      "env": {
        "PYTHONPATH": "/path/to/World Of Taxonomy",
        "DATABASE_URL": "postgresql://user:pass@host/db?sslmode=require"
      }
    }
  }
}`}
          </pre>
          <p className="text-xs text-muted-foreground">
            Replace <code className="font-mono">/path/to/World Of Taxonomy</code> with your clone path
            and supply your <code className="font-mono">DATABASE_URL</code>.
            Restart Claude Desktop after saving.
          </p>
        </div>

        <div className="p-6 space-y-3">
          <p className="text-sm font-medium">Run the server directly</p>
          <pre className="rounded-lg bg-secondary/60 px-4 py-3 text-xs font-mono overflow-x-auto text-foreground/90 leading-relaxed">
{`# From the repo root (requires DATABASE_URL in environment)
python3 -m world_of_taxonomy mcp`}
          </pre>
        </div>

        <div className="p-6 space-y-3">
          <p className="text-sm font-medium">MCP Resources</p>
          <p className="text-xs text-muted-foreground">
            In addition to tools, the MCP server exposes resources that clients can read:
          </p>
          <div className="space-y-2 mt-2">
            {[
              { uri: 'taxonomy://systems', desc: 'List of all classification systems in JSON' },
              { uri: 'taxonomy://stats', desc: 'Knowledge graph statistics in JSON' },
              { uri: 'taxonomy://wiki/{slug}', desc: 'Wiki guide pages in Markdown (10 pages)' },
            ].map(({ uri, desc }) => (
              <div key={uri} className="flex items-start gap-2 text-xs">
                <code className="font-mono text-primary/80 shrink-0">{uri}</code>
                <span className="text-muted-foreground">{desc}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick-nav */}
      <div className="flex flex-wrap gap-2">
        {TOOL_GROUPS.map((g) => (
          <a
            key={g.id}
            href={`#${g.id}`}
            className="px-3 py-1.5 rounded-lg border border-border/50 bg-card text-xs font-medium hover:bg-secondary/50 transition-colors"
          >
            {g.title} ({g.tools.length})
          </a>
        ))}
      </div>

      {/* Tool groups */}
      {TOOL_GROUPS.map((group) => (
        <section key={group.id} id={group.id} className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
              {group.icon}
            </div>
            <div>
              <h2 className="text-lg font-semibold">{group.title}</h2>
              <p className="text-sm text-muted-foreground">{group.description}</p>
            </div>
          </div>
          <div className="rounded-xl border border-border/50 bg-card p-5 space-y-0">
            {group.tools.map((tool) => (
              <ToolCard key={tool.name} tool={tool} />
            ))}
          </div>
        </section>
      ))}

      {/* Example conversation */}
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
            <ClipboardCheck className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Example Conversation</h2>
            <p className="text-sm text-muted-foreground">What it looks like in Claude Desktop</p>
          </div>
        </div>
        <div className="rounded-xl border border-border/50 bg-card p-6 space-y-4">
          <div className="space-y-3">
            {[
              { role: 'user', text: 'What NAICS code should I use for a telemedicine platform?' },
              { role: 'tool', text: 'classify_business("telemedicine platform") -> NAICS 621999, ISIC 8620, SOC 29-1171' },
              { role: 'assistant', text: 'NAICS 621999 (All Other Miscellaneous Ambulatory Health Care Services) is the best fit. The ISIC equivalent is 8620 (Medical and dental practice activities). Let me show you the full hierarchy...' },
              { role: 'tool', text: 'get_ancestors("naics_2022", "621999") -> 62 > 621 > 6219 > 621999' },
              { role: 'assistant', text: 'The full NAICS path: 62 (Health Care) > 621 (Ambulatory Health Care) > 6219 (Other Ambulatory) > 621999 (All Other Miscellaneous).' },
            ].map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === 'user' ? '' : 'ml-4'}`}>
                <span className={`shrink-0 text-[10px] font-mono uppercase rounded px-1.5 py-0.5 h-fit ${
                  msg.role === 'user' ? 'bg-blue-500/10 text-blue-500' :
                  msg.role === 'tool' ? 'bg-emerald-500/10 text-emerald-500' :
                  'bg-purple-500/10 text-purple-500'
                }`}>
                  {msg.role}
                </span>
                <p className={`text-xs leading-relaxed ${msg.role === 'tool' ? 'font-mono text-foreground/70' : 'text-foreground/80'}`}>
                  {msg.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <div className="rounded-xl border border-border/50 bg-card p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="font-semibold">Want to use the REST API instead?</p>
          <p className="text-sm text-muted-foreground mt-0.5">
            Same data, same coverage - HTTP JSON endpoints with no client library needed.
          </p>
        </div>
        <Link
          href="/api"
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shrink-0"
        >
          API Reference <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </div>
  )
}
