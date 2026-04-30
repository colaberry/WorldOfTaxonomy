## System Architecture and Data Flows

> **TL;DR:** Three consumer interfaces (web app, REST API, MCP server) backed by PostgreSQL and a wiki knowledge layer. Data flows from 1,000 official sources through an ingestion pipeline into three core tables. Wiki content serves four channels from one source of truth.

---

## System architecture overview

The platform serves three consumer interfaces - a web application, a REST API, and an MCP server - all backed by a shared PostgreSQL database and wiki knowledge layer.

```mermaid
graph TB
  subgraph Data["Data Layer"]
    PG[(PostgreSQL)]
    WIKI["wiki/*.md files"]
  end
  subgraph Backend["Python Backend"]
    INGEST["Ingesters - 1,000 systems"]
    API["FastAPI REST API - /api/v1/*"]
    MCP["MCP Server - stdio transport"]
    WIKILOADER["Wiki Loader - wiki.py"]
  end
  subgraph Frontend["Next.js Frontend"]
    NEXT["Next.js 16 App Router"]
    GUIDE["/guide/* pages"]
  end
  subgraph Consumers
    BROWSER["Web Browsers"]
    AIAGENT["AI Agents - Claude, GPT, etc."]
    CRAWLER["AI Crawlers - Perplexity, etc."]
    DEV["Developer Applications"]
  end
  INGEST -->|ingest| PG
  API -->|query| PG
  MCP -->|query| PG
  WIKILOADER -->|read| WIKI
  MCP -->|instructions| WIKILOADER
  NEXT -->|proxy /api/*| API
  NEXT -->|read| WIKI
  GUIDE -->|render| WIKI
  BROWSER --> NEXT
  BROWSER --> GUIDE
  AIAGENT --> MCP
  CRAWLER -->|/llms-full.txt| NEXT
  DEV --> API
```

## Four-channel wiki data flow

The wiki system follows the "write once, serve four ways" pattern. A single set of curated markdown files feeds all distribution channels.

```mermaid
graph LR
  MD["wiki/*.md - Source of Truth"] --> CH1["Channel 1: Next.js /guide/slug - SEO Web Pages"]
  MD --> CH2["Channel 2: MCP instructions - AI Agent Context"]
  MD --> CH3["Channel 3: llms-full.txt - AI Crawler Discovery"]
  MD --> CH4["Channel 4: GET /api/v1/wiki - Developer API"]
  CH1 --> GOOGLE["Search Engines"]
  CH1 --> HUMANS["Human Readers"]
  CH2 --> AGENTS["AI Agents"]
  CH3 --> CRAWLERS["AI Crawlers"]
  CH4 --> DEVS["Developer Apps"]
```

| Channel | Format | Refresh | Audience |
|---------|--------|---------|----------|
| Web pages at /guide/ | Server-rendered HTML with SEO metadata | Static generation at build time | Human readers, search engines |
| MCP instructions | Plain text injected at session start | Loaded on MCP initialize | AI agents (Claude, GPT, Gemini) |
| llms-full.txt | Concatenated plain text | Regenerated on build | AI crawlers (Perplexity, Google AI) |
| Wiki API | JSON with raw markdown | On-demand from disk | Developer applications, RAG pipelines |

## Classification data ingestion pipeline

Raw data from official sources flows through the ingestion pipeline into three database tables.

```mermaid
graph TD
  subgraph Sources["Official Sources"]
    CSV["CSV files - NAICS, ISIC"]
    XLSX["Excel files - NACE, ANZSIC"]
    HTML["HTML/PDF - SIC, NIC"]
    CURATED["Expert-Curated - Domain taxonomies"]
  end
  subgraph Pipeline["Ingestion Pipeline"]
    PARSE["Parse and Validate"]
    UPSERT["Upsert Nodes into classification_node"]
    XWALK["Build Crosswalks into equivalence"]
    PROV["Set Provenance - 4-tier audit"]
  end
  subgraph DB["Database Tables"]
    SYS["classification_system - 1,000+ systems"]
    NODE["classification_node - 1.2M+ nodes"]
    EQUIV["equivalence - 321K+ edges"]
  end
  CSV --> PARSE
  XLSX --> PARSE
  HTML --> PARSE
  CURATED --> PARSE
  PARSE --> UPSERT
  PARSE --> XWALK
  PARSE --> PROV
  UPSERT --> NODE
  XWALK --> EQUIV
  PROV --> SYS
  SYS --- NODE
  NODE --- EQUIV
```

### Ingestion steps

1. **Parse**: Read the source file (CSV, Excel, HTML, or hardcoded data). Validate code format, hierarchy, and completeness.
2. **Upsert nodes**: Insert or update rows in `classification_node` with code, title, description, level, parent_code, is_leaf, and seq_order.
3. **Build crosswalks**: Create bidirectional edges in the `equivalence` table with match_type (exact, partial, broader, narrower, related).
4. **Set provenance**: Update `classification_system` with data_provenance tier, source_url, source_date, license, and source_file_hash.

## API request flow

Every API request passes through rate limiting and authentication before reaching the query layer.

```mermaid
sequenceDiagram
  participant C as Client
  participant RL as Rate Limiter
  participant AUTH as Auth Layer
  participant R as Router
  participant Q as Query Layer
  participant DB as PostgreSQL

  C->>RL: GET /api/v1/search?q=physician
  RL->>RL: Check rate - 30/min anon, 1000/min auth
  RL->>AUTH: Forward request
  AUTH->>AUTH: Validate session cookie or API key
  AUTH->>R: Authenticated request
  R->>Q: search(conn, query, limit)
  Q->>DB: SELECT with ts_vector query
  DB-->>Q: Matching nodes
  Q-->>R: Results with system context
  R-->>C: JSON response
```

### Rate limit tiers

| Tier | Requests/Minute | Daily Limit | Best For |
|------|-----------------|-------------|----------|
| Anonymous | 30 | Unlimited | Quick exploration |
| Free | 1,000 | Unlimited | Development |
| Pro | 5,000 | 100,000 | Production apps |
| Enterprise | 50,000 | Unlimited | High-volume |

## MCP session lifecycle

When an AI agent connects to the MCP server, it receives structural knowledge about the entire knowledge graph before making any tool calls.

```mermaid
sequenceDiagram
  participant AI as AI Agent
  participant MCP as MCP Server
  participant WIKI as Wiki Loader
  participant DB as PostgreSQL

  AI->>MCP: initialize - JSON-RPC
  MCP->>WIKI: build_wiki_context()
  WIKI-->>MCP: Structural knowledge - ~15K tokens
  MCP-->>AI: serverInfo + instructions + capabilities
  Note over AI: Agent now knows all 1,000 systems and crosswalk topology
  AI->>MCP: tools/call search_classifications
  MCP->>DB: Query nodes
  DB-->>MCP: Results
  MCP-->>AI: Tool response as JSON
  AI->>MCP: resources/read taxonomy://wiki/crosswalk-map
  MCP->>WIKI: load_wiki_page - crosswalk-map
  WIKI-->>MCP: Full markdown content
  MCP-->>AI: Resource content
```

### MCP capabilities

The server advertises 26 tools and wiki resources:

- **Tools**: list_classification_systems, search_classifications, get_industry, browse_children, get_equivalences, translate_code, classify_business, get_audit_report, and 18 more
- **Resources**: taxonomy://systems, taxonomy://stats, taxonomy://wiki/{slug} for each guide page

## Database schema

The three core tables and their relationships:

```mermaid
erDiagram
  classification_system {
    string id PK
    string name
    string region
    string data_provenance
    string source_url
    string source_file_hash
  }
  classification_node {
    string system_id FK
    string code
    string title
    int level
    string parent_code
    boolean is_leaf
  }
  equivalence {
    string source_system FK
    string source_code
    string target_system FK
    string target_code
    string match_type
  }
  classification_system ||--o{ classification_node : "has"
  classification_system ||--o{ equivalence : "source"
  classification_system ||--o{ equivalence : "target"
```

- Parent-child hierarchy within a system is modeled by `classification_node.parent_code`
- Crosswalk edges are bidirectional: if A maps to B, B maps to A

## Technology stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Database | PostgreSQL (with pgbouncer) | 1.2M+ nodes, 321K+ edges |
| Backend | Python 3.9+, FastAPI, asyncpg | REST API + MCP server |
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4, shadcn/ui | Web application |
| Visualization | D3.js (Galaxy View), Cytoscape.js (Crosswalk Explorer) | Interactive graphs |
| Auth | Magic-link cookie session + API keys (`wot_` prefix) | Tiered access |
| Rate Limiting | slowapi | Per-tier enforcement |
| MCP | Custom JSON-RPC over stdio | AI agent integration |
| Content | Markdown + remark + remarkGfm | Wiki and blog rendering |

## Self-hosting

Two commands to run everything locally:

```bash
git clone https://github.com/colaberry/WorldOfTaxonomy.git
cd WorldOfTaxonomy && docker compose up
```

Web app at `localhost:3000`. API at `localhost:8000`. MCP server via `python -m world_of_taxonomy mcp`.
