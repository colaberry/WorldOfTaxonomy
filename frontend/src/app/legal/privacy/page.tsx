import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Privacy - WorldOfTaxonomy',
  description: 'What data WorldOfTaxonomy collects, why, where it is stored, and how to delete it.',
  alternates: { canonical: 'https://worldoftaxonomy.com/legal/privacy' },
}

const LAST_UPDATED = '2026-04-28'

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 space-y-8 prose prose-sm dark:prose-invert">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Privacy Policy</h1>
        <p className="text-xs text-muted-foreground">Last updated: {LAST_UPDATED}</p>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Plain English</h2>
        <p>
          We collect the minimum data needed to operate the service. We do
          not sell your data. We do not run third-party tracking on
          authenticated pages. You can delete your account at any time and
          we will purge your account record on the same day.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">What we collect and why</h2>
        <table className="w-full text-sm border border-border/50 rounded">
          <thead className="bg-secondary/40">
            <tr>
              <th className="text-left p-2 border-b border-border/50">Data</th>
              <th className="text-left p-2 border-b border-border/50">Why</th>
              <th className="text-left p-2 border-b border-border/50">Retention</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="p-2 border-b border-border/30">Email address</td>
              <td className="p-2 border-b border-border/30">Sign-in via magic link; account ownership.</td>
              <td className="p-2 border-b border-border/30">Until you delete your account.</td>
            </tr>
            <tr>
              <td className="p-2 border-b border-border/30">API keys (hashed)</td>
              <td className="p-2 border-b border-border/30">Authenticate API and MCP requests.</td>
              <td className="p-2 border-b border-border/30">Until you revoke the key.</td>
            </tr>
            <tr>
              <td className="p-2 border-b border-border/30">IP address (request log)</td>
              <td className="p-2 border-b border-border/30">Rate limiting, abuse prevention, debugging.</td>
              <td className="p-2 border-b border-border/30">30 days.</td>
            </tr>
            <tr>
              <td className="p-2 border-b border-border/30">Request metadata (path, method, status, timing)</td>
              <td className="p-2 border-b border-border/30">Operational metrics and uptime monitoring.</td>
              <td className="p-2 border-b border-border/30">30 days raw, indefinitely aggregated.</td>
            </tr>
            <tr>
              <td className="p-2 border-b border-border/30">Sign-in cookies (`dev_session`)</td>
              <td className="p-2 border-b border-border/30">Keep you signed in across page loads.</td>
              <td className="p-2 border-b border-border/30">60 minutes; httpOnly + SameSite=Lax.</td>
            </tr>
            <tr>
              <td className="p-2">Classify lead emails</td>
              <td className="p-2">Anonymous /classify usage; product follow-ups.</td>
              <td className="p-2">Until you ask us to delete.</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">What we do NOT do</h2>
        <ul className="list-disc pl-6 space-y-1.5">
          <li>Sell your data to anyone, ever.</li>
          <li>Run third-party advertising networks.</li>
          <li>Run analytics that fingerprint your browser. We may add a privacy-respecting analytics tool (e.g. Plausible, PostHog with PII off) and we will list it here when we do.</li>
          <li>Store passwords. Sign-in is passwordless via magic link.</li>
          <li>Read your API request bodies for content. We log path + status, not payloads.</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Sub-processors</h2>
        <p>To run the service we use a small set of third parties:</p>
        <ul className="list-disc pl-6 space-y-1.5">
          <li><strong>Cloud hosting:</strong> Google Cloud Run (compute), Cloud SQL (Postgres), Secret Manager (credentials). Data resides in the region we deploy to (currently US-Central1).</li>
          <li><strong>Email delivery:</strong> Resend, for magic-link sign-in emails. Resend sees your email address and the magic-link URL.</li>
          <li><strong>Error monitoring:</strong> Sentry (when enabled), for backend exceptions. Stack traces and URL paths are captured; request bodies are not.</li>
          <li><strong>GitHub:</strong> Source-code hosting only; not part of the runtime data path.</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Your rights</h2>
        <ul className="list-disc pl-6 space-y-1.5">
          <li><strong>Access:</strong> request a copy of the data we hold about you.</li>
          <li><strong>Correction:</strong> ask us to correct anything inaccurate.</li>
          <li><strong>Deletion:</strong> ask us to delete your account and the records associated with your email. We act within seven days and confirm by email.</li>
          <li><strong>Portability:</strong> we export your account record + non-revoked API key metadata in JSON on request.</li>
          <li><strong>Objection:</strong> object to processing for any of the purposes above; we will work out a path with you or stop processing.</li>
        </ul>
        <p>
          Requests go through the{' '}
          <Link href="/developers#contact" className="underline">contact form</Link>
          ; please use the email address associated with your account so we
          can verify identity.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Children</h2>
        <p>
          The service is not directed at children under 13 (or 16 in
          jurisdictions where that is the threshold). We do not knowingly
          collect data from children. If you believe a child has signed
          up, contact us and we will delete the account.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">International transfers</h2>
        <p>
          We process data in the United States. If you are accessing the
          service from outside the U.S., your data is transferred there
          for processing. We rely on Standard Contractual Clauses or
          equivalent mechanisms with our sub-processors where required.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Changes</h2>
        <p>
          Material changes will be flagged at the top of this page and, if
          you have an account, sent to your registered email at least 14
          days before they take effect.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Contact</h2>
        <p>
          Privacy questions, requests, or complaints:{' '}
          <Link href="/developers#contact" className="underline">contact form</Link>
          . We do not publish a direct privacy email. The form delivers to
          a backend address that the data-protection team reads.
        </p>
      </section>
    </div>
  )
}
