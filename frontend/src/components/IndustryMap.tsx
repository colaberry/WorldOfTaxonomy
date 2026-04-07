'use client'

import Link from 'next/link'
import {
  Factory,
  Building2,
  HeartPulse,
  Cpu,
  ShoppingCart,
  Banknote,
  GraduationCap,
  Truck,
  Wheat,
  Pickaxe,
  Zap,
  HardHat,
  Utensils,
  Palette,
  Globe,
  Briefcase,
  Shield,
  Landmark,
  TreePine,
  Ship,
  type LucideIcon,
} from 'lucide-react'

interface IndustrySector {
  name: string
  icon: LucideIcon
  query: string
  color: string
  description: string
}

const SECTORS: IndustrySector[] = [
  { name: 'Agriculture', icon: Wheat, query: 'agriculture', color: '#22C55E', description: 'Farming, forestry, fishing' },
  { name: 'Mining', icon: Pickaxe, query: 'mining', color: '#A1A1AA', description: 'Extraction, quarrying, oil & gas' },
  { name: 'Manufacturing', icon: Factory, query: 'manufacturing', color: '#F59E0B', description: 'Production & assembly' },
  { name: 'Utilities', icon: Zap, query: 'utilities electricity', color: '#EAB308', description: 'Electric, gas, water supply' },
  { name: 'Construction', icon: HardHat, query: 'construction', color: '#F97316', description: 'Building & infrastructure' },
  { name: 'Retail & Trade', icon: ShoppingCart, query: 'retail trade', color: '#EC4899', description: 'Wholesale & retail commerce' },
  { name: 'Transport', icon: Truck, query: 'transport logistics', color: '#8B5CF6', description: 'Logistics, warehousing, postal' },
  { name: 'Accommodation', icon: Utensils, query: 'accommodation food', color: '#EF4444', description: 'Hotels, restaurants, catering' },
  { name: 'Information & Tech', icon: Cpu, query: 'information technology software', color: '#3B82F6', description: 'Software, data, telecom' },
  { name: 'Finance', icon: Banknote, query: 'finance insurance banking', color: '#10B981', description: 'Banking, insurance, funds' },
  { name: 'Real Estate', icon: Building2, query: 'real estate', color: '#6366F1', description: 'Property & leasing' },
  { name: 'Professional Services', icon: Briefcase, query: 'professional scientific technical', color: '#14B8A6', description: 'Legal, consulting, R&D' },
  { name: 'Public Admin', icon: Landmark, query: 'public administration government', color: '#64748B', description: 'Government & defense' },
  { name: 'Education', icon: GraduationCap, query: 'education', color: '#0EA5E9', description: 'Schools, universities, training' },
  { name: 'Healthcare', icon: HeartPulse, query: 'health care hospital', color: '#EF4444', description: 'Hospitals, clinics, social work' },
  { name: 'Arts & Recreation', icon: Palette, query: 'arts entertainment recreation', color: '#D946EF', description: 'Sports, culture, gambling' },
  { name: 'Environment', icon: TreePine, query: 'environment waste water', color: '#16A34A', description: 'Waste, remediation, recycling' },
  { name: 'Defence', icon: Shield, query: 'defence military', color: '#475569', description: 'Military & security' },
  { name: 'Maritime', icon: Ship, query: 'water transport shipping', color: '#0284C7', description: 'Shipping & water transport' },
  { name: 'International', icon: Globe, query: 'international organization', color: '#7C3AED', description: 'Extraterritorial organizations' },
]

export function IndustryMap() {
  return (
    <div className="space-y-4">
      <div className="text-center space-y-1">
        <h2 className="text-xl sm:text-2xl font-semibold tracking-tight">
          Explore by Industry
        </h2>
        <p className="text-sm text-muted-foreground">
          Pick an industry to discover its classification codes across all global standards
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-2 sm:gap-3">
        {SECTORS.map((sector) => (
          <Link
            key={sector.name}
            href={`/explore?q=${encodeURIComponent(sector.query)}`}
            className="group flex flex-col items-center gap-2 p-3 sm:p-4 rounded-xl border border-border/50 bg-card hover:border-border hover:shadow-md transition-all duration-200"
          >
            <div
              className="flex items-center justify-center w-10 h-10 sm:w-12 sm:h-12 rounded-xl transition-transform duration-200 group-hover:scale-110"
              style={{ backgroundColor: `${sector.color}15`, color: sector.color }}
            >
              <sector.icon className="h-5 w-5 sm:h-6 sm:w-6" />
            </div>
            <div className="text-center">
              <div className="text-xs sm:text-sm font-medium group-hover:text-foreground transition-colors">
                {sector.name}
              </div>
              <div className="text-[10px] sm:text-xs text-muted-foreground leading-tight mt-0.5 hidden sm:block">
                {sector.description}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
