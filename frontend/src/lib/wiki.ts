import fs from 'fs'
import path from 'path'
import { remark } from 'remark'
import remarkGfm from 'remark-gfm'
import remarkHtml from 'remark-html'

const WIKI_DIR = path.join(process.cwd(), 'src', 'content', 'wiki')

export interface WikiMeta {
  slug: string
  file: string
  title: string
  description: string
  order: number
}

let _cachedMeta: WikiMeta[] | null = null

export function getWikiMeta(): WikiMeta[] {
  if (_cachedMeta) return _cachedMeta
  const metaPath = path.join(WIKI_DIR, '_meta.json')
  const raw = fs.readFileSync(metaPath, 'utf-8')
  const data: WikiMeta[] = JSON.parse(raw)
  _cachedMeta = data.sort((a, b) => a.order - b.order)
  return _cachedMeta
}

export function getWikiContent(slug: string): string | null {
  const meta = getWikiMeta()
  const entry = meta.find((e) => e.slug === slug)
  if (!entry) return null
  const filePath = path.join(WIKI_DIR, entry.file)
  if (!fs.existsSync(filePath)) return null
  return fs.readFileSync(filePath, 'utf-8')
}

export async function renderWikiHtml(markdown: string): Promise<string> {
  const result = await remark().use(remarkGfm).use(remarkHtml, { sanitize: false }).process(markdown)
  return result.toString()
}

export function getWikiSlugs(): string[] {
  return getWikiMeta().map((e) => e.slug)
}
