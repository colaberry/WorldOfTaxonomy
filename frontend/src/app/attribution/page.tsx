import type { Metadata } from 'next'
import Link from 'next/link'
import { ScrollText } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Attribution - WorldOfTaxonomy',
  description:
    'Source attribution for the 1,000+ classification systems aggregated by WorldOfTaxonomy, an open-source project by Colaberry Inc and Colaberry Research Labs.',
  openGraph: {
    title: 'Attribution - WorldOfTaxonomy',
    description:
      'Source attribution for the 1,000+ classification systems aggregated by WorldOfTaxonomy.',
    url: 'https://worldoftaxonomy.com/attribution',
    type: 'website',
  },
  alternates: { canonical: 'https://worldoftaxonomy.com/attribution' },
}

const SOURCES: { authority: string; systems: string; license: string }[] = [
  { authority: 'United Nations Statistics Division', systems: 'ISIC Rev 4, CPC v2.1, COICOP 2018, SITC Rev 4, BEC Rev 5, UN M.49, COFOG, SEEA', license: 'UN open-data terms; attribution required' },
  { authority: 'World Customs Organization (WCO)', systems: 'HS 2022', license: 'WCO terms; attribution required' },
  { authority: 'Eurostat / European Commission', systems: 'NACE Rev 2, NUTS 2021, CPV 2008, CN 2024, PRODCOM, ESCO Occupations, ESCO Skills, EU Taxonomy', license: 'European Commission Reuse Notice (CC-BY 4.0)' },
  { authority: 'World Health Organization (WHO)', systems: 'ICD-11 MMS, ICD-10-AM, ICD-10-GM, ICD-O-3, ATC WHO 2021, ICF, ICHI, WHO Essential Medicines, WHO FCTC, GBD Cause List', license: 'WHO terms; non-commercial reuse with attribution' },
  { authority: 'International Labour Organization (ILO)', systems: 'ISCO-08, ILO Core Conventions', license: 'CC-BY-NC-SA 3.0 IGO; attribution required' },
  { authority: 'UNESCO Institute for Statistics', systems: 'ISCED 2011, ISCED-F 2013, FORD Frascati 2015', license: 'UNESCO Open Access; CC-BY-SA 3.0 IGO' },
  { authority: 'US Census Bureau', systems: 'NAICS 2022 (and historical NAICS 2017, 2012), US FIPS', license: 'US Government work; public domain in US, attribution requested' },
  { authority: 'US Bureau of Labor Statistics', systems: 'SOC 2018', license: 'US Government work; public domain in US' },
  { authority: 'US Department of Labor (O*NET)', systems: 'O*NET-SOC, O*NET Knowledge Areas, Abilities, Work Activities, Work Context, Interests, Work Values, Work Styles', license: 'CC-BY 4.0 (O*NET Resource Center)' },
  { authority: 'US Department of Education / NCES', systems: 'CIP 2020', license: 'US Government work; public domain in US' },
  { authority: 'US Centers for Medicare & Medicaid Services', systems: 'ICD-10-CM, ICD-10-PCS, MS-DRG, HCPCS Level II, NUCC HCPT', license: 'US Government work; public domain in US' },
  { authority: 'US National Library of Medicine', systems: 'MeSH, RxNorm (skeleton)', license: 'NLM Terms and Conditions; attribution required' },
  { authority: 'US National Cancer Institute', systems: 'NCI Thesaurus, CTCAE', license: 'NCI public terms; attribution required' },
  { authority: 'EPO + USPTO', systems: 'Patent CPC', license: 'EPO/USPTO public-domain CPC scheme' },
  { authority: 'ISO', systems: 'ISO 3166-1, ISO 3166-2, ISO 31000, ISO/IEC 27001:2022, ISO 9001:2015, and 25+ other ISO management standards (skeleton structure only; full clause text remains under ISO copyright)', license: 'Skeleton structure published with attribution; full standard text is copyrighted by ISO' },
  { authority: 'IATA, ICAO, IMO', systems: 'IATA Aircraft Type Codes, ICAO Annexes, IMO Vessel Type Codes, IMO MARPOL, IMO SOLAS, ICAO Airport Code Regions, IMO Ship Type Classification, ISO Container Types (ISO 6346)', license: 'Industry-association public schedules; attribution required' },
  { authority: 'OECD', systems: 'OECD DAC, OECD MNE Guidelines', license: 'OECD Terms and Conditions (CC-BY-NC-SA)' },
  { authority: 'World Bank', systems: 'WB Income Groups', license: 'CC-BY 4.0' },
  { authority: 'GS1 US', systems: 'UNSPSC v24', license: 'GS1 US terms; attribution required, no resale' },
  { authority: 'MSCI / S&P Global', systems: 'GICS Bridge', license: 'Skeleton structure shown for reference; full GICS is licensed; do not redistribute the full hierarchy' },
  { authority: 'WRI / WBCSD', systems: 'GHG Protocol', license: 'CC-BY-NC-SA 3.0' },
  { authority: 'Other national statistical offices', systems: 'NIC 2008 (India), JSIC 2013 (Japan), ANZSIC 2006 (Australia/NZ), KSIC, SSIC, MSIC, TSIC, PSIC, GB/T 4754, ATECO, NAF, PKD, SBI, SNI, DB07, TOL, CIIU variants for Latin America, and 100+ others', license: 'Each country&apos;s open-data terms; attribution required to the originating statistical office' },
  { authority: 'Other standards bodies + regulators', systems: 'GRI, SASB SICS, TCFD, ISSB S1/S2, SBTi, CDP, GDPR Articles, CFR Title 49, FMCSA, NERC CIP, NIST CSF, PCI DSS, SOC 2, HIPAA, OSHA, FedRAMP, CMMC, FISMA, FFIEC, FATF, Basel III/IV, Solvency II, MiFID II, PSD2, REACH, RoHS, MDR, IVDR, EU AI Act, NIS2, DORA, CSRD, CBAM, and many others', license: 'Each authority&apos;s public terms; attribution required, no derivative claim of authorship' },
]

export default function AttributionPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-10">
      <header className="space-y-3">
        <div className="flex items-center gap-2 text-sm text-primary font-medium">
          <ScrollText className="h-4 w-4" />
          Legal
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">Attribution</h1>
        <p className="text-sm text-muted-foreground leading-relaxed">
          WorldOfTaxonomy is an open-source project by{' '}
          <strong>Colaberry Inc</strong> and{' '}
          <strong>Colaberry Research Labs</strong>, released under the MIT License at{' '}
          <a
            href="https://github.com/colaberry/WorldOfTaxonomy"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            github.com/colaberry/WorldOfTaxonomy
          </a>
          . The aggregated knowledge graph builds on data published by the authorities below. Each system is the
          intellectual product of its issuing authority and is used here under the terms of that authority&apos;s
          open-data license. We do not claim authorship of any underlying classification.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Source authorities</h2>
        <div className="overflow-x-auto rounded-lg border border-border/40">
          <table className="w-full text-sm">
            <thead className="text-xs uppercase tracking-wider text-muted-foreground border-b border-border/50 bg-card/40">
              <tr>
                <th className="text-left py-2 px-3">Authority</th>
                <th className="text-left py-2 px-3">Systems</th>
                <th className="text-left py-2 px-3">License / terms</th>
              </tr>
            </thead>
            <tbody className="text-muted-foreground">
              {SOURCES.map((s, i) => (
                <tr key={i} className="border-b border-border/30 last:border-b-0 align-top">
                  <td className="py-2 px-3 font-medium text-foreground">{s.authority}</td>
                  <td className="py-2 px-3 leading-relaxed">{s.systems}</td>
                  <td className="py-2 px-3 leading-relaxed">{s.license}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">If we missed an attribution</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          We make a good-faith effort to credit every source correctly. If you represent an issuing authority and
          believe the credit, license, or scope shown here is incorrect or insufficient, please open an issue at{' '}
          <a
            href="https://github.com/colaberry/WorldOfTaxonomy/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            our issue tracker
          </a>{' '}
          and we will correct it within seven business days.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">Project license</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          The WorldOfTaxonomy software (this website, REST API, MCP server, ingest pipeline) is released under the
          <strong> MIT License</strong>. The aggregated <em>data</em> is provided under each underlying authority&apos;s
          terms; users are responsible for honoring those terms when redistributing or using the data downstream.
        </p>
      </section>

      <footer className="text-xs text-muted-foreground/70 pt-6 border-t border-border/40">
        See also the{' '}
        <Link href="/terms" className="text-primary hover:underline">
          Terms of Service
        </Link>{' '}
        and{' '}
        <Link href="/privacy" className="text-primary hover:underline">
          Privacy Policy
        </Link>
        .
      </footer>
    </div>
  )
}
