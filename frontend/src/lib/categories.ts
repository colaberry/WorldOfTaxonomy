import type { ClassificationSystem } from './types'

export interface SystemCategory {
  id: string
  label: string
  description: string
  accent: string       // border/icon color (CSS color)
  bg: string           // card background tint (CSS color, low opacity)
  systemIds: string[]  // exact system IDs; domain_* matched by prefix
}

export const SYSTEM_CATEGORIES: SystemCategory[] = [
  {
    id: 'industry',
    label: 'Industry',
    description: 'National and international industry classification standards',
    accent: '#F59E0B',
    bg: 'rgba(245,158,11,0.08)',
    systemIds: [
      'naics_2022', 'isic_rev4', 'nace_rev2', 'sic_1987',
      'nic_2008', 'wz_2008', 'onace_2008', 'noga_2008',
      'anzsic_2006', 'jsic_2013',
    ],
  },
  {
    id: 'geographic',
    label: 'Geographic',
    description: 'Country, subdivision, and regional classification systems',
    accent: '#64748B',
    bg: 'rgba(100,116,139,0.08)',
    systemIds: ['iso_3166_1', 'iso_3166_2', 'un_m49'],
  },
  {
    id: 'trade',
    label: 'Product / Trade',
    description: 'Harmonized trade codes and product classification hierarchies',
    accent: '#D97706',
    bg: 'rgba(217,119,6,0.08)',
    systemIds: ['hs_2022', 'cpc_v21', 'unspsc_v24'],
  },
  {
    id: 'occupational',
    label: 'Occupational',
    description: 'Skills, roles, and occupational classification frameworks',
    accent: '#7C3AED',
    bg: 'rgba(124,58,237,0.08)',
    systemIds: [
      'isco_08', 'soc_2018', 'anzsco_2022',
      'esco_occupations', 'esco_skills', 'onet_soc',
    ],
  },
  {
    id: 'education',
    label: 'Education',
    description: 'Academic programs, credentials, and educational levels',
    accent: '#059669',
    bg: 'rgba(5,150,105,0.08)',
    systemIds: ['isced_2011', 'iscedf_2013', 'cip_2020'],
  },
  {
    id: 'health',
    label: 'Health / Clinical',
    description: 'Medical diagnoses, drugs, lab tests, and clinical codes',
    accent: '#E11D48',
    bg: 'rgba(225,29,72,0.08)',
    systemIds: ['atc_who', 'icd_11', 'loinc'],
  },
  {
    id: 'regulatory',
    label: 'Financial / Regulatory',
    description: 'Patents, financial standards, governance, and regulatory codes',
    accent: '#0369A1',
    bg: 'rgba(3,105,161,0.08)',
    systemIds: [
      'cofog', 'gics_bridge', 'ghg_protocol', 'patent_cpc',
      'cfr_title_49', 'fmcsa_regs', 'gdpr', 'iso_31000',
    ],
  },
  {
    id: 'domain',
    label: 'Domain Deep-Dives',
    description: 'Sector vocabularies for emerging and specialized industries',
    accent: '#475569',
    bg: 'rgba(71,85,105,0.08)',
    systemIds: [],  // matched by domain_ prefix at runtime
  },
]

export function getCategoryForSystem(systemId: string): SystemCategory {
  if (systemId.startsWith('domain_')) {
    return SYSTEM_CATEGORIES.find((c) => c.id === 'domain')!
  }
  return (
    SYSTEM_CATEGORIES.find((c) => c.systemIds.includes(systemId)) ??
    SYSTEM_CATEGORIES[SYSTEM_CATEGORIES.length - 1]
  )
}

export function groupSystemsByCategory(
  systems: ClassificationSystem[]
): Array<{ category: SystemCategory; systems: ClassificationSystem[] }> {
  return SYSTEM_CATEGORIES.map((cat) => ({
    category: cat,
    systems: systems.filter((s) =>
      cat.id === 'domain'
        ? s.id.startsWith('domain_')
        : cat.systemIds.includes(s.id)
    ),
  })).filter((g) => g.systems.length > 0)
}
