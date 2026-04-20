"""Unit tests for business-classification kind detection."""

import pytest

from world_of_taxonomy.system_kind import is_business_classification


class TestIndustryClassifications:
    @pytest.mark.parametrize("system_id", [
        "naics_2022", "naics_2017", "naics_2012",
        "isic_rev4", "isic_rev31",
        "nace_rev2", "nace_lt", "nace_tr",
        "sic_1987", "sic_sa",
        "anzsic_2006",
        "jsic_2013",
        "nic_2008",
        "wz_2008", "onace_2008", "noga_2008",
        "ateco_2007", "naf_rev2", "pkd_2007", "sbi_2008",
        "sni_2007", "db07", "tol_2008",
        "csic_2017", "cnae_2012",
        "kbli_2020", "ksic_2017", "ssic_2020", "msic_2008", "tsic_2009",
        "psic_2009", "psic_pk", "vsic_2018", "bsic",
        "ciiu_co", "ciiu_ar", "ciiu_cl", "ciiu_pe", "ciiu_ec", "ciiu_ve",
        "ciiu_cr", "ciiu_gt", "ciiu_pa",
        "scian_2018",
        "cae_rev3", "cz_nace", "teaor_2008", "caen_rev2",
        "nkd_2007", "sk_nace", "nkid", "emtak", "nk_lv",
        "okved_2", "caeb",
        "isic_ng", "isic_eg", "isic_sa",
    ])
    def test_industry_systems_included(self, system_id):
        assert is_business_classification(system_id) is True


class TestOccupationClassifications:
    @pytest.mark.parametrize("system_id", [
        "soc_2018", "isco_08", "anzsco_2022",
        "noc_2021", "uksoc_2020", "kldb_2010", "rome_v4",
        "onet_soc", "esco_occupations", "esco_skills",
    ])
    def test_occupation_systems_included(self, system_id):
        assert is_business_classification(system_id) is True


class TestNonBusinessExcluded:
    @pytest.mark.parametrize("system_id", [
        "cfr_title_49", "fmcsa_regs", "eccn",
        "hcpcs_l2", "icd10cm", "icd10_pcs", "icd10_am", "icd10_gm",
        "ms_drg", "nucc_hcpt", "loinc", "mesh", "icd_11",
        "us_fips", "hts_us", "schedule_b", "cn_2024",
        "gdpr_articles", "sfdr", "eu_taxonomy", "eu_nuts_2021",
        "cip_2020",
        "anzsrc_for_2020", "arxiv_taxonomy", "patent_cpc",
        "acm_ccs", "msc_2020", "pacs", "lcc", "jel",
        "basel_exposure", "gics_bridge", "icb",
        "atc_who", "cpv_2008", "prodcom",
    ])
    def test_non_business_systems_excluded(self, system_id):
        assert is_business_classification(system_id) is False


class TestDomainSystemsExcluded:
    def test_domain_prefix_excluded(self):
        assert is_business_classification("domain_truck_freight") is False
        assert is_business_classification("domain_insurance_types") is False
