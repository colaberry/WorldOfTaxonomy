'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ChevronDown, Globe, KeyRound, LogIn, LogOut, Sparkles, User } from 'lucide-react'
import { ThemeToggle } from '@/components/ThemeToggle'
import { getStoredUser, clearAuth, isLoggedIn } from '@/lib/auth'
import type { StoredUser } from '@/lib/auth'

interface SessionUser {
  email: string
  name?: string
}

export function Header() {
  const pathname = usePathname()
  const router   = useRouter()
  const [user, setUser] = useState<SessionUser | null>(null)

  useEffect(() => {
    let cancelled = false

    async function detectUser() {
      // First check the magic-link session (httpOnly dev_session cookie).
      // /api/v1/developers/me returns 200 + user record when signed in,
      // 401 otherwise. Distinct from the legacy /api/v1/auth/me (which
      // uses the Authorization header / HS256 JWT path).
      try {
        const res = await fetch('/api/v1/developers/me', { credentials: 'include' })
        if (res.ok) {
          const body = await res.json()
          if (!cancelled) {
            setUser({ email: body.email, name: body.email.split('@')[0] })
          }
          return
        }
      } catch {
        // Ignore network errors; fall through to legacy detection.
      }
      // Fallback: legacy localStorage token from the old /login flow.
      // Eligible for removal once all users have migrated to magic-link.
      if (!cancelled) {
        setUser(isLoggedIn() ? (getStoredUser() as SessionUser | null) : null)
      }
    }

    detectUser()
    return () => {
      cancelled = true
    }
  }, [pathname])

  const navItems = [
    { href: '/', label: 'Galaxy', active: pathname === '/' },
    { href: '/crosswalks', label: 'Crosswalks', active: pathname === '/crosswalks' || pathname.startsWith('/crosswalks/') },
    { href: '/explore', label: 'Explore', active: pathname === '/explore' },
    { href: '/codes', label: 'Codes', active: pathname.startsWith('/codes') },
    { href: '/guide', label: 'Guide', active: pathname.startsWith('/guide') },
    { href: '/blog',  label: 'Blog',  active: pathname.startsWith('/blog') },
    { href: '/developers', label: 'Builders', active: pathname === '/developers' },
    { href: '/about', label: 'About', active: pathname === '/about' },
    { href: '/pricing', label: 'Pricing', active: pathname === '/pricing' },
  ]

  async function handleSignOut() {
    // Clear both the magic-link cookie (server-side) and any legacy
    // localStorage token. Either path could have signed the user in.
    try {
      await fetch('/api/v1/auth/sign-out', {
        method: 'POST',
        credentials: 'include',
      })
    } catch {
      // Ignore; falling through to local cleanup is still useful.
    }
    clearAuth()
    setUser(null)
    router.push('/')
  }

  return (
    <header className="border-b border-border/50 bg-card/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-2 text-foreground font-semibold tracking-tight"
        >
          <Globe className="h-5 w-5 text-primary" />
          <span className="hidden sm:inline">World Of Taxonomy</span>
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

          <Link
            href="/classify"
            className={`ml-1 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all shadow-sm ${
              pathname.startsWith('/classify')
                ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white ring-2 ring-amber-300/60 dark:ring-amber-400/40'
                : 'bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:from-amber-400 hover:to-orange-400 hover:shadow-md'
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span className="hidden md:inline">Classify My Business</span>
            <span className="md:hidden">Classify</span>
          </Link>

          {/* Auth */}
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors outline-none">
                <User className="h-3.5 w-3.5" />
                <span className="hidden sm:inline max-w-[100px] truncate text-xs">{user.name || user.email}</span>
                <ChevronDown className="h-3 w-3" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52 p-1">
                <div className="px-3 py-2 border-b border-border/50 mb-1">
                  <p className="text-xs font-medium truncate">{user.name || 'Account'}</p>
                  <p className="text-[11px] text-muted-foreground truncate">{user.email}</p>
                </div>
                <Link
                  href="/developers/keys"
                  className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50 rounded transition-colors"
                >
                  <KeyRound className="h-3.5 w-3.5" />
                  API keys
                </Link>
                <button
                  onClick={handleSignOut}
                  className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50 rounded transition-colors"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign out
                </button>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Link
              href={`/sign-in${pathname && pathname !== '/' ? `?next=${encodeURIComponent(pathname)}` : ''}`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              <LogIn className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Sign in</span>
            </Link>
          )}

          <ThemeToggle />
        </nav>
      </div>
    </header>
  )
}
