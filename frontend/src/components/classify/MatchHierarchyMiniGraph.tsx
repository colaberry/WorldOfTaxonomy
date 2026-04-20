'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Loader2, GitBranch } from 'lucide-react'
import { getAncestors, getChildren } from '@/lib/api'
import { getSystemColor } from '@/lib/colors'
import type { ClassificationNode } from '@/lib/types'

interface Props {
  systemId: string
  code: string
  title: string
}

interface HierarchyRow {
  code: string
  title: string
  level: number
  isCurrent: boolean
  isChild: boolean
}

const MAX_CHILDREN = 4
const ROW_HEIGHT = 26
const CONNECTOR_X = 18
const LEFT_PAD = 28

export function MatchHierarchyMiniGraph({ systemId, code, title }: Props) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [ancestors, setAncestors] = useState<ClassificationNode[]>([])
  const [children, setChildren] = useState<ClassificationNode[]>([])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    Promise.all([
      getAncestors(systemId, code),
      getChildren(systemId, code).catch(() => [] as ClassificationNode[]),
    ])
      .then(([ancs, kids]) => {
        if (cancelled) return
        setAncestors(ancs)
        setChildren(kids)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load hierarchy')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [systemId, code])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8 text-xs text-muted-foreground">
        <Loader2 className="size-3.5 mr-2 animate-spin" />
        Loading hierarchy...
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-6 text-center text-xs text-muted-foreground">
        {error}
      </div>
    )
  }

  const color = getSystemColor(systemId)
  const shownChildren = children.slice(0, MAX_CHILDREN)
  const hiddenChildrenCount = Math.max(0, children.length - MAX_CHILDREN)

  const properAncestors = ancestors.filter((a) => a.code !== code)
  const currentLevel =
    ancestors.find((a) => a.code === code)?.level ??
    (properAncestors[properAncestors.length - 1]?.level ?? 0) + 1

  const rows: HierarchyRow[] = [
    ...properAncestors.map((a) => ({
      code: a.code,
      title: a.title,
      level: a.level,
      isCurrent: false,
      isChild: false,
    })),
    { code, title, level: currentLevel, isCurrent: true, isChild: false },
    ...shownChildren.map((c) => ({
      code: c.code,
      title: c.title,
      level: c.level,
      isCurrent: false,
      isChild: true,
    })),
  ]

  const totalRows = rows.length + (hiddenChildrenCount > 0 ? 1 : 0)
  const svgHeight = totalRows * ROW_HEIGHT + 10
  const svgWidth = 360

  const minLevel = Math.min(...rows.map((r) => r.level))
  const rowX = (r: HierarchyRow) =>
    LEFT_PAD + (r.level - minLevel) * CONNECTOR_X

  return (
    <div className="space-y-3">
      <div className="relative">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto"
          preserveAspectRatio="xMinYMin meet"
        >
          {rows.map((r, i) => {
            if (i === 0) return null
            const prev = rows[i - 1]
            const x1 = rowX(prev) + 4
            const y1 = i * ROW_HEIGHT - ROW_HEIGHT / 2 + 5
            const x2 = rowX(r) + 4
            const y2 = i * ROW_HEIGHT + 5
            return (
              <path
                key={`connector-${i}`}
                d={`M ${x1} ${y1} V ${y2 - 2} H ${x2}`}
                stroke={color}
                strokeOpacity={0.4}
                strokeWidth={1.2}
                fill="none"
              />
            )
          })}
        </svg>

        <div className="absolute inset-0">
          {rows.map((r, i) => {
            const top = i * ROW_HEIGHT
            const left = rowX(r) + 10
            const href = `/codes/${systemId}/${encodeURIComponent(r.code)}`
            return (
              <div
                key={`row-${i}-${r.code}`}
                className="absolute flex items-center gap-2 text-xs"
                style={{ top, left, right: 4 }}
              >
                <span
                  className="inline-block size-1.5 rounded-full shrink-0"
                  style={{
                    backgroundColor: r.isCurrent ? color : `${color}88`,
                  }}
                />
                {r.isCurrent ? (
                  <div
                    className="flex items-baseline gap-2 px-2 py-0.5 rounded font-semibold"
                    style={{
                      backgroundColor: `${color}22`,
                      color,
                    }}
                  >
                    <span className="font-mono">{r.code}</span>
                    <span className="truncate max-w-[240px] text-foreground">
                      {r.title}
                    </span>
                  </div>
                ) : (
                  <Link
                    href={href}
                    className="flex items-baseline gap-2 hover:underline text-foreground/80 hover:text-foreground"
                  >
                    <span className="font-mono text-muted-foreground">
                      {r.code}
                    </span>
                    <span className="truncate max-w-[240px]">{r.title}</span>
                  </Link>
                )}
              </div>
            )
          })}

          {hiddenChildrenCount > 0 && (
            <div
              className="absolute flex items-center gap-2 text-xs text-muted-foreground italic"
              style={{
                top: rows.length * ROW_HEIGHT,
                left:
                  rowX({
                    code: '',
                    title: '',
                    level: (rows[rows.length - 1]?.level ?? 0),
                    isCurrent: false,
                    isChild: true,
                  }) + 10,
              }}
            >
              + {hiddenChildrenCount} more{' '}
              {hiddenChildrenCount === 1 ? 'subcategory' : 'subcategories'}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <GitBranch className="size-3.5" />
          Level {ancestors.length + 1} of {systemId.toUpperCase()}
          {children.length > 0 && (
            <>
              {' '}&middot; {children.length}{' '}
              {children.length === 1 ? 'child' : 'children'}
            </>
          )}
        </div>
        <Link
          href={`/codes/${systemId}/${encodeURIComponent(code)}`}
          className="text-primary hover:underline font-medium"
        >
          Open full tree -&gt;
        </Link>
      </div>
    </div>
  )
}
