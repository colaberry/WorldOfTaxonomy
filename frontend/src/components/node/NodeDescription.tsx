import { ExternalLink } from 'lucide-react'

import { parseNodeDescription } from '@/lib/nodeDescription'

interface NodeDescriptionProps {
  /** The raw description prose from `classification_node.description`. */
  description: string | null | undefined
  /**
   * Per-code authority deep link (NodeResponse.source_url_for_code).
   * Rendered as "View on <authority>" when present. Null means the
   * system has no per-code page; the caller falls back to the
   * system-level source_url elsewhere in the page.
   */
  sourceUrlForCode?: string | null
  /**
   * Authority name ("U.S. Census Bureau", etc.) used to label the
   * per-code source link. Falls back to "authority source" when unknown.
   */
  authority?: string | null
}

export function NodeDescription({
  description,
  sourceUrlForCode,
  authority,
}: NodeDescriptionProps) {
  const parsed = parseNodeDescription(description)
  const hasBody =
    parsed.definition.length > 0 ||
    parsed.illustrativeExamples.length > 0 ||
    parsed.crossReferences.length > 0

  if (!hasBody && !sourceUrlForCode) return null

  const sourceLabel = authority ? `View on ${authority}` : 'View authority source'

  return (
    <section className="space-y-3">
      {parsed.definition.map((paragraph, i) => (
        <p
          key={`def-${i}`}
          className="text-sm text-muted-foreground max-w-3xl leading-relaxed"
        >
          {paragraph}
        </p>
      ))}

      {parsed.illustrativeExamples.length > 0 && (
        <div className="space-y-1.5">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Illustrative examples
          </h3>
          <ul className="list-disc pl-5 space-y-0.5 text-sm text-muted-foreground max-w-3xl">
            {parsed.illustrativeExamples.map((item, i) => (
              <li key={`ex-${i}`}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {parsed.crossReferences.length > 0 && (
        <div className="space-y-1.5">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Cross-references
          </h3>
          <ul className="list-disc pl-5 space-y-0.5 text-sm text-muted-foreground max-w-3xl">
            {parsed.crossReferences.map((item, i) => (
              <li key={`cr-${i}`}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {sourceUrlForCode && (
        <a
          href={sourceUrlForCode}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          {sourceLabel} <ExternalLink className="h-3 w-3" />
        </a>
      )}
    </section>
  )
}
