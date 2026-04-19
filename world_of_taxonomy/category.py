"""Domain vs standard category helper.

A classification system is a Domain taxonomy iff its id starts with "domain_".
Everything else is an Official standard (NAICS, ISIC, NACE, ICD, SOC, ...).

This distinction drives a two-section UI pattern: plain-language domain
taxonomies surface first for non-experts, standards second for compliance.
"""


DOMAIN_PREFIX = "domain_"
CATEGORY_DOMAIN = "domain"
CATEGORY_STANDARD = "standard"

DOMAIN_LABEL = "Domain taxonomies"
STANDARD_LABEL = "Official standard codes"

EDGE_STANDARD_STANDARD = "standard_standard"
EDGE_STANDARD_DOMAIN = "standard_domain"
EDGE_DOMAIN_STANDARD = "domain_standard"
EDGE_DOMAIN_DOMAIN = "domain_domain"


def get_category(system_id: str) -> str:
    return CATEGORY_DOMAIN if system_id.startswith(DOMAIN_PREFIX) else CATEGORY_STANDARD


def is_domain(system_id: str) -> bool:
    return system_id.startswith(DOMAIN_PREFIX)


def compute_edge_kind(source_system: str, target_system: str) -> str:
    src = get_category(source_system)
    tgt = get_category(target_system)
    return f"{src}_{tgt}"
