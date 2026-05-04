import Link from 'next/link'
import type { Metadata } from 'next'
import {
  Globe, Lightbulb, Bot, Users, ArrowRight,
  Blocks, GitCompareArrows, MessageSquare,
} from 'lucide-react'
import { CrosswalkRingPreview } from '@/components/visualizations/CrosswalkRingPreview'

export const metadata: Metadata = {
  title: 'About - World Of Taxonomy',
  description:
    'The story behind World Of Taxonomy - a fascination with global standards turned into a unified classification knowledge graph for humans and AI.',
  openGraph: {
    title: 'About World Of Taxonomy',
    description:
      'A fascination with global standards turned into a unified classification knowledge graph for humans and AI.',
    url: 'https://worldoftaxonomy.com/about',
    type: 'website',
  },
  alternates: {
    canonical: 'https://worldoftaxonomy.com/about',
  },
}

export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 space-y-16">

      {/* Hero */}
      <section className="space-y-6">
        <div className="flex items-center gap-2 text-sm text-primary font-medium">
          <Globe className="h-4 w-4" />
          About this project
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight leading-tight">
          A fascination with how the world organizes itself
        </h1>
        <p className="text-lg text-muted-foreground leading-relaxed">
          World Of Taxonomy started with a simple observation: every country,
          every industry, and every international body has its own way of
          classifying the same things - jobs, products, diseases, trades,
          education, risk. And anyone working across borders has to navigate
          all of them.
        </p>
      </section>

      {/* The Problem */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5 text-amber-500" />
          <h2 className="text-xl font-semibold">The problem that sparked this</h2>
        </div>
        <div className="space-y-4 text-muted-foreground leading-relaxed">
          <p>
            If you have ever worked in global trade, you know the headache.
            Your product has an HS code for customs, an NAICS code for
            statistics, a CPC code for the UN, and a completely different
            classification in the country you are shipping to. A doctor
            writing a referral in Germany uses ICD-10-GM while their
            colleague in Australia uses ICD-10-AM. A recruiter posting the
            same role in the US, the EU, and India is dealing with SOC,
            ISCO, and NIC respectively.
          </p>
          <p>
            These are not obscure bureaucratic artifacts. These systems
            shape how governments measure economies, how hospitals get paid,
            how trade flows across borders, and how researchers compare data
            across nations. They are the invisible infrastructure of the
            global economy.
          </p>
          <p>
            Yet there was no single place to explore them side by side, see
            how they connect, or translate between them. That gap fascinated
            me.
          </p>
        </div>
      </section>

      {/* The Experiment */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Blocks className="h-5 w-5 text-blue-500" />
          <h2 className="text-xl font-semibold">An experiment in connecting standards</h2>
        </div>

        <div className="space-y-2">
          <CrosswalkRingPreview topN={250} height={560} />
          <p className="text-center text-[11px] text-muted-foreground/70">
            Each dot is a classification system. Lines are crosswalk connections between them. Click to explore.
          </p>
        </div>

        <div className="space-y-4 text-muted-foreground leading-relaxed">
          <p>
            World Of Taxonomy is an attempt to bring these systems together.
            Not to replace them - each one exists for a reason - but to
            connect them as peers in a single knowledge graph. One place
            where you can look up an NAICS code and see its equivalent in
            ISIC, NACE, ANZSIC, and a hundred other national systems. Where
            you can explore how medical codes map across ICD-10, ICD-11,
            LOINC, and SNOMED. Where occupation taxonomies from the US, EU,
            and the ILO are linked through crosswalk edges.
          </p>
          <p>
            Today it connects over 1,000 classification systems, 1.2 million
            nodes, and 320,000+ crosswalk edges - spanning industry,
            medicine, trade, education, occupations, regulations, and more.
          </p>
        </div>
      </section>

      {/* Why now - AI */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-purple-500" />
          <h2 className="text-xl font-semibold">Why this matters in the age of AI</h2>
        </div>
        <div className="space-y-4 text-muted-foreground leading-relaxed">
          <p>
            AI is fascinating. And one thing AI needs desperately is
            structured, reliable knowledge about how the real world is
            organized. When an AI agent processes a trade document, drafts
            a compliance report, or helps a researcher compare healthcare
            data across countries, it needs to navigate the same taxonomy
            maze that humans do.
          </p>
          <p>
            A global standards connection system like World Of Taxonomy can
            be genuinely useful here - not just for humans browsing a
            website, but for AI systems that need structured crosswalk data
            through APIs and MCP servers. The goal is to make these
            taxonomies machine-accessible so that both humans and AI can
            work with them fluently.
          </p>
        </div>

        {/* API + MCP callout */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          <Link
            href="/developers"
            className="flex items-center gap-3 p-4 rounded-lg bg-card border border-border/50 hover:border-primary/30 transition-colors group"
          >
            <GitCompareArrows className="h-5 w-5 text-primary shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium group-hover:text-primary transition-colors">REST API</div>
              <div className="text-xs text-muted-foreground">Search, browse, translate codes</div>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
          </Link>
          <Link
            href="/developers#mcp"
            className="flex items-center gap-3 p-4 rounded-lg bg-card border border-border/50 hover:border-primary/30 transition-colors group"
          >
            <Bot className="h-5 w-5 text-primary shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium group-hover:text-primary transition-colors">MCP Server</div>
              <div className="text-xs text-muted-foreground">Connect AI agents directly</div>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
          </Link>
        </div>
      </section>

      {/* Call to Community */}
      <section className="space-y-4">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-emerald-500" />
          <h2 className="text-xl font-semibold">This is an open experiment</h2>
        </div>
        <div className="space-y-4 text-muted-foreground leading-relaxed">
          <p>
            World Of Taxonomy is an experimental effort, open source and
            evolving. The APIs and MCP servers are being published to
            empower anyone - researchers, developers, policy analysts, AI
            builders - who works across classification boundaries.
          </p>
          <p>
            I would love for the community to use it, break it, and tell me
            what to improve. Whether you spot a wrong mapping, want a system
            added, or have ideas for how this could be more useful - your
            feedback is what makes this better.
          </p>
        </div>

        <div className="flex flex-wrap gap-3 pt-2">
          <a
            href="https://github.com/colaberry/WorldOfTaxonomy/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            <MessageSquare className="h-4 w-4" />
            Share feedback on GitHub
          </a>
          <Link
            href="/explore"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-card border border-border/50 text-sm font-medium hover:border-primary/30 transition-colors"
          >
            Start exploring
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Sign-off */}
      <section className="border-t border-border/50 pt-8">
        <p className="text-sm text-muted-foreground italic">
          Built with curiosity by{' '}
          <a
            href="https://www.linkedin.com/in/ramdhan/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-foreground not-italic font-medium hover:text-primary hover:underline transition-colors"
          >Ram Katamaraja</a>
          {' '}and the{' '}
          <a
            href="https://www.colaberry.ai"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline not-italic"
          >
            Colaberry AI
          </a>
          {' '}team.
        </p>
        <p className="text-sm leading-relaxed text-muted-foreground pt-3">
          World Of Taxonomy is an open-source project published by{' '}
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
          .
        </p>
      </section>
    </div>
  )
}
