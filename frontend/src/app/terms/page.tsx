import type { Metadata } from 'next'
import Link from 'next/link'
import { FileText } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Terms of Service - WorldOfTaxonomy',
  description:
    'Terms governing use of WorldOfTaxonomy, an open-source classification knowledge graph published by Colaberry Inc and Colaberry Research Labs.',
  openGraph: {
    title: 'Terms of Service - WorldOfTaxonomy',
    description:
      'Terms governing use of WorldOfTaxonomy, an open-source classification knowledge graph.',
    url: 'https://worldoftaxonomy.com/terms',
    type: 'website',
  },
  alternates: { canonical: 'https://worldoftaxonomy.com/terms' },
}

const LAST_UPDATED = '2026-04-30'

export default function TermsPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 space-y-10">
      <header className="space-y-3">
        <div className="flex items-center gap-2 text-sm text-primary font-medium">
          <FileText className="h-4 w-4" />
          Legal
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">Terms of Service</h1>
        <p className="text-sm text-muted-foreground">
          Last updated: {LAST_UPDATED}. Please read these Terms before using WorldOfTaxonomy.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">1. Who we are</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          WorldOfTaxonomy (&ldquo;we&rdquo;, &ldquo;us&rdquo;, &ldquo;the Service&rdquo;) is an open-source
          classification knowledge graph published by{' '}
          <strong>Colaberry Inc</strong> and{' '}
          <strong>Colaberry Research Labs</strong> (collectively, &ldquo;Colaberry&rdquo;). The source code
          is available under the MIT License at{' '}
          <a
            href="https://github.com/colaberry/WorldOfTaxonomy"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            github.com/colaberry/WorldOfTaxonomy
          </a>
          .
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">2. The Service</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          We provide a website, REST API, and Model Context Protocol (MCP) server that expose a unified
          knowledge graph of 1,000+ classification systems. The Service is offered as-is for informational
          purposes. The website and free API tier are open to the public; higher-volume API access requires
          a developer account and may be subject to paid plans in the future.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">3. Accounts</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          To obtain an API key you must register with a valid email address. We send a one-time magic link
          to that address; possession of the link is the only credential. You are responsible for keeping
          your magic links and API keys confidential. You must not share an API key with parties outside
          your organization.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">4. Acceptable use</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">You agree not to:</p>
        <ul className="list-disc list-inside text-sm leading-relaxed text-muted-foreground space-y-1">
          <li>attempt to bypass rate limits, abuse-protection mechanisms, or authentication;</li>
          <li>use the Service to harm, harass, or impersonate any person or entity;</li>
          <li>scrape the Service&apos;s public web pages at a rate that materially affects availability for
            other users (the source data is also available via the API and as bulk downloads in the open-source
            repository);</li>
          <li>misrepresent the source of the data or the affiliation of Colaberry with any third party;</li>
          <li>upload or transmit any content that is unlawful, infringing, or misleading.</li>
        </ul>
        <p className="text-sm leading-relaxed text-muted-foreground">
          We reserve the right to revoke any API key, suspend any account, or block any IP that violates
          these Terms or threatens the availability of the Service. We try to give notice before doing so
          but may act immediately when necessary.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">5. Open-source license vs. service Terms</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          The source code is released under the <strong>MIT License</strong>. Anyone may fork, modify,
          and self-host. These Terms govern only your use of the hosted Service operated by Colaberry at{' '}
          <code className="text-xs bg-secondary/50 px-1 py-0.5 rounded">worldoftaxonomy.com</code> and its
          subdomains. Your rights under the MIT License are independent of these Terms.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">6. Source-data attribution</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          The classification systems aggregated by WorldOfTaxonomy are produced by national governments,
          intergovernmental bodies, and standards organizations (Census Bureau, UN, WHO, ILO, WCO, ISO, and
          others). They retain their original licenses, which we honor. See the{' '}
          <Link href="/attribution" className="text-primary hover:underline">
            Attribution page
          </Link>{' '}
          for the full list and licensing terms.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">7. Data accuracy and disclaimer</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          We aggregate data from authoritative sources but do not guarantee accuracy or completeness. For
          any decision with legal, regulatory, financial, clinical, or safety consequences,{' '}
          <strong>consult the official source</strong> of the relevant classification system. The Service
          is provided <strong>&ldquo;as is&rdquo;</strong>, without warranty of any kind, express or implied,
          including but not limited to warranties of merchantability, fitness for a particular purpose, and
          non-infringement.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">8. Limitation of liability</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          To the maximum extent permitted by law, neither Colaberry nor any of its officers, employees, or
          contributors will be liable for any indirect, incidental, special, consequential, or punitive
          damages arising out of or related to your use of the Service. Our aggregate liability under any
          claim related to the Service is limited to the greater of (a) the amount you paid us for the
          Service in the twelve months preceding the claim or (b) USD 100.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">9. Termination</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          You may stop using the Service at any time. You may delete your account and revoke all your API
          keys from the developer dashboard. We may terminate or suspend your access immediately if you
          violate these Terms or if continued service would create legal or operational risk.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">10. Changes</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          We may update these Terms. Material changes will be announced on the website and via email to
          registered developers. Continued use after the effective date constitutes acceptance.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">11. Governing law</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          These Terms are governed by the laws of the State of Texas, USA, without regard to its conflicts
          of laws principles. Any disputes will be resolved in the state or federal courts located in Travis
          County, Texas. Nothing in this clause limits any non-waivable rights you have under your local law.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">12. Contact</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          For questions about these Terms, use the contact form at{' '}
          <Link href="/developers" className="text-primary hover:underline">
            /developers
          </Link>{' '}
          or open an issue at{' '}
          <a
            href="https://github.com/colaberry/WorldOfTaxonomy/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            our GitHub issue tracker
          </a>
          .
        </p>
      </section>

      <footer className="text-xs text-muted-foreground/70 pt-6 border-t border-border/40">
        WorldOfTaxonomy is an open-source project by Colaberry Inc and Colaberry Research Labs. See the{' '}
        <Link href="/privacy" className="text-primary hover:underline">
          Privacy Policy
        </Link>{' '}
        for how we handle your data.
      </footer>
    </div>
  )
}
