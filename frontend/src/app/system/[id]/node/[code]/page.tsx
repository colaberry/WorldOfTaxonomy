import type { Metadata } from 'next'
import {
  serverGetNode,
  serverGetAncestors,
  serverGetChildren,
  serverGetEquivalences,
  serverGetSystems,
} from '@/lib/server-api'
import { NodeDetail } from './NodeDetail'

interface Props {
  params: Promise<{ id: string; code: string }>
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id, code } = await params
  const nodeCode = decodeURIComponent(code)
  try {
    const [node, systems] = await Promise.all([
      serverGetNode(id, nodeCode),
      serverGetSystems(),
    ])
    const systemName = systems.find((s) => s.id === id)?.name ?? id
    return {
      title: `${nodeCode} - ${node.title} - ${systemName} - World Of Taxonomy`,
      description: `${systemName} code ${nodeCode}: ${node.title}. Level ${node.level}${node.description ? `. ${node.description}` : ''}. Browse hierarchy and cross-system equivalences.`,
      openGraph: {
        title: `${systemName} ${nodeCode} - ${node.title}`,
        description: node.description ?? `Classification code ${nodeCode} in ${systemName}`,
        url: `https://worldoftaxonomy.com/system/${id}/node/${code}`,
        type: 'website',
      },
      alternates: {
        canonical: `https://worldoftaxonomy.com/system/${id}/node/${code}`,
      },
    }
  } catch {
    return { title: 'Node - World Of Taxonomy' }
  }
}

export default async function NodePage({ params }: Props) {
  const { id, code } = await params
  const nodeCode = decodeURIComponent(code)

  let node = null
  let ancestors = null
  let children = null
  let equivalences = null
  let systems = null

  try {
    ;[node, ancestors, systems] = await Promise.all([
      serverGetNode(id, nodeCode),
      serverGetAncestors(id, nodeCode),
      serverGetSystems(),
    ])
    // Fetch children and equivalences after we know the node exists
    if (node) {
      const fetches: Promise<unknown>[] = [
        serverGetEquivalences(id, nodeCode).then((r) => { equivalences = r }),
      ]
      if (!node.is_leaf) {
        fetches.push(serverGetChildren(id, nodeCode).then((r) => { children = r }))
      }
      await Promise.all(fetches)
    }
  } catch {
    // Server fetch failed - client component will fetch from browser
  }

  return (
    <NodeDetail
      id={id}
      code={code}
      initialNode={node}
      initialAncestors={ancestors}
      initialChildren={children}
      initialEquivalences={equivalences}
      initialSystems={systems}
    />
  )
}
