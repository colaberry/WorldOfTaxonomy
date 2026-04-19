# Classify Synonyms - Modern Business Terms to Official Classification Vocabulary

Modern business descriptions use words that rarely appear verbatim in official
classification titles. A "telemedicine platform" is filed under NAICS 621111
"Offices of Physicians," not under anything containing the word "telemedicine."
A "fintech" is filed under 522 "Credit Intermediation" or 523 "Securities."

This page is the curated bridge between the two vocabularies. It powers the
classify engine's synonym-expansion fallback: when a user's query contains a
modern term like "telemedicine," the classifier silently also searches for
"physicians," "ambulatory health," and other official synonyms.

## How it works

Each entry maps one colloquial/modern term to the set of official classification
keywords that typically cover it. The classify engine applies the expansion
before running its OR-fallback PostgreSQL full-text query, so these synonyms
raise recall without touching precision on queries that already resolve.

This is curated content, not an exhaustive thesaurus. Add a new entry only when:

1. A real user query produced zero matches, AND
2. There is a clearly correct official term that the user did not type, AND
3. The mapping is stable (not a passing trend).

Log-driven curation: the classify telemetry flags zero-result queries; those
are the pool to review weekly.

## Synonym map

The authoritative data lives in the fenced JSON block below. The classify
engine parses this file at startup; the `/guide/classify-synonyms` page renders
the same content for humans; llms-full.txt ships the same content to AI
crawlers. One source of truth, three surfaces.

```json
{
  "telemedicine": ["physicians", "ambulatory", "medical", "health care"],
  "telehealth": ["physicians", "ambulatory", "medical", "health care"],
  "urgent care": ["ambulatory", "physicians", "medical", "outpatient"],
  "fintech": ["financial", "banking", "credit", "payment", "securities"],
  "neobank": ["banking", "credit", "financial"],
  "crypto exchange": ["securities", "financial", "investment"],
  "saas": ["software", "computing", "information technology"],
  "marketplace": ["retail", "wholesale", "electronic", "commerce"],
  "e-commerce": ["retail", "electronic", "mail-order", "commerce"],
  "ecommerce": ["retail", "electronic", "mail-order", "commerce"],
  "dark kitchen": ["restaurant", "food", "catering"],
  "ghost kitchen": ["restaurant", "food", "catering"],
  "cloud kitchen": ["restaurant", "food", "catering"],
  "coworking": ["real estate", "office", "leasing"],
  "ridesharing": ["taxi", "transportation", "passenger"],
  "rideshare": ["taxi", "transportation", "passenger"],
  "food delivery": ["restaurant", "courier", "delivery"],
  "last mile": ["courier", "delivery", "local"],
  "micromobility": ["transportation", "rental", "leasing"],
  "edtech": ["education", "school", "instruction", "training"],
  "online learning": ["education", "school", "instruction"],
  "mooc": ["education", "school", "instruction"],
  "proptech": ["real estate", "property", "leasing"],
  "agtech": ["agriculture", "farming", "crop"],
  "cleantech": ["renewable", "energy", "environmental"],
  "greentech": ["renewable", "energy", "environmental"],
  "biotech": ["biological", "pharmaceutical", "research"],
  "medtech": ["medical", "device", "manufacturing"],
  "healthtech": ["health", "medical", "software"],
  "insurtech": ["insurance", "software"],
  "regtech": ["compliance", "software", "regulatory"],
  "legaltech": ["legal", "software"],
  "hr tech": ["employment", "human resources", "software"],
  "adtech": ["advertising", "marketing", "software"],
  "streaming": ["broadcasting", "media", "motion picture"],
  "podcast": ["broadcasting", "audio", "media"],
  "creator economy": ["independent artists", "media", "advertising"],
  "influencer": ["advertising", "marketing", "independent artists"],
  "convenience store": ["convenience retailers", "grocery", "retail"],
  "deli": ["restaurant", "limited-service", "food"],
  "corner store": ["convenience retailers", "grocery"],
  "electric vehicle": ["motor vehicle", "automobile", "manufacturing"],
  "ev charging": ["electric power", "utilities", "charging"],
  "solar installer": ["electrical contractors", "construction", "renewable"],
  "web3": ["software", "computing", "financial"],
  "nft": ["software", "digital", "art"],
  "defi": ["financial", "securities", "software"],
  "smart home": ["electronic", "appliance", "manufacturing"],
  "iot": ["electronic", "manufacturing", "computing"],
  "drone": ["aircraft", "aerospace", "manufacturing"],
  "autonomous vehicle": ["motor vehicle", "automobile", "manufacturing"],
  "esports": ["spectator sports", "promoter", "athlete"],
  "vr": ["software", "computing", "video"],
  "ar": ["software", "computing", "video"],
  "metaverse": ["software", "computing"],
  "gig work": ["independent", "self-employed", "personal services"],
  "freelance": ["independent", "self-employed", "personal services"],
  "plant based": ["food manufacturing", "vegetable", "specialty food"],
  "vegan": ["food manufacturing", "vegetable", "specialty food"],
  "baby sitting": ["child", "child care", "day care", "childcare"],
  "babysitting": ["child", "child care", "day care", "childcare"],
  "babysitter": ["child", "child care", "day care", "childcare"],
  "daycare": ["child", "child care", "day care"],
  "childcare": ["child", "child care", "day care"],
  "nanny": ["child", "child care", "personal care", "household"],
  "au pair": ["child", "child care", "household"],
  "preschool": ["child", "child day care", "preschool", "kindergarten"],
  "dog walker": ["pet care", "personal services"],
  "dog walking": ["pet care", "personal services"],
  "pet sitter": ["pet care", "personal services"],
  "pet sitting": ["pet care", "personal services"],
  "house sitter": ["personal services", "household", "building services"],
  "house sitting": ["personal services", "household", "building services"],
  "cleaning service": ["janitorial", "cleaning", "building services"],
  "tutor": ["educational support", "instruction", "tutoring"],
  "tutoring": ["educational support", "instruction", "tutoring"],
  "personal trainer": ["fitness", "recreation", "personal services"],
  "life coach": ["personal services", "coaching", "counseling"],
  "handyman": ["repair", "maintenance", "building services"]
}
```

## Schema

- **Key**: lowercase modern/colloquial term (single or multi-word). Matched as a
  case-insensitive substring of the full user query, not just token-level.
- **Value**: array of 2-5 official classification keywords that typically cover
  the term. These keywords feed into `to_tsquery('english', ...)` as OR clauses.

## Maintenance

Add entries in alphabetical order within the JSON block. Every entry should be
justified by at least one real user query that failed without it. The classify
engine will refresh its in-process cache on next restart.
