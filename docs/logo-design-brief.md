# WorldOfTaxonomy Logo Design Brief

## Brand

**Name:** World of Taxonomy (WorldOfTaxonomy)
**Abbreviation:** WoT
**Domain:** worldoftaxonomy.com
**Tagline:** The open-source Rosetta Stone for global classification systems

## What the product does

WorldOfTaxonomy is a knowledge graph that connects 1,000+ classification systems (industry codes, medical codes, trade codes, occupation codes) across 249 countries. It lets users translate any code in one system to its equivalent in another - like a Rosetta Stone for data.

The core visual metaphor: systems are nodes arranged in a ring, connected by crosswalk edges. Think of a constellation or a network diagram shaped like a globe.

## Logo concept

A **"WoT" monogram** where the **"o" doubles as a connected node/globe** with network edges radiating outward.

The "o" serves triple duty:
- The letter "o" in the word "WoT"
- A globe (representing "World")
- A central hub node with connection lines (representing the taxonomy graph and crosswalk edges)

The "W" and "T" sit on either side, with subtle connection lines tying them to the central node, making the whole monogram feel like a small network graph.

```
Rough concept sketch:

   W · T
    \|/
   --o--
    /|\

The "o" is a circle (globe/node).
Lines radiate from it to nearby nodes and to the W and T.
```

## Requirements

### Variants needed

| Variant | Use case | Size |
|---------|----------|------|
| **Favicon** | Browser tab, bookmarks | 16x16, 32x32, 48x48 px |
| **App icon** | PWA, mobile home screen | 192x192, 512x512 px |
| **Header logo** | Website nav bar, inline with "World Of Taxonomy" text | ~20-28px height |
| **Full lockup** | README, marketing, social cards | Monogram + "WorldOfTaxonomy" wordmark side by side |
| **Social avatar** | GitHub org, Twitter/X, LinkedIn | Square, 400x400 px |

### Favicon / small size

At 16x16 the full "WoT" monogram won't be legible. The favicon should be just the **"o" node with 3-4 radiating connection lines** - a simplified graph hub. It should be instantly recognizable as "that connected node" even at tiny sizes.

### Color

| Context | Requirement |
|---------|-------------|
| **Primary** | Works on both dark (#09090B) and light (#FFFFFF) backgrounds |
| **Accent** | The app's current primary accent is a blue-violet (oklch 0.65 0.25 270). The logo can use this or propose a complementary palette. |
| **Monochrome** | Must work in pure white (for dark bg) and pure black (for light bg) |
| **Single color** | Must work as a single-color mark (no gradients required for legibility) |

### Style guidelines

- **Minimal line weight** - clean, modern, technical feel
- **Geometric** - circles, straight lines, consistent angles
- **Not corporate-heavy** - this is an open-source developer tool, not an enterprise SaaS. Think GitHub Octocat energy, not Salesforce energy.
- **No literal globe imagery** (no latitude/longitude lines, no continents) - the "world" is implied by the circular node shape, not by drawing Earth
- **Connection lines should feel like a graph/network**, not like a starburst or sunburst
- **The network nodes at the endpoints of connection lines can vary slightly in size** to suggest the diversity of classification systems (some large like NAICS, some small like JSIC)

### Technical specs

- Deliver as **SVG** (primary) + PNG exports at each size
- SVG should be clean, minimal paths, no embedded rasters
- Must render crisply at exact pixel sizes (favicon especially - pixel-hint if needed)
- No text in the favicon variant (just the node symbol)
- Wordmark font suggestion welcome, but we can also specify separately

## Inspiration / mood

- The product's **crosswalk ring visualization**: ~200 nodes arranged in a circle grouped by color, with chord-like edges connecting related systems across the ring. This is the signature visual of the product.
- **Constellation maps**: nodes (stars) connected by thin lines on a dark background
- **Network graph diagrams**: the kind you see in graph databases or knowledge graph visualizations
- **Minimal tech logos**: Linear, Vercel, Supabase, Resend - clean geometric marks that work at any size

## What to avoid

- Literal globe/Earth imagery (continents, lat/long grid lines)
- Tree diagrams (too generic for "taxonomy")
- Overly complex marks that break down at small sizes
- Gradients as a structural element (ok as optional enhancement, not required for the mark to work)
- Clip art aesthetic
- Serif fonts in the wordmark

## Deliverables

1. 2-3 concept directions for review
2. Chosen direction refined to final
3. SVG source files for all variants
4. PNG exports: favicon (16, 32, 48), app icon (192, 512), social (400x400)
5. Simple brand usage guide (minimum clear space, minimum size, color specs)

## Contact

Ram Katamaraja - ram@colaberry.com
