import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Attribution - WorldOfTaxonomy',
  description: 'Sources and licenses for the 1,000+ classification systems in the WorldOfTaxonomy knowledge graph.',
  alternates: { canonical: 'https://worldoftaxonomy.com/legal/attribution' },
}

const LAST_UPDATED = '2026-04-28'

interface SourceGroup {
  heading: string
  blurb?: string
  sources: { name: string; authority: string; license: string; url?: string }[]
}

const GROUPS: SourceGroup[] = [
  {
    heading: 'Industry classification (US, EU, regional)',
    sources: [
      { name: 'NAICS 2022, NAICS 2017, NAICS 2012', authority: 'U.S. Census Bureau', license: 'Public domain (U.S. government work)', url: 'https://www.census.gov/naics/' },
      { name: 'SIC 1987', authority: 'U.S. OMB / OSHA', license: 'Public domain (U.S. government work)' },
      { name: 'ISIC Rev 4, ISIC Rev 3.1', authority: 'United Nations Statistics Division', license: 'UN open content; attribution required', url: 'https://unstats.un.org/unsd/classifications/' },
      { name: 'NACE Rev 2 (and EU member-state derivatives: WZ, ATECO, NAF, etc.)', authority: 'Eurostat', license: 'Reuse permitted with attribution; see Eurostat copyright notice', url: 'https://ec.europa.eu/eurostat/web/nace' },
      { name: 'ANZSIC 2006', authority: 'Australian Bureau of Statistics / Stats NZ', license: 'CC BY 4.0', url: 'https://www.abs.gov.au/' },
      { name: 'NIC 2008 (India), JSIC 2013 (Japan), GB/T 4754-2017 (China), KSIC 2017 (South Korea), and other national derivatives', authority: 'National statistical offices', license: 'Per each country\'s open-data terms; consult source page' },
      { name: 'CIIU Rev 4 derivatives (Latin America, Africa, ASEAN)', authority: 'Adapted from ISIC by national statistical offices', license: 'Per each country\'s open-data terms' },
    ],
  },
  {
    heading: 'Geographic',
    sources: [
      { name: 'ISO 3166-1, ISO 3166-2', authority: 'ISO', license: 'ISO terms; reuse permitted for attribution and reference', url: 'https://www.iso.org/iso-3166-country-codes.html' },
      { name: 'UN M.49', authority: 'United Nations Statistics Division', license: 'UN open content', url: 'https://unstats.un.org/unsd/methodology/m49/' },
      { name: 'EU NUTS 2021', authority: 'Eurostat', license: 'Reuse permitted with attribution', url: 'https://ec.europa.eu/eurostat/web/nuts' },
      { name: 'US FIPS', authority: 'U.S. NIST', license: 'Public domain (U.S. government work)' },
    ],
  },
  {
    heading: 'Trade and product',
    sources: [
      { name: 'HS 2022', authority: 'World Customs Organization', license: 'WCO copyright; data reuse permitted with attribution', url: 'https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature.aspx' },
      { name: 'CPC v2.1', authority: 'United Nations Statistics Division', license: 'UN open content', url: 'https://unstats.un.org/unsd/classifications/Econ/cpc' },
      { name: 'UNSPSC v24', authority: 'GS1 US', license: 'Free to use; no redistribution beyond intended use', url: 'https://www.unspsc.org/' },
      { name: 'CN 2024 (Combined Nomenclature)', authority: 'European Commission', license: 'Reuse permitted with attribution' },
      { name: 'HTS (US)', authority: 'U.S. International Trade Commission', license: 'Public domain' },
      { name: 'SITC Rev 4, BEC Rev 5', authority: 'United Nations Statistics Division', license: 'UN open content' },
    ],
  },
  {
    heading: 'Occupational and skills',
    sources: [
      { name: 'ISCO-08', authority: 'International Labour Organization', license: 'ILO open content', url: 'https://www.ilo.org/public/english/bureau/stat/isco/' },
      { name: 'SOC 2018', authority: 'U.S. Bureau of Labor Statistics', license: 'Public domain' },
      { name: 'O*NET-SOC, O*NET Knowledge / Abilities / Work Activities / Work Context / Interests / Work Values', authority: 'U.S. Department of Labor', license: 'CC BY 4.0', url: 'https://www.onetonline.org/' },
      { name: 'ESCO Occupations, ESCO Skills, ESCO Qualifications', authority: 'European Commission', license: 'CC BY 4.0', url: 'https://esco.ec.europa.eu/' },
      { name: 'ANZSCO 2022', authority: 'ABS / Stats NZ', license: 'CC BY 4.0' },
      { name: 'NOC 2021', authority: 'Statistics Canada / ESDC', license: 'Statistics Canada Open Licence' },
      { name: 'UK SOC 2020', authority: 'UK Office for National Statistics', license: 'Open Government Licence v3.0' },
      { name: 'KldB 2010', authority: 'German Federal Employment Agency', license: 'Reuse permitted with attribution' },
      { name: 'ROME v4', authority: 'France Travail', license: 'Etalab Open License' },
    ],
  },
  {
    heading: 'Education',
    sources: [
      { name: 'ISCED 2011, ISCED-F 2013', authority: 'UNESCO Institute for Statistics', license: 'UNESCO open content', url: 'https://uis.unesco.org/en/topic/international-standard-classification-education-isced' },
      { name: 'CIP 2020', authority: 'U.S. NCES', license: 'Public domain' },
      { name: 'EQF Levels (EU)', authority: 'European Commission', license: 'CC BY 4.0' },
      { name: 'AQF (Australia)', authority: 'AQF Council', license: 'CC BY 4.0' },
      { name: 'NQF (UK)', authority: 'Ofqual', license: 'Open Government Licence v3.0' },
      { name: 'Bloom\'s Taxonomy', authority: 'Public domain (foundational educational framework)', license: 'Public domain' },
    ],
  },
  {
    heading: 'Health and clinical',
    sources: [
      { name: 'ICD-11 MMS, ICD-O-3, ICF', authority: 'World Health Organization', license: 'CC BY-ND 3.0 IGO', url: 'https://icd.who.int/' },
      { name: 'ICD-10-CM', authority: 'U.S. CDC / NCHS', license: 'Public domain (US government); some derivatives have separate licensing' },
      { name: 'ICD-10-PCS', authority: 'U.S. CMS', license: 'Public domain' },
      { name: 'ICD-10-GM, ICD-10-CA, ICD-10-AM', authority: 'National derivatives', license: 'Per each country\'s licensing terms' },
      { name: 'LOINC', authority: 'Regenstrief Institute', license: 'LOINC License (free; attribution required)', url: 'https://loinc.org/' },
      { name: 'ATC WHO 2021', authority: 'WHO Collaborating Centre for Drug Statistics Methodology', license: 'Free for non-commercial; commercial use requires license', url: 'https://www.whocc.no/atc_ddd_index/' },
      { name: 'MeSH', authority: 'U.S. National Library of Medicine', license: 'Public domain (US government)' },
      { name: 'NCI Thesaurus', authority: 'U.S. National Cancer Institute', license: 'Public domain' },
      { name: 'NDC', authority: 'U.S. FDA', license: 'Public domain' },
      { name: 'CTCAE', authority: 'U.S. NIH/NCI', license: 'Public domain' },
      { name: 'WHO Essential Medicines, CDC Vaccine Schedule, GBD Cause List', authority: 'WHO / CDC / IHME', license: 'Per each publisher\'s open-content terms' },
      { name: 'CPT (Skeleton), DSM-5 (Skeleton), SNOMED CT (Skeleton)', authority: 'AMA / APA / SNOMED International', license: 'Trademarked. WoT carries only category-level skeletons for navigation; redistribution of the full code set requires a license from the publisher.' },
    ],
  },
  {
    heading: 'Financial, environmental, regulatory',
    sources: [
      { name: 'COFOG, SEEA, SDG 2030, COICOP 2018', authority: 'United Nations', license: 'UN open content' },
      { name: 'GICS Bridge', authority: 'MSCI / S&P', license: 'Trademarked; WoT carries only the public bridge mapping' },
      { name: 'GHG Protocol', authority: 'WRI / WBCSD', license: 'Reuse permitted with attribution' },
      { name: 'GRI Standards', authority: 'Global Reporting Initiative', license: 'Free to use; attribution required' },
      { name: 'TCFD, ISSB S1/S2, SBTi, CDP', authority: 'IFRS Foundation, SBTi, CDP', license: 'Per each publisher\'s open-content terms' },
      { name: 'Patent CPC (Cooperative Patent Classification)', authority: 'EPO / USPTO', license: 'Public domain' },
      { name: 'GDPR, ePrivacy, NIS2, DORA, EU AI Act, MiFID II, etc.', authority: 'European Commission / EUR-Lex', license: 'Reuse permitted (EUR-Lex), attribution required' },
      { name: 'CFR Title 49, FMCSA, OSHA 1910 / 1926, FAR, DFARS, ITAR, EAR, etc.', authority: 'U.S. federal agencies', license: 'Public domain' },
      { name: 'ISO management-system standards (9001, 14001, 27001, etc.)', authority: 'ISO', license: 'Trademarked; WoT carries only category-level skeletons for navigation' },
    ],
  },
  {
    heading: 'Domain taxonomies (curated by WorldOfTaxonomy)',
    blurb: 'The "Domain" taxonomies (system_id starts with "domain_") are plain-language on-ramps curated by the WorldOfTaxonomy team. They are MIT-licensed alongside the rest of the project source. Their content is informational and is mapped to official standards via the crosswalk graph.',
    sources: [],
  },
]

export default function AttributionPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 space-y-8 prose prose-sm dark:prose-invert">
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Source attribution</h1>
        <p className="text-xs text-muted-foreground">Last updated: {LAST_UPDATED}</p>
      </div>

      <p>
        WorldOfTaxonomy aggregates classification systems from many
        publishers. Each system retains its original publisher, authority,
        and license. Below is the catalog grouped by domain. The
        per-system license string also appears on{' '}
        <Link href="/explore" className="underline">each system&apos;s detail page</Link>.
      </p>

      <p className="text-sm text-muted-foreground border-l-2 border-amber-500/50 pl-3">
        This list is not exhaustive at the per-derivative level. The
        full machine-readable list of all 1,000+ systems with their
        license strings is available at{' '}
        <code>GET /api/v1/systems</code> and on each system&apos;s page.
      </p>

      {GROUPS.map((group) => (
        <section key={group.heading} className="space-y-3">
          <h2 className="text-lg font-semibold border-b border-border/50 pb-1">
            {group.heading}
          </h2>
          {group.blurb && (
            <p className="text-sm text-muted-foreground">{group.blurb}</p>
          )}
          {group.sources.length > 0 && (
            <ul className="space-y-3 text-sm">
              {group.sources.map((s) => (
                <li key={s.name} className="border-l-2 border-border/50 pl-3">
                  <div className="font-medium">{s.name}</div>
                  <div className="text-xs text-muted-foreground">
                    Authority: {s.authority}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    License: {s.license}
                  </div>
                  {s.url && (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs underline"
                    >
                      Visit source
                    </a>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      ))}

      <section className="space-y-3 border-t border-border/50 pt-6">
        <h2 className="text-lg font-semibold">Reporting an error or takedown</h2>
        <p>
          If you are a rights holder and believe content on
          WorldOfTaxonomy infringes your license, or if you spot a
          mis-attribution, please use the{' '}
          <Link href="/developers#contact" className="underline">contact form</Link>
          . We respond within seven days.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Software license</h2>
        <p>
          The WorldOfTaxonomy software is MIT-licensed at{' '}
          <a
            href="https://github.com/colaberry/WorldOfTaxonomy"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            github.com/colaberry/WorldOfTaxonomy
          </a>
          . The MIT license governs the code; the per-source attributions
          above govern the data.
        </p>
      </section>
    </div>
  )
}
