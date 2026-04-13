"""Nation-Sector Geographic Synergy crosswalk.

Maps ISO 3166-1 alpha-2 country codes to NAICS 2-digit sector codes,
representing publicly known nation-sector leadership and strength relationships.

Based on widely published economic competitiveness data (WEF, OECD, World Bank,
IMF), not proprietary data. Hand-coded. ~100 edges.

match_type:
  'leadership' - established, globally recognized sector strength
  'emerging'   - growing strength, recognized but not yet dominant

(country_code, naics_sector, match_type, note)
"""
from __future__ import annotations

from typing import Optional

# (iso_3166_1 alpha-2, naics_2022 2-digit sector, match_type, note)
GEO_SECTOR_EDGES: list[tuple[str, str, str, Optional[str]]] = [
    # United States - technology, finance, healthcare, professional services
    ("US", "54", "leadership", "Professional and tech services - global leader"),
    ("US", "51", "leadership", "Information/software - Silicon Valley, Seattle"),
    ("US", "52", "leadership", "Finance and insurance - Wall Street, fintech"),
    ("US", "62", "leadership", "Healthcare - pharma, biotech, medical devices"),
    ("US", "5417", "leadership", "R&D and scientific - NIH, DARPA, universities"),
    ("US", "11",  "leadership", "Agriculture - world's largest grain exporter"),
    ("US", "21",  "leadership", "Mining and oil/gas - shale, Permian Basin"),

    # Germany - advanced manufacturing, automotive, engineering
    ("DE", "31",  "leadership", "Manufacturing - automotive, machinery, chemicals"),
    ("DE", "32",  "leadership", "Chemical manufacturing - BASF, Bayer, Covestro"),
    ("DE", "33",  "leadership", "Automotive and precision machinery (Baden-Wurttemberg)"),
    ("DE", "54",  "leadership", "Engineering and professional services - Mittelstand"),
    ("DE", "23",  "leadership", "Construction - infrastructure, green building"),

    # China - manufacturing, mining, technology
    ("CN", "31",  "leadership", "Manufacturing - world's factory, electronics"),
    ("CN", "32",  "leadership", "Chemical and material manufacturing - scale"),
    ("CN", "33",  "leadership", "Automotive, electronics, heavy industry"),
    ("CN", "21",  "leadership", "Mining - rare earths, coal, metals (top producer)"),
    ("CN", "51",  "leadership", "Internet and digital economy - Alibaba, Tencent"),
    ("CN", "44",  "leadership", "Retail - world's largest e-commerce market"),

    # Japan - automotive, electronics, robotics, finance
    ("JP", "33",  "leadership", "Automotive and precision electronics - Toyota, Sony"),
    ("JP", "32",  "leadership", "Advanced materials and semiconductors"),
    ("JP", "52",  "leadership", "Finance and insurance - Nikkei, major banks"),
    ("JP", "54",  "leadership", "Engineering and consulting services"),
    ("JP", "31",  "emerging",   "Pharmaceutical and specialty manufacturing"),

    # United Kingdom - finance, professional services, pharma
    ("GB", "52",  "leadership", "Finance and insurance - City of London, Lloyd's"),
    ("GB", "54",  "leadership", "Professional, scientific, technical services"),
    ("GB", "62",  "leadership", "Healthcare - NHS procurement, pharma (AstraZeneca, GSK)"),
    ("GB", "51",  "emerging",   "Fintech and digital media - London tech hub"),
    ("GB", "11",  "emerging",   "Agriculture - precision farming innovation"),

    # India - IT services, pharma, steel
    ("IN", "54",  "leadership", "IT and software services - Bangalore, Hyderabad"),
    ("IN", "51",  "leadership", "Information technology services - TCS, Infosys"),
    ("IN", "62",  "leadership", "Pharmaceuticals - generic drugs, vaccines (Serum)"),
    ("IN", "32",  "emerging",   "Steel and chemical manufacturing"),
    ("IN", "11",  "leadership", "Agriculture - rice, wheat, cotton (major exporter)"),

    # South Korea - semiconductors, shipbuilding, automotive
    ("KR", "33",  "leadership", "Semiconductors, automotive, shipbuilding (TSMC rival)"),
    ("KR", "32",  "leadership", "Steel and chemical manufacturing - POSCO"),
    ("KR", "51",  "emerging",   "Internet, gaming, K-content - Kakao, Naver"),
    ("KR", "52",  "emerging",   "Financial services - expanding globally"),

    # Australia - mining, agriculture, financial services
    ("AU", "21",  "leadership", "Mining - iron ore, coal, LNG, gold (top exporter)"),
    ("AU", "11",  "leadership", "Agriculture - beef, wheat, wool exports"),
    ("AU", "52",  "leadership", "Financial services - four major banks"),
    ("AU", "62",  "emerging",   "Healthcare and biotech - CSIRO, pharma"),

    # Canada - energy, mining, finance
    ("CA", "21",  "leadership", "Oil sands, mining, forestry - Alberta, BC"),
    ("CA", "52",  "leadership", "Financial services - Toronto Bay Street"),
    ("CA", "11",  "leadership", "Agriculture - wheat, canola, pulses exports"),
    ("CA", "54",  "emerging",   "AI research - Montreal, Toronto, Vector Institute"),

    # France - aerospace, luxury, nuclear energy
    ("FR", "33",  "leadership", "Aerospace - Airbus, Safran, Dassault (Toulouse)"),
    ("FR", "31",  "emerging",   "Pharmaceuticals - Sanofi"),
    ("FR", "22",  "leadership", "Nuclear energy - EDF, 70% nuclear electricity"),
    ("FR", "54",  "leadership", "Professional services and consulting - Paris hub"),
    ("FR", "72",  "leadership", "Accommodation and food - luxury tourism, Michelin"),

    # Switzerland - pharma, finance, precision manufacturing
    ("CH", "62",  "leadership", "Pharmaceuticals - Roche, Novartis (Basel)"),
    ("CH", "52",  "leadership", "Private banking and asset management"),
    ("CH", "33",  "leadership", "Precision instruments, watchmaking, medtech"),
    ("CH", "54",  "leadership", "Professional and financial services - Zurich"),

    # Netherlands - logistics, agriculture, energy
    ("NL", "48",  "leadership", "Logistics and transport - Port of Rotterdam"),
    ("NL", "11",  "leadership", "High-tech agriculture - greenhouse horticulture"),
    ("NL", "52",  "leadership", "Financial services - ING, ABN AMRO, Aegon"),
    ("NL", "54",  "emerging",   "Tech and semiconductor equipment - ASML"),

    # Singapore - finance, logistics, biomedical
    ("SG", "52",  "leadership", "Finance - regional financial hub, SGX"),
    ("SG", "48",  "leadership", "Logistics - Port of Singapore, Changi Airport"),
    ("SG", "54",  "leadership", "Professional services - Asia-Pacific HQs"),
    ("SG", "62",  "emerging",   "Biomedical manufacturing and research hub"),

    # Saudi Arabia - oil and gas, construction
    ("SA", "21",  "leadership", "Oil and gas - Aramco, world largest oil exporter"),
    ("SA", "23",  "leadership", "Construction - NEOM, Vision 2030 megaprojects"),
    ("SA", "52",  "emerging",   "Finance - sovereign wealth, Islamic banking"),
    ("SA", "44",  "emerging",   "Retail - diversification, e-commerce growth"),

    # UAE - finance, logistics, tourism
    ("AE", "52",  "leadership", "Finance - Dubai DIFC, Abu Dhabi ADGM"),
    ("AE", "48",  "leadership", "Logistics - DP World, Jebel Ali port"),
    ("AE", "72",  "leadership", "Tourism and accommodation - Dubai, Abu Dhabi"),
    ("AE", "23",  "emerging",   "Construction - continuous infrastructure build"),

    # Brazil - agriculture, mining, oil
    ("BR", "11",  "leadership", "Agriculture - soybeans, beef, coffee, sugarcane"),
    ("BR", "21",  "leadership", "Mining - iron ore (Vale), oil (Petrobras deepwater)"),
    ("BR", "31",  "emerging",   "Ethanol and bioenergy manufacturing"),
    ("BR", "52",  "emerging",   "Financial services - fintech hub (Nubank)"),

    # Sweden - telecom, manufacturing, cleantech
    ("SE", "33",  "leadership", "Manufacturing - Volvo, Scania, Atlas Copco"),
    ("SE", "51",  "leadership", "Telecom and software - Ericsson, Spotify, Klarna"),
    ("SE", "54",  "leadership", "Engineering, design and consulting"),
    ("SE", "22",  "emerging",   "Clean energy and grid technology"),

    # Israel - cybersecurity, medtech, agri-tech
    ("IL", "54",  "leadership", "Cybersecurity, defense tech, R&D - Start-Up Nation"),
    ("IL", "62",  "leadership", "Medical devices and digital health"),
    ("IL", "11",  "leadership", "Agricultural technology - drip irrigation, seeds"),
    ("IL", "51",  "leadership", "Software - Check Point, Wix, Monday.com"),

    # Taiwan - semiconductors, electronics
    ("TW", "33",  "leadership", "Semiconductors and electronics - TSMC, Foxconn"),
    ("TW", "32",  "leadership", "Display panels - AUO, Innolux"),
    ("TW", "54",  "emerging",   "IC design and electronics services"),

    # South Africa - mining, finance
    ("ZA", "21",  "leadership", "Mining - gold, platinum, chrome, coal"),
    ("ZA", "52",  "leadership", "Financial services - Johannesburg Stock Exchange"),
    ("ZA", "11",  "emerging",   "Agriculture - wine, citrus, deciduous fruit"),

    # Norway - oil and gas, maritime, aquaculture
    ("NO", "21",  "leadership", "Oil and gas - North Sea, Equinor sovereign fund"),
    ("NO", "48",  "leadership", "Maritime shipping - world's leading ship-owning nation"),
    ("NO", "11",  "leadership", "Aquaculture - Atlantic salmon, largest exporter"),
    ("NO", "22",  "emerging",   "Hydropower and clean energy transition"),

    # Finland - telecom, forestry, tech
    ("FI", "51",  "leadership", "Technology and telecom - Nokia legacy, gaming (Rovio)"),
    ("FI", "11",  "leadership", "Forestry and paper - UPM, Stora Enso"),
    ("FI", "33",  "emerging",   "Cleantech and energy equipment"),

    # Indonesia - mining, agriculture, digital
    ("ID", "21",  "leadership", "Mining - nickel, coal, tin (key EV minerals)"),
    ("ID", "11",  "leadership", "Agriculture - palm oil, rice, rubber"),
    ("ID", "51",  "emerging",   "Digital economy - Gojek, Tokopedia, growing fast"),
]


async def ingest_crosswalk_geo_sector(conn) -> int:
    """Ingest Nation-Sector Geographic Synergy crosswalk edges.

    Maps ISO 3166-1 alpha-2 country codes to NAICS 2-digit sector codes
    in the equivalence table, representing publicly known nation-sector
    leadership and strength relationships.

    Returns count of edges inserted.
    """
    # Map domain-specific match labels to equivalence table allowed values
    # (exact, partial, broad, narrow)
    _MATCH_MAP = {"leadership": "broad", "emerging": "partial"}

    rows = [
        (
            "iso_3166_1",
            country_code,
            "naics_2022",
            naics_sector,
            _MATCH_MAP.get(match_type, match_type),
            note or "",
        )
        for country_code, naics_sector, match_type, note in GEO_SECTOR_EDGES
    ]

    await conn.executemany(
        """INSERT INTO equivalence
               (source_system, source_code, target_system, target_code, match_type, notes)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING""",
        rows,
    )

    return len(rows)
