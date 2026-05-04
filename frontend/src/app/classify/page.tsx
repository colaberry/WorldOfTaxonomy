import type { Metadata } from 'next'
import { ClassifyTool } from './ClassifyTool'

export const metadata: Metadata = {
  title: 'Classify My Business - World Of Taxonomy',
  description:
    'Find NAICS, ISIC, SIC, NACE, and SOC codes for any business, product, ' +
    'or occupation. Free cross-system classification across 1,000+ taxonomy systems.',
  openGraph: {
    title: 'Classify My Business - World Of Taxonomy',
    description:
      'Find the right industry and occupation codes for your business ' +
      'across NAICS, ISIC, SIC, NACE, and SOC.',
    url: 'https://worldoftaxonomy.com/classify',
    type: 'website',
  },
  alternates: {
    canonical: 'https://worldoftaxonomy.com/classify',
  },
}

export default function ClassifyPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      <header className="space-y-3">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">
          Classify My Business
        </h1>
        <p className="text-lg text-muted-foreground">
          Describe your business, product, or occupation in plain English.
          We return the matching codes across the major industry and
          occupation classification systems.
        </p>
      </header>

      <ClassifyTool />

      <section className="pt-8 border-t border-border space-y-4">
        <h2 className="text-xl font-semibold">What you get</h2>
        <ul className="space-y-2 text-sm text-muted-foreground">
          <li>
            <span className="font-medium text-foreground">5 major systems</span> -
            NAICS (US), ISIC (UN), SIC (US), NACE (EU), SOC (US occupations).
          </li>
          <li>
            <span className="font-medium text-foreground">Top 3 matches per system</span> -
            ranked by relevance to your description.
          </li>
          <li>
            <span className="font-medium text-foreground">Cross-system context</span> -
            see how codes map across NAICS, ISIC, SIC, NACE in one view.
          </li>
          <li>
            <span className="font-medium text-foreground">Full result set?</span> -
            all 1,000 systems and crosswalk edges are available on the
            paid API (see <a href="/pricing" className="text-primary underline">pricing</a>).
          </li>
        </ul>
      </section>
    </div>
  )
}
