"""Business-classification kind detector.

Classify endpoints use `is_business_classification` to decide which
country-specific systems may join the candidate set. A country like the
US has 15 non-domain official systems, but only a handful are general-
purpose business classifications (NAICS, SOC, O*NET). The rest are
specialty standards (ICD-10-CM, HCPCS, CFR Title 49, ECCN, FIPS) that
flood unrelated noise into an industry query.

A `classification_system.kind` column would be the proper fix. Until
that migration lands, pattern-matching on system_id is the pragmatic
gate.
"""

from __future__ import annotations

# Exact IDs for systems that do not follow family prefixes.
_EXACT_BUSINESS_IDS: frozenset[str] = frozenset({
    # Industry variants with idiosyncratic names
    "db07",           # Denmark
    "bsic",           # Bangladesh
    "caeb",           # Bolivia
    "nkid",           # Bulgaria
    "nk_lv",          # Latvia
    "emtak",          # Estonia
    "okved_2",        # Russia
    "sk_nace",        # Slovakia
    "cz_nace",        # Czech Republic
    # Occupation
    "onet_soc",
})

# System_id prefixes that identify general-purpose business classifications:
# industry (NAICS/ISIC/NACE/SIC family + country variants) and occupation.
# Kept broad on purpose: a new country-specific ISIC variant like isic_xx
# should be covered without code changes.
_BUSINESS_PREFIXES: tuple[str, ...] = (
    # Industry (NAICS/ISIC/NACE family + country-specific industrial codes)
    "naics_", "isic_", "nace_", "sic_", "scian_",
    "anzsic_", "jsic_", "nic_",
    "wz_", "onace_", "noga_",
    "ciiu_", "cnae_", "ateco_", "naf_", "pkd_", "sbi_",
    "sni_", "tol_", "csic_", "kbli_", "ksic_", "ssic_",
    "msic_", "tsic_", "psic_", "vsic_",
    "cae_", "caen_", "caem_", "kved_", "nkd_", "teaor_",
    "stakod_", "isat_", "clanae_", "skd_",
    "nacebel_", "nacelu_", "nve_",
    "slsic_",
    "nace_bel_", "nace_lu_", "nace_ie_",
    "nace_cy_", "nace_mt_", "nace_lt", "nace_tr", "nace_ge", "nace_am",
    "kd_",  # Serbia, Montenegro, Bosnia, Kosovo variants
    # Occupation (SOC/ISCO family + country variants)
    "soc_", "isco_", "anzsco_", "noc_", "uksoc_", "uk_soc_",
    "kldb_", "rome_", "esco_occupations", "esco_skills",
)


def is_business_classification(system_id: str) -> bool:
    """Return True if system_id is a general-purpose business classification.

    "Business classification" here means industry (NAICS/ISIC/NACE/SIC family)
    or occupation (SOC/ISCO family) - the kind of system a business owner
    would expect to appear when classifying a company, product, or role.

    Domain taxonomies, medical codes, regulatory codes, trade/tariff codes,
    research/academic taxonomies, finance/ESG frameworks, and geographic
    codes are NOT business classifications for this purpose.
    """
    if not system_id or system_id.startswith("domain_"):
        return False
    if system_id in _EXACT_BUSINESS_IDS:
        return True
    return any(system_id.startswith(p) for p in _BUSINESS_PREFIXES)
