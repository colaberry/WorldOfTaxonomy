import type { Metadata } from 'next'
import Link from 'next/link'
import { ShieldCheck } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Privacy Policy - WorldOfTaxonomy',
  description:
    'How WorldOfTaxonomy collects, uses, and protects personal data. GDPR and CCPA compliant. Published by Colaberry Inc and Colaberry Research Labs.',
  openGraph: {
    title: 'Privacy Policy - WorldOfTaxonomy',
    description:
      'How WorldOfTaxonomy collects, uses, and protects personal data. GDPR and CCPA compliant.',
    url: 'https://worldoftaxonomy.com/privacy',
    type: 'website',
  },
  alternates: { canonical: 'https://worldoftaxonomy.com/privacy' },
}

const LAST_UPDATED = '2026-04-30'

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 space-y-10">
      <header className="space-y-3">
        <div className="flex items-center gap-2 text-sm text-primary font-medium">
          <ShieldCheck className="h-4 w-4" />
          Legal
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">Privacy Policy</h1>
        <p className="text-sm text-muted-foreground">
          Last updated: {LAST_UPDATED}. This policy describes how WorldOfTaxonomy collects, uses, and
          protects your personal data, and explains your rights under GDPR, UK GDPR, and CCPA/CPRA.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">1. Data controller</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          The data controller for personal data processed via{' '}
          <code className="text-xs bg-secondary/50 px-1 py-0.5 rounded">worldoftaxonomy.com</code> is{' '}
          <strong>Colaberry Inc</strong>, on behalf of itself and{' '}
          <strong>Colaberry Research Labs</strong>. Contact:{' '}
          <Link href="/developers" className="text-primary hover:underline">
            contact form on /developers
          </Link>
          {' '}or open an issue at our GitHub repository.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">2. What we collect, why, and on what legal basis</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs uppercase tracking-wider text-muted-foreground border-b border-border/50">
              <tr>
                <th className="text-left py-2 pr-4">Category</th>
                <th className="text-left py-2 pr-4">Why</th>
                <th className="text-left py-2">Legal basis (GDPR Art. 6)</th>
              </tr>
            </thead>
            <tbody className="text-muted-foreground">
              <tr className="border-b border-border/30">
                <td className="py-2 pr-4 align-top">Email address (developer signup)</td>
                <td className="py-2 pr-4 align-top">Send the magic-link sign-in email; identify your account; let you receive operational notices.</td>
                <td className="py-2 align-top">Performance of contract (Art. 6(1)(b)) - delivering the service you requested.</td>
              </tr>
              <tr className="border-b border-border/30">
                <td className="py-2 pr-4 align-top">IP address (request-time)</td>
                <td className="py-2 pr-4 align-top">Apply per-IP rate limits, detect abuse, comply with our security obligations.</td>
                <td className="py-2 align-top">Legitimate interests (Art. 6(1)(f)) - protecting the service from abuse.</td>
              </tr>
              <tr className="border-b border-border/30">
                <td className="py-2 pr-4 align-top">Email address (contact form)</td>
                <td className="py-2 pr-4 align-top">Reply to enterprise inquiries.</td>
                <td className="py-2 align-top">Legitimate interests (Art. 6(1)(f)) - responding to a request you initiated.</td>
              </tr>
              <tr className="border-b border-border/30">
                <td className="py-2 pr-4 align-top">Email address (classify lead capture)</td>
                <td className="py-2 pr-4 align-top">Provide the demo classification result; occasionally tell you about new features. You can opt out at any time.</td>
                <td className="py-2 align-top">Performance of contract for the demo result; legitimate interests for follow-up email.</td>
              </tr>
              <tr className="border-b border-border/30">
                <td className="py-2 pr-4 align-top">API request log (method, route, status, IP, user-agent)</td>
                <td className="py-2 pr-4 align-top">Operational metrics, abuse detection, billing for paid tiers.</td>
                <td className="py-2 align-top">Legitimate interests (Art. 6(1)(f)).</td>
              </tr>
              <tr className="border-b border-border/30">
                <td className="py-2 pr-4 align-top">Auth + CSRF cookies (<code className="text-xs">dev_session</code>, <code className="text-xs">wot_csrf</code>)</td>
                <td className="py-2 pr-4 align-top">Strictly necessary for sign-in and to prevent cross-site request forgery on state-changing requests.</td>
                <td className="py-2 align-top">Performance of contract; strictly necessary cookies under ePrivacy.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm leading-relaxed text-muted-foreground">
          We do <strong>not</strong> use third-party advertising trackers, remarketing pixels, or session-replay tools.
          We do <strong>not</strong> sell or share personal data with advertisers.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">3. How long we keep data</h2>
        <ul className="list-disc list-inside text-sm leading-relaxed text-muted-foreground space-y-1">
          <li>Account email + API keys: until you delete the account or 12 months after the last sign-in, whichever comes first.</li>
          <li>Email-send audit log (hashed email + IP): 7 days, then deleted automatically by a daily cron.</li>
          <li>API request log: 30 days for operational metrics, then aggregated and the row-level data deleted.</li>
          <li>Classify lead emails: 24 months after last interaction; you can request immediate deletion.</li>
          <li>Server logs at the infrastructure layer (Cloud Run): 30 days per Google Cloud&apos;s default retention.</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">4. Where data is processed</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Application servers run on Google Cloud (Cloud Run, Cloud SQL) in the <code className="text-xs">us-central1</code> region. The website
          and edge layer are served from Cloudflare&apos;s global network. Email is delivered via Resend (US-based).
        </p>
        <p className="text-sm leading-relaxed text-muted-foreground">
          For users in the European Economic Area, the United Kingdom, or Switzerland, your data may be transferred
          to the United States. Such transfers are made under <strong>Standard Contractual Clauses</strong> (the EU
          Commission&apos;s 2021 SCCs) entered into between Colaberry and each sub-processor (Google Cloud, Cloudflare,
          Resend), supplemented where necessary by encryption in transit and at rest, organizational access controls,
          and the additional safeguards described in those processors&apos; published SCC addenda.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">5. Sub-processors</h2>
        <ul className="list-disc list-inside text-sm leading-relaxed text-muted-foreground space-y-1">
          <li><strong>Google Cloud</strong> (US) - application hosting, database, secret management.</li>
          <li><strong>Cloudflare</strong> (US/global) - CDN, DDoS protection, edge rate limiting.</li>
          <li><strong>Resend</strong> (US) - transactional email delivery (magic-link, contact-form notifications).</li>
          <li><strong>Sentry</strong> (US) - error monitoring; Authorization headers, cookies, and the <code className="text-xs">dev_session</code> cookie value are scrubbed before events leave our servers.</li>
        </ul>
        <p className="text-sm leading-relaxed text-muted-foreground">
          We will update this list when sub-processors change. Material changes are announced on the website and by
          email to active developers.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">6. Your rights</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Under GDPR, UK GDPR, and CCPA/CPRA you have the following rights with respect to your personal data:
        </p>
        <ul className="list-disc list-inside text-sm leading-relaxed text-muted-foreground space-y-1">
          <li><strong>Access</strong> - request a copy of the data we hold about you.</li>
          <li><strong>Rectification</strong> - request correction of inaccurate data.</li>
          <li><strong>Erasure (&ldquo;right to be forgotten&rdquo;)</strong> - request deletion of your account and associated data.</li>
          <li><strong>Restriction</strong> - request that we stop processing while a dispute is resolved.</li>
          <li><strong>Portability</strong> - request a machine-readable copy of the data you provided.</li>
          <li><strong>Objection</strong> - object to processing based on legitimate interests.</li>
          <li><strong>Withdraw consent</strong> - where processing is based on consent (none today, but reserved for future features).</li>
          <li><strong>Lodge a complaint</strong> with a supervisory authority (in the EU, your local data-protection authority; in the UK, the ICO).</li>
        </ul>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Most rights can be exercised directly: revoke API keys and delete your account from the developer dashboard.
          For requests we can&apos;t handle in-product, use the contact form. We respond within 30 days.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">7. CCPA / CPRA notice (California residents)</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          We do not sell or share personal information as those terms are defined under the CCPA/CPRA. California
          residents have the rights described above and may also designate an authorized agent to exercise them.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">8. Children</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          The Service is not directed to children under 16. We do not knowingly collect data from children. If you
          believe we have, contact us and we will delete it.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">9. Cookies</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          We use only strictly necessary cookies: <code className="text-xs">dev_session</code> (authentication, httpOnly,
          SameSite=Lax, ~60 minutes) and <code className="text-xs">wot_csrf</code> (CSRF double-submit token, same lifetime).
          Strictly necessary cookies do not require consent under ePrivacy. We do not use analytics, advertising, or
          tracking cookies. If we add any non-essential cookies in the future, we will deploy a consent banner first.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">10. Security</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Passwords are not stored; sign-in is by single-use magic link. API keys are stored as bcrypt hashes; the raw
          key is shown to you exactly once. All traffic is served over HTTPS with HSTS. We run automated dependency
          scanning, secret scanning, and security headers (CSP, X-Frame-Options, X-Content-Type-Options) on every
          deploy. We will notify affected users without undue delay (and within 72 hours where GDPR applies) of any
          personal-data breach.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">11. Changes to this policy</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          We may update this policy. Material changes are announced on the website and by email to active developers
          at least 30 days before they take effect.
        </p>
      </section>

      <footer className="text-xs text-muted-foreground/70 pt-6 border-t border-border/40">
        WorldOfTaxonomy is an open-source project by Colaberry Inc and Colaberry Research Labs. See the{' '}
        <Link href="/terms" className="text-primary hover:underline">
          Terms of Service
        </Link>{' '}
        and{' '}
        <Link href="/attribution" className="text-primary hover:underline">
          Attribution page
        </Link>
        .
      </footer>
    </div>
  )
}
