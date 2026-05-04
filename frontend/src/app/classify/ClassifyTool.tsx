'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { AlertTriangle, ArrowRight, Briefcase, CheckCircle2, ChevronDown, ChevronUp, GitBranch, Globe, Layers, Loader2, Network, Share2, Sparkles, Terminal, X } from 'lucide-react'
import {
  classifyDemo,
  getCountriesList,
  ApiError,
  type ClassifyDemoAtom,
  type ClassifyDemoResponse,
  type CountryListEntry,
} from '@/lib/api'
import { getSystemColor } from '@/lib/colors'
import { sendEnterpriseLead } from '@/lib/enterpriseIngest'
import { MatchCrosswalkMiniGraph } from '@/components/classify/MatchCrosswalkMiniGraph'
import { MatchHierarchyMiniGraph } from '@/components/classify/MatchHierarchyMiniGraph'
import { PartitionedSections } from '@/components/classify/PartitionedMatches'

const EMAIL_KEY = 'wot_classify_lead_email'
const SNAPSHOT_KEY = 'wot_classify_last_result'

interface ClassifySnapshot {
  text: string
  countries: string[]
  result: ClassifyDemoResponse
}
const EXAMPLES = [
  'telemedicine platform',
  'bakery that also sells coffee',
  'logistics company for frozen goods',
  'registered nurse in pediatrics',
  'online language-learning marketplace',
]

export function ClassifyTool() {
  const [email, setEmail] = useState('')
  const [emailLocked, setEmailLocked] = useState(false)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ClassifyDemoResponse | null>(null)
  const [countries, setCountries] = useState<string[]>([])
  const [countryOptions, setCountryOptions] = useState<CountryListEntry[] | null>(null)

  useEffect(() => {
    let cancelled = false
    getCountriesList()
      .then((list) => {
        if (!cancelled) setCountryOptions(list)
      })
      .catch(() => {
        if (!cancelled) setCountryOptions([])
      })
    return () => {
      cancelled = true
    }
  }, [])

  // Hydrate remembered email from prior session so repeat visitors skip the gate.
  useEffect(() => {
    if (typeof window === 'undefined') return
    const saved = window.localStorage.getItem(EMAIL_KEY)
    if (saved) {
      setEmail(saved)
      setEmailLocked(true)
    }
  }, [])

  // Rehydrate last classify result so a browser back from a result link
  // restores the panel instead of showing an empty form.
  useEffect(() => {
    if (typeof window === 'undefined') return
    const raw = window.sessionStorage.getItem(SNAPSHOT_KEY)
    if (!raw) return
    try {
      const snap = JSON.parse(raw) as ClassifySnapshot
      if (snap.result && typeof snap.text === 'string') {
        setText(snap.text)
        setCountries(Array.isArray(snap.countries) ? snap.countries : [])
        setResult(snap.result)
      }
    } catch {
      window.sessionStorage.removeItem(SNAPSHOT_KEY)
    }
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const cleanEmail = email.trim().toLowerCase()
    const cleanText = text.trim()
    if (!cleanEmail || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(cleanEmail)) {
      setError('Please enter a valid email address.')
      return
    }
    if (cleanText.length < 2) {
      setError('Please describe your business in at least a few words.')
      return
    }

    setLoading(true)
    try {
      const data = await classifyDemo(cleanEmail, cleanText, countries)
      setResult(data)
      // Fire the enterprise lead webhook in parallel with our primary
      // classify_lead DB write. Fire-and-forget per Ali's Apr 24 spec;
      // never blocks the user's response, never surfaces errors in the UI.
      void sendEnterpriseLead('classify_lead', {
        email: cleanEmail,
        metadata: {
          description: cleanText,
          countries,
        },
      })
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(EMAIL_KEY, cleanEmail)
        const snapshot: ClassifySnapshot = {
          text: cleanText,
          countries,
          result: data,
        }
        window.sessionStorage.setItem(SNAPSHOT_KEY, JSON.stringify(snapshot))
      }
      setEmailLocked(true)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Request failed (${err.status}). Please try again.`)
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  function useExample(q: string) {
    setText(q)
    setResult(null)
    setError(null)
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem(SNAPSHOT_KEY)
    }
  }

  return (
    <div className="space-y-6">
      {/* Form card */}
      <form
        onSubmit={handleSubmit}
        className="rounded-xl border border-border bg-card p-5 sm:p-6 space-y-4 shadow-sm"
      >
        <div className="space-y-2">
          <label htmlFor="classify-email" className="block text-sm font-medium">
            Your email
            {emailLocked && (
              <span className="ml-2 text-xs text-muted-foreground font-normal">
                (remembered - <button type="button" className="underline" onClick={() => setEmailLocked(false)}>change</button>)
              </span>
            )}
          </label>
          <input
            id="classify-email"
            type="email"
            autoComplete="email"
            required
            disabled={emailLocked}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30 disabled:opacity-60"
          />
          <p className="text-xs text-muted-foreground">
            We use your email only to send occasional updates about World Of Taxonomy.
            No spam, unsubscribe anytime.
          </p>
        </div>

        <div className="space-y-2">
          <label htmlFor="classify-text" className="block text-sm font-medium">
            Describe your business, product, or occupation
          </label>
          <textarea
            id="classify-text"
            required
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g. a telemedicine platform connecting patients to licensed doctors"
            rows={3}
            maxLength={500}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30 resize-y"
          />
          <div className="flex flex-wrap gap-2 pt-1">
            <span className="text-xs text-muted-foreground">Try:</span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => useExample(ex)}
                className="text-xs rounded-full border border-border bg-background px-2.5 py-0.5 hover:bg-muted transition-colors"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        <CountryMultiPicker
          selected={countries}
          onChange={setCountries}
          options={countryOptions}
        />

        {error && (
          <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">
            <AlertTriangle className="size-4 mt-0.5 shrink-0" />
            <div>{error}</div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60 transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Classifying...
            </>
          ) : (
            <>
              <Sparkles className="size-4" />
              Classify
            </>
          )}
        </button>
      </form>

      {/* Results */}
      {result && <ClassifyResults data={result} />}
    </div>
  )
}

function CountryMultiPicker({
  selected,
  onChange,
  options,
}: {
  selected: string[]
  onChange: (codes: string[]) => void
  options: CountryListEntry[] | null
}) {
  const [text, setText] = useState('')
  const [open, setOpen] = useState(false)
  const [activeIdx, setActiveIdx] = useState(0)

  const selectedEntries = useMemo(
    () =>
      selected.map(
        (code) =>
          options?.find((o) => o.code === code) ?? {
            code,
            title: code,
            system_count: 0,
            has_official: false,
          }
      ),
    [selected, options]
  )

  const filtered = useMemo(() => {
    if (!options) return []
    const q = text.trim().toLowerCase()
    const available = options.filter((o) => !selected.includes(o.code))
    if (!q) return available.slice(0, 50)
    return available
      .filter(
        (o) =>
          o.title.toLowerCase().includes(q) ||
          o.code.toLowerCase().startsWith(q)
      )
      .slice(0, 50)
  }, [options, text, selected])

  useEffect(() => {
    setActiveIdx(0)
  }, [text, selected])

  const add = (code: string) => {
    if (!code || selected.includes(code)) return
    onChange([...selected, code])
    setText('')
    setActiveIdx(0)
  }

  const remove = (code: string) => {
    onChange(selected.filter((c) => c !== code))
  }

  return (
    <div className="space-y-2">
      <label htmlFor="classify-countries" className="block text-sm font-medium">
        <Globe className="inline-block size-3.5 mr-1 -mt-0.5 text-muted-foreground" />
        Countries (optional)
      </label>
      {selectedEntries.length > 0 && (
        <div className="flex flex-wrap gap-2 pb-1">
          {selectedEntries.map((c) => (
            <span
              key={c.code}
              className="inline-flex items-center gap-1 rounded-full bg-primary/10 text-primary px-2.5 py-1 text-xs font-medium"
            >
              {c.title} ({c.code})
              <button
                type="button"
                onClick={() => remove(c.code)}
                className="hover:text-primary/70"
                aria-label={`Remove ${c.title}`}
              >
                <X className="size-3" />
              </button>
            </span>
          ))}
        </div>
      )}
      <div className="relative">
        <input
          id="classify-countries"
          type="text"
          value={text}
          placeholder="Type to search (e.g. India, Germany, US)..."
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          onChange={(e) => {
            setText(e.target.value)
            setOpen(true)
          }}
          onKeyDown={(e) => {
            if (e.key === 'ArrowDown') {
              e.preventDefault()
              setOpen(true)
              setActiveIdx((i) => Math.min(i + 1, filtered.length - 1))
            } else if (e.key === 'ArrowUp') {
              e.preventDefault()
              setActiveIdx((i) => Math.max(i - 1, 0))
            } else if (e.key === 'Enter') {
              e.preventDefault()
              if (filtered[activeIdx]) add(filtered[activeIdx].code)
            } else if (e.key === 'Escape') {
              setOpen(false)
            } else if (e.key === 'Backspace' && text === '' && selected.length > 0) {
              remove(selected[selected.length - 1])
            }
          }}
          disabled={!options}
          autoComplete="off"
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30 disabled:opacity-50"
        />
        {open && filtered.length > 0 && (
          <ul className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-md border border-border bg-popover shadow-lg">
            {filtered.map((c, i) => (
              <li key={c.code}>
                <button
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault()
                    add(c.code)
                  }}
                  onMouseEnter={() => setActiveIdx(i)}
                  className={
                    'flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left text-sm transition-colors ' +
                    (i === activeIdx ? 'bg-accent text-accent-foreground' : 'hover:bg-muted')
                  }
                >
                  <span>
                    <span className="font-medium">{c.title}</span>
                    <span className="ml-2 font-mono text-xs text-muted-foreground">{c.code}</span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {c.system_count} system{c.system_count === 1 ? '' : 's'}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <p className="text-xs text-muted-foreground">
        Leave empty for the default demo set (NAICS, ISIC, NACE, SIC, SOC). Select one or more
        countries to classify against their local systems plus global recommended standards.
      </p>
    </div>
  )
}

function ScopeSummary({ scope }: { scope: NonNullable<ClassifyDemoResponse['scope']> }) {
  return (
    <div className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-xs space-y-1">
      <div className="flex items-center gap-1.5 font-medium">
        <Globe className="size-3.5 text-muted-foreground" />
        Scoped to {scope.countries.join(', ')}
      </div>
      <div className="text-muted-foreground">
        {scope.country_specific_systems.length} country-specific + {scope.global_standard_systems.length} global standard systems
        ({scope.candidate_systems.length} total).
      </div>
    </div>
  )
}

function ClassifyResults({ data }: { data: ClassifyDemoResponse }) {
  const hasMatches = data.domain_matches.length + data.standard_matches.length > 0
  const isCompound = data.compound === true && Array.isArray(data.atoms) && data.atoms.length > 0

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <CheckCircle2 className="size-4 text-primary" />
        Results for <span className="font-medium text-foreground">&ldquo;{data.query}&rdquo;</span>
      </div>

      {data.scope && <ScopeSummary scope={data.scope} />}

      {data.llm_used && data.llm_keywords && data.llm_keywords.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-violet-400/30 bg-violet-50/60 dark:bg-violet-400/5 px-3 py-2 text-xs">
          <Sparkles className="size-3.5 text-violet-600 dark:text-violet-400 shrink-0" />
          <span className="text-muted-foreground">
            No direct matches, so we expanded your query with AI:
          </span>
          <span className="flex flex-wrap gap-1.5">
            {data.llm_keywords.map((kw) => (
              <span
                key={kw}
                className="rounded-full border border-violet-400/40 bg-white dark:bg-violet-950/40 px-2 py-0.5 font-mono text-[11px] text-violet-700 dark:text-violet-300"
              >
                {kw}
              </span>
            ))}
          </span>
        </div>
      )}

      {isCompound ? (
        <CompoundResults data={data} />
      ) : !hasMatches ? (
        <div className="rounded-xl border border-border bg-card p-6 text-sm">
          <p className="font-medium">No strong matches found.</p>
          <p className="text-muted-foreground mt-2">
            Try a broader description (e.g. &ldquo;hospital&rdquo; instead of &ldquo;22-bed
            rural critical-access hospital&rdquo;), or explore the systems directly on the{' '}
            <Link href="/explore" className="text-primary underline">Explore page</Link>.
          </p>
        </div>
      ) : (
        <PartitionedMatches
          domainMatches={data.domain_matches}
          standardMatches={data.standard_matches}
        />
      )}

      {/* Upgrade CTA */}
      <div className="rounded-xl border border-primary/30 bg-primary/5 p-5 sm:p-6">
        <div className="flex items-start gap-3">
          <Sparkles className="size-5 text-primary mt-0.5" />
          <div className="flex-1 space-y-2">
            <h3 className="font-semibold">Need more systems or programmatic access?</h3>
            <p className="text-sm text-muted-foreground">{data.upgrade_cta}</p>
            <Link
              href="/pricing"
              className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:underline"
            >
              See pricing <ArrowRight className="size-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Secondary CTAs - only render when there is a result worth acting on */}
      {hasMatches && (
        <div className="grid sm:grid-cols-2 gap-3">
          <a
            href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(
              `Just classified "${data.query}" with World Of Taxonomy - codes across NAICS, ISIC, SIC, NACE, SOC in seconds. Free and open source:`
            )}&url=${encodeURIComponent('https://worldoftaxonomy.com/classify')}&via=ramdhanyk`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-3 rounded-xl border border-border bg-card p-4 hover:border-primary/40 hover:bg-accent/40 transition"
          >
            <Share2 className="size-5 text-primary mt-0.5 shrink-0" />
            <div className="flex-1 space-y-1">
              <h3 className="text-sm font-medium">Share your result</h3>
              <p className="text-xs text-muted-foreground">
                Post this classification to X
              </p>
            </div>
            <ArrowRight className="size-3.5 text-muted-foreground mt-1 shrink-0" />
          </a>

          <Link
            href="/mcp"
            className="flex items-start gap-3 rounded-xl border border-border bg-card p-4 hover:border-primary/40 hover:bg-accent/40 transition"
          >
            <Terminal className="size-5 text-primary mt-0.5 shrink-0" />
            <div className="flex-1 space-y-1">
              <h3 className="text-sm font-medium">Use it in Claude Desktop</h3>
              <p className="text-xs text-muted-foreground">
                Add the MCP server and classify from any chat
              </p>
            </div>
            <ArrowRight className="size-3.5 text-muted-foreground mt-1 shrink-0" />
          </Link>
        </div>
      )}

      {/* Disclaimer + report link */}
      <div className="rounded-md border border-border bg-muted/30 p-4 text-xs text-muted-foreground space-y-1.5">
        <p>{data.disclaimer}</p>
        <p>
          <a
            href={data.report_issue_url}
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-foreground"
          >
            Report a data issue on GitHub
          </a>
        </p>
      </div>
    </div>
  )
}

function CompoundResults({ data }: { data: ClassifyDemoResponse }) {
  const atoms = data.atoms ?? []
  const hero: ClassifyDemoAtom | null =
    data.hero ??
    atoms.find((a) => a.domain_matches.length + a.standard_matches.length > 0) ??
    atoms[0] ??
    null
  const rest = atoms.filter((a) => a !== hero)

  return (
    <div className="space-y-5">
      {/* Compound detection banner */}
      <div className="flex items-start gap-3 rounded-xl border border-amber-400/30 bg-amber-50/40 dark:bg-amber-400/5 p-4">
        <Layers className="size-5 text-amber-500 mt-0.5 shrink-0" />
        <div className="flex-1 space-y-1">
          <p className="text-sm font-semibold">
            We detected {atoms.length} distinct business lines in your description.
          </p>
          <p className="text-xs text-muted-foreground">
            Compound establishments often need multiple NAICS / ISIC codes (primary + secondary).
            We&rsquo;re showing the full classification for the first line below, plus the others we detected.
          </p>
        </div>
      </div>

      {/* Hero atom - full results */}
      {hero && (
        <div className="space-y-3">
          <div className="flex items-baseline gap-2">
            <span className="text-[10px] uppercase tracking-wide font-semibold text-primary bg-primary/10 rounded px-2 py-0.5">
              Featured line
            </span>
            <h3 className="text-sm font-medium">{hero.phrase}</h3>
          </div>
          {hero.domain_matches.length + hero.standard_matches.length > 0 ? (
            <PartitionedMatches
              domainMatches={hero.domain_matches}
              standardMatches={hero.standard_matches}
            />
          ) : (
            <div className="rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
              No automatic match for &ldquo;{hero.phrase}&rdquo; - our team can help classify it correctly.
            </div>
          )}
        </div>
      )}

      {/* Other detected atoms - teased */}
      {rest.length > 0 && (
        <div className="rounded-xl border border-border bg-card/50 p-4 sm:p-5 space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Briefcase className="size-4 text-muted-foreground" />
            Other business lines detected
          </div>
          <ul className="grid sm:grid-cols-2 gap-2">
            {rest.map((a) => {
              const top =
                a.domain_matches[0]?.results[0] ?? a.standard_matches[0]?.results[0]
              return (
                <li
                  key={a.phrase}
                  className="flex items-start justify-between gap-3 rounded-md border border-border bg-background px-3 py-2"
                >
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{a.phrase}</div>
                    {top ? (
                      <div className="text-xs text-muted-foreground truncate">
                        <span className="font-mono">{top.code}</span> {top.title}
                      </div>
                    ) : (
                      <div className="text-xs text-muted-foreground italic">
                        Classification pending review
                      </div>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {/* Consultation CTA - primary revenue hook for compound cases */}
      {data.cta && (
        <div className="rounded-xl border-2 border-primary/40 bg-gradient-to-br from-primary/10 to-primary/5 p-5 sm:p-6">
          <div className="flex items-start gap-3">
            <Sparkles className="size-5 text-primary mt-0.5 shrink-0" />
            <div className="flex-1 space-y-2">
              <h3 className="font-semibold">{data.cta.title}</h3>
              <p className="text-sm text-muted-foreground">{data.cta.message}</p>
              <Link
                href={data.cta.url}
                className="inline-flex items-center gap-1 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                {data.cta.cta_label} <ArrowRight className="size-3.5" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function PartitionedMatches({
  domainMatches,
  standardMatches,
}: {
  domainMatches: ClassifyDemoResponse['domain_matches']
  standardMatches: ClassifyDemoResponse['standard_matches']
}) {
  return (
    <PartitionedSections
      domain={{
        items: domainMatches,
        heading: 'Start here: Domain taxonomies',
        caption: 'Plain-language categories curated by World Of Taxonomy',
      }}
      standard={{
        items: standardMatches,
        heading: 'Official standard codes',
        caption: 'NAICS, ISIC, NACE, SIC, SOC and peers',
      }}
      getKey={(match) => match.system_id}
      renderItem={(match, i, section) => (
        <SystemMatchCard
          match={match}
          defaultShowHierarchy={section === 'domain' ? i === 0 : false}
        />
      )}
    />
  )
}

function SystemMatchCard({
  match,
  defaultShowHierarchy = false,
}: {
  match: ClassifyDemoResponse['domain_matches'][number]
  defaultShowHierarchy?: boolean
}) {
  const color = getSystemColor(match.system_id)
  const [showGraph, setShowGraph] = useState(false)
  const [showHierarchy, setShowHierarchy] = useState(defaultShowHierarchy)
  const topResult = match.results[0]

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <div
        className="px-5 py-3 border-b border-border flex items-center justify-between"
        style={{ backgroundColor: `${color}12` }}
      >
        <div className="flex items-center gap-2">
          <span
            className="inline-block size-2.5 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="font-semibold text-sm">{match.system_name}</span>
        </div>
        <Link
          href={`/system/${match.system_id}`}
          className="text-xs text-muted-foreground hover:text-foreground hover:underline"
        >
          Browse all codes →
        </Link>
      </div>
      <ul className="divide-y divide-border">
        {match.results.map((r, i) => (
          <li key={`${match.system_id}-${r.code}`} className="px-5 py-3">
            <Link
              href={`/system/${match.system_id}/node/${r.code}`}
              className="flex items-start justify-between gap-4 group"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  <span className="font-mono text-sm font-semibold text-foreground">
                    {r.code}
                  </span>
                  {i === 0 && (
                    <span className="text-[10px] uppercase tracking-wide font-semibold text-primary bg-primary/10 rounded px-1.5 py-0.5">
                      Top match
                    </span>
                  )}
                </div>
                <div className="text-sm text-foreground/90 mt-0.5 group-hover:text-primary transition-colors">
                  {r.title}
                </div>
              </div>
              <ArrowRight className="size-4 text-muted-foreground group-hover:text-primary mt-1 shrink-0" />
            </Link>
          </li>
        ))}
      </ul>
      {topResult && (
        <div className="border-t border-border divide-y divide-border">
          <div>
            <button
              type="button"
              onClick={() => setShowHierarchy((s) => !s)}
              className="w-full flex items-center justify-between px-5 py-2.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors"
              aria-expanded={showHierarchy}
            >
              <span className="flex items-center gap-1.5">
                <GitBranch className="size-3.5" />
                {showHierarchy ? 'Hide hierarchy' : 'Show hierarchy'}
                <span className="font-mono">({topResult.code})</span>
              </span>
              {showHierarchy ? (
                <ChevronUp className="size-3.5" />
              ) : (
                <ChevronDown className="size-3.5" />
              )}
            </button>
            {showHierarchy && (
              <div className="px-5 pb-4 pt-1">
                <MatchHierarchyMiniGraph
                  systemId={match.system_id}
                  code={topResult.code}
                  title={topResult.title}
                />
              </div>
            )}
          </div>
          {(topResult.crosswalk_count ?? 0) > 0 && (
            <div>
              <button
                type="button"
                onClick={() => setShowGraph((s) => !s)}
                className="w-full flex items-center justify-between px-5 py-2.5 text-xs text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors"
                aria-expanded={showGraph}
              >
                <span className="flex items-center gap-1.5">
                  <Network className="size-3.5" />
                  {showGraph
                    ? 'Hide crosswalks'
                    : `Show ${topResult.crosswalk_count} crosswalk${topResult.crosswalk_count === 1 ? '' : 's'} to other systems`}
                  <span className="font-mono">({topResult.code})</span>
                </span>
                {showGraph ? (
                  <ChevronUp className="size-3.5" />
                ) : (
                  <ChevronDown className="size-3.5" />
                )}
              </button>
              {showGraph && (
                <div className="px-5 pb-4 pt-1">
                  <MatchCrosswalkMiniGraph
                    systemId={match.system_id}
                    systemName={match.system_name}
                    code={topResult.code}
                    title={topResult.title}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
