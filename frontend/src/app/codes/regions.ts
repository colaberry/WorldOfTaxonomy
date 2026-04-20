export type RegionBucket =
  | 'North America'
  | 'Global'
  | 'Europe'
  | 'Asia-Pacific'
  | 'Latin America'
  | 'Middle East & Africa'
  | 'Other'

export const REGION_ORDER: readonly RegionBucket[] = [
  'North America',
  'Global',
  'Europe',
  'Asia-Pacific',
  'Latin America',
  'Middle East & Africa',
  'Other',
] as const

const NORTH_AMERICA = new Set([
  'north america',
  'united states',
  'canada',
  'mexico',
  'usa/uk',
])

const EUROPE_KEYWORDS = [
  'europe',
  'european union',
  'eu',
]

const EUROPE_COUNTRIES = new Set([
  'austria', 'belgium', 'bulgaria', 'croatia', 'cyprus', 'czech republic',
  'denmark', 'estonia', 'finland', 'france', 'germany', 'greece', 'hungary',
  'iceland', 'ireland', 'italy', 'latvia', 'lithuania', 'luxembourg', 'malta',
  'netherlands', 'norway', 'poland', 'portugal', 'romania', 'slovakia',
  'slovenia', 'spain', 'sweden', 'switzerland', 'turkey', 'united kingdom',
  'ukraine', 'serbia', 'bosnia and herzegovina', 'north macedonia',
  'montenegro', 'albania', 'kosovo', 'moldova', 'georgia', 'armenia',
  'gulf states', 'west africa',
])

const ASIA_PACIFIC = new Set([
  'asia-pacific', 'australia', 'australia/nz', 'australia / new zealand',
  'new zealand', 'japan', 'south korea', 'china', 'singapore', 'malaysia',
  'thailand', 'philippines', 'indonesia', 'vietnam', 'india', 'pakistan',
  'bangladesh', 'sri lanka', 'nepal', 'bhutan', 'myanmar', 'cambodia',
  'laos', 'mongolia', 'kazakhstan', 'uzbekistan', 'azerbaijan',
  'kyrgyzstan', 'tajikistan', 'turkmenistan', 'afghanistan', 'brunei',
  'east timor', 'maldives', 'fiji', 'papua new guinea', 'samoa', 'tonga',
  'vanuatu', 'solomon islands', 'southeast asia',
])

const LATIN_AMERICA = new Set([
  'argentina', 'bolivia', 'brazil', 'chile', 'colombia', 'costa rica',
  'cuba', 'dominican republic', 'ecuador', 'el salvador', 'guatemala',
  'haiti', 'honduras', 'jamaica', 'nicaragua', 'panama', 'paraguay',
  'peru', 'puerto rico', 'trinidad and tobago', 'uruguay', 'venezuela',
  'barbados', 'bahamas', 'guyana', 'suriname', 'belize',
  'antigua and barbuda', 'saint lucia', 'grenada',
  'saint vincent and the grenadines', 'dominica', 'saint kitts and nevis',
  'south america',
])

const MIDDLE_EAST_AFRICA = new Set([
  'algeria', 'angola', 'bahrain', 'benin', 'botswana', 'burkina faso',
  'burundi', 'cabo verde', 'cameroon', 'central african republic', 'chad',
  'comoros', 'democratic republic of the congo', 'djibouti', 'egypt',
  'equatorial guinea', 'eritrea', 'eswatini', 'ethiopia', 'gabon',
  'gambia', 'ghana', 'guinea', 'guinea-bissau', 'iran', 'iraq',
  'israel', 'ivory coast', 'jordan', 'kenya', 'kuwait', 'lebanon',
  'lesotho', 'liberia', 'libya', 'madagascar', 'malawi', 'mali',
  'mauritania', 'mauritius', 'morocco', 'mozambique', 'namibia', 'niger',
  'nigeria', 'oman', 'palestine', 'qatar', 'republic of the congo',
  'rwanda', 'saudi arabia', 'senegal', 'seychelles', 'sierra leone',
  'somalia', 'south africa', 'south sudan', 'sudan', 'syria', 'tanzania',
  'togo', 'tunisia', 'uganda', 'united arab emirates', 'yemen', 'zambia',
  'zimbabwe', 'africa',
])

export function classifyRegion(region: string | null): RegionBucket {
  if (!region) return 'Other'
  const r = region.toLowerCase().trim()

  if (NORTH_AMERICA.has(r)) return 'North America'
  if (r.startsWith('global') || r === 'worldwide') return 'Global'
  if (EUROPE_COUNTRIES.has(r)) return 'Europe'
  if (EUROPE_KEYWORDS.some((kw) => r.includes(kw))) return 'Europe'
  if (ASIA_PACIFIC.has(r)) return 'Asia-Pacific'
  if (LATIN_AMERICA.has(r)) return 'Latin America'
  if (MIDDLE_EAST_AFRICA.has(r)) return 'Middle East & Africa'
  return 'Other'
}
