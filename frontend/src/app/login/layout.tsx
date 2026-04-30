import type { Metadata } from 'next'

// /login is the OAuth picker. Index would surface a sign-in widget
// in search results, which is hostile UX. robots.txt disallow handles
// crawler-side; this is the page-level noindex/nofollow.
export const metadata: Metadata = {
  robots: { index: false, follow: false },
}

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
