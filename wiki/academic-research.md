# Academic and Research Classification

> **TL;DR:** WoT hosts 30 academic and research classification systems: subject taxonomies for preprints (arXiv) and journals (Scopus ASJC, WoS Categories, ERA FoR, ANZSRC FOR/SEO, FORD Frascati, JEL, MSC, PACS, ACM CCS), library classifications (Dewey, UDC, LCC, LCSH, Getty AAT, UNESCO Thesaurus), education-quality and accreditation frameworks (AACSB, ABET), education-level frameworks (EQF, AQF, NQF UK, NGSS, CCSS, Bloom Taxonomy), and skills/competence frameworks (DigComp, e-CF, SFIA, LinkedIn Skills, WorldSkills).

---

## Subject classification (research output anchors)

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `arxiv_taxonomy` | 165 | arXiv / Cornell | Preprint subject categories (cs.LG, math.AG, etc.) |
| `msc_2020` | 92 | AMS | Mathematics Subject Classification |
| `pacs` | 70 | AIP | Physics and Astronomy Classification (legacy, still cited) |
| `acm_ccs` | 67 | ACM | ACM Computing Classification System 2012 |
| `jel` | 98 | American Economic Association | Journal of Economic Literature codes |
| `scopus_asjc` | 28 | Elsevier | Scopus All Science Journal Classification |
| `wos_categories` | 25 | Clarivate | Web of Science subject categories |
| `era_for` | 24 | ARC (Australia) | Excellence in Research for Australia, Fields of Research |
| `anzsrc_for_2020` | 166 | ABS / Stats NZ | ANZSRC Fields of Research 2020 |
| `anzsrc_seo` | 17 | ABS / Stats NZ | ANZSRC Socio-Economic Objectives |
| `ford_frascati` | 48 | OECD | Fields of Research and Development (Frascati Manual 2015) |

**Use this layer when**: classifying preprints, journal articles, grant applications, or research-output reporting.

## Library classification

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `dewey_decimal` | 11 | OCLC | Dewey Decimal Classification (skeleton: 10 main classes + general) |
| `udc` | 11 | UDC Consortium | Universal Decimal Classification (skeleton) |
| `lcc` | 111 | Library of Congress | Library of Congress Classification |
| `lcsh` | 20 | Library of Congress | LCSH Subject Headings (skeleton) |
| `getty_aat` | 14 | Getty Research Institute | Art and Architecture Thesaurus (skeleton) |
| `unesco_thesaurus` | 15 | UNESCO | UNESCO Thesaurus (skeleton) |

**Use this layer when**: cataloging or anchoring against bibliographic / archival metadata.

## Education accreditation, levels, and pedagogy

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `aacsb` | 14 | AACSB International | Business school accreditation standards |
| `abet` | 14 | ABET | Engineering / computing / applied-science program accreditation |
| `eqf` | 13 | European Commission | European Qualifications Framework (8 levels) |
| `aqf` | 14 | Australia | Australian Qualifications Framework |
| `nqf_uk` | 14 | UK | UK National Qualifications Framework |
| `bloom_taxonomy` | 14 | Bloom et al. | Bloom's Taxonomy of educational objectives (revised 2001) |
| `ngss` | 14 | Achieve Inc. (US) | Next Generation Science Standards |
| `ccss` | 18 | NGA / CCSSO (US) | Common Core State Standards |

## Skills and competence frameworks

| System | Codes | Authority | Scope |
|--------|-------|-----------|-------|
| `digcomp_22` | 27 | European Commission JRC | Digital Competence Framework for Citizens 2.2 |
| `ecf_v4` | 35 | CEN (EU) | European e-Competence Framework v4 |
| `sfia_v8` | 14 | SFIA Foundation | Skills Framework for the Information Age v8 |
| `linkedin_skills` | 17 | LinkedIn | LinkedIn Skills Taxonomy (skeleton; mapped from public docs) |
| `worldskills` | 14 | WorldSkills International | Skill competition categories |

These overlap with [Occupation Systems](./occupation-systems.md) (ESCO Skills, O*NET Knowledge / Abilities); the difference is granularity. ESCO Skills has 14K entries; SFIA / e-CF are framework-level (~30 each), suited for capability assessment rather than skill tagging.

## Decision tree

| What you are doing | Use |
|---|---|
| Tagging a preprint | `arxiv_taxonomy` (CS / math / physics) or `msc_2020` (math) |
| Classifying a journal article | `scopus_asjc` or `wos_categories` |
| Funding agency reporting (US/EU) | `ford_frascati` (OECD) or `era_for` / `anzsrc_*` (Australia) |
| Cataloging a book in a library | `dewey_decimal`, `udc`, or `lcc` |
| Subject heading on a record | `lcsh`, `unesco_thesaurus`, `getty_aat` |
| Anchoring a course / qualification level | `eqf`, `aqf`, `nqf_uk`, or local equivalent |
| Accrediting a business school | `aacsb` |
| Accrediting an engineering program | `abet` |
| Designing learning objectives | `bloom_taxonomy` + `ngss` / `ccss` |
| Assessing IT capability | `sfia_v8` or `ecf_v4` |
| Assessing digital citizenship | `digcomp_22` |

## Related reading

- [Occupation Systems](./occupation-systems.md) - skills frameworks crossover (ESCO, O*NET).
- [Web Vocabularies](./web-vocabularies.md) - schema.org `Course` and `EducationalOccupationalProgram` types map to these.
- [Inclusion Policy](./inclusion-policy.md) - many academic taxonomies are skeletons; rationale documented.
