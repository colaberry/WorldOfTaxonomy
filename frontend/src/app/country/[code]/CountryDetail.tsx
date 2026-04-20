'use client'

import { useQuery } from '@tanstack/react-query'
import { getCountryProfile } from '@/lib/api'
import type { CountryProfile, CountrySystem } from '@/lib/api'
import Link from 'next/link'
import { ArrowLeft, Globe, Building2, ChevronRight, ChevronDown } from 'lucide-react'
import { classifySystem, CATEGORY_ORDER, type SystemCategory } from '@/lib/systemCategory'

const RELEVANCE_LABEL: Record<string, string> = {
  official: 'Official National Standard',
  regional: 'Regional / Bloc Standard',
  recommended: 'UN / International Recommended',
  historical: 'Historical',
}

const RELEVANCE_COLOR: Record<string, string> = {
  official: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800',
  regional: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800',
  recommended: 'text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700',
  historical: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800',
}

const RELEVANCE_DOT: Record<string, string> = {
  official: 'bg-green-500',
  regional: 'bg-blue-500',
  recommended: 'bg-slate-400',
  historical: 'bg-amber-500',
}

const NAICS_SECTOR_NAMES: Record<string, string> = {
  '11': 'Agriculture, Forestry, Fishing',
  '21': 'Mining, Quarrying, Oil & Gas',
  '22': 'Utilities',
  '23': 'Construction',
  '31': 'Manufacturing',
  '32': 'Manufacturing',
  '33': 'Manufacturing',
  '42': 'Wholesale Trade',
  '44': 'Retail Trade',
  '45': 'Retail Trade',
  '48': 'Transportation & Warehousing',
  '49': 'Transportation & Warehousing',
  '51': 'Information',
  '52': 'Finance & Insurance',
  '53': 'Real Estate',
  '54': 'Professional & Technical Services',
  '55': 'Management of Companies',
  '56': 'Administrative & Support Services',
  '61': 'Educational Services',
  '62': 'Health Care & Social Assistance',
  '71': 'Arts, Entertainment & Recreation',
  '72': 'Accommodation & Food Services',
  '81': 'Other Services',
  '92': 'Public Administration',
}

function SystemCard({ system }: { system: CountrySystem }) {
  const colorClass = RELEVANCE_COLOR[system.relevance] ?? RELEVANCE_COLOR.recommended
  const dotClass = RELEVANCE_DOT[system.relevance] ?? RELEVANCE_DOT.recommended
  return (
    <Link
      href={`/system/${system.id}`}
      className="group flex items-start gap-3 rounded-lg border border-border/50 bg-card p-4 hover:border-border hover:bg-accent/30 transition-colors"
    >
      <span className={`mt-1 h-2.5 w-2.5 rounded-full shrink-0 ${dotClass}`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-foreground text-sm">{system.name}</span>
          <span className={`text-xs px-1.5 py-0.5 rounded border font-medium ${colorClass}`}>
            {RELEVANCE_LABEL[system.relevance] ?? system.relevance}
          </span>
        </div>
        {system.full_name && system.full_name !== system.name && (
          <p className="text-xs text-muted-foreground mt-0.5 truncate">{system.full_name}</p>
        )}
        <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
          <span>{system.node_count.toLocaleString()} codes</span>
          {system.authority && <span>{system.authority}</span>}
        </div>
        {system.csl_notes && (
          <p className="text-xs text-muted-foreground/70 mt-1 italic">{system.csl_notes}</p>
        )}
      </div>
      <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 opacity-0 group-hover:opacity-100 transition-opacity mt-1" />
    </Link>
  )
}

interface CountryDetailProps {
  code: string
  initialProfile: CountryProfile | null
}

export function CountryDetail({ code, initialProfile }: CountryDetailProps) {
  const upperCode = code.toUpperCase()

  const { data: profile, isLoading, isError } = useQuery({
    queryKey: ['country', upperCode],
    queryFn: () => getCountryProfile(upperCode),
    initialData: initialProfile ?? undefined,
    staleTime: 0,
    retry: 1,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="text-sm">Loading country profile...</span>
        </div>
      </div>
    )
  }

  if (isError || !profile) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <p className="text-lg font-semibold text-foreground mb-2">Country not found</p>
        <p className="text-sm text-muted-foreground mb-6">
          No taxonomy data found for country code <code className="font-mono">{upperCode}</code>.
        </p>
        <Link href="/" className="text-sm text-primary hover:underline flex items-center gap-1 justify-center">
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>
      </div>
    )
  }

  const { country, classification_systems, sector_strengths } = profile

  const byRelevance = ['official', 'regional', 'recommended', 'historical'].reduce(
    (acc, rel) => {
      const systems = classification_systems.filter((s) => s.relevance === rel)
      if (systems.length > 0) acc[rel] = systems
      return acc
    },
    {} as Record<string, CountrySystem[]>
  )

  const leaderStrengths = sector_strengths.filter((s) => s.match_type === 'exact')
  const broadStrengths = sector_strengths.filter((s) => s.match_type === 'broad')
  const emergingStrengths = sector_strengths.filter((s) => s.match_type === 'partial')

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 space-y-8">
      {/* Back link */}
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        World map
      </Link>

      {/* Header */}
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <Globe className="h-7 w-7 text-primary shrink-0" />
          <div>
            <h1 className="text-2xl font-bold text-foreground">
              {country.title ?? upperCode}
            </h1>
            <p className="text-sm text-muted-foreground">
              <span className="font-mono">{upperCode}</span>
              {country.parent_region && (
                <span> &middot; {country.parent_region}</span>
              )}
            </p>
          </div>
        </div>
        <p className="text-sm text-muted-foreground pt-1">
          {classification_systems.length} classification{' '}
          {classification_systems.length === 1 ? 'system' : 'systems'} applicable
          {sector_strengths.length > 0 && (
            <span> &middot; {sector_strengths.length} sector{' '}
              {sector_strengths.length === 1 ? 'strength' : 'strengths'} identified</span>
          )}
        </p>
      </div>

      {/* Sector strengths */}
      {sector_strengths.length > 0 && (
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <Building2 className="h-4 w-4 text-muted-foreground" />
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Sector Strengths
            </h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {leaderStrengths.length > 0 && leaderStrengths.map((s) => (
              <div
                key={s.naics_sector}
                className="flex items-center gap-2 rounded-md border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-950 px-3 py-2"
              >
                <span className="h-2 w-2 rounded-full bg-green-500 shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-green-700 dark:text-green-300 truncate">
                    {s.sector_name || NAICS_SECTOR_NAMES[s.naics_sector] || `Sector ${s.naics_sector}`}
                  </p>
                  <p className="text-xs text-green-600/70 dark:text-green-400/70">
                    NAICS {s.naics_sector} &middot; Leadership strength
                  </p>
                </div>
              </div>
            ))}
            {broadStrengths.length > 0 && broadStrengths.map((s) => (
              <div
                key={s.naics_sector}
                className="flex items-center gap-2 rounded-md border border-cyan-200 dark:border-cyan-800 bg-cyan-50 dark:bg-cyan-950 px-3 py-2"
              >
                <span className="h-2 w-2 rounded-full bg-cyan-500 shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-cyan-700 dark:text-cyan-300 truncate">
                    {s.sector_name || NAICS_SECTOR_NAMES[s.naics_sector] || `Sector ${s.naics_sector}`}
                  </p>
                  <p className="text-xs text-cyan-600/70 dark:text-cyan-400/70">
                    NAICS {s.naics_sector}{s.notes ? ` - ${s.notes}` : ''}
                  </p>
                </div>
              </div>
            ))}
            {emergingStrengths.length > 0 && emergingStrengths.map((s) => (
              <div
                key={s.naics_sector}
                className="flex items-center gap-2 rounded-md border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950 px-3 py-2"
              >
                <span className="h-2 w-2 rounded-full bg-blue-500 shrink-0" />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-blue-700 dark:text-blue-300 truncate">
                    {s.sector_name || NAICS_SECTOR_NAMES[s.naics_sector] || `Sector ${s.naics_sector}`}
                  </p>
                  <p className="text-xs text-blue-600/70 dark:text-blue-400/70">
                    NAICS {s.naics_sector} &middot; Emerging strength
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Classification systems by relevance group, categorized */}
      <section className="space-y-8">
        {(['official', 'regional', 'recommended', 'historical'] as const).map((rel) => {
          const systems = byRelevance[rel]
          if (!systems) return null

          const byCategory = new Map<SystemCategory, CountrySystem[]>()
          for (const s of systems) {
            const cat = classifySystem(s.id)
            const list = byCategory.get(cat) ?? []
            list.push(s)
            byCategory.set(cat, list)
          }
          for (const list of byCategory.values()) {
            list.sort((a, b) => b.node_count - a.node_count)
          }

          const orderedCategories = CATEGORY_ORDER.filter((c) => byCategory.has(c))

          return (
            <div key={rel} className="space-y-3">
              <div className="flex items-baseline justify-between gap-3">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  {RELEVANCE_LABEL[rel]}
                </h2>
                <span className="text-xs text-muted-foreground">
                  {systems.length} {systems.length === 1 ? 'system' : 'systems'}
                </span>
              </div>
              <div className="space-y-2">
                {orderedCategories.map((cat, i) => {
                  const list = byCategory.get(cat)!
                  const autoOpen = rel === 'official' && i === 0
                  const codes = list.reduce((acc, s) => acc + s.node_count, 0)
                  return (
                    <details
                      key={`${rel}-${cat}`}
                      open={autoOpen}
                      className="group rounded-lg border border-border/50 bg-card/50"
                    >
                      <summary className="flex items-center justify-between gap-3 cursor-pointer list-none px-4 py-2.5">
                        <div className="flex items-center gap-2">
                          <ChevronDown className="size-3.5 text-muted-foreground transition-transform group-open:rotate-0 -rotate-90" />
                          <span className="font-medium text-sm">{cat}</span>
                          <span className="text-xs text-muted-foreground">
                            {list.length} {list.length === 1 ? 'system' : 'systems'} · {codes.toLocaleString()} codes
                          </span>
                        </div>
                      </summary>
                      <div className="px-4 pb-3 pt-1 space-y-2">
                        {list.map((s) => (
                          <SystemCard key={s.id} system={s} />
                        ))}
                      </div>
                    </details>
                  )
                })}
              </div>
            </div>
          )
        })}
      </section>

      {classification_systems.length === 0 && (
        <div className="rounded-lg border border-border bg-muted/30 px-6 py-10 text-center">
          <p className="text-sm text-muted-foreground">
            No classification systems have been linked to this country yet.
          </p>
          <p className="text-xs text-muted-foreground/70 mt-1">
            Run <code className="font-mono">ingest crosswalk_country_system</code> to populate.
          </p>
        </div>
      )}

      {/* Footer note */}
      <p className="text-xs text-muted-foreground/60 text-center border-t border-border pt-4">
        Country taxonomy profiles are derived from ISO 3166-1, regional standards bodies, and UN agency recommendations.
        {' '}<Link href="/" className="underline hover:text-muted-foreground">Explore all systems</Link>
      </p>
    </div>
  )
}
