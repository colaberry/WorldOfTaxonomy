'use client'

import { useQuery } from '@tanstack/react-query'
import { getSystems, getStats } from '@/lib/api'

export default function DashboardPage() {
  const { data: systems } = useQuery({
    queryKey: ['systems'],
    queryFn: getSystems,
  })

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  })

  const totalNodes = systems?.reduce((sum, s) => sum + s.node_count, 0) ?? 0
  const totalEdges = stats?.reduce((sum, s) => sum + s.edge_count, 0) ?? 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-6 rounded-lg bg-card border border-border/50">
          <div className="text-xs text-muted-foreground mb-2">Total Systems</div>
          <div className="text-3xl font-semibold font-mono">{systems?.length ?? 0}</div>
        </div>
        <div className="p-6 rounded-lg bg-card border border-border/50">
          <div className="text-xs text-muted-foreground mb-2">Total Codes</div>
          <div className="text-3xl font-semibold font-mono">{totalNodes.toLocaleString()}</div>
        </div>
        <div className="p-6 rounded-lg bg-card border border-border/50">
          <div className="text-xs text-muted-foreground mb-2">Crosswalk Edges</div>
          <div className="text-3xl font-semibold font-mono">{totalEdges.toLocaleString()}</div>
        </div>
      </div>

      {systems && systems.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Systems Overview</h2>
          <div className="rounded-lg border border-border/50 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-card border-b border-border/50">
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground">System</th>
                  <th className="text-left px-4 py-3 font-medium text-muted-foreground hidden sm:table-cell">Region</th>
                  <th className="text-right px-4 py-3 font-medium text-muted-foreground">Codes</th>
                </tr>
              </thead>
              <tbody>
                {systems.map((s) => (
                  <tr key={s.id} className="border-b border-border/30 last:border-0">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: s.tint_color || '#3B82F6' }}
                        />
                        {s.name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground hidden sm:table-cell">{s.region}</td>
                    <td className="px-4 py-3 text-right font-mono">{s.node_count.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {stats && stats.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Crosswalk Matrix</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {stats.map((s, i) => (
              <div key={i} className="p-3 rounded-lg bg-card border border-border/50 flex items-center justify-between">
                <span className="text-xs font-mono">
                  {s.source_system} &harr; {s.target_system}
                </span>
                <span className="text-xs font-mono text-muted-foreground">
                  {s.edge_count.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
