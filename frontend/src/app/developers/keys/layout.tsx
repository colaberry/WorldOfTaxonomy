import type { Metadata } from 'next'

// Cookie-gated dashboard. Anonymous visitors get redirected to
// /developers/signup. Indexing this URL would only surface a redirect.
export const metadata: Metadata = {
  robots: { index: false, follow: false },
}

export default function DevelopersKeysLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
