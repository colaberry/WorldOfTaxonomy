'use client'

// Magic-link callback. Reads ?t=... from the URL, hands it to the
// backend which consumes the single-use token and sets the
// dev_session cookie. On success we redirect into /developers/keys.

import { useEffect, useState } from 'react'

export default function AuthMagicPage() {
  const [status, setStatus] = useState<'verifying' | 'error'>('verifying')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('t')
    const next = params.get('next')
    if (!token) {
      setStatus('error')
      setErrorMessage('Missing token. Request a new sign-in link.')
      return
    }

    const callbackUrl = new URL('/api/v1/auth/magic-callback', window.location.origin)
    callbackUrl.searchParams.set('t', token)
    if (next) callbackUrl.searchParams.set('next', next)

    fetch(callbackUrl.toString(), {
      method: 'GET',
      credentials: 'include',
    })
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}))
          throw new Error(body.detail ?? `Sign-in failed (${res.status})`)
        }
        const body = await res.json().catch(() => ({}))
        const target = body.redirect ?? '/'
        window.location.replace(target)
      })
      .catch((err: Error) => {
        setStatus('error')
        setErrorMessage(err.message)
      })
  }, [])

  return (
    <div className="max-w-xl mx-auto px-4 py-16 space-y-4">
      {status === 'verifying' && (
        <>
          <h1 className="text-3xl font-semibold">Signing you in...</h1>
          <p className="text-muted-foreground">One moment.</p>
        </>
      )}
      {status === 'error' && (
        <>
          <h1 className="text-3xl font-semibold">Sign-in link is invalid</h1>
          <p className="text-muted-foreground">
            {errorMessage} Links expire after 15 minutes and only work once.{' '}
            <a href="/sign-in" className="underline">
              Request a new link
            </a>
            .
          </p>
        </>
      )}
    </div>
  )
}
