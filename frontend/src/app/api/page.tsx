import Link from 'next/link'
import { Braces, ArrowLeft, Key, ExternalLink, Zap, Shield, Globe, Search, GitFork, FlaskConical, BookOpen, MessageSquare, ClipboardCheck } from 'lucide-react'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'API Reference - WorldOfTaxonomy',
  description: 'Complete REST API reference for WorldOfTaxonomy. 50+ endpoints for searching, browsing, translating, and exporting classification codes across 1,000+ systems.',
  openGraph: {
    title: 'API Reference - WorldOfTaxonomy',
    description: 'Complete REST API reference for WorldOfTaxonomy. 50+ endpoints for classification systems, crosswalks, search, and export.',
    type: 'website',
  },
}

/* ── Endpoint data ── */

interface Param {
  name: string
  location: 'path' | 'query' | 'body'
  type: string
  required: boolean
  description: string
  default?: string
}

interface Endpoint {
  method: 'GET' | 'POST' | 'DELETE'
  path: string
  description: string
  params: Param[]
  tier?: 'free' | 'auth' | 'pro' | 'enterprise'
  tryIt?: string // relative URL to try in browser
}

interface EndpointGroup {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  endpoints: Endpoint[]
}

const GROUPS: EndpointGroup[] = [
  {
    id: 'systems',
    title: 'Systems & Nodes',
    description: 'Browse classification systems and navigate their hierarchies',
    icon: <Globe className="h-5 w-5" />,
    endpoints: [
      {
        method: 'GET', path: '/api/v1/systems',
        description: 'List all classification systems with metadata and node counts.',
        params: [
          { name: 'group_by', location: 'query', type: 'string', required: false, description: 'Group results (e.g. "region")' },
          { name: 'country', location: 'query', type: 'string', required: false, description: 'Filter by ISO 3166-1 alpha-2 country code' },
        ],
        tryIt: '/api/v1/systems',
      },
      {
        method: 'GET', path: '/api/v1/systems/{id}',
        description: 'Get a system with its root-level nodes.',
        params: [
          { name: 'id', location: 'path', type: 'string', required: true, description: 'System ID (e.g. naics_2022, isic_rev4)' },
        ],
        tryIt: '/api/v1/systems/naics_2022',
      },
      {
        method: 'GET', path: '/api/v1/systems/{id}/nodes/{code}',
        description: 'Fetch a single classification node by system and code.',
        params: [
          { name: 'id', location: 'path', type: 'string', required: true, description: 'System ID' },
          { name: 'code', location: 'path', type: 'string', required: true, description: 'Node code (e.g. 6211, A01)' },
        ],
        tryIt: '/api/v1/systems/naics_2022/nodes/6211',
      },
      {
        method: 'GET', path: '/api/v1/systems/{id}/nodes/{code}/children',
        description: 'Get direct children of a node to navigate the hierarchy downward.',
        params: [
          { name: 'id', location: 'path', type: 'string', required: true, description: 'System ID' },
          { name: 'code', location: 'path', type: 'string', required: true, description: 'Parent node code' },
        ],
        tryIt: '/api/v1/systems/naics_2022/nodes/62/children',
      },
      {
        method: 'GET', path: '/api/v1/systems/{id}/nodes/{code}/ancestors',
        description: 'Get the full path from root to this node.',
        params: [
          { name: 'id', location: 'path', type: 'string', required: true, description: 'System ID' },
          { name: 'code', location: 'path', type: 'string', required: true, description: 'Node code' },
        ],
        tryIt: '/api/v1/systems/naics_2022/nodes/6211/ancestors',
      },
      {
        method: 'GET', path: '/api/v1/systems/{id}/nodes/{code}/equivalences',
        description: 'Get cross-system equivalence mappings for a node.',
        params: [
          { name: 'id', location: 'path', type: 'string', required: true, description: 'System ID' },
          { name: 'code', location: 'path', type: 'string', required: true, description: 'Node code' },
        ],
        tryIt: '/api/v1/systems/naics_2022/nodes/6211/equivalences',
      },
    ],
  },
  {
    id: 'search',
    title: 'Search',
    description: 'Full-text search across 1.2M+ classification nodes',
    icon: <Search className="h-5 w-5" />,
    endpoints: [
      {
        method: 'GET', path: '/api/v1/search',
        description: 'Full-text search across all classification systems. Searches titles and codes.',
        params: [
          { name: 'q', location: 'query', type: 'string', required: true, description: 'Search query (e.g. "physician", "farming", "6211")' },
          { name: 'system', location: 'query', type: 'string', required: false, description: 'Filter to a specific system ID' },
          { name: 'limit', location: 'query', type: 'integer', required: false, description: 'Max results (1-200)', default: '50' },
          { name: 'grouped', location: 'query', type: 'boolean', required: false, description: 'Group results by system', default: 'false' },
          { name: 'context', location: 'query', type: 'boolean', required: false, description: 'Include ancestors/children for each match', default: 'false' },
        ],
        tryIt: '/api/v1/search?q=physician&limit=5',
      },
    ],
  },
  {
    id: 'crosswalks',
    title: 'Crosswalks',
    description: 'Explore 321K+ equivalence edges connecting classification systems',
    icon: <GitFork className="h-5 w-5" />,
    endpoints: [
      {
        method: 'GET', path: '/api/v1/equivalences/stats',
        description: 'Get counts of equivalence edges per system pair.',
        params: [
          { name: 'system_id', location: 'query', type: 'string', required: false, description: 'Filter to a specific system' },
        ],
        tryIt: '/api/v1/equivalences/stats',
      },
      {
        method: 'GET', path: '/api/v1/systems/{source}/crosswalk/{target}/graph',
        description: 'Get graph data (nodes + edges) for crosswalk visualization between two systems.',
        params: [
          { name: 'source', location: 'path', type: 'string', required: true, description: 'Source system ID' },
          { name: 'target', location: 'path', type: 'string', required: true, description: 'Target system ID' },
          { name: 'limit', location: 'query', type: 'integer', required: false, description: 'Max edges (1-5000)', default: '500' },
          { name: 'section', location: 'query', type: 'string', required: false, description: 'Filter to edges within a section code' },
        ],
        tryIt: '/api/v1/systems/naics_2022/crosswalk/isic_rev4/graph?limit=50',
      },
      {
        method: 'GET', path: '/api/v1/systems/{source}/crosswalk/{target}/sections',
        description: 'Section-level summary of crosswalk edges. Returns top-level groupings with edge counts for progressive drill-down.',
        params: [
          { name: 'source', location: 'path', type: 'string', required: true, description: 'Source system ID' },
          { name: 'target', location: 'path', type: 'string', required: true, description: 'Target system ID' },
        ],
        tryIt: '/api/v1/systems/naics_2022/crosswalk/isic_rev4/sections',
      },
    ],
  },
  {
    id: 'explore',
    title: 'Explore & Compare',
    description: 'Advanced queries for translation, comparison, and analysis',
    icon: <FlaskConical className="h-5 w-5" />,
    endpoints: [
      {
        method: 'GET', path: '/api/v1/systems/{id}/nodes/{code}/translations',
        description: 'All cross-system mappings for a code in one call.',
        params: [
          { name: 'id', location: 'path', type: 'string', required: true, description: 'System ID' },
          { name: 'code', location: 'path', type: 'string', required: true, description: 'Node code' },
        ],
        tryIt: '/api/v1/systems/naics_2022/nodes/6211/translations',
      },
      {
        method: 'GET', path: '/api/v1/systems/{id}/nodes/{code}/siblings',
        description: 'Other nodes at the same hierarchy level under the same parent.',
        params: [
          { name: 'id', location: 'path', type: 'string', required: true, description: 'System ID' },
          { name: 'code', location: 'path', type: 'string', required: true, description: 'Node code' },
        ],
        tryIt: '/api/v1/systems/naics_2022/nodes/6211/siblings',
      },
      {
        method: 'GET', path: '/api/v1/systems/{id}/nodes/{code}/subtree',
        description: 'Aggregate stats for all nodes under a given code: total count, leaf count, max depth.',
        params: [
          { name: 'id', location: 'path', type: 'string', required: true, description: 'System ID' },
          { name: 'code', location: 'path', type: 'string', required: true, description: 'Root node code' },
        ],
        tryIt: '/api/v1/systems/naics_2022/nodes/62/subtree',
      },
      {
        method: 'GET', path: '/api/v1/compare',
        description: 'Side-by-side top-level sectors for two systems.',
        params: [
          { name: 'a', location: 'query', type: 'string', required: true, description: 'First system ID' },
          { name: 'b', location: 'query', type: 'string', required: true, description: 'Second system ID' },
        ],
        tryIt: '/api/v1/compare?a=naics_2022&b=isic_rev4',
      },
      {
        method: 'GET', path: '/api/v1/diff',
        description: 'Find codes in system A that have no equivalence mapping to system B.',
        params: [
          { name: 'a', location: 'query', type: 'string', required: true, description: 'Source system ID' },
          { name: 'b', location: 'query', type: 'string', required: true, description: 'Target system to check against' },
        ],
        tryIt: '/api/v1/diff?a=naics_2022&b=isic_rev4',
      },
      {
        method: 'GET', path: '/api/v1/nodes/{code}',
        description: 'Find all systems that contain a given code (resolve ambiguous codes).',
        params: [
          { name: 'code', location: 'path', type: 'string', required: true, description: 'Code to look up across all systems' },
        ],
        tryIt: '/api/v1/nodes/0111',
      },
      {
        method: 'GET', path: '/api/v1/systems/stats',
        description: 'Per-system leaf and total node counts for granularity comparison.',
        params: [
          { name: 'system_id', location: 'query', type: 'string', required: false, description: 'Filter to a specific system' },
        ],
        tryIt: '/api/v1/systems/stats',
      },
    ],
  },
  {
    id: 'countries',
    title: 'Countries',
    description: 'Taxonomy coverage and profiles for 249 countries',
    icon: <Globe className="h-5 w-5" />,
    endpoints: [
      {
        method: 'GET', path: '/api/v1/countries/stats',
        description: 'Per-country taxonomy coverage stats for all countries. Used by the world map visualization.',
        params: [],
        tryIt: '/api/v1/countries/stats',
      },
      {
        method: 'GET', path: '/api/v1/countries/{code}',
        description: 'Taxonomy profile for a country: official systems, regional standards, and sector strengths.',
        params: [
          { name: 'code', location: 'path', type: 'string', required: true, description: 'ISO 3166-1 alpha-2 code (e.g. US, DE, IN)' },
        ],
        tryIt: '/api/v1/countries/US',
      },
    ],
  },
  {
    id: 'classify',
    title: 'Classification',
    description: 'AI-powered classification of free-text descriptions',
    icon: <Zap className="h-5 w-5" />,
    endpoints: [
      {
        method: 'POST', path: '/api/v1/classify',
        description: 'Classify a business, product, occupation, or activity description against taxonomy systems. Returns matching codes with relevance scores.',
        params: [
          { name: 'text', location: 'body', type: 'string', required: true, description: 'Free-text description (2-500 chars)' },
          { name: 'systems', location: 'body', type: 'string[]', required: false, description: 'System IDs to search (default: all major systems)' },
          { name: 'limit', location: 'body', type: 'integer', required: false, description: 'Max matches per system', default: '5' },
        ],
        tier: 'pro',
      },
      {
        method: 'POST', path: '/api/v1/systems/{id}/nodes/{code}/generate',
        description: 'Generate AI-suggested sub-classifications for a node (preview only, no DB write).',
        params: [
          { name: 'id', location: 'path', type: 'string', required: true, description: 'System ID' },
          { name: 'code', location: 'path', type: 'string', required: true, description: 'Parent node code' },
          { name: 'count', location: 'body', type: 'integer', required: false, description: 'Number of sub-categories to generate (1-10)', default: '5' },
        ],
        tier: 'auth',
      },
      {
        method: 'POST', path: '/api/v1/systems/{id}/nodes/{code}/generate/accept',
        description: 'Persist user-accepted AI-generated nodes to the database.',
        params: [
          { name: 'id', location: 'path', type: 'string', required: true, description: 'System ID' },
          { name: 'code', location: 'path', type: 'string', required: true, description: 'Parent node code' },
          { name: 'nodes', location: 'body', type: 'GeneratedNode[]', required: true, description: 'Array of {code, title, description} to accept' },
        ],
        tier: 'auth',
      },
    ],
  },
  {
    id: 'auth',
    title: 'Authentication',
    description: 'OAuth sign-in (GitHub / Google / LinkedIn) and API-key management. Magic-link signup for the developer dashboard lives under /developers.',
    icon: <Shield className="h-5 w-5" />,
    endpoints: [
      {
        method: 'GET', path: '/api/v1/auth/me',
        description: 'Get current user profile. Requires a JWT obtained via OAuth.',
        params: [],
        tier: 'auth',
      },
      {
        method: 'POST', path: '/api/v1/auth/keys',
        description: 'Create a long-lived API key (wot_ prefix).',
        params: [
          { name: 'name', location: 'body', type: 'string', required: false, description: 'Key name', default: '"Default"' },
        ],
        tier: 'auth',
      },
      {
        method: 'GET', path: '/api/v1/auth/keys',
        description: 'List all API keys for the current user.',
        params: [],
        tier: 'auth',
      },
      {
        method: 'DELETE', path: '/api/v1/auth/keys/{key_id}',
        description: 'Deactivate an API key.',
        params: [
          { name: 'key_id', location: 'path', type: 'string', required: true, description: 'API key UUID' },
        ],
        tier: 'auth',
      },
      {
        method: 'GET', path: '/api/v1/auth/oauth/{provider}/authorize',
        description: 'Get the OAuth authorization URL for a provider. Redirect the user to this URL.',
        params: [
          { name: 'provider', location: 'path', type: 'string', required: true, description: 'OAuth provider: github, google, or linkedin' },
          { name: 'redirect_to', location: 'query', type: 'string', required: false, description: 'Destination URL after auth completes' },
        ],
      },
      {
        method: 'GET', path: '/api/v1/auth/oauth/{provider}/callback',
        description: 'OAuth callback handler. Exchanges code for token, upserts user, issues JWT.',
        params: [
          { name: 'provider', location: 'path', type: 'string', required: true, description: 'OAuth provider' },
          { name: 'code', location: 'query', type: 'string', required: false, description: 'Authorization code from provider' },
          { name: 'state', location: 'query', type: 'string', required: false, description: 'CSRF state parameter' },
        ],
      },
    ],
  },
  {
    id: 'wiki',
    title: 'Wiki & Content',
    description: 'Curated guide pages and audit reports',
    icon: <BookOpen className="h-5 w-5" />,
    endpoints: [
      {
        method: 'GET', path: '/api/v1/wiki',
        description: 'List all wiki guide pages with metadata.',
        params: [],
        tryIt: '/api/v1/wiki',
      },
      {
        method: 'GET', path: '/api/v1/wiki/{slug}',
        description: 'Get a single wiki page by slug.',
        params: [
          { name: 'slug', location: 'path', type: 'string', required: true, description: 'Page slug (e.g. getting-started)' },
        ],
        tryIt: '/api/v1/wiki/getting-started',
      },
      {
        method: 'GET', path: '/api/v1/audit/provenance',
        description: 'Aggregate audit report: provenance tiers, missing hashes, structural derivation accounting, skeleton systems.',
        params: [],
        tryIt: '/api/v1/audit/provenance',
      },
    ],
  },
  {
    id: 'contact',
    title: 'Contact',
    description: 'Enterprise inquiries',
    icon: <MessageSquare className="h-5 w-5" />,
    endpoints: [
      {
        method: 'POST', path: '/api/v1/contact',
        description: 'Submit an enterprise inquiry or general contact form.',
        params: [
          { name: 'name', location: 'body', type: 'string', required: true, description: 'Your name (1-200 chars)' },
          { name: 'company', location: 'body', type: 'string', required: false, description: 'Company name (max 200 chars)' },
          { name: 'email', location: 'body', type: 'string', required: true, description: 'Email address' },
          { name: 'message', location: 'body', type: 'string', required: true, description: 'Message (10-2000 chars)' },
        ],
      },
    ],
  },
]

const METHOD_COLORS: Record<string, string> = {
  GET: 'text-emerald-500 bg-emerald-500/10',
  POST: 'text-blue-500 bg-blue-500/10',
  DELETE: 'text-red-500 bg-red-500/10',
}

const TIER_BADGES: Record<string, { label: string; className: string }> = {
  pro: { label: 'Pro+', className: 'text-amber-600 bg-amber-500/10' },
  enterprise: { label: 'Enterprise', className: 'text-purple-600 bg-purple-500/10' },
  auth: { label: 'Auth required', className: 'text-sky-600 bg-sky-500/10' },
}

const LOCATION_LABELS: Record<string, string> = {
  path: 'path',
  query: 'query',
  body: 'body',
}

function EndpointCard({ ep }: { ep: Endpoint }) {
  const tierBadge = ep.tier ? TIER_BADGES[ep.tier] : null
  return (
    <div className="border-b border-border/30 last:border-0 py-4 first:pt-0 last:pb-0">
      <div className="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-3">
        <div className="flex items-center gap-2 shrink-0">
          <span className={`inline-flex items-center rounded px-2 py-0.5 text-[11px] font-mono font-semibold ${METHOD_COLORS[ep.method] ?? ''}`}>
            {ep.method}
          </span>
          {tierBadge && (
            <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium ${tierBadge.className}`}>
              {tierBadge.label}
            </span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <code className="font-mono text-xs text-foreground/90 break-all">{ep.path}</code>
            {ep.tryIt && (
              <a
                href={ep.tryIt}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 inline-flex items-center gap-1 text-[10px] text-primary hover:underline"
                title="Try this endpoint in your browser"
              >
                <ExternalLink className="h-3 w-3" /> Try it
              </a>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-1">{ep.description}</p>
        </div>
      </div>

      {ep.params.length > 0 && (
        <div className="mt-3 ml-0 sm:ml-16">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-muted-foreground">
                <th className="pb-1 pr-3 font-medium">Parameter</th>
                <th className="pb-1 pr-3 font-medium hidden sm:table-cell">Location</th>
                <th className="pb-1 pr-3 font-medium hidden sm:table-cell">Type</th>
                <th className="pb-1 font-medium">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/20">
              {ep.params.map((p) => (
                <tr key={p.name}>
                  <td className="py-1 pr-3 font-mono text-foreground/80 whitespace-nowrap">
                    {p.name}
                    {p.required && <span className="text-red-400 ml-0.5">*</span>}
                  </td>
                  <td className="py-1 pr-3 text-muted-foreground hidden sm:table-cell">
                    <span className="bg-secondary/60 px-1.5 py-0.5 rounded text-[10px]">
                      {LOCATION_LABELS[p.location]}
                    </span>
                  </td>
                  <td className="py-1 pr-3 font-mono text-muted-foreground hidden sm:table-cell">{p.type}</td>
                  <td className="py-1 text-muted-foreground">
                    {p.description}
                    {p.default && <span className="ml-1 text-foreground/50">(default: {p.default})</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function ApiReferencePage() {
  const totalEndpoints = GROUPS.reduce((sum, g) => sum + g.endpoints.length, 0)

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
          <Braces className="h-3.5 w-3.5 text-primary" />
          API Reference
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          REST API Reference
        </h1>
        <p className="text-muted-foreground text-base max-w-2xl leading-relaxed">
          {totalEndpoints} endpoints for searching, browsing, translating, and exporting classification
          codes across 1,000+ systems. JSON over HTTP - no SDK required.
        </p>
      </div>

      {/* Overview cards */}
      <div className="grid sm:grid-cols-3 gap-4">
        {[
          { label: 'Base URL', value: '/api/v1', mono: true },
          { label: 'Auth', value: 'Bearer token or wot_ API key', mono: false },
          { label: 'Rate limits', value: '30/min anon, 1,000/min auth', mono: false },
        ].map(({ label, value, mono }) => (
          <div key={label} className="rounded-lg border border-border/50 bg-card p-4">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">{label}</p>
            <p className={`text-sm ${mono ? 'font-mono' : ''} text-foreground/80`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Auth flow */}
      <div className="rounded-xl border border-border/50 bg-card p-6 space-y-3">
        <p className="text-sm font-medium flex items-center gap-2">
          <Key className="h-4 w-4 text-muted-foreground" />
          Authentication flow
        </p>
        <pre className="rounded-lg bg-secondary/60 px-4 py-3 text-xs font-mono overflow-x-auto text-foreground/90 leading-relaxed">
{`# 1. Sign up at /developers/signup (email-only, magic link sent
#    to your inbox). Or sign in with GitHub / Google / LinkedIn at
#    /login -> redirected back with a JWT.

# 2. (OAuth path) Use the JWT to mint a long-lived API key:
curl -X POST /api/v1/auth/keys \\
  -H "Authorization: Bearer eyJ..." \\
  -d '{"name": "My App"}'
# Response: { "key": "wot_abc123...", "api_key": {...} }

# 2'. (Magic-link path) Visit /developers/keys in the browser and
#     click "Generate key". Copy the value once - we never show it
#     again.

# 3. Use the API key in all future requests:
curl /api/v1/search?q=physician \\
  -H "Authorization: Bearer wot_abc123..."`}
        </pre>
      </div>

      {/* Quick-nav */}
      <div className="flex flex-wrap gap-2">
        {GROUPS.map((g) => (
          <a
            key={g.id}
            href={`#${g.id}`}
            className="px-3 py-1.5 rounded-lg border border-border/50 bg-card text-xs font-medium hover:bg-secondary/50 transition-colors"
          >
            {g.title} ({g.endpoints.length})
          </a>
        ))}
      </div>

      {/* Endpoint groups */}
      {GROUPS.map((group) => (
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
            {group.endpoints.map((ep) => (
              <EndpointCard key={`${ep.method}-${ep.path}`} ep={ep} />
            ))}
          </div>
        </section>
      ))}

      {/* Utility endpoints */}
      <section id="utility" className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary border border-border/50">
            <ClipboardCheck className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Utility</h2>
            <p className="text-sm text-muted-foreground">Bot-facing and LLM-friendly endpoints</p>
          </div>
        </div>
        <div className="rounded-xl border border-border/50 bg-card p-5 space-y-0">
          {[
            { path: '/robots.txt', desc: 'Robots.txt for search engine crawlers' },
            { path: '/llms.txt', desc: 'Short summary for LLM crawlers' },
            { path: '/llms-full.txt', desc: 'Comprehensive documentation for LLM ingestion' },
          ].map(({ path, desc }) => (
            <div key={path} className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 py-3 border-b border-border/30 last:border-0">
              <span className={`inline-flex items-center rounded px-2 py-0.5 text-[11px] font-mono font-semibold w-fit shrink-0 ${METHOD_COLORS.GET}`}>
                GET
              </span>
              <code className="font-mono text-xs text-foreground/80 flex-1">{path}</code>
              <span className="text-xs text-muted-foreground">{desc}</span>
              <a href={path} target="_blank" rel="noopener noreferrer" className="shrink-0 inline-flex items-center gap-1 text-[10px] text-primary hover:underline">
                <ExternalLink className="h-3 w-3" /> Try it
              </a>
            </div>
          ))}
        </div>
      </section>

      {/* Footer CTA */}
      <div className="rounded-xl border border-border/50 bg-card p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="font-semibold">Need higher limits or custom integrations?</p>
          <p className="text-sm text-muted-foreground mt-0.5">
            Pro and Enterprise plans include bulk export, classification API, and dedicated support.
          </p>
        </div>
        <Link
          href="/pricing"
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors shrink-0"
        >
          View pricing
        </Link>
      </div>
    </div>
  )
}
