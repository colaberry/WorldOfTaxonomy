/**
 * Parser for NAICS 2022 node descriptions.
 *
 * The Census Bureau publishes descriptions as a single free-text column
 * with implicit sections: a definition paragraph, an optional
 * "Illustrative Examples" list, and an optional "Cross-References" list.
 * Splitting these surfaces them as distinct UI blocks instead of one
 * wall of text, so a user on a NAICS node can see at a glance what the
 * code covers, what examples qualify, and which codes to look at next.
 *
 * Systems other than NAICS 2022 either carry no description or use a
 * prose format without these markers; for those, parse() returns the
 * whole string as the definition and empty lists for the rest.
 */

export interface ParsedNodeDescription {
  /** The lead paragraphs, rendered as plain text blocks. */
  definition: string[]
  /** Bullet lines from "Illustrative Examples:" section. */
  illustrativeExamples: string[]
  /** Bullet lines from "Cross-References." section. */
  crossReferences: string[]
}

const EMPTY: ParsedNodeDescription = Object.freeze({
  definition: [],
  illustrativeExamples: [],
  crossReferences: [],
}) as ParsedNodeDescription

const ILLUSTRATIVE_HEADING = /^Illustrative\s+Examples?\s*[:.]?\s*$/i
const CROSS_REF_HEADING = /^Cross[- ]?References?\s*[.:]?\s*(?:Establishments.*)?$/i

export function parseNodeDescription(
  raw: string | null | undefined
): ParsedNodeDescription {
  if (!raw) return EMPTY

  const lines = raw.replace(/\r\n/g, '\n').split('\n').map((l) => l.trim())

  const definition: string[] = []
  const illustrativeExamples: string[] = []
  const crossReferences: string[] = []

  type Section = 'definition' | 'illustrative' | 'crossref'
  let section: Section = 'definition'
  let buffer: string[] = []

  const flushBuffer = () => {
    if (buffer.length === 0) return
    const paragraph = buffer.join(' ').trim()
    if (paragraph) definition.push(paragraph)
    buffer = []
  }

  for (const line of lines) {
    if (ILLUSTRATIVE_HEADING.test(line)) {
      flushBuffer()
      section = 'illustrative'
      continue
    }
    if (CROSS_REF_HEADING.test(line)) {
      flushBuffer()
      section = 'crossref'
      continue
    }

    if (section === 'definition') {
      if (line === '') {
        flushBuffer()
      } else {
        buffer.push(line)
      }
      continue
    }

    if (line === '') continue

    const cleaned = line.replace(/^[-\u2013\u2014\s]+/, '').trim()
    if (!cleaned) continue

    if (section === 'illustrative') illustrativeExamples.push(cleaned)
    else crossReferences.push(cleaned)
  }

  flushBuffer()

  return { definition, illustrativeExamples, crossReferences }
}
