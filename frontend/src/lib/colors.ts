export const SYSTEM_TINTS: Record<string, string> = {
  naics_2022: '#F59E0B',
  isic_rev4: '#3B82F6',
  nace_rev2: '#6366F1',
  sic_1987: '#78716C',
  anzsic_2006: '#14B8A6',
  nic_2008: '#F97316',
  wz_2008: '#EF4444',
  onace_2008: '#DC2626',
  noga_2008: '#B91C1C',
  jsic_2013: '#F43F5E',
}

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
  return SYSTEM_TINTS[systemId] || '#3B82F6'
}

export function getSectorColor(sectorCode: string): string {
  return SECTOR_COLORS[sectorCode] || '#6366F1'
}
