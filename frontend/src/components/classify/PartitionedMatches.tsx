'use client'

import type { ReactNode } from 'react'

export interface PartitionedSection<T> {
  items: T[]
  heading: string
  caption: string
}

export function PartitionedSections<T>({
  domain,
  standard,
  renderItem,
  getKey,
}: {
  domain: PartitionedSection<T>
  standard: PartitionedSection<T>
  renderItem: (item: T, index: number, section: 'domain' | 'standard') => ReactNode
  getKey: (item: T) => string
}) {
  // When only one category has results, skip the section headings and
  // render a flat list so the UI does not show an empty bucket.
  if (domain.items.length === 0 || standard.items.length === 0) {
    const flat: Array<{ item: T; section: 'domain' | 'standard' }> = [
      ...domain.items.map((item) => ({ item, section: 'domain' as const })),
      ...standard.items.map((item) => ({ item, section: 'standard' as const })),
    ]
    return (
      <div className="grid gap-4">
        {flat.map(({ item, section }, i) => (
          <div key={getKey(item)}>{renderItem(item, i, section)}</div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-sm font-semibold">{domain.heading}</h3>
          <span className="text-xs text-muted-foreground">{domain.caption}</span>
        </div>
        <div className="grid gap-4">
          {domain.items.map((item, i) => (
            <div key={getKey(item)}>{renderItem(item, i, 'domain')}</div>
          ))}
        </div>
      </section>
      <section className="space-y-3">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-sm font-semibold">{standard.heading}</h3>
          <span className="text-xs text-muted-foreground">{standard.caption}</span>
        </div>
        <div className="grid gap-4">
          {standard.items.map((item, i) => (
            <div key={getKey(item)}>{renderItem(item, i, 'standard')}</div>
          ))}
        </div>
      </section>
    </div>
  )
}
