'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Globe, AlertCircle } from 'lucide-react'
import { setAuth } from '@/lib/auth'

/**
 * OAuth callback page.
 *
 * The backend redirects here after successful OAuth with:
 *   ?token=<jwt>&email=<email>&name=<display name>
 *
 * We store the token + user in localStorage and redirect to the home page
 * (or wherever the user was going before signing in).
 */
export default function AuthCallbackPage() {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token  = params.get('token')
    const email  = params.get('email')
    const name   = params.get('name') ?? ''
    const err    = params.get('error')

    if (err) {
      setError('Sign-in failed. Please try again.')
      return
    }

    if (!token || !email) {
      setError('Invalid response from authentication provider.')
      return
    }

    setAuth(token, { email, name })

    // Redirect to home (or a post-login destination if we add one later)
    router.replace('/')
  }, [router])

  if (error) {
    return (
      <div className="min-h-[calc(100vh-10rem)] flex items-center justify-center px-4">
        <div className="w-full max-w-sm space-y-4 text-center">
          <div className="flex justify-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-destructive/10 border border-destructive/20">
              <AlertCircle className="h-6 w-6 text-destructive" />
            </div>
          </div>
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            onClick={() => router.push('/login')}
            className="text-sm text-primary hover:underline"
          >
            Back to sign in
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-[calc(100vh-10rem)] flex items-center justify-center px-4">
      <div className="flex flex-col items-center gap-4 text-muted-foreground">
        <Globe className="h-8 w-8 text-primary animate-pulse" />
        <p className="text-sm">Signing you in...</p>
      </div>
    </div>
  )
}
