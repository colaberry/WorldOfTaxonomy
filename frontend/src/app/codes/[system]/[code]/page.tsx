import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import {
  serverGetNode,
  serverGetChildren,
  serverGetAncestors,
  serverGetEquivalences,
  serverGetSiblings,
  serverGetSystem,
  serverGetSystems,
} from '@/lib/server-api'
import { MAJOR_SYSTEMS } from '../../constants'
import { SectorPage } from './SectorPage'

interface Props {
  params: Promise<{ system: string; code: string }>
}

export const revalidate = 3600

export async function generateStaticParams() {
  const params: Array<{ system: string; code: string }> = []
  for (const systemId of MAJOR_SYSTEMS) {
    try {
      const detail = await serverGetSystem(systemId)
      for (const root of detail.roots) {
        params.push({ system: systemId, code: encodeURIComponent(root.code) })
      }
    } catch {
      // Skip systems that fail to resolve at build time; ISR will fill
      // them on first request.
    }
  }
  return params
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { system, code } = await params
  const nodeCode = decodeURIComponent(code)
  try {
    const [node, systems] = await Promise.all([
      serverGetNode(system, nodeCode),
      serverGetSystems(),
    ])
    const sys = systems.find((s) => s.id === system)
    const systemLabel = sys?.name ?? system
    const systemFull = sys?.full_name ?? systemLabel
    const title = `${systemLabel} ${nodeCode} - ${node.title} | Definition, Subcategories, Crosswalks`
    const description = node.description?.trim()
      ? `${systemLabel} code ${nodeCode} covers "${node.title}". ${node.description.trim().slice(0, 180)}`
      : `${systemLabel} classification code ${nodeCode} - ${node.title}. See subcategories, definitions, and cross-system mappings to ISIC, NAICS, NACE, SIC, and more.`
    const canonical = `https://worldoftaxonomy.com/codes/${system}/${code}`
    return {
      title,
      description,
      openGraph: {
        title: `${systemLabel} ${nodeCode} - ${node.title}`,
        description: `${systemFull} code ${nodeCode}. Definitions, subcategories, and crosswalks to other classification systems.`,
        url: canonical,
        type: 'article',
      },
      alternates: { canonical },
      keywords: [
        `${systemLabel} ${nodeCode}`,
        `${nodeCode} ${node.title}`,
        `${systemLabel} code`,
        'classification code',
        'crosswalk',
      ],
    }
  } catch {
    return { title: 'Classification Code - World Of Taxonomy' }
  }
}

export default async function CodePage({ params }: Props) {
  const { system, code } = await params
  const nodeCode = decodeURIComponent(code)

  let node, ancestors, children, equivalences, allSystems, systemDetail, siblings
  try {
    ;[node, ancestors, equivalences, allSystems, systemDetail] = await Promise.all([
      serverGetNode(system, nodeCode),
      serverGetAncestors(system, nodeCode),
      serverGetEquivalences(system, nodeCode),
      serverGetSystems(),
      serverGetSystem(system),
    ])
    const [childrenRes, siblingsRes] = await Promise.all([
      node.is_leaf
        ? Promise.resolve([])
        : serverGetChildren(system, nodeCode).catch(() => []),
      node.parent_code
        ? serverGetSiblings(system, nodeCode).catch(() => [])
        : Promise.resolve([]),
    ])
    children = childrenRes
    siblings = siblingsRes
  } catch {
    notFound()
  }

  const sys = allSystems.find((s) => s.id === system) ?? systemDetail
  if (!sys) notFound()

  return (
    <SectorPage
      system={sys}
      allSystems={allSystems}
      node={node}
      ancestors={ancestors}
      children={children ?? []}
      siblings={siblings ?? []}
      equivalences={equivalences}
    />
  )
}
