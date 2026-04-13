'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { getSystems } from '@/lib/api'
import { groupSystemsByCategory } from '@/lib/categories'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ChevronDown, Globe } from 'lucide-react'
import { ThemeToggle } from '@/components/ThemeToggle'

export function Header() {
  const pathname = usePathname()
  const router = useRouter()
  const { data: systems } = useQuery({
    queryKey: ['systems'],
    queryFn: getSystems,
  })

  const grouped = systems ? groupSystemsByCategory(systems) : []

  const navItems = [
    { href: '/', label: 'Galaxy', active: pathname === '/' },
    { href: '/explore', label: 'Explore', active: pathname === '/explore' },
  ]

  return (
    <header className="border-b border-border/50 bg-card/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-2 text-foreground font-semibold tracking-tight"
        >
          <Globe className="h-5 w-5 text-primary" />
          <span className="hidden sm:inline">WorldOfTaxanomy</span>
          <span className="sm:hidden">WoT</span>
        </Link>

        <nav className="flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                item.active
                  ? 'text-foreground bg-secondary'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
              }`}
            >
              {item.label}
            </Link>
          ))}

          {/* Systems dropdown - grouped by category */}
          <DropdownMenu>
            <DropdownMenuTrigger
              className={`px-3 py-1.5 text-sm rounded-md transition-colors flex items-center gap-1 outline-none ${
                pathname.startsWith('/system')
                  ? 'text-foreground bg-secondary'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
              }`}
            >
              Systems
              <ChevronDown className="h-3.5 w-3.5" />
            </DropdownMenuTrigger>

            <DropdownMenuContent
              align="end"
              className="w-72 max-h-[80vh] overflow-y-auto p-0"
            >
              {/* Header row with count + link to dashboard */}
              <div className="flex items-center justify-between px-3 py-2 border-b border-border/50 sticky top-0 bg-popover z-10">
                <span className="text-xs text-muted-foreground font-medium">
                  {systems?.length ?? 82} classification systems
                </span>
                <Link
                  href="/dashboard"
                  className="text-xs text-primary hover:underline"
                  onClick={(e) => e.stopPropagation()}
                >
                  View all
                </Link>
              </div>

              {grouped.map(({ category: cat, systems: catSystems }) => (
                <div key={cat.id}>
                  {/* Category heading */}
                  <div
                    className="px-3 py-1.5 flex items-center gap-2 sticky top-[37px] bg-popover z-[5] border-b border-border/20"
                  >
                    <span
                      className="w-2 h-2 rounded-sm shrink-0"
                      style={{ backgroundColor: cat.accent }}
                    />
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      {cat.label}
                    </span>
                    <span className="text-[10px] text-muted-foreground/60 ml-auto">
                      {catSystems.length}
                    </span>
                  </div>

                  {/* Systems in this category */}
                  {catSystems
                    .slice()
                    .sort((a, b) => b.node_count - a.node_count)
                    .map((system) => (
                      <button
                        key={system.id}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-secondary/50 transition-colors text-left"
                        onClick={() => router.push(`/system/${system.id}`)}
                      >
                        <span
                          className="w-1.5 h-1.5 rounded-full shrink-0"
                          style={{ backgroundColor: system.tint_color || cat.accent }}
                        />
                        <span className="truncate flex-1">{system.name}</span>
                        <span className="text-[10px] font-mono text-muted-foreground shrink-0">
                          {system.node_count >= 1000
                            ? `${(system.node_count / 1000).toFixed(0)}k`
                            : system.node_count}
                        </span>
                      </button>
                    ))}
                </div>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <Link
            href="/dashboard"
            className={`px-3 py-1.5 text-sm rounded-md transition-colors hidden sm:block ${
              pathname === '/dashboard'
                ? 'text-foreground bg-secondary'
                : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
            }`}
          >
            Dashboard
          </Link>

          <ThemeToggle />
        </nav>
      </div>
    </header>
  )
}
