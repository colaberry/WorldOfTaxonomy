"""SOC 2018 / NAICS 2022 crosswalk.

Maps SOC 2018 major occupation groups (XX-0000 format) to NAICS 2022 sectors
where those occupations predominantly work.

Based on BLS Occupational Employment and Wage Statistics (OEWS) industry
staffing patterns. Hand-coded ~55 edges mapping 23 SOC major groups to
their primary and secondary NAICS sectors.

(soc_code, naics_code, match_type, note)
"""
from __future__ import annotations

from typing import Optional

# SOC 2018 Major Groups:
# 11-0000 Management
# 13-0000 Business and Financial Operations
# 15-0000 Computer and Mathematical
# 17-0000 Architecture and Engineering
# 19-0000 Life, Physical, and Social Science
# 21-0000 Community and Social Service
# 23-0000 Legal
# 25-0000 Educational Instruction and Library
# 27-0000 Arts, Design, Entertainment, Sports, and Media
# 29-0000 Healthcare Practitioners and Technical
# 31-0000 Healthcare Support
# 33-0000 Protective Service
# 35-0000 Food Preparation and Serving Related
# 37-0000 Building and Grounds Cleaning and Maintenance
# 39-0000 Personal Care and Service
# 41-0000 Sales and Related
# 43-0000 Office and Administrative Support
# 45-0000 Farming, Fishing, and Forestry
# 47-0000 Construction and Extraction
# 49-0000 Installation, Maintenance, and Repair
# 51-0000 Production (Manufacturing)
# 53-0000 Transportation and Material Moving

# NAICS 2022 sectors (2-digit):
# 11 Agriculture, 21 Mining, 22 Utilities, 23 Construction
# 31-33 Manufacturing, 42 Wholesale, 44-45 Retail, 48-49 Transport
# 51 Information, 52 Finance, 53 Real Estate, 54 Professional
# 55 Management of Companies, 56 Admin/Support, 61 Education
# 62 Health Care, 71 Arts/Recreation, 72 Food Service, 81 Other
# 92 Public Administration

# (soc_code, naics_code, match_type, note)
SOC_NAICS_EDGES: list[tuple[str, str, str, Optional[str]]] = [
    # Management (11-0000) - cross-industry, strongest in large sectors
    ("11-0000", "52", "broad", "Financial managers, bank and insurance executives"),
    ("11-0000", "54", "broad", "Management consultants and professional services principals"),
    ("11-0000", "62", "broad", "Hospital administrators and healthcare managers"),
    ("11-0000", "61", "broad", "School principals and education administrators"),
    ("11-0000", "92", "broad", "Government executives and agency administrators"),

    # Business and Financial Operations (13-0000)
    ("13-0000", "52", "broad", "Accountants, financial analysts, underwriters"),
    ("13-0000", "54", "broad", "Management analysts, HR specialists, compliance"),
    ("13-0000", "55", "narrow", "Corporate HQ financial and compliance staff"),

    # Computer and Mathematical (15-0000)
    ("15-0000", "51", "broad", "Software developers, IT professionals in tech sector"),
    ("15-0000", "54", "broad", "Data scientists, systems analysts in professional services"),
    ("15-0000", "52", "narrow", "FinTech, algorithmic trading, risk modeling"),

    # Architecture and Engineering (17-0000)
    ("17-0000", "23", "broad", "Civil engineers, architects in construction"),
    ("17-0000", "54", "broad", "Engineering consultants and technical services"),
    ("17-0000", "21", "narrow", "Petroleum and mining engineers"),
    ("17-0000", "22", "narrow", "Power systems and utilities engineers"),

    # Life, Physical, and Social Science (19-0000)
    ("19-0000", "54", "broad", "Research scientists in R&D services"),
    ("19-0000", "62", "narrow", "Medical researchers and clinical scientists"),
    ("19-0000", "11", "narrow", "Agricultural scientists, soil scientists"),

    # Community and Social Service (21-0000)
    ("21-0000", "62", "broad", "Social workers, counselors in healthcare sector"),
    ("21-0000", "92", "broad", "Community outreach and government social services"),
    ("21-0000", "61", "narrow", "School counselors and education social workers"),

    # Legal (23-0000)
    ("23-0000", "54", "broad", "Lawyers, paralegals in legal services"),
    ("23-0000", "92", "narrow", "Government attorneys and public defenders"),

    # Educational Instruction and Library (25-0000)
    ("25-0000", "61", "broad", "Teachers, professors, librarians in education sector"),
    ("25-0000", "62", "narrow", "Healthcare educators and training specialists"),

    # Arts, Design, Entertainment, Sports, and Media (27-0000)
    ("27-0000", "71", "broad", "Artists, performers, athletes in entertainment"),
    ("27-0000", "51", "broad", "Graphic designers, writers, journalists in media"),
    ("27-0000", "54", "narrow", "Industrial designers, advertising creatives"),

    # Healthcare Practitioners and Technical (29-0000)
    ("29-0000", "62", "broad", "Physicians, nurses, therapists in health care"),
    ("29-0000", "61", "narrow", "School nurses and health educators"),

    # Healthcare Support (31-0000)
    ("31-0000", "62", "broad", "Medical aides, orderlies, home health aides"),

    # Protective Service (33-0000)
    ("33-0000", "92", "broad", "Police, firefighters, corrections officers in government"),
    ("33-0000", "56", "narrow", "Security guards in admin/support services sector"),

    # Food Preparation and Serving Related (35-0000)
    ("35-0000", "72", "broad", "Cooks, servers, fast food workers in food service"),
    ("35-0000", "61", "narrow", "School cafeteria workers"),

    # Building and Grounds Cleaning and Maintenance (37-0000)
    ("37-0000", "56", "broad", "Janitors, landscapers in facility services"),
    ("37-0000", "62", "narrow", "Hospital and healthcare facility housekeeping"),

    # Personal Care and Service (39-0000)
    ("39-0000", "81", "broad", "Hairdressers, childcare workers in personal services"),
    ("39-0000", "62", "narrow", "Home health and personal care aides"),

    # Sales and Related (41-0000)
    ("41-0000", "44", "broad", "Retail sales, cashiers in retail trade"),
    ("41-0000", "42", "narrow", "Wholesale trade representatives and agents"),
    ("41-0000", "52", "narrow", "Insurance agents and financial sales representatives"),

    # Office and Administrative Support (43-0000)
    ("43-0000", "52", "broad", "Bank tellers, insurance clerks, office admins"),
    ("43-0000", "92", "broad", "Government clerks, postal workers, office support"),
    ("43-0000", "54", "narrow", "Legal and medical secretaries"),

    # Farming, Fishing, and Forestry (45-0000)
    ("45-0000", "11", "broad", "Farmers, farm workers, loggers in agriculture"),

    # Construction and Extraction (47-0000)
    ("47-0000", "23", "broad", "Carpenters, electricians, plumbers in construction"),
    ("47-0000", "21", "narrow", "Miners, drillers, extraction workers"),

    # Installation, Maintenance, and Repair (49-0000)
    ("49-0000", "23", "narrow", "Building maintenance in construction sector"),
    ("49-0000", "56", "broad", "Facility maintenance in admin/support services"),
    ("49-0000", "81", "narrow", "Appliance and equipment repair in other services"),

    # Production (Manufacturing) (51-0000)
    ("51-0000", "31", "broad", "Factory workers across all manufacturing subsectors"),

    # Transportation and Material Moving (53-0000)
    ("53-0000", "48", "broad", "Truck drivers, couriers in transportation sector"),
    ("53-0000", "42", "narrow", "Warehouse workers in wholesale distribution"),
    ("53-0000", "44", "narrow", "Delivery workers in retail trade"),
]


async def ingest_crosswalk_soc_naics(conn) -> int:
    """Ingest SOC 2018 / NAICS 2022 crosswalk edges.

    Hand-coded based on BLS OEWS staffing pattern data.
    Returns count of edges inserted.
    """
    rows = [
        ("soc_2018", soc_code, "naics_2022", naics_code, match_type, note or "")
        for soc_code, naics_code, match_type, note in SOC_NAICS_EDGES
    ]

    await conn.executemany(
        """INSERT INTO equivalence
               (source_system, source_code, target_system, target_code, match_type, notes)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (source_system, source_code, target_system, target_code) DO NOTHING""",
        rows,
    )

    return len(rows)
