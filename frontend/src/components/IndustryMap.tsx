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
  ClipboardList,
  Scissors,
  Atom,
  Brain,
  Dna,
  Rocket,
  Wind,
  Layers,
  Coins,
  Bot,
  BatteryCharging,
  CircuitBoard,
  FlaskConical,
  Glasses,
  Microscope,
  Droplets,
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
  { name: 'Agriculture',          icon: Wheat,         query: 'agriculture',                           color: '#22C55E', description: 'Farming, forestry, fishing' },
  { name: 'Mining',               icon: Pickaxe,       query: 'mining',                                color: '#A1A1AA', description: 'Extraction, quarrying, oil & gas' },
  { name: 'Manufacturing',        icon: Factory,       query: 'manufacturing',                         color: '#F59E0B', description: 'Production & assembly' },
  { name: 'Utilities',            icon: Zap,           query: 'utilities electricity',                 color: '#EAB308', description: 'Electric, gas, water supply' },
  { name: 'Construction',         icon: HardHat,       query: 'construction',                          color: '#F97316', description: 'Building & infrastructure' },
  { name: 'Retail & Trade',       icon: ShoppingCart,  query: 'retail trade',                          color: '#EC4899', description: 'Wholesale & retail commerce' },
  { name: 'Transport',            icon: Truck,         query: 'transport logistics',                   color: '#8B5CF6', description: 'Logistics, warehousing, postal' },
  { name: 'Accommodation',        icon: Utensils,      query: 'accommodation food',                    color: '#EF4444', description: 'Hotels, restaurants, catering' },
  { name: 'Information & Tech',   icon: Cpu,           query: 'information technology software',       color: '#3B82F6', description: 'Software, data, telecom' },
  { name: 'Finance',              icon: Banknote,      query: 'finance insurance banking',             color: '#10B981', description: 'Banking, insurance, funds' },
  { name: 'Real Estate',          icon: Building2,     query: 'real estate',                           color: '#6366F1', description: 'Property & leasing' },
  { name: 'Professional Services',icon: Briefcase,     query: 'professional scientific technical',     color: '#14B8A6', description: 'Legal, consulting, R&D' },
  { name: 'Public Admin',         icon: Landmark,      query: 'public administration government',      color: '#64748B', description: 'Government & defense' },
  { name: 'Education',            icon: GraduationCap, query: 'education',                             color: '#0EA5E9', description: 'Schools, universities, training' },
  { name: 'Healthcare',           icon: HeartPulse,    query: 'health care hospital',                  color: '#F43F5E', description: 'Hospitals, clinics, social work' },
  { name: 'Arts & Recreation',    icon: Palette,       query: 'arts entertainment recreation',         color: '#D946EF', description: 'Sports, culture, gambling' },
  { name: 'Environment',          icon: TreePine,      query: 'environment waste water',               color: '#16A34A', description: 'Waste, remediation, recycling' },
  { name: 'Defence',              icon: Shield,        query: 'defence military',                      color: '#475569', description: 'Military & security' },
  { name: 'Maritime',             icon: Ship,          query: 'water transport shipping',              color: '#0284C7', description: 'Shipping & water transport' },
  { name: 'International',        icon: Globe,         query: 'international organization',            color: '#7C3AED', description: 'Extraterritorial organizations' },
  { name: 'Admin & Support',      icon: ClipboardList, query: 'administrative support staffing',       color: '#C2410C', description: 'Staffing, cleaning, travel, security' },
  { name: 'Other Services',       icon: Scissors,      query: 'other services repair personal care',   color: '#BE185D', description: 'Repair, personal care, membership orgs' },
  { name: 'Quantum Computing',    icon: Atom,           query: 'quantum computing',                    color: '#7C3AED', description: 'Hardware, algorithms, sensors' },
  { name: 'AI & Data',            icon: Brain,          query: 'artificial intelligence machine learning', color: '#3B82F6', description: 'ML, LLMs, data platforms' },
  { name: 'Biotechnology',        icon: Microscope,     query: 'biotechnology genomics',               color: '#10B981', description: 'Genomics, therapeutics, diagnostics' },
  { name: 'Space & Satellite',    icon: Rocket,         query: 'space satellite launch',               color: '#4F46E5', description: 'Launch, satellite, exploration' },
  { name: 'Climate Tech',         icon: Wind,           query: 'climate technology renewable',         color: '#22C55E', description: 'Carbon, clean energy, adaptation' },
  { name: 'Advanced Materials',   icon: Layers,         query: 'advanced materials nanomaterials',     color: '#F59E0B', description: 'Composites, nano, smart materials' },
  { name: 'Digital Assets',       icon: Coins,          query: 'digital assets crypto blockchain',     color: '#EAB308', description: 'Crypto, DeFi, tokenization, Web3' },
  { name: 'Robotics & Autonomy',  icon: Bot,            query: 'autonomous robotics automation',       color: '#94A3B8', description: 'Drones, autonomous vehicles, cobots' },
  { name: 'Energy Storage',       icon: BatteryCharging,query: 'energy storage battery',               color: '#0D9488', description: 'Batteries, fuel cells, thermal storage' },
  { name: 'Semiconductors',       icon: CircuitBoard,   query: 'semiconductor chip fabrication',       color: '#EF4444', description: 'Chips, wafers, packaging, EDA' },
  { name: 'Synthetic Biology',    icon: Dna,            query: 'synthetic biology',                    color: '#06B6D4', description: 'Engineered organisms, biosynthesis' },
  { name: 'XR & Metaverse',       icon: Glasses,        query: 'extended reality virtual augmented',   color: '#EC4899', description: 'VR, AR, MR, spatial computing' },
  { name: 'Chemical Industry',    icon: FlaskConical,   query: 'chemical industry specialty',          color: '#F97316', description: 'Specialty, bulk, fine chemicals' },
  { name: 'Cyber & Security',     icon: Shield,         query: 'defence security cyber',               color: '#334155', description: 'Cyber, C4ISR, munitions, ITAR' },
  { name: 'Water & Environment',  icon: Droplets,       query: 'water environment treatment',          color: '#0EA5E9', description: 'Treatment, desalination, remediation' },
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
