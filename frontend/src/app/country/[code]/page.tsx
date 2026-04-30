import type { Metadata } from 'next'
import { CountryDetail } from './CountryDetail'
import { serverGetCountryProfile } from '@/lib/server-api'

interface Props {
  params: Promise<{ code: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { code } = await params
  const upper = code.toUpperCase()

  try {
    const profile = await serverGetCountryProfile(upper)
    const title = profile.country?.title ?? upper
    return {
      title: `${title} - Taxonomy Profile - WorldOfTaxonomy`,
      description: `${profile.classification_systems?.length ?? 0} classification systems applicable to ${title}. Browse official, regional, and recommended standards.`,
      openGraph: {
        title: `${title} - Taxonomy Profile`,
        description: `Classification systems for ${title}`,
        url: `https://worldoftaxonomy.com/country/${upper}`,
        type: 'website',
      },
      alternates: { canonical: `https://worldoftaxonomy.com/country/${upper}` },
    }
  } catch {
    return { title: `${upper} - WorldOfTaxonomy` }
  }
}

export default async function CountryPage({ params }: Props) {
  const { code } = await params
  const upper = code.toUpperCase()

  let profile = null
  try {
    profile = await serverGetCountryProfile(upper)
  } catch {
    // Backend unavailable - client component will fetch on its own
  }

  return <CountryDetail code={upper} initialProfile={profile} />
}
