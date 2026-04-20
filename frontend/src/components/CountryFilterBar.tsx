'use client'

import { Globe, X } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { CountryListEntry } from '@/lib/api'

interface Props {
  country: string
  countries: CountryListEntry[] | null
  countriesError: string | null
  onChange: (code: string) => void
  label?: string
  compact?: boolean
}

export function CountryFilterBar({
  country,
  countries,
  countriesError,
  onChange,
  label = 'Country',
  compact = false,
}: Props) {
  const selected = countries?.find((c) => c.code === country) ?? null

  const optionLabel = (c: CountryListEntry) =>
    `${c.title} (${c.code}${c.has_official ? ', has official' : ''})`

  const [text, setText] = useState(selected ? optionLabel(selected) : '')

  useEffect(() => {
    setText(selected ? optionLabel(selected) : '')
  }, [selected])

  const byLabel = useMemo(() => {
    const map = new Map<string, string>()
    countries?.forEach((c) => {
      map.set(optionLabel(c).toLowerCase(), c.code)
      map.set(c.code.toLowerCase(), c.code)
      map.set(c.title.toLowerCase(), c.code)
    })
    return map
  }, [countries])

  const commit = (raw: string) => {
    const trimmed = raw.trim()
    if (!trimmed) {
      onChange('')
      return
    }
    const code = byLabel.get(trimmed.toLowerCase())
    if (code) {
      onChange(code)
    } else {
      setText(selected ? optionLabel(selected) : '')
    }
  }

  const containerClass = compact
    ? 'flex flex-wrap items-center gap-2'
    : 'flex flex-wrap items-center gap-3 rounded-xl border border-border bg-card px-4 py-3'

  const listId = compact ? 'country-filter-options-compact' : 'country-filter-options'

  return (
    <div className={containerClass}>
      <Globe className="size-4 text-muted-foreground" aria-hidden />
      {!compact && (
        <label
          htmlFor="country-filter"
          className="text-sm font-medium text-muted-foreground"
        >
          {label}
        </label>
      )}
      <input
        id="country-filter"
        type="text"
        list={listId}
        value={text}
        placeholder="All countries"
        onChange={(e) => {
          const v = e.target.value
          setText(v)
          const code = byLabel.get(v.trim().toLowerCase())
          if (code) onChange(code)
          else if (v.trim() === '') onChange('')
        }}
        onBlur={(e) => commit(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault()
            commit((e.target as HTMLInputElement).value)
          }
        }}
        disabled={!countries && !countriesError}
        aria-label={label}
        autoComplete="off"
        className={
          compact
            ? 'rounded-md border border-border bg-card px-2 py-1.5 text-xs focus:border-primary/60 focus:outline-none disabled:opacity-50'
            : 'flex-1 min-w-[220px] max-w-sm rounded-md border border-border bg-background px-2 py-1.5 text-sm focus:border-primary/60 focus:outline-none disabled:opacity-50'
        }
      />
      <datalist id={listId}>
        {countries?.map((c) => (
          <option key={c.code} value={optionLabel(c)} />
        ))}
      </datalist>
      {selected && (
        <button
          type="button"
          onClick={() => {
            setText('')
            onChange('')
          }}
          className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="size-3" />
          Clear
        </button>
      )}
      {countriesError && (
        <span className="text-xs text-destructive">{countriesError}</span>
      )}
    </div>
  )
}
