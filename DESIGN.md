# Design System - WorldOfTaxanomy

## Product Context
- **What this is:** A unified global industry classification graph that federates ISIC, NAICS, NACE, ANZSIC, JSIC, and other national classification systems as equal peers, connecting each industry node to its domain-specific taxonomies (ICD codes, drug classifications, crop taxonomies, financial instrument codes, etc.)
- **Who it's for:** Researchers, data engineers, business analysts, policy makers, and AI agents exploring the structure of global economic activity
- **Space/industry:** Data infrastructure, reference/encyclopedia, knowledge graph
- **Project type:** Web app + REST API + MCP server
- **Architecture model:** Federation - each classification system is a sovereign tree connected by equivalence edges, not forced into a single hierarchy

## Aesthetic Direction
- **Direction:** Industrial/Utilitarian meets Editorial - "The Observatory"
- **Decoration level:** Intentional - subtle depth through layered surfaces, thin rule lines, grain texture. No decorative elements; the data IS the decoration
- **Mood:** Looking at a constellation map of human economic activity. Dense when you need data, spacious when you're exploring. The feel of a well-designed encyclopedia crossed with a data observatory
- **Reference sites:** NAICS.com (anti-reference - government-form feel), NAICS Pro (clean but analytics-only), Wikidata (powerful but intimidating), Synaptica Graphite (enterprise SaaS generic)

## Typography
- **Display/Hero:** Instrument Serif - warm, literary, signals 'knowledge' not 'startup'. Used for sector names, page titles, the hero. Deliberate risk: no other taxonomy tool uses serif
- **Body:** Instrument Sans - pairs perfectly with Instrument Serif, excellent legibility at small sizes. Used for descriptions, navigation labels, UI text
- **UI/Labels:** Instrument Sans (same as body, weight 500-600)
- **Data/Tables:** Geist Mono (tabular-nums) - crisp alignment for NAICS codes, ISIC codes, ICD codes, API endpoints. Essential for a code-heavy product
- **Code:** Geist Mono
- **Loading:** Google Fonts CDN for Instrument family; Geist via self-hosted or Vercel CDN
- **Scale (typographic depth - Risk 2):**
  - 2-digit sectors: Instrument Serif, 1.8rem - the hierarchy is felt through type
  - 3-digit sub-sectors: Instrument Sans 600, 1.2rem
  - 4-digit industry groups: Instrument Sans 500, 0.95rem
  - 5-digit industries: Instrument Sans 400, 0.85rem
  - 6-digit detail codes: Geist Mono, 0.8rem

## Color
- **Approach:** Restrained core + semantic sector hues + system tints
- **Background (dark):** #08090D (deep observatory ink)
- **Background (light):** #FAFAF8 (warm paper)
- **Surface (dark):** #0F1117 / **(light):** #FFFFFF
- **Elevated (dark):** #1A1D27 / **(light):** #F5F5F0
- **Primary text (dark):** #E8E6E1 / **(light):** #1A1A1A
- **Secondary text:** #A8A69E (dark) / #4A4A48 (light)
- **Muted text:** #7A7872
- **Accent (interactive):** #3B82F6 (navigation, links, focus states)
- **Semantic:** success #4ADE80, warning #F59E0B, error #EF4444, info #3B82F6
- **Dark mode:** Default. Reduced saturation on sector hues (glow at 0.3 opacity, not full saturation)

### 20 NAICS Sector Hues (wayfinding)
| Sector | Code | Color | Hex |
|--------|------|-------|-----|
| Agriculture | 11 | Green | #4ADE80 |
| Mining | 21 | Amber | #F59E0B |
| Utilities | 22 | Cyan | #06B6D4 |
| Construction | 23 | Red | #EF4444 |
| Manufacturing | 31-33 | Purple | #8B5CF6 |
| Wholesale | 42 | Pink | #EC4899 |
| Retail | 44-45 | Orange | #F97316 |
| Transportation | 48-49 | Teal | #14B8A6 |
| Information | 51 | Blue | #3B82F6 |
| Finance | 52 | Indigo | #6366F1 |
| Real Estate | 53 | Violet | #A78BFA |
| Professional | 54 | Emerald | #10B981 |
| Management | 55 | Slate | #64748B |
| Admin & Support | 56 | Stone | #78716C |
| Education | 61 | Blue | #2563EB |
| Healthcare | 62 | Teal | #0D9488 |
| Arts | 71 | Rose | #E11D48 |
| Accommodation | 72 | Amber | #D97706 |
| Other Services | 81 | Gray | #9CA3AF |
| Public Admin | 92 | Navy | #1E40AF |

### Classification System Tints (federation wayfinding)
| System | Region | Tint |
|--------|--------|------|
| ISIC | Global (UN) | Neutral - no tint, the universal baseline |
| NAICS | North America | Warm (subtle amber undertone) |
| NACE | European Union | Cool blue undertone |
| ANZSIC | Australia/NZ | Teal undertone |
| JSIC | Japan | Subtle rose undertone |
| SIC | USA/UK legacy | Muted gray undertone |
| NIC | India | Warm orange undertone |
| GB/T | China | Subtle red undertone |

## Spacing
- **Base unit:** 4px
- **Density:** Compact in tree views (scanning hundreds of nodes), comfortable in content panels (reading descriptions, exploring relationships)
- **Scale:** 2xs(2px) xs(4px) sm(8px) md(16px) lg(24px) xl(32px) 2xl(48px) 3xl(64px)

## Layout
- **Approach:** Hybrid - grid-disciplined for data/tree views, editorial for landing/overview pages
- **Primary layout:** Galaxy View (landing) → System Treemap (sector overview) → Tree-Panel Explorer (node detail)
- **Galaxy View:** Multiple classification constellations, ISIC center, regional systems as satellites, equivalence edges glowing between matching nodes
- **Treemap:** Each sector proportionally sized, colored by sector hue, clickable to drill down
- **Explorer:** 280px sidebar tree + content panel with breadcrumbs, description, domain taxonomies, MCP endpoint
- **Grid:** 12-column at desktop, 6 at tablet, 1 at mobile
- **Max content width:** 1200px
- **Border radius:** sm:4px (chips, badges), md:8px (cards, inputs, buttons), lg:12px (panels, modals), full:9999px (avatars, toggles)

## Motion
- **Approach:** Minimal-functional - speed is the feature for a reference tool
- **Easing:** enter(ease-out) exit(ease-in) move(ease-in-out)
- **Duration:** micro(80ms) short(150ms) medium(250ms) long(400ms)
- **Tree expand/collapse:** 150ms ease-out
- **Panel transitions:** 250ms ease-in-out
- **Treemap zoom:** 400ms ease-in-out (the one place animation earns its keep)
- **Galaxy view orbit:** CSS animation, subtle, continuous, 60s cycle
- **Node glow pulse (selected):** CSS animation, 2s cycle, subtle opacity shift 0.25→0.4
- **No decorative animation** - every animation serves comprehension

## Design Risks (deliberate departures from category norms)

### Risk 1: The Galaxy View (Living Map → Federation Galaxy)
The landing page shows multiple classification constellations. ISIC in the center, NAICS/NACE/ANZSIC as satellite clusters. Click a constellation to enter that system's treemap. Equivalence edges glow between matching nodes across systems. Clicking a NAICS node highlights the corresponding ISIC, NACE, and ANZSIC equivalents simultaneously.

### Risk 2: Typography as Data Visualization
Font family, size, and weight encode hierarchy depth. Sector names are large serif. Sub-sectors are medium sans-serif. Detail codes are compact monospace. The tree is scannable at a glance - no indentation needed to feel depth.

### Risk 3: Observatory Dark Canvas
Deep #08090D background. Taxonomy nodes glow with their sector color at 0.3 opacity. Active nodes pulse gently. Equivalence edges between classification systems show as faint arc lines. The product feels like a constellation map of human economic activity.

### Risk 4: MCP-First Identity
Every node shows its MCP/API endpoint inline. JSON previews on hover. A "machine view" toggle shows raw graph structure. The design language incorporates monospace accents and structured data displays. This signals: this tool is for builders, not just browsers.

## Network Views

The knowledge graph is navigable through three semantic zoom levels. Each level is a distinct view the user can enter, not just a zoom on the same canvas. The views share the observatory aesthetic (dark canvas, glowing nodes, arc edges) but differ in layout, density, and what connections are visible.

### Level 1: Galaxy View (system-to-system)
- **What you see:** Each classification system (ISIC, NAICS, NACE, ANZSIC, JSIC, SIC, NIC, GB/T) rendered as a force-directed cluster. Cluster size proportional to number of codes in the system. ISIC gravitates toward center (most connected).
- **Edges:** Glowing equivalence arcs between systems, thickness proportional to the number of crosswalk mappings between them. NAICS↔ISIC is thick (well-mapped). GB/T↔ANZSIC is thin or absent.
- **Interaction:** Hover a system cluster to see its stats (codes, sectors, region). Click to zoom into that system's Sector View. Drag to rearrange.
- **Layout:** Force-directed (d3-force or similar). Systems repel each other, equivalence edges pull them together. Stable within 2 seconds.
- **Node style:** System clusters are large circles with the system tint color. Label in Instrument Serif. Code count in Geist Mono beneath.
- **Edge style:** Curved arcs (quadratic bezier), sector-colored where possible, 0.15 opacity at rest, 0.5 on hover. Animated particle flow along edges (subtle, 1 particle/second) to show directionality of crosswalk coverage.

### Level 2: Sector View (industry-to-industry within and across systems)
- **What you see:** The 20 sectors of a chosen classification system as a force-directed graph. Each sector node is sized by economic weight (establishments, revenue, or code count). Domain taxonomy satellites orbit each sector.
- **Edges within system:** Parent-child hierarchy shown as thin gray edges (the tree structure, flattened into a graph).
- **Edges across systems:** When "cross-system" toggle is on, equivalent sectors in other systems appear as ghost nodes at the periphery, connected by equivalence arcs. E.g., viewing NAICS shows ghost NACE sectors with faint connecting arcs.
- **Taxonomy satellites:** Each sector has small orbiting nodes for its attached domain taxonomies (ICD-10, ATC, HS codes, etc.). These orbit slowly. Shared taxonomies that span multiple sectors show as edges between sector nodes - making cross-cutting relationships visible.
- **Interaction:** Click a sector to zoom into its sub-tree. Click a taxonomy satellite to see its full classification. Toggle cross-system equivalences on/off. Filter by taxonomy type.
- **Node style:** Sector nodes use their sector hue, glowing. Taxonomy satellites are smaller, dimmer, labeled in Geist Mono. Ghost nodes from other systems use that system's tint with 0.3 opacity.
- **Layout:** Force-directed with sector nodes in an approximate circle, taxonomy satellites orbiting via radial force.

### Level 3: Node View (single industry + all connections)
- **What you see:** One industry node at center (e.g., NAICS 6211 "Offices of Physicians"). Radiating outward in concentric rings:
  - **Ring 1:** Equivalent nodes in other systems (ISIC 8620, NACE 86.21, ANZSIC 8512) - connected by thick equivalence arcs
  - **Ring 2:** Domain taxonomies attached to this node (ICD-10, CPT, ATC, NPI) - connected by taxonomy-attachment edges
  - **Ring 3:** Related nodes within the same system (sibling industries, parent sector) - connected by thin hierarchy edges
  - **Ring 4 (optional):** Cross-sector nodes that share a domain taxonomy - faint edges showing, e.g., "Chemical Safety" connecting Manufacturing and Agriculture
- **Interaction:** Click any ring node to re-center the graph on it. Hover to see details panel. "Machine View" toggle (Risk 4) replaces the visual graph with a structured JSON/table view showing all connections as data.
- **Node style:** Center node large, glowing with sector color, pulsing gently. Ring 1 nodes use their respective system tints. Ring 2 taxonomy nodes are compact with Geist Mono labels. Ring 3/4 are increasingly dim.
- **Edge style:** Equivalence arcs = solid, sector-colored. Taxonomy edges = dashed, muted. Hierarchy edges = dotted, gray. Cross-sector sharing = faint gradient between two sector colors.

### Shared Network Conventions
- **Force layout engine:** d3-force (web) or equivalent. Must stabilize in <2s, support 500+ visible nodes without jank.
- **Zoom/pan:** Scroll to zoom, drag to pan. Double-click a node to re-center. Pinch-zoom on mobile.
- **Search integration:** Searching from any network view highlights matching nodes and fades non-matches to 0.1 opacity.
- **Minimap:** Small overview in bottom-right corner showing current viewport position within the full graph.
- **Performance:** Nodes beyond viewport are culled. Edges use WebGL rendering for >200 edges. Labels LOD: show all at close zoom, show only large nodes at far zoom.
- **Export:** Each view can be exported as SVG (vector) or PNG (raster) for publications/reports.
- **URL-addressable:** Each view state is encoded in the URL hash. Sharing a link opens the exact same view, zoom level, and selected node.

### Network View Motion
- **Node enter:** Fade in + scale from 0.5 to 1.0, 250ms, staggered by distance from center
- **Edge enter:** Draw along path (SVG stroke-dashoffset animation), 400ms
- **Zoom transition between levels:** 600ms ease-in-out, with crossfade between layouts
- **Force simulation:** Warm start from previous layout when drilling down, preventing jarring rearrangement
- **Selection pulse:** Selected node glows brighter, 2s cycle

## API & MCP Design Language
- Endpoints displayed in Geist Mono, method color-coded (GET=green, POST=blue, PUT=amber, DELETE=red)
- JSON responses rendered with syntax highlighting using sector colors
- MCP tool schemas shown inline on node detail pages
- Copy-to-clipboard on all endpoints and code blocks

## Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-06 | Initial design system created | Created by /design-consultation based on competitive research of NAICS.com, NAICS Pro, Wikidata, Synaptica |
| 2026-04-06 | Federation model over ISIC-root or NAICS-first | Each classification system is sovereign; forcing a single root misrepresents how they actually relate |
| 2026-04-06 | All 4 design risks adopted | Living Map, Typographic Depth, Observatory Canvas, MCP-First - maximum differentiation from category |
| 2026-04-06 | Instrument Serif for display | Deliberate departure from sans-serif-everything in data tools; signals 'knowledge' over 'dashboard' |
| 2026-04-06 | 20 sector hues + system tints | Two-layer color wayfinding: always know which system AND which sector you're in |
| 2026-04-06 | Dark mode as default | Observatory metaphor + data-dense exploration = dark-first. Light mode available via toggle |
| 2026-04-06 | Three-level network view | Galaxy (system-to-system), Sector (industry + taxonomy satellites), Node (single node + all connections). All three levels needed to show the full graph |
