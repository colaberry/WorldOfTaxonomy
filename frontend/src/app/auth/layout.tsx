import type { Metadata } from 'next'

// /auth/* pages are auth-flow stops (magic-link callback, OAuth
// callback). They have no public utility and should never appear in
// search results. robots.txt disallow handles crawler-side; this
// metadata sets the page-level noindex/nofollow as a belt-and-suspenders.
export const metadata: Metadata = {
  robots: { index: false, follow: false },
}

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
