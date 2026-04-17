import { serverGetSystems, serverGetStats } from '@/lib/server-api'
import CrosswalkExplorerClient from './CrosswalkExplorerClient'

export default async function CrosswalkExplorerPage() {
  const [systems, stats] = await Promise.all([
    serverGetSystems(),
    serverGetStats(),
  ])

  return <CrosswalkExplorerClient systems={systems} stats={stats} />
}
