'use client'

import Link from 'next/link'
import { getSystemColor } from '@/lib/colors'
import type { CountrySystem } from '@/lib/api'
import { useCountryFilter } from '@/lib/useCountryFilter'
import { CountryFilterBar } from '@/components/CountryFilterBar'

interface Props {
  children: React.ReactNode
}

export function CountryFilterShell({ children }: Props) {
  const {
    country,
    setCountry,
    countries,
    countriesError,
    countrySystems,
    countrySystemsError,
    selectedCountry,
  } = useCountryFilter()

  return (
    <div className="space-y-6">
      <CountryFilterBar
        country={country}
        countries={countries}
        countriesError={countriesError}
        onChange={setCountry}
      />

      {country ? (
        <CountryFilteredView
          countryCode={country}
          countryTitle={selectedCountry?.title || country}
          systems={countrySystems}
          error={countrySystemsError}
        />
      ) : (
        children
      )}
    </div>
  )
}

function CountryFilteredView({
  countryCode: _countryCode,
  countryTitle,
  systems,
  error,
}: {
  countryCode: string
  countryTitle: string
  systems: CountrySystem[] | null
  error: string | null
}) {
  if (error) {
    return (
      <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
        {error}
      </div>
    )
  }
  if (!systems) {
    return (
      <div className="rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
        Loading systems applicable to {countryTitle}...
      </div>
    )
  }
  if (systems.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
        No classification systems recorded for {countryTitle} yet.
      </div>
    )
  }

  const grouped = new Map<string, CountrySystem[]>()
  for (const s of systems) {
    const key = s.relevance
    const list = grouped.get(key) ?? []
    list.push(s)
    grouped.set(key, list)
  }

  const sections: { key: CountrySystem['relevance']; label: string; hint: string }[] = [
    { key: 'official', label: 'Official national standard', hint: "The country's own classification." },
    { key: 'regional', label: 'Regional bloc standard', hint: 'Applies via a regional agreement (e.g. EU member of NACE).' },
    { key: 'recommended', label: 'Internationally recommended', hint: 'UN/WCO/WHO standards universally applicable.' },
    { key: 'historical', label: 'Historical / legacy', hint: 'Retired but still referenced.' },
  ]

  return (
    <section className="space-y-6">
      <header className="space-y-1">
        <h2 className="text-xl font-semibold tracking-tight">
          {countryTitle} &middot; {systems.length} applicable systems
        </h2>
        <p className="text-xs text-muted-foreground">
          Ordered by relevance. Click any system to open its detail page.
        </p>
      </header>
      {sections.map(({ key, label, hint }) => {
        const list = grouped.get(key) ?? []
        if (list.length === 0) return null
        return (
          <div key={key} className="space-y-2">
            <div>
              <h3 className="text-sm font-semibold">{label}</h3>
              <p className="text-xs text-muted-foreground">{hint}</p>
            </div>
            <ul className="grid sm:grid-cols-2 gap-3">
              {list.map((s) => (
                <li key={s.id}>
                  <Link
                    href={`/system/${s.id}`}
                    className="block rounded-xl border border-border bg-card p-4 hover:border-primary/50 transition-colors"
                    style={{ boxShadow: `inset 3px 0 0 0 ${getSystemColor(s.id)}` }}
                  >
                    <div className="flex items-baseline justify-between gap-2">
                      <span className="font-semibold text-sm">{s.name}</span>
                      <span className="text-xs text-muted-foreground">
                        {s.node_count.toLocaleString()} codes
                      </span>
                    </div>
                    {s.full_name && (
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {s.full_name}
                      </p>
                    )}
                    {s.csl_notes && (
                      <p className="text-xs text-muted-foreground mt-2 italic line-clamp-2">
                        {s.csl_notes}
                      </p>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )
      })}
    </section>
  )
}
