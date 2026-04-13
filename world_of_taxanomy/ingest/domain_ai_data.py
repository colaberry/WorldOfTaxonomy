"""AI and Data domain taxonomy ingester.

Organizes artificial intelligence and data sector types aligned with
NAICS 5415 (Computer systems design), NAICS 5182 (Data processing),
and NAICS 5191 (Internet publishing/broadcasting).

Code prefix: dai_
Categories: AI model types, data infrastructure, AI verticals, MLOps/governance.

Hand-coded. Public domain.
"""
from __future__ import annotations

from typing import Optional

# (code, title, level, parent_code)
AI_NODES: list[tuple[str, str, int, Optional[str]]] = [
    # -- AI Model Types --
    ("dai_model",           "AI Model Types",                                        1, None),
    ("dai_model_found",     "Foundation Models (large pre-trained LLMs, VLMs)",     2, "dai_model"),
    ("dai_model_gen",       "Generative AI (text, image, video, audio, code gen)",  2, "dai_model"),
    ("dai_model_discrim",   "Discriminative Models (classifiers, regression)",      2, "dai_model"),
    ("dai_model_rl",        "Reinforcement Learning (RL, RLHF, multi-agent)",       2, "dai_model"),
    ("dai_model_multi",     "Multimodal AI (vision-language, audio-visual models)", 2, "dai_model"),
    ("dai_model_edge",      "Edge and Embedded AI (TinyML, on-device inference)",   2, "dai_model"),

    # -- Data Infrastructure --
    ("dai_infra",           "Data Infrastructure",                                   1, None),
    ("dai_infra_lake",      "Data Lakes and Lakehouses (S3, Databricks, Iceberg)",  2, "dai_infra"),
    ("dai_infra_warehouse", "Data Warehouses (Snowflake, BigQuery, Redshift)",      2, "dai_infra"),
    ("dai_infra_pipeline",  "Data Pipelines and ETL/ELT (Airflow, dbt, Fivetran)", 2, "dai_infra"),
    ("dai_infra_vector",    "Vector Databases (Pinecone, Weaviate, pgvector)",      2, "dai_infra"),
    ("dai_infra_stream",    "Streaming and Real-Time Data (Kafka, Flink, Kinesis)", 2, "dai_infra"),

    # -- AI Application Verticals --
    ("dai_vert",            "AI Application Verticals",                              1, None),
    ("dai_vert_health",     "AI in Healthcare (clinical NLP, imaging AI, genomics)", 2, "dai_vert"),
    ("dai_vert_finance",    "AI in Financial Services (fraud, trading, risk)",       2, "dai_vert"),
    ("dai_vert_logistics",  "AI in Logistics (route optimization, demand forecast)", 2, "dai_vert"),
    ("dai_vert_mfg",        "AI in Manufacturing (predictive maintenance, QC)",     2, "dai_vert"),
    ("dai_vert_legal",      "AI in Legal and Compliance (contract AI, regulatory)", 2, "dai_vert"),
    ("dai_vert_science",    "AI for Science (drug discovery, materials, climate)",  2, "dai_vert"),

    # -- MLOps and AI Governance --
    ("dai_ops",             "MLOps and AI Governance",                               1, None),
    ("dai_ops_registry",    "Model Registry and Versioning",                        2, "dai_ops"),
    ("dai_ops_lineage",     "Data Lineage and Provenance",                          2, "dai_ops"),
    ("dai_ops_observe",     "AI Observability and Monitoring",                      2, "dai_ops"),
    ("dai_ops_govern",      "AI Governance, Bias Detection and Fairness",           2, "dai_ops"),
]

_DOMAIN_ROW = (
    "domain_ai_data",
    "AI and Data Types",
    "AI model types, data infrastructure, AI application verticals, "
    "MLOps and AI governance taxonomy",
    "WorldOfTaxanomy",
    None,
)

# NAICS prefixes: 5415 (Computer systems), 5182 (Data processing), 5191 (Internet)
_NAICS_PREFIXES = ["5415", "5182", "5191"]


def _determine_level(code: str) -> int:
    """Return 1 for top categories, 2 for specific AI/data types."""
    return 1 if len(code.split("_")) == 2 else 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent category code, or None for top-level categories."""
    parts = code.split("_")
    if len(parts) <= 2:
        return None
    return "_".join(parts[:2])


async def ingest_domain_ai_data(conn) -> int:
    """Ingest AI and Data domain taxonomy.

    Registers in domain_taxonomy, stores nodes in classification_node
    (system_id='domain_ai_data'), and links NAICS 5415/5182/5191 nodes
    via node_taxonomy_link.

    Returns total node count.
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        "domain_ai_data",
        "AI and Data Types",
        "AI model types, data infrastructure, AI application verticals, "
        "MLOps and AI governance taxonomy",
        "1.0",
        "Global",
        "WorldOfTaxanomy",
    )

    await conn.execute(
        """INSERT INTO domain_taxonomy
               (id, name, full_name, authority, url, code_count)
           VALUES ($1, $2, $3, $4, $5, 0)
           ON CONFLICT (id) DO UPDATE SET code_count = 0""",
        *_DOMAIN_ROW,
    )

    parent_codes = {parent for _, _, _, parent in AI_NODES if parent is not None}

    rows = [
        (
            "domain_ai_data",
            code,
            title,
            level,
            parent,
            code.split("_")[1],
            code not in parent_codes,
        )
        for code, title, level, parent in AI_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(AI_NODES)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'domain_ai_data'",
        count,
    )
    await conn.execute(
        "UPDATE domain_taxonomy SET code_count = $1 WHERE id = 'domain_ai_data'",
        count,
    )

    naics_codes = [
        row["code"]
        for prefix in _NAICS_PREFIXES
        for row in await conn.fetch(
            "SELECT code FROM classification_node "
            "WHERE system_id = 'naics_2022' AND code LIKE $1",
            prefix + "%",
        )
    ]

    if naics_codes:
        await conn.executemany(
            """INSERT INTO node_taxonomy_link
                   (system_id, node_code, taxonomy_id, relevance)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (system_id, node_code, taxonomy_id) DO NOTHING""",
            [("naics_2022", code, "domain_ai_data", "primary") for code in naics_codes],
        )

    return count
