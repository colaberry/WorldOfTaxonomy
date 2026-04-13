export const SYSTEM_TINTS: Record<string, string> = {
  // Industry
  naics_2022:    '#F59E0B',
  isic_rev4:     '#3B82F6',
  nace_rev2:     '#6366F1',
  sic_1987:      '#78716C',
  anzsic_2006:   '#14B8A6',
  nic_2008:      '#F97316',
  wz_2008:       '#EF4444',
  onace_2008:    '#DC2626',
  noga_2008:     '#B91C1C',
  jsic_2013:     '#F43F5E',

  // Geographic
  iso_3166_1:    '#64748B',
  iso_3166_2:    '#94A3B8',
  un_m49:        '#475569',

  // Product / Trade
  hs_2022:       '#D97706',
  cpc_v21:       '#92400E',
  unspsc_v24:    '#B45309',

  // Occupational
  isco_08:           '#2563EB',
  soc_2018:          '#1D4ED8',
  anzsco_2022:       '#1E40AF',
  esco_occupations:  '#7C3AED',
  esco_skills:       '#6D28D9',
  onet_soc:          '#4F46E5',

  // Education
  isced_2011:    '#059669',
  iscedf_2013:   '#047857',
  cip_2020:      '#065F46',

  // Health / Clinical
  atc_who:       '#E11D48',
  icd_11:        '#BE123C',
  loinc:         '#9F1239',

  // Financial / Regulatory
  cofog:         '#0369A1',
  gics_bridge:   '#075985',
  ghg_protocol:  '#166534',
  patent_cpc:    '#854D0E',
  cfr_title_49:  '#7F1D1D',
  fmcsa_regs:    '#991B1B',
  gdpr:          '#5B21B6',
  iso_31000:     '#4C1D95',
}

// All domain_* systems share a slate tint
const DOMAIN_TINT = '#475569'

export const SECTOR_COLORS: Record<string, string> = {
  // NAICS sectors
  '11': '#4ADE80', '21': '#F59E0B', '22': '#06B6D4',
  '23': '#EF4444', '31-33': '#8B5CF6', '42': '#3B82F6',
  '44-45': '#F97316', '48-49': '#14B8A6', '51': '#6366F1',
  '52': '#A78BFA', '53': '#10B981', '54': '#D97706',
  '55': '#0D9488', '56': '#78716C', '61': '#2563EB',
  '62': '#1E40AF', '71': '#E11D48', '72': '#9CA3AF',
  '81': '#64748B', '92': '#7A7872',
  // ISIC/NACE/ANZSIC/SIC/JSIC letter sections
  A: '#4ADE80', B: '#F59E0B', C: '#8B5CF6', D: '#06B6D4',
  E: '#14B8A6', F: '#EF4444', G: '#F97316', H: '#14B8A6',
  I: '#D97706', J: '#3B82F6', K: '#6366F1', L: '#A78BFA',
  M: '#10B981', N: '#78716C', O: '#1E40AF', P: '#2563EB',
  Q: '#0D9488', R: '#E11D48', S: '#9CA3AF', T: '#64748B',
  U: '#7A7872',
}

export function getSystemColor(systemId: string): string {
  if (systemId.startsWith('domain_')) return DOMAIN_TINT
  return SYSTEM_TINTS[systemId] || '#3B82F6'
}

export function getSectorColor(sectorCode: string): string {
  return SECTOR_COLORS[sectorCode] || '#6366F1'
}
