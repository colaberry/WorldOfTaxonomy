'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Loader2, Network } from 'lucide-react'
import { getEquivalences } from '@/lib/api'
import { getSystemColor } from '@/lib/colors'
import type { Equivalence } from '@/lib/types'

interface Props {
  systemId: string
  systemName: string
  code: string
  title: string
}

interface Connection {
  systemId: string
  edgeCount: number
  exactCount: number
  firstTargetCode: string
}

function groupBySystem(eqs: Equivalence[]): Connection[] {
  const buckets = new Map<string, { edges: Equivalence[] }>()
  for (const e of eqs) {
    const bucket = buckets.get(e.target_system) ?? { edges: [] }
    bucket.edges.push(e)
    buckets.set(e.target_system, bucket)
  }
  const conns: Connection[] = []
  for (const [sysId, { edges }] of buckets) {
    conns.push({
      systemId: sysId,
      edgeCount: edges.length,
      exactCount: edges.filter((e) => e.match_type === 'exact').length,
      firstTargetCode: edges[0].target_code,
    })
  }
  conns.sort((a, b) => b.edgeCount - a.edgeCount)
  return conns.slice(0, 8)
}

export function MatchCrosswalkMiniGraph({
  systemId,
  systemName,
  code,
  title,
}: Props) {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [connections, setConnections] = useState<Connection[]>([])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getEquivalences(systemId, code)
      .then((eqs) => {
        if (cancelled) return
        setConnections(groupBySystem(eqs))
      })
      .catch(() => {
        if (!cancelled) setError('Could not load crosswalks')
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
        Loading crosswalks...
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

  if (connections.length === 0) {
    return (
      <div className="py-6 text-center text-xs text-muted-foreground">
        No crosswalk edges recorded for{' '}
        <span className="font-mono">
          {systemId}:{code}
        </span>{' '}
        yet.
      </div>
    )
  }

  const width = 360
  const height = 220
  const cx = width / 2
  const cy = height / 2
  const orbit = Math.min(cx - 60, cy - 40)
  const centerColor = getSystemColor(systemId)
  const maxEdges = Math.max(...connections.map((c) => c.edgeCount))

  const positioned = connections.map((c, i) => {
    const angle = (i / connections.length) * 2 * Math.PI - Math.PI / 2
    return {
      ...c,
      x: cx + orbit * Math.cos(angle),
      y: cy + orbit * Math.sin(angle),
      color: getSystemColor(c.systemId),
      weight: 1 + (c.edgeCount / maxEdges) * 2.5,
    }
  })

  return (
    <div className="space-y-3">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-auto"
        preserveAspectRatio="xMidYMid meet"
      >
        {positioned.map((c) => (
          <line
            key={`line-${c.systemId}`}
            x1={cx}
            y1={cy}
            x2={c.x}
            y2={c.y}
            stroke={c.color}
            strokeOpacity={0.35}
            strokeWidth={c.weight}
          />
        ))}

        {positioned.map((c) => (
          <g
            key={`sat-${c.systemId}`}
            onClick={() =>
              router.push(`/crosswalks/${systemId}/${code}/${c.systemId}`)
            }
            className="cursor-pointer"
          >
            <circle
              cx={c.x}
              cy={c.y}
              r={18}
              fill={c.color}
              fillOpacity={0.15}
              stroke={c.color}
              strokeOpacity={0.5}
              strokeWidth={1.5}
              className="hover:opacity-80 transition-opacity"
            />
            <text
              x={c.x}
              y={c.y}
              textAnchor="middle"
              dy="0.35em"
              fill={c.color}
              fontFamily="'Geist Mono', monospace"
              fontSize={9}
              pointerEvents="none"
            >
              {c.systemId.slice(0, 6).toUpperCase()}
            </text>
            <text
              x={c.x}
              y={c.y + 30}
              textAnchor="middle"
              fill="currentColor"
              fontFamily="'Geist Mono', monospace"
              fontSize={9}
              className="text-muted-foreground"
              pointerEvents="none"
            >
              {c.edgeCount}
            </text>
          </g>
        ))}

        <g>
          <circle
            cx={cx}
            cy={cy}
            r={30}
            fill={centerColor}
            fillOpacity={0.2}
            stroke={centerColor}
            strokeOpacity={0.7}
            strokeWidth={2}
          />
          <text
            x={cx}
            y={cy - 2}
            textAnchor="middle"
            fill={centerColor}
            fontFamily="'Geist Mono', monospace"
            fontSize={10}
            fontWeight={600}
            pointerEvents="none"
          >
            {code}
          </text>
          <text
            x={cx}
            y={cy + 10}
            textAnchor="middle"
            fill="currentColor"
            fontFamily="'Geist Mono', monospace"
            fontSize={8}
            className="text-muted-foreground"
            pointerEvents="none"
          >
            {systemName.length > 10 ? systemName.slice(0, 9) + '...' : systemName}
          </text>
        </g>
      </svg>

      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <Network className="size-3.5" />
          {connections.reduce((s, c) => s + c.edgeCount, 0)} crosswalk edges across{' '}
          {connections.length} {connections.length === 1 ? 'system' : 'systems'}
        </div>
        <Link
          href={`/codes/${systemId}/${encodeURIComponent(code)}`}
          className="text-primary hover:underline font-medium"
        >
          See full detail -&gt;
        </Link>
      </div>

      <div className="sr-only">
        Matched {systemName} code {code} ({title}) maps to codes in{' '}
        {connections.map((c) => c.systemId).join(', ')}.
      </div>
    </div>
  )
}
