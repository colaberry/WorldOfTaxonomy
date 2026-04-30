import type { MetadataRoute } from 'next'

// The frontend serves /robots.txt at worldoftaxonomy.com. The backend
// has its own ROBOTS_TXT constant (in api/app.py) that is unused in
// production because the frontend route at /robots.txt resolves first.
// This file is the source-of-truth.
//
// Policy:
//   - Allow legitimate AI crawlers (GPTBot, ClaudeBot, PerplexityBot,
//     Google-Extended, CCBot) full access so they can index the wiki
//     and llms-full.txt.
//   - Apply a Crawl-delay of 2s for the catch-all so misbehaving bots
//     do not hammer the origin.
//   - Block SEO-tool scrapers (AhrefsBot, SemrushBot, MJ12bot, DotBot)
//     from /api/*. They respect robots.txt; for adversarial bots
//     Cloudflare + the per-IP rate guard are the real enforcement.
//   - Disallow indexing of pages that have no public utility:
//     auth flows, dashboards, developer signup. They are also
//     noindex'd at the page level.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [
          '/auth/',
          '/dashboard',
          '/developers/keys',
          '/developers/signup',
          '/login',
        ],
        crawlDelay: 2,
      },
      { userAgent: 'GPTBot',          allow: '/' },
      { userAgent: 'ClaudeBot',       allow: '/' },
      { userAgent: 'PerplexityBot',   allow: '/' },
      { userAgent: 'Google-Extended', allow: '/' },
      { userAgent: 'CCBot',           allow: '/' },
      { userAgent: 'AhrefsBot',       disallow: '/api/' },
      { userAgent: 'SemrushBot',      disallow: '/api/' },
      { userAgent: 'MJ12bot',         disallow: '/api/' },
      { userAgent: 'DotBot',          disallow: '/api/' },
    ],
    sitemap: 'https://worldoftaxonomy.com/sitemap.xml',
    host: 'https://worldoftaxonomy.com',
  }
}
