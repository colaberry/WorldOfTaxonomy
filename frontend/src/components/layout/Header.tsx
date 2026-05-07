'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ChevronDown, Key, LogIn, LogOut, Sparkles, User } from 'lucide-react'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Logo } from '@/components/Logo'
import { isLoggedIn, logout } from '@/lib/auth'

export function Header() {
  const pathname = usePathname()
  const router   = useRouter()
  // Cookie-based session detection. The wot_csrf cookie is the
  // JS-readable companion of dev_session (which is httponly). Presence
  // == signed in. We re-check on every navigation so the menu updates
  // after a magic-link callback or a sign-out.
  const [signedIn, setSignedIn] = useState<boolean>(false)

  useEffect(() => {
    setSignedIn(isLoggedIn())
  }, [pathname])

  // Top-level nav surfaces. Galaxy stays out front (it's the visual
  // home / marquee); Builders + Pricing are conversion-critical so
  // they remain top-level. Data-discovery surfaces collapse into an
  // "Explore" dropdown; static content collapses into "Learn". About
  // moved to the footer.
  const exploreItems = [
    { href: '/crosswalks', label: 'Crosswalks', active: pathname === '/crosswalks' || pathname.startsWith('/crosswalks/'), description: 'Translate codes across systems' },
    { href: '/explore', label: 'Search', active: pathname === '/explore', description: 'Full-text search across all 1,000 systems' },
    { href: '/codes', label: 'Codes', active: pathname.startsWith('/codes'), description: 'Browse the full code index' },
  ]
  const exploreActive = exploreItems.some((i) => i.active)

  const learnItems = [
    { href: '/guide', label: 'Guide', active: pathname.startsWith('/guide'), description: 'Concept guides and tutorials' },
    { href: '/blog', label: 'Blog', active: pathname.startsWith('/blog'), description: 'Updates and deep-dives' },
  ]
  const learnActive = learnItems.some((i) => i.active)

  const topLevelItems = [
    { href: '/', label: 'Galaxy', active: pathname === '/' },
    { href: '/developers', label: 'Builders', active: pathname === '/developers' },
    { href: '/pricing', label: 'Pricing', active: pathname === '/pricing' },
  ]

  async function handleSignOut() {
    await logout()
    setSignedIn(false)
    router.push('/')
  }

  return (
    <header className="border-b border-border/50 bg-card/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-2 text-foreground font-semibold tracking-tight"
        >
          <Logo variant="lockup" height={24} className="hidden sm:inline-flex" aria-label="World Of Taxonomy" />
          <Logo variant="mark" height={32} className="inline-flex sm:hidden" aria-label="WoT" />
        </Link>

        <nav className="flex items-center gap-1">
          {/* Galaxy - the marquee/home entry, always top-level */}
          <Link
            href="/"
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
              pathname === '/'
                ? 'text-foreground bg-secondary'
                : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
            }`}
          >
            Galaxy
          </Link>

          {/* Explore dropdown: Crosswalks, Search, Codes */}
          <DropdownMenu>
            <DropdownMenuTrigger
              className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded-md transition-colors outline-none ${
                exploreActive
                  ? 'text-foreground bg-secondary'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
              }`}
            >
              Explore
              <ChevronDown className="h-3 w-3" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-64 p-1">
              {exploreItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`w-full flex flex-col gap-0.5 px-3 py-2 rounded transition-colors ${
                    item.active
                      ? 'bg-secondary text-foreground'
                      : 'hover:bg-secondary/50 text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <span className="text-sm font-medium">{item.label}</span>
                  <span className="text-xs text-muted-foreground/80">{item.description}</span>
                </Link>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Learn dropdown: Guide, Blog */}
          <DropdownMenu>
            <DropdownMenuTrigger
              className={`flex items-center gap-1 px-3 py-1.5 text-sm rounded-md transition-colors outline-none ${
                learnActive
                  ? 'text-foreground bg-secondary'
                  : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
              }`}
            >
              Learn
              <ChevronDown className="h-3 w-3" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-64 p-1">
              {learnItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`w-full flex flex-col gap-0.5 px-3 py-2 rounded transition-colors ${
                    item.active
                      ? 'bg-secondary text-foreground'
                      : 'hover:bg-secondary/50 text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <span className="text-sm font-medium">{item.label}</span>
                  <span className="text-xs text-muted-foreground/80">{item.description}</span>
                </Link>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Remaining top-level items: Builders, Pricing */}
          {topLevelItems.slice(1).map((item) => (
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
            className={`ml-1 flex items-center gap-1.5 shrink-0 whitespace-nowrap px-3 py-1.5 rounded-full text-sm font-medium transition-all shadow-sm ${
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
          {signedIn ? (
            <DropdownMenu>
              <DropdownMenuTrigger className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors outline-none">
                <User className="h-3.5 w-3.5" />
                <span className="hidden sm:inline text-xs">Account</span>
                <ChevronDown className="h-3 w-3" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-52 p-1">
                <Link
                  href="/developers/keys"
                  className="w-full flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50 rounded transition-colors"
                >
                  <Key className="h-3.5 w-3.5" />
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
              href="/login"
              className="flex items-center gap-1.5 shrink-0 whitespace-nowrap px-3 py-1.5 rounded-md text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
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
