import type { Metadata } from 'next'

// Email-only signup form. No public utility; should not appear in
// search. The conversion path for new developers is the /developers
// landing page, not this form.
export const metadata: Metadata = {
  robots: { index: false, follow: false },
}

export default function DevelopersSignupLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
