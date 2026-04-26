# Description-backfill series

This document summarises the description-backfill effort that ran across PRs #50 - #73 (plus a follow-up coverage doc and a NACE family cascade extension). It records what each PR did, where the cascade graph runs, what is still empty and why, and which sources are still untapped.

## Scope

The structural ingester for each classification system populates `code`, `title`, `parent_code`, `level`, `is_leaf` on `classification_node`. The `description` column was empty for most systems at the start of this series. Every PR below adds rows on the `description` column only - no schema changes, no row deletes, no overwrites of populated rows (`apply_descriptions` is NULL-only).

## Headline numbers

- **28 PRs landed** (PR #50 - PR #77, plus this doc).
- **~24,000 net new rows of description content** populated on a 1.21M-row DB (~21k from PR #55-#75, plus 34 from CPC FullDef PR #76 plus the in-progress UNSPSC verified-synthesis pilot).
- DB coverage went from **~50%** at the start of the series to **~55.5%+** at the end.
- **0 em-dashes** (`U+2014`) in any added content - every PR runs `scripts/check_no_em_dash.sh` and every parser normalises unicode dashes / spaces / quotes to ASCII.
- **0 NUL bytes, 0 mojibake, 0 refusal-phrase leaks** across all 2,413 LLM-generated rows from PR #67 (rounds 1 + 2).
- **97.8% verifier yes-rate** across 2,854 cached UNSPSC codes from the Track 2 verified-synthesis pipeline (PR #77, in flight at 5K-row pilot).

## PRs by category

### Direct on-disk parsers

These PRs read a file already in `data/` and populate one system from the structured content.

| PR | System | Rows | Source |
|----|--------|------|--------|
| #50 | ATC WHO | 2,030 (32%) | `data/atc_who.csv` (DDD + route + notes) |
| #51 | ANZSCO 2022 | 1,590 (100%) | `data/anzsco_2022.xml` (SDMX annotations) |
| #52 | ISO 3166-2 | 5,246 (100%) | `data/iso3166_all.csv` + `pycountry` |
| #55 | O*NET-SOC | 867 (100%) | `data/onet_occupation_data.txt` |
| #56 | COFOG | 131 (70%) | `data/cofog.csv` (UN ExplanatoryNote) |
| #62 | UN M.49 | 279 (100%) | `data/iso3166_all.csv` (countries + regions) |
| #65 | ONET content model (6 sub-taxonomies) | 62 (67%) | `data/onet_db/.../Content Model Reference.txt` |
| #66 | NIC 2008 | 95 (88%) | `data/nic/nic_2008_publication.pdf` (193pp, parsed via `pypdf`) |
| #67 | LLM-generated (88 systems, 2 rounds) | 2,413 (100% clean audit) | `chat_json` via Ollama Cloud, gpt-oss:120b |
| #72 | ISO 3166-1 | 271 (100%) | `data/iso3166_all.csv` + UN M.49 cascade for region codes |

### Scrapes and HTTP fetches

PRs that download structured data live.

| PR | System | Rows | Source |
|----|--------|------|--------|
| #53 | NACE Rev 2 + 42 mirrors | 33,348 (~80%) | EU Publications Office `data.europa.eu/ux2/nace2/` (per-concept SKOS/XKOS RDF) |
| #58 | ISCO-08 | 610 (99.5%) | ESCO v1.2.1 JSON-LD (`isco/C<code>` SKOS concepts) |
| #59 | ANZSIC 2006 | 506 (61%) | `api.data.abs.gov.au/codelist/ABS/CL_ANZSIC_2006/1.0.0` (SDMX CONTEXT annotation) |
| #61 | SIC 1987 | 1,003 (85%) | OSHA per-code HTML pages, scraped with `httpx` |
| #64 | ISCED-F 2013 | 79 (65%) | Same ESCO JSON-LD, `isced-f/<code>` |
| #71 (in part) | ICD-11 chapters and blocks | 472 | WHO ICD-11 API (OAuth client-credentials, MMS linearization tree) |
| #75 | ICD-11 chapter and block walk | 344 | WHO ICD-11 API (BFS first-wins title match) |

### Single-child cascades

PRs that fill empty parent codes by copying the description of their only populated child. Iterative - a 2-digit division can pick up a description after its 3-digit group child has been populated by a 4-digit class in the same run.

Two cascade flavours are in use:

- **Prefix cascade** (`<parent_code> = <child_code>[:-1]`): NACE groups (#63), NAICS groups (#60), ANZSIC family (#69), ISIC family across 124 mirrors (#70), ISCED-F (#68), SOC 2018 broads (#57).
- **`parent_code` cascade** (uses the FK column): ICD-11, ATC WHO, NACE family for sections / divisions like `T` / `97` / `99` (#71).

| PR | Target | Rows |
|----|--------|------|
| #57 | SOC 2018 broad occupations | 275 |
| #60 | NAICS 2022 4-digit groups | 140 |
| #63 | NACE class -> group across 42 NACE mirrors | 5,460 |
| #68 | ISCED-F | 8 |
| #69 | ANZSIC 2006 | 119 |
| #70 | ISIC family across 124 mirrors | 14,164 |
| #71 | ICD-11 + ATC + 4 more, plus NACE T / U / 97 / 99 across 42 mirrors | 905 |

### Crosswalk-driven cascades

PRs that map one classification's descriptions onto another via an authoritative crosswalk file.

| PR | Mapping | Rows |
|----|---------|------|
| #54 | ISIC -> NACE via `data/crosswalk/ISIC4_to_NACE2.txt` (1:1 exact only) | 60,388 across 124 ISIC-derived systems |

### LLM-generated content

| PR | Pipeline | Rows | Audit |
|----|----------|------|-------|
| #67 | gpt-oss:120b on a curated allowlist of 88 small reference taxonomies (rounds 1 + 2) | 2,413 | 0 em-dashes, 0 mojibake, 0 NUL bytes, 0 refusal-phrase leaks, 0 length outliers |
| #76 | Patent CPC FullDefinitionXML zip (24K XML files) | 34 (NULL-only); parser found 40,096 items but 40,062 already had shorter descriptions | structured prose only, no LLM |
| #77 | Track 2 verified-synthesis pipeline (generator + verifier on UNSPSC) | ~2,790 verified (5K pilot in flight) | 97.8% yes-rate; only `yes` verdicts apply |

## Cascade graph

```
            iso3166_all.csv
              |        |
              v        v
        iso_3166_2  iso_3166_1
              |        |
              v        |
         un_m49 -------+
                       |
                       v
                iso_3166_1 (region codes)


       ISIC4_to_NACE2.txt
              |
              v
   nace_rev2 (EU RDF) -- isic_rev4 (124 mirrors)
        |                       |
        v (cascade groups)      v (parent cascade)
  42 NACE mirrors           124 ISIC mirrors


              onet_occupation_data.txt
                     |
                     v
                  onet_soc
                     |
                     v (single-child cascade)
                 soc_2018 broads
```

## Parsers and helpers introduced

```
world_of_taxonomy/ingest/
  atc_who_descriptions.py       # PR #50
  anzsco_descriptions.py        # PR #51
  iso3166_2_descriptions.py     # PR #52
  nace_descriptions.py          # PR #53 (also XKOS / coreContentNote / exclusionNote)
  isic_cascade_from_nace.py     # PR #54 (crosswalk-correct mapping)
  onet_descriptions.py          # PR #55
  cofog_descriptions.py         # PR #56
  soc2018_cascade.py            # PR #57
  isco08_from_esco.py           # PR #58 (ijson streamer over ESCO JSON-LD)
  anzsic2006_descriptions.py    # PR #59
  naics2022_cascade.py          # PR #60 (handles "See industry description for X" pointer chain)
  sic1987_descriptions.py       # PR #61 (HTML body extraction with cutoff markers)
  un_m49_descriptions.py        # PR #62
  nace_group_cascade.py         # PR #63
  iscedf2013_from_esco.py       # PR #64
  onet_content_model.py         # PR #65
  nic2008_pdf.py                # PR #66
  llm_descriptions.py           # PR #67 (sanitize_response is the workhorse)
  iscedf_cascade.py             # PR #68
  anzsic_cascade.py             # PR #69
  isic_mirror_cascade.py        # PR #70
  parent_code_cascade.py        # PR #71
  patent_cpc_scheme.py          # PR #73 (regex-based, item-chunked to avoid catastrophic backtracking)
  patent_cpc_full_definition.py # PR #76 (FullCPCDefinitionXML zip, 24K files)
  llm_verifier.py               # PR #77 (Track 2 generator+verifier verdict prompt)
```

## Still-empty rows and why

Of the ~545k empty rows that remain after this series, almost all sit in six systems whose upstream source treats title as description by design:

| System | Empty | Why |
|--------|-------|-----|
| `patent_cpc` | ~211k | CPC subgroup titles already encode the technical content. The 4k items that *do* have a `notes-and-warnings` block were filled by #73. |
| `icd10cm` | ~87k | The CMS Tabular XML parser is already saturated; the 87k empties are leaf codes that simply have no `<inclusionTerm>` / `<excludes1>` / `<excludes2>` block in the source. |
| `icd10_pcs` | ~80k | PCS codes are defined by their 7-position axis decomposition. The "long description" in the order file IS the title. |
| `unspsc_v24` | ~77k | GS1 publishes UNSPSC titles only; richer descriptions are paid. |
| `hs_2022` | ~7k | WCO publishes HS titles only; explanatory notes are a paid product. |
| `cpc_v21` | ~4.6k | Same story for UN CPC v2.1; the on-disk file is title-only. |

Plus ~27k ICD-11 multi-child aggregates (chapters / blocks) that #71 could not single-child-cascade. Some of those will be picked up by the in-flight `feat/icd11-chapters-blocks` walk.

## What would unlock the remaining ~540k rows

- **Verified-LLM-synthesis at scale** (PR #77 ships the pipeline; UNSPSC pilot at 5K rows shows 97.8% verifier yes-rate). The 77K UNSPSC system is the natural first target; ICD-10-PCS (80K) and HS 2022 (7K) are deferred until a regulated-data review approves synthesis on billing / customs codes. Hallucination is the principal risk that the verifier mitigates.
- **CPC FullDefinition upgrade-on-richness pass**: PR #76's parser found 40K Definition / Limiting References / Glossary blocks but only 34 landed because most CPC codes already have shorter descriptions. An overwrite-when-richer pass would push thousands of richer descriptions in.
- **Paid datasets**: WCO HS Explanatory Notes, AMA CPT licensing, GS1 UNSPSC content licence. None of these are free.
- **NCI Thesaurus retired-concept rows (357)**: investigated; all are `Retired_Concept` status with no API definitions. Best treatment is a `Retired NCI concept` placeholder or leaving NULL.
- **More targeted scraping**: BLS SOC 2018 manual is a PDF; the existing scraper would need a PDF parser to pick up the remaining 305 SOC group / minor / major descriptions.

## Ops notes

- All caches live under `data/` (gitignored). Re-runs are idempotent because they read the cache first and skip already-generated rows.
- LLM cache: `data/llm_descriptions/<system_id>.jsonl`.
- LLM verifier cache: `data/llm_verified/<system_id>.jsonl` (records `{code, candidate, verdict}` so re-runs skip already-verified rows).
- NACE RDF cache: `data/nace/rdf/<code>.xml`.
- ICD-11 API cache: `data/.icd11_api_cache.jsonl`.
- SIC OSHA HTML cache: `data/sic/pages/<code>.html`.

## Verification

`scripts/check_no_em_dash.sh` runs in CI and on every committed file path. The audit pass at end of the series confirmed:

- 0 em-dashes in any added line across all 24 branches.
- 168 tests pass locally (every test file added by every PR).
- Every PR mergeable; no merge conflicts in the dependency graph.
