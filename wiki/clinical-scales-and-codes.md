# Clinical Scales and Specialty Codes

> **TL;DR:** Companion to [Medical Coding](./medical-coding.md). Where that page covers the major disease and lab classifications (ICD-10/11, MeSH, LOINC, ATC, SNOMED CT), this page catalogs the 40 supporting clinical scales and specialty codes WoT hosts: bedside / point-of-care scales (APGAR, ASA Physical Status, BMI, Bristol Stool, Pain Scale, Glasgow Coma — coming soon — Mohs hardness for skin pathology), national / regional ICD variants (ICD-10-CM not duplicated here, but ICD-10-CA / GM / AM and ICD-O-3, ICF, ICHI, ICPC-2), procedure / billing codes (CPT, HCPCS L2/L3, NUCC HCPT, MS-DRG, G-DRG), drug and medication codes (RxNorm, NDC, EDQM Dosage Forms), nursing taxonomies (NANDA-I, NIC Nursing, ICN Nursing), specialty registries (NCI Thesaurus, OMIM, Orphanet, GMDN, FHIR Resources, DICOM Modality), and quality measure frameworks (HEDIS, CMS Star Ratings, CTCAE, GBD Causes, WHO Essential Medicines, CDC Vaccine Schedule, DSM-5).

---

## Bedside and point-of-care scales

Small bounded enumerations clinicians use at every shift.

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `apgar_score` | 12 | AAP | APGAR newborn assessment (Appearance / Pulse / Grimace / Activity / Respiration; 0-2 each, 0-10 total) |
| `asa_physical` | 11 | ASA | American Society of Anesthesiologists Physical Status (ASA I-VI) |
| `bmi_categories` | 11 | WHO | Body Mass Index categories (underweight / normal / overweight / obese class I-III) |
| `blood_types` | 14 | various | ABO + Rh blood types |
| `bristol_stool` | 11 | NHS / Lewis | Bristol Stool Form Scale (Type 1-7) |
| `pain_scale` | 12 | various | Numeric Pain Rating Scale (0-10) and named scales |
| `mohs_hardness` | 11 | Mohs | Mineralogical hardness scale (used in dermatopathology and materials) |

These score-style scales are universally used and trivially small; they're in WoT primarily so downstream classifiers can resolve "ASA III" or "BMI obese class II" against an authoritative anchor.

## ICD national variants

WoT hosts ICD-10-CM (US, separately listed) and ICD-11 in [Medical Coding](./medical-coding.md). National variants:

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `icd10_ca` | 23 | CIHI | Canadian ICD-10 modification (skeleton; Canadian Institute for Health Information) |
| `icd10_gm` | 51 | DIMDI / BfArM | German ICD-10 modification |
| `icd10_am` | 52 | IHACPA | Australian ICD-10 modification |
| `icdo3` | 115 | WHO | International Classification of Diseases for Oncology, 3rd ed. |
| `icf` | 34 | WHO | International Classification of Functioning, Disability and Health |
| `ichi_who` | 15 | WHO | International Classification of Health Interventions |
| `icpc2` | 18 | WONCA / WHO | International Classification of Primary Care, 2nd ed. |

## Procedure and billing codes

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `cpt_ama` | 18 | AMA | Current Procedural Terminology (skeleton; full CPT requires AMA license) |
| `hcpcs_l2` | 59 | CMS | Healthcare Common Procedure Coding System Level II (durable medical equipment, drugs, supplies) |
| `hcpcs_l3` | 13 | CMS / state Medicaid | HCPCS Level III (state-specific, legacy) |
| `nucc_hcpt` | 94 | NUCC | Healthcare Provider Taxonomy (provider type / specialty) |
| `ms_drg` | 50 | CMS | Medicare Severity Diagnosis Related Groups (US inpatient billing) |
| `g_drg` | 26 | InEK | German Diagnosis Related Groups |

## Drug, dosage, and medication

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `rxnorm` | 16 | NLM | RxNorm normalized drug-name standard (skeleton; full corpus is large) |
| `ndc_fda` | 112,077 | FDA | National Drug Code (every US-marketed drug product) |
| `edqm_dosage` | 17 | EDQM (Council of Europe) | Standard Terms for pharmaceutical dose forms / routes / containers |
| `who_essential_med` | 27 | WHO | WHO Model List of Essential Medicines (categories) |
| `cdc_vaccine` | 18 | CDC | CDC vaccine schedule categories |

## Nursing taxonomies

Nursing has its own controlled vocabularies for diagnoses and interventions.

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `nanda_nursing_dx` | 14 | NANDA-I | NANDA International nursing diagnoses (skeleton) |
| `nic_nursing_intv` | 14 | Iowa | Nursing Interventions Classification (skeleton) |
| `icn_nursing` | 14 | ICN | International Classification for Nursing Practice (ICNP, skeleton) |

## Specialty registries and large reference works

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `nci_thesaurus` | 211,072 | NCI | NCI Thesaurus (cancer-research terminology, the largest health system in WoT) |
| `omim` | 14 | Johns Hopkins / NCBI | Online Mendelian Inheritance in Man (skeleton; categories of genetic disorders) |
| `orphanet` | 16 | INSERM | Orphanet rare-disease classification (skeleton) |
| `gmdn` | 17 | GMDN Agency | Global Medical Device Nomenclature |
| `dicom_modality` | 16 | NEMA / DICOM | Standard imaging modality codes (CT, MR, US, etc.) |
| `fhir_resources` | 15 | HL7 | FHIR resource type catalog (Patient, Encounter, Observation, etc.) |

## Quality, outcome, and population-health measures

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `hedis` | 15 | NCQA | Healthcare Effectiveness Data and Information Set quality measures |
| `cms_star` | 13 | CMS | CMS Star Ratings categories (Medicare Advantage, hospitals, nursing homes) |
| `ctcae` | 27 | NCI | Common Terminology Criteria for Adverse Events (clinical-trial AE grading) |
| `gbd_cause` | 23 | IHME | Global Burden of Disease cause hierarchy |
| `dsm5` | 21 | APA | Diagnostic and Statistical Manual of Mental Disorders 5th ed. (skeleton) |

## Decision tree

| What you are doing | Use |
|---|---|
| Newborn assessment | `apgar_score` |
| Pre-anesthesia risk assessment | `asa_physical` |
| Adult-weight category | `bmi_categories` |
| Pain assessment | `pain_scale` |
| Cancer pathology coding | `icdo3` |
| Disability and functioning assessment | `icf` |
| Primary-care complaint coding | `icpc2` |
| Health intervention coding | `ichi_who` |
| US inpatient billing | `ms_drg` + `cpt_ama` + `hcpcs_l2` |
| US drug-product identification | `ndc_fda` |
| Pharmaceutical dose-form standard | `edqm_dosage` |
| Provider type classification | `nucc_hcpt` |
| Imaging study modality | `dicom_modality` |
| Cancer terminology lookup | `nci_thesaurus` |
| Rare-disease lookup | `orphanet` + `omim` |
| Adverse-event grading in trials | `ctcae` |
| Global burden of disease analysis | `gbd_cause` |
| FHIR resource modeling | `fhir_resources` |
| Quality reporting (US Medicare) | `hedis` + `cms_star` |
| Vaccine scheduling (US) | `cdc_vaccine` |
| Mental-health diagnosis | `dsm5` (skeleton; pair with ICD-10/11 mental-health chapters) |

## Related reading

- [Medical Coding](./medical-coding.md) - the major disease and lab classifications (ICD-10/11, MeSH, LOINC, ATC, SNOMED CT, NDC).
- [Regulatory Standards](./regulatory-standards.md) - HIPAA, FDA 21 CFR, DEA, Joint Commission, CAP, CLIA, USP.
- [Inclusion Policy](./inclusion-policy.md) - many clinical systems are skeletons; rationale documented.
