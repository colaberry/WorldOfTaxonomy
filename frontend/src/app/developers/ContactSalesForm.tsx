'use client'

import { useState } from 'react'
import { sendEnterpriseLead } from '@/lib/enterpriseIngest'

/**
 * Contact Sales form. Posts to TWO endpoints in parallel on submit:
 *
 *   1. Our own /api/v1/contact (existing enterprise_inquiry webhook path)
 *   2. Enterprise Accelerator lead ingestion endpoint (Ali's Apr 24 spec:
 *      source=worldoftaxonomy, entry=developer_contact)
 *
 * Primary UX is driven by the /api/v1/contact response. The enterprise
 * webhook is fire-and-forget; we do not surface its errors to the user.
 *
 * Previously this form used the browser's native form POST behaviour
 * (action="/api/v1/contact"). Converting to JS-driven was required to
 * add a parallel webhook call with page_url / document.referrer / UTM
 * parameters, per Ali's spec. Visual design is unchanged.
 */
export function ContactSalesForm() {
  const [name, setName] = useState('')
  const [company, setCompany] = useState('')
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage(null)
    setStatus('idle')

    const trimmedName = name.trim()
    const trimmedEmail = email.trim()
    const trimmedMessage = message.trim()
    const trimmedCompany = company.trim()

    // Fail-fast client-side validation matching the backend rules.
    if (!trimmedName) {
      setErrorMessage('Please enter your name.')
      return
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(trimmedEmail)) {
      setErrorMessage('Please enter a valid email address.')
      return
    }
    if (trimmedMessage.length < 10) {
      setErrorMessage('Please add a bit more detail (at least 10 characters).')
      return
    }

    setSubmitting(true)

    // Fire both requests in parallel. The primary request is to our
    // /api/v1/contact handler; its success / failure drives the UX. The
    // enterprise webhook is secondary attribution and never surfaces
    // errors to the user.
    const primary = fetch('/api/v1/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: trimmedName,
        company: trimmedCompany || undefined,
        email: trimmedEmail,
        message: trimmedMessage,
      }),
    })

    void sendEnterpriseLead('developer_contact', {
      name: trimmedName,
      email: trimmedEmail,
      company: trimmedCompany || undefined,
      metadata: { message: trimmedMessage },
    })

    try {
      const resp = await primary
      if (!resp.ok) {
        setStatus('error')
        setErrorMessage('We could not send your message. Please try again.')
        return
      }
      setStatus('success')
      setName('')
      setCompany('')
      setEmail('')
      setMessage('')
    } catch {
      setStatus('error')
      setErrorMessage('Network error. Please try again in a moment.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="grid sm:grid-cols-2 gap-4" onSubmit={handleSubmit}>
      <input
        type="text"
        name="name"
        placeholder="Name"
        required
        value={name}
        onChange={(e) => setName(e.target.value)}
        disabled={submitting}
        className="px-3 py-2 rounded-lg bg-secondary border border-border/50 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
      />
      <input
        type="text"
        name="company"
        placeholder="Company"
        value={company}
        onChange={(e) => setCompany(e.target.value)}
        disabled={submitting}
        className="px-3 py-2 rounded-lg bg-secondary border border-border/50 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
      />
      <input
        type="email"
        name="email"
        placeholder="Email"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        disabled={submitting}
        className="px-3 py-2 rounded-lg bg-secondary border border-border/50 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 sm:col-span-2"
      />
      <textarea
        name="message"
        placeholder="Tell us about your use case..."
        required
        rows={3}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={submitting}
        className="px-3 py-2 rounded-lg bg-secondary border border-border/50 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 sm:col-span-2 resize-none"
      />
      <button
        type="submit"
        disabled={submitting}
        className="px-4 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors sm:col-span-2 disabled:opacity-60"
      >
        {submitting ? 'Sending...' : 'Send inquiry'}
      </button>
      {status === 'success' && (
        <p className="text-sm text-muted-foreground sm:col-span-2" role="status">
          Thanks - we will be in touch shortly.
        </p>
      )}
      {status === 'error' && errorMessage && (
        <p className="text-sm text-destructive sm:col-span-2" role="alert">
          {errorMessage}
        </p>
      )}
      {status === 'idle' && errorMessage && (
        <p className="text-sm text-destructive sm:col-span-2" role="alert">
          {errorMessage}
        </p>
      )}
    </form>
  )
}
