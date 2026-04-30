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
          <Logo variant="mark" height={32} className="inline-flex" />
          <span className="hidden sm:inline text-base">World Of Taxonomy</span>
          <span className="sm:hidden text-base">WoT</span>
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
