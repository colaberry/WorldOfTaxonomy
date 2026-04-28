import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Terms of Service - WorldOfTaxonomy',
  description: 'Terms of service for the WorldOfTaxonomy public beta.',
  alternates: { canonical: 'https://worldoftaxonomy.com/legal/terms' },
}

const LAST_UPDATED = '2026-04-28'

export default function TermsPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 space-y-8 prose prose-sm dark:prose-invert">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Terms of Service</h1>
        <p className="text-xs text-muted-foreground">Last updated: {LAST_UPDATED}</p>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">1. Beta service</h2>
        <p>
          WorldOfTaxonomy is currently in public beta. The service, the data,
          and the API surface may change without notice. We do not guarantee
          uptime or feature stability during the beta period.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">2. Acceptable use</h2>
        <p>By using the WorldOfTaxonomy API or website you agree:</p>
        <ul className="list-disc pl-6 space-y-1.5">
          <li>Not to attempt to disrupt the service (denial-of-service, scraping at rates above your published quota, brute-forcing credentials).</li>
          <li>Not to misrepresent classification results as the authoritative source. The data is informational, not regulatory.</li>
          <li>Not to use the service to violate the law, infringe intellectual property, or harass others.</li>
          <li>To respect the rate limits associated with your account tier.</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">3. API keys and accounts</h2>
        <p>
          You are responsible for keeping your API keys confidential. Treat
          them like passwords. If a key is compromised, revoke it at{' '}
          <Link href="/developers/keys" className="underline">/developers/keys</Link>{' '}
          and generate a new one. We may suspend or revoke keys that we
          reasonably believe are compromised, abused, or shared across
          unrelated parties beyond the org they were issued to.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">4. Source data attribution</h2>
        <p>
          WorldOfTaxonomy aggregates classification systems from many
          authorities (governments, intergovernmental bodies, standards
          organizations). Each underlying system is licensed by its
          publisher and we credit the source on each system page. See the{' '}
          <Link href="/legal/attribution" className="underline">attribution page</Link>{' '}
          for the full list and link to original publications.
        </p>
        <p>
          Some sources are public domain (e.g. U.S. government works), some
          require attribution (e.g. NACE Eurostat), some prohibit
          redistribution beyond fair use (e.g. ICD-10-CM commercial
          licensing constraints). When you build something on top of
          WorldOfTaxonomy, you remain responsible for complying with the
          original publisher&apos;s license for the codes you redistribute.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">5. Open-source code license</h2>
        <p>
          The WorldOfTaxonomy software (API server, ingesters, frontend,
          MCP server) is open source under the MIT license at{' '}
          <a
            href="https://github.com/colaberry/WorldOfTaxonomy"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            github.com/colaberry/WorldOfTaxonomy
          </a>
          . The MIT license governs the code. The source-data
          attributions above govern the data.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">6. No warranty, no liability</h2>
        <p>
          The service is provided &quot;as is&quot; without warranty of any kind,
          express or implied, including merchantability or fitness for a
          particular purpose. To the maximum extent permitted by law, we
          are not liable for any indirect, incidental, special,
          consequential, or punitive damages arising from your use of the
          service. Our total liability for direct damages will not exceed
          the amount you paid us in the twelve months preceding the claim
          (which during the public beta is zero).
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">7. Privacy</h2>
        <p>
          We collect the minimum data needed to operate the service: your
          email (for sign-in), your IP address (for rate limiting and abuse
          prevention), and request metadata (path, status, timing). Full
          details on the{' '}
          <Link href="/legal/privacy" className="underline">privacy page</Link>.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">8. Changes</h2>
        <p>
          We may update these terms during the beta. We will not change
          them retroactively to your detriment without notice. The
          &quot;Last updated&quot; date at the top reflects the most recent revision.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">9. Contact</h2>
        <p>
          Questions, takedown requests, or compliance inquiries:{' '}
          <Link href="/developers#contact" className="underline">
            contact form
          </Link>
          . We do not publish a direct email address.
        </p>
      </section>
    </div>
  )
}
