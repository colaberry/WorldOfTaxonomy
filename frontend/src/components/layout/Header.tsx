'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { getSystems } from '@/lib/api'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
            <DropdownMenuContent align="end" className="w-56">
              {systems?.slice().sort((a, b) => b.node_count - a.node_count).map((system) => (
                <DropdownMenuItem
                  key={system.id}
                  className="cursor-pointer"
                  onSelect={() => {
                    router.push(`/system/${system.id}`)
                  }}
                >
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: system.tint_color || '#3B82F6' }}
                  />
                  <span className="truncate">{system.name}</span>
                  <span className="ml-auto text-xs text-muted-foreground font-mono">
                    {system.node_count.toLocaleString()}
                  </span>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          <Link
            href="/dashboard"
            className="px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground rounded-md transition-colors hidden sm:block"
          >
            Dashboard
          </Link>

          <ThemeToggle />
        </nav>
      </div>
    </header>
  )
}
