# Regulatory and Compliance Standards

> **TL;DR:** WoT hosts 120 regulatory and compliance frameworks: US federal regulations (HIPAA, SOX, GDPR, OSHA, FDA), US security and accounting frameworks (NIST CSF, NIST 800-53, SOC 2, PCI DSS, US GAAP), EU directives and acts (GDPR, NIS2, DORA, MDR, EU AI Act, CSRD), ISO management system standards (9001, 14001, 27001, 22301, 45001, 13485, 42001 for AI), and global treaties (Basel III, FATF, ILO, Paris Agreement, IMO MARPOL/SOLAS). This page maps which framework applies when, and which ones overlap.

---

## What this layer is for

Regulatory frameworks describe **what an organization must do** to operate within a jurisdiction or sector. They are orthogonal to industry and process classifications: a healthcare provider in the US must comply with HIPAA (jurisdiction), the Joint Commission (sector), SOC 2 (if SaaS), and ISO 27001 (if international). Industry codes (NAICS) and process frameworks (APQC PCF) tell you *what work* the organization does; regulatory frameworks tell you *which rules constrain that work*.

This layer matters when downstream products need to:

- Map a customer's regulated obligations to a sector vocabulary (LegalTech, GRC platforms, audit tooling).
- Anchor a control to multiple overlapping frameworks (a NIST 800-53 control often satisfies SOC 2, ISO 27001, and HIPAA Security Rule simultaneously).
- Surface relevant rules when an industry classification is known (NAICS 6221 General Medical Hospitals -> HIPAA + Joint Commission + CMS Conditions of Participation).
- Drive contract-clause libraries that map clauses to applicable frameworks.

## US Federal Regulations

Statutory frameworks codified in US law, administered by federal agencies.

### Healthcare

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_hipaa` | 36 | HHS / OCR | Health Insurance Portability and Accountability Act |
| `reg_fda_21cfr` | 28 | FDA | Title 21 of the Code of Federal Regulations (drugs, devices, food) |
| `reg_dea` | 25 | DEA | Drug Enforcement Administration scheduling and registration |

### Financial services

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_sox` | 58 | SEC / PCAOB | Sarbanes-Oxley Act (public-company financial reporting) |
| `reg_glba` | 28 | Multiple | Gramm-Leach-Bliley Act (financial privacy) |
| `reg_fcra` | 27 | FTC / CFPB | Fair Credit Reporting Act |
| `reg_sec` | 29 | SEC | Securities and Exchange Commission rules |
| `reg_finra` | 28 | FINRA | Financial Industry Regulatory Authority rules |
| `reg_cfpb` | 22 | CFPB | Consumer Financial Protection Bureau regulations |
| `reg_naic` | 21 | NAIC | National Association of Insurance Commissioners model laws |
| `reg_ffiec` | 25 | FFIEC | Federal Financial Institutions Examination Council IT Handbook |

### Privacy and consumer protection

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_ccpa` | 34 | California AG | California Consumer Privacy Act / CPRA |
| `reg_ferpa` | 30 | DoEd | Family Educational Rights and Privacy Act |
| `reg_coppa` | 23 | FTC | Children's Online Privacy Protection Act |
| `reg_ftc_safeguards` | 23 | FTC | FTC Safeguards Rule (financial-institution data security) |
| `reg_ada` | 31 | DOJ | Americans with Disabilities Act |

### Workplace safety

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_osha_1910` | 47 | OSHA | OSHA General Industry standards (29 CFR 1910) |
| `reg_osha_1926` | 49 | OSHA | OSHA Construction standards (29 CFR 1926) |

### Energy and environment

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_clean_air` | 28 | EPA | Clean Air Act |
| `reg_clean_water` | 26 | EPA | Clean Water Act |
| `reg_cercla` | 27 | EPA | Comprehensive Environmental Response, Compensation, and Liability Act (Superfund) |
| `reg_rcra` | 29 | EPA | Resource Conservation and Recovery Act |
| `reg_tsca` | 25 | EPA | Toxic Substances Control Act |
| `reg_nerc_cip` | 48 | NERC / FERC | NERC Critical Infrastructure Protection (electric grid) |

### Federal IT and contracting

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_fisma` | 27 | OMB / NIST | Federal Information Security Modernization Act |
| `reg_fedramp` | 40 | GSA | Federal Risk and Authorization Management Program |
| `reg_far` | 32 | GSA / DoD / NASA | Federal Acquisition Regulation |
| `reg_dfars` | 25 | DoD | Defense Federal Acquisition Regulation Supplement |
| `reg_itar` | 32 | State Dept | International Traffic in Arms Regulations |
| `reg_ear` | 31 | BIS / Commerce | Export Administration Regulations |

## US Frameworks (Voluntary or Sector-Specific)

Not laws themselves but widely adopted as the de-facto basis for compliance, audit, and accreditation in their respective sectors.

### Cybersecurity and IT governance

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_nist_csf` | 28 | NIST | NIST Cybersecurity Framework 2.0 (Identify, Protect, Detect, Respond, Recover, Govern) |
| `reg_nist_800_53` | 36 | NIST | NIST SP 800-53 Rev 5 security and privacy controls |
| `reg_nist_800_171` | 28 | NIST | NIST SP 800-171 Rev 3 (controlled unclassified information) |
| `reg_cmmc` | 25 | DoD | Cybersecurity Maturity Model Certification 2.0 |
| `reg_cis_controls` | 29 | CIS | CIS Critical Security Controls v8 |
| `reg_pci_dss` | 27 | PCI SSC | PCI Data Security Standard v4.0 |
| `reg_soc2` | 37 | AICPA | SOC 2 Trust Services Criteria |
| `reg_hitrust` | 27 | HITRUST | HITRUST Common Security Framework (healthcare) |
| `reg_cobit` | 45 | ISACA | COBIT 2019 (governance and management of enterprise IT) |
| `reg_coso` | 27 | COSO | Committee of Sponsoring Organizations Internal Control Framework |

### Accounting and audit

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_us_gaap` | 33 | FASB | US Generally Accepted Accounting Principles (ASC codification) |
| `reg_fasb` | 19 | FASB | Financial Accounting Standards Board statements |
| `reg_pcaob` | 28 | PCAOB | Public Company Accounting Oversight Board auditing standards |
| `reg_aicpa` | 21 | AICPA | American Institute of Certified Public Accountants standards |

### Healthcare accreditation and standards

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_joint_commission` | 30 | TJC | Joint Commission hospital accreditation standards |
| `reg_cap` | 21 | CAP | College of American Pathologists laboratory accreditation |
| `reg_clia` | 20 | CMS | Clinical Laboratory Improvement Amendments |
| `reg_usp` | 21 | USP | US Pharmacopeia chapters (drug compounding, packaging, sterility) |

### Engineering and building

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_ashrae` | 23 | ASHRAE | Standards for HVAC, refrigeration, building energy |
| `reg_asme` | 26 | ANSI / ASME | Boiler, pressure vessel, and piping codes |

## EU Regulations and Directives

Binding rules across EU member states, often with extraterritorial reach (a US SaaS targeting EU residents must comply with GDPR, etc.).

### Privacy and digital services

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_eprivacy` | 15 | Member states / EDPB | ePrivacy Directive (cookies, electronic comms) |
| `reg_eu_data_act` | 20 | Commission | EU Data Act (data sharing, switching, public-sector access) |
| `reg_dsa` | 21 | Commission | Digital Services Act (online intermediaries, very large platforms) |
| `reg_dma` | 19 | Commission | Digital Markets Act (gatekeeper obligations) |
| `reg_eu_whistleblower` | 17 | Member states | Whistleblower Protection Directive |

### Cybersecurity and resilience

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_nis2` | 24 | ENISA / member states | NIS2 Directive (network and information security) |
| `reg_dora` | 27 | ESAs | Digital Operational Resilience Act (financial sector ICT risk) |
| `reg_eu_cra` | 20 | Commission | EU Cyber Resilience Act (products with digital elements) |
| `reg_eu_ai_act` | 27 | Commission | EU AI Act (risk-tiered AI system obligations) |

### Financial services

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_mifid2` | 24 | ESMA / national | Markets in Financial Instruments Directive II |
| `reg_solvency2` | 22 | EIOPA | Solvency II (insurance prudential) |
| `reg_psd2` | 19 | EBA | Payment Services Directive 2 (open banking) |

### Health and life sciences

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_mdr` | 22 | EC / notified bodies | EU Medical Device Regulation |
| `reg_ivdr` | 17 | EC / notified bodies | In Vitro Diagnostic Medical Devices Regulation |

### Sustainability and environment

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_csrd` | 25 | Commission / EFRAG | Corporate Sustainability Reporting Directive |
| `reg_cbam` | 18 | Commission | Carbon Border Adjustment Mechanism |
| `reg_sfdr_detail` | 22 | ESAs | Sustainable Finance Disclosure Regulation (detailed RTS) |
| `reg_eu_deforestation` | 20 | Commission | EU Deforestation Regulation |
| `reg_emas` | 25 | Commission | Eco-Management and Audit Scheme |

### Products and chemicals

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_reach` | 19 | ECHA | REACH (registration, evaluation, authorization of chemicals) |
| `reg_rohs` | 22 | EC / member states | RoHS Directive (restriction of hazardous substances) |
| `reg_weee` | 21 | EC / member states | WEEE Directive (waste electrical and electronic equipment) |
| `reg_eu_packaging` | 19 | Commission | EU Packaging and Packaging Waste Regulation |
| `reg_eu_batteries` | 18 | Commission | EU Batteries Regulation |
| `reg_eu_machinery` | 20 | Commission | EU Machinery Regulation |

## ISO Management System Standards

Voluntary international standards that organizations certify against. Each defines a Plan-Do-Check-Act management system for a specific domain. Often combined into integrated management systems (e.g., ISO 9001 + ISO 14001 + ISO 45001).

| System | Codes | Year | Scope |
|--------|-------|------|-------|
| `reg_iso_9001` | 35 | 2015 | Quality management systems |
| `reg_iso_14001` | 29 | 2015 | Environmental management systems |
| `reg_iso_27001` | 30 | 2022 | Information security management |
| `reg_iso_27701` | 27 | 2019 | Privacy information management (extension of 27001) |
| `reg_iso_22000` | 31 | 2018 | Food safety management |
| `reg_iso_45001` | 30 | 2018 | Occupational health and safety |
| `reg_iso_50001` | 26 | 2018 | Energy management |
| `reg_iso_13485` | 28 | 2016 | Medical-device quality management |
| `reg_iso_22301` | 26 | 2019 | Business continuity management |
| `reg_iso_22313` | 24 | 2020 | BCMS implementation guidance (companion to 22301) |
| `reg_iso_20000` | 23 | 2018 | IT service management (aligns with ITIL) |
| `reg_iso_26000` | 22 | 2010 | Social responsibility (guidance, not certifiable) |
| `reg_iso_37001` | 29 | 2016 | Anti-bribery management |
| `reg_iso_42001` | 32 | 2023 | AI management systems (the newest big one) |
| `reg_iso_28000` | 24 | 2022 | Supply chain security management |
| `reg_iso_55001` | 25 | 2014 | Asset management |
| `reg_iso_41001` | 23 | 2018 | Facility management |
| `reg_iso_30401` | 22 | 2018 | Knowledge management |
| `reg_iso_21001` | 31 | 2018 | Educational organization management |
| `reg_iso_39001` | 24 | 2012 | Road traffic safety management |
| `reg_iso_37101` | 23 | 2016 | Sustainable communities |
| `reg_iso_14064` | 20 | various | Greenhouse gas accounting and verification |
| `reg_iso_14040` | 25 | 2006 | Life cycle assessment principles |
| `reg_iso_19011` | 30 | 2018 | Auditing management systems |
| `reg_iso_31010` | 26 | 2019 | Risk assessment techniques |

## Global Treaties and Multilateral Frameworks

Binding international agreements and recommendations adopted by sovereign states.

### Finance and trade

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_basel3` | 24 | BIS / BCBS | Basel III/IV bank capital and liquidity framework |
| `reg_fatf` | 29 | FATF | 40 Recommendations on AML / CFT |
| `reg_wto_sps` | 19 | WTO | Sanitary and Phytosanitary Measures Agreement |
| `reg_wto_tbt` | 17 | WTO | Technical Barriers to Trade Agreement |
| `reg_uncitral` | 20 | UN | UNCITRAL Model Laws (international commerce) |

### Labor and human rights

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_ilo_core` | 16 | ILO | Core labor conventions (forced labor, child labor, discrimination, freedom of association) |
| `reg_ungp` | 22 | UN | UN Guiding Principles on Business and Human Rights |
| `reg_oecd_mne` | 22 | OECD | OECD Guidelines for Multinational Enterprises |

### Environment

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_montreal` | 19 | UNEP | Montreal Protocol (ozone-depleting substances) |
| `reg_paris` | 20 | UNFCCC | Paris Agreement on climate change |
| `reg_kimberley` | 17 | KP Plenary | Kimberley Process (conflict diamonds) |
| `reg_codex` | 22 | FAO / WHO | Codex Alimentarius (food standards) |
| `reg_who_fctc` | 18 | WHO | Framework Convention on Tobacco Control |

### Maritime and aviation

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_unclos` | 25 | UN | UN Convention on the Law of the Sea |
| `reg_marpol` | 20 | IMO | International Convention for the Prevention of Pollution from Ships |
| `reg_solas` | 21 | IMO | International Convention for the Safety of Life at Sea |
| `reg_icao_annex` | 26 | ICAO | ICAO Annexes to the Chicago Convention |

### Project and sustainable finance

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_equator` | 18 | EPFI banks | Equator Principles (project finance environmental and social risk) |
| `reg_ifc_ps` | 21 | IFC | IFC Performance Standards on Environmental and Social Sustainability |

### Intellectual property

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `reg_berne` | 18 | WIPO | Berne Convention for the Protection of Literary and Artistic Works |

## Cross-framework overlaps to know

Several controls and obligations recur across multiple frameworks. This is where downstream tooling pays off most: a single library of "evidence" can map to many frameworks.

| If you have | You substantially satisfy |
|---|---|
| ISO 27001 certified | Most of NIST CSF, big chunks of SOC 2 (Security), HIPAA Security Rule, PCI DSS technical controls |
| SOC 2 Type II | Vendor due-diligence baseline; ISO 27001 control overlap is ~60% |
| NIST 800-171 | CMMC Level 2 baseline (DoD contractors) |
| HITRUST CSF certified | HIPAA + ISO 27001 + NIST CSF + state privacy laws (the framework was designed as an aggregator) |
| GDPR | Most of CCPA / CPRA; ISO 27701 directly extends ISO 27001 to cover GDPR principles |
| ISO 9001 | Foundation for ISO 13485 (medical devices), ISO 22000 (food), AS 9100 (aerospace) - all are 9001 + sector additions |
| Basel III | Solvency II builds the same prudential discipline for insurers |

## Crosswalk navigation

```bash
# Find regulatory frameworks in WoT
GET /api/v1/systems?prefix=reg_

# Browse a specific framework
GET /api/v1/systems/reg_hipaa/nodes
GET /api/v1/systems/reg_iso_27001/nodes

# Search across all regulatory content
GET /api/v1/search?q=encryption&systems=reg_nist_800_53,reg_iso_27001,reg_pci_dss
```

Equivalence edges between regulatory frameworks are not yet wired at scale; this is a high-value follow-up. The cross-framework overlap table above is the manual map; programmatic crosswalks (NIST 800-53 control -> ISO 27001 Annex A control, for example) are queued for a future PR.

## What WoT does not host

- **State-level regulations** other than CCPA / CPRA. The 50 US state privacy / breach-notification laws are out of scope until a downstream product needs them.
- **Country-specific privacy laws** outside the US and EU (LGPD, POPIA, PIPL, etc.). Audit candidates for follow-up if customer demand surfaces.
- **Industry-specific contractual frameworks** with restricted licensing (FAA Part 145 detailed AC content, ISO 15926 industrial process). Behind paywalls; out per the inclusion-policy assessment.
- **Commercial accreditation programs** that are private products of the accreditor (Underwriters Laboratories test programs, J.D. Power scorecards).

## Related reading

- [Process and Activity Frameworks](./process-frameworks.md) - PCF, SCOR, ITIL, COBIT (COBIT especially overlaps the IT-governance subset of this page).
- [Industry Classification Guide](./industry-classification.md) - which NAICS sectors trigger which regulatory regimes.
- [Inclusion Policy](./inclusion-policy.md) - why state-level and country-specific privacy laws are not in WoT yet.
