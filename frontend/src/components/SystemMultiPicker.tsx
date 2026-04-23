'use client'

import { useEffect, useMemo, useState } from 'react'
import { Layers, X } from 'lucide-react'
import type { ClassificationSystem } from '@/lib/types'

interface Props {
  selected: string[]
  onChange: (ids: string[]) => void
  options: ClassificationSystem[] | undefined
  label?: string
  placeholder?: string
  className?: string
}

export function SystemMultiPicker({
  selected,
  onChange,
  options,
  label = 'Systems',
  placeholder = 'All Systems (type to filter)',
  className = '',
}: Props) {
  const [text, setText] = useState('')
  const [open, setOpen] = useState(false)
  const [activeIdx, setActiveIdx] = useState(0)

  const selectedEntries = useMemo(
    () =>
      selected
        .map((id) => options?.find((o) => o.id === id) ?? null)
        .filter((s): s is ClassificationSystem => s !== null),
    [selected, options]
  )

  const filtered = useMemo(() => {
    if (!options) return []
    const q = text.trim().toLowerCase()
    const available = options.filter((o) => !selected.includes(o.id))
    const sorted = available.slice().sort((a, b) => a.name.localeCompare(b.name))
    if (!q) return sorted.slice(0, 80)
    return sorted
      .filter((o) => {
        const hay = [o.id, o.name, o.full_name, o.authority, o.region]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
        return hay.includes(q)
      })
      .slice(0, 80)
  }, [options, text, selected])

  useEffect(() => {
    setActiveIdx(0)
  }, [text, selected])

  const add = (id: string) => {
    if (!id || selected.includes(id)) return
    onChange([...selected, id])
    setText('')
    setActiveIdx(0)
  }

  const remove = (id: string) => {
    onChange(selected.filter((c) => c !== id))
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {selectedEntries.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedEntries.map((s) => (
            <span
              key={s.id}
              className="inline-flex items-center gap-1 rounded-full bg-primary/10 text-primary px-2.5 py-1 text-xs font-medium"
              style={s.tint_color ? { borderLeft: `3px solid ${s.tint_color}` } : {}}
            >
              {s.name}
              <button
                type="button"
                onClick={() => remove(s.id)}
                className="hover:text-primary/70"
                aria-label={`Remove ${s.name}`}
              >
                <X className="size-3" />
              </button>
            </span>
          ))}
          {selected.length > 0 && (
            <button
              type="button"
              onClick={() => onChange([])}
              className="inline-flex items-center gap-1 rounded-full bg-secondary/70 text-muted-foreground hover:text-foreground px-2.5 py-1 text-xs"
            >
              <X className="size-3" />
              Clear all
            </button>
          )}
        </div>
      )}
      <div className="relative">
        <Layers className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <input
          type="text"
          value={text}
          placeholder={placeholder}
          aria-label={label}
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
              if (filtered[activeIdx]) add(filtered[activeIdx].id)
            } else if (e.key === 'Escape') {
              setOpen(false)
            } else if (e.key === 'Backspace' && text === '' && selected.length > 0) {
              remove(selected[selected.length - 1])
            }
          }}
          disabled={!options}
          autoComplete="off"
          className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-card border border-border/50 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary disabled:opacity-50"
        />
        {open && filtered.length > 0 && (
          <ul className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-md border border-border bg-popover shadow-lg">
            {filtered.map((s, i) => (
              <li key={s.id}>
                <button
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault()
                    add(s.id)
                  }}
                  onMouseEnter={() => setActiveIdx(i)}
                  className={
                    'flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left text-sm transition-colors ' +
                    (i === activeIdx ? 'bg-accent text-accent-foreground' : 'hover:bg-muted')
                  }
                >
                  <span className="min-w-0 flex-1">
                    <span className="font-medium">{s.name}</span>
                    {s.region && (
                      <span className="ml-2 text-xs text-muted-foreground">{s.region}</span>
                    )}
                  </span>
                  <span className="font-mono text-xs text-muted-foreground shrink-0">
                    {s.node_count.toLocaleString()}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
