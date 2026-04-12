"""GDPR Article Taxonomy ingester.

General Data Protection Regulation (EU) 2016/679.
Published by the European Union. Open (EUR-Lex). Hand-coded.
Reference: https://eur-lex.europa.eu/eli/reg/2016/679/oj

Hierarchy (2 levels):
  Chapter  (level 1, code 'gdpr_ch_{N}')   - 11 chapters
  Article  (level 2, code 'gdpr_art_{N}')  - 99 articles (all leaves)

Total: 110 nodes.
"""
from __future__ import annotations

from typing import Optional

# Article-to-chapter mapping: article_number -> chapter_number
# Based on GDPR structure (EUR-Lex 2016/679)
_ARTICLE_TO_CHAPTER: dict[int, int] = {
    # Chapter I: General provisions (Art. 1-4)
    1: 1, 2: 1, 3: 1, 4: 1,
    # Chapter II: Principles (Art. 5-11)
    5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2,
    # Chapter III: Rights of the data subject (Art. 12-23)
    12: 3, 13: 3, 14: 3, 15: 3, 16: 3, 17: 3, 18: 3,
    19: 3, 20: 3, 21: 3, 22: 3, 23: 3,
    # Chapter IV: Controller and processor (Art. 24-43)
    24: 4, 25: 4, 26: 4, 27: 4, 28: 4, 29: 4, 30: 4,
    31: 4, 32: 4, 33: 4, 34: 4, 35: 4, 36: 4, 37: 4,
    38: 4, 39: 4, 40: 4, 41: 4, 42: 4, 43: 4,
    # Chapter V: Transfers of personal data to third countries (Art. 44-49)
    44: 5, 45: 5, 46: 5, 47: 5, 48: 5, 49: 5,
    # Chapter VI: Independent supervisory authorities (Art. 50-59)
    50: 6, 51: 6, 52: 6, 53: 6, 54: 6, 55: 6,
    56: 6, 57: 6, 58: 6, 59: 6,
    # Chapter VII: Cooperation and consistency (Art. 60-76)
    60: 7, 61: 7, 62: 7, 63: 7, 64: 7, 65: 7,
    66: 7, 67: 7, 68: 7, 69: 7, 70: 7, 71: 7,
    72: 7, 73: 7, 74: 7, 75: 7, 76: 7,
    # Chapter VIII: Remedies, liability and penalties (Art. 77-84)
    77: 8, 78: 8, 79: 8, 80: 8, 81: 8, 82: 8, 83: 8, 84: 8,
    # Chapter IX: Provisions relating to specific processing situations (Art. 85-91)
    85: 9, 86: 9, 87: 9, 88: 9, 89: 9, 90: 9, 91: 9,
    # Chapter X: Delegated acts and implementing acts (Art. 92-93)
    92: 10, 93: 10,
    # Chapter XI: Final provisions (Art. 94-99)
    94: 11, 95: 11, 96: 11, 97: 11, 98: 11, 99: 11,
}

# Chapter titles
_CHAPTER_TITLES: dict[int, str] = {
    1:  "Chapter I - General Provisions",
    2:  "Chapter II - Principles",
    3:  "Chapter III - Rights of the Data Subject",
    4:  "Chapter IV - Controller and Processor",
    5:  "Chapter V - Transfers of Personal Data to Third Countries or International Organisations",
    6:  "Chapter VI - Independent Supervisory Authorities",
    7:  "Chapter VII - Cooperation and Consistency",
    8:  "Chapter VIII - Remedies, Liability and Penalties",
    9:  "Chapter IX - Provisions Relating to Specific Processing Situations",
    10: "Chapter X - Delegated Acts and Implementing Acts",
    11: "Chapter XI - Final Provisions",
}

# Article titles (key articles - full titles from GDPR text)
_ARTICLE_TITLES: dict[int, str] = {
    1:  "Subject-matter and objectives",
    2:  "Material scope",
    3:  "Territorial scope",
    4:  "Definitions",
    5:  "Principles relating to processing of personal data",
    6:  "Lawfulness of processing",
    7:  "Conditions for consent",
    8:  "Conditions applicable to child's consent in relation to information society services",
    9:  "Processing of special categories of personal data",
    10: "Processing of personal data relating to criminal convictions and offences",
    11: "Processing which does not require identification",
    12: "Transparent information, communication and modalities for the exercise of rights",
    13: "Information to be provided where personal data are collected from the data subject",
    14: "Information to be provided where personal data have not been obtained from the data subject",
    15: "Right of access by the data subject",
    16: "Right to rectification",
    17: "Right to erasure ('right to be forgotten')",
    18: "Right to restriction of processing",
    19: "Notification obligation regarding rectification or erasure or restriction",
    20: "Right to data portability",
    21: "Right to object",
    22: "Automated individual decision-making, including profiling",
    23: "Restrictions",
    24: "Responsibility of the controller",
    25: "Data protection by design and by default",
    26: "Joint controllers",
    27: "Representatives of controllers or processors not established in the Union",
    28: "Processor",
    29: "Processing under the authority of the controller or processor",
    30: "Records of processing activities",
    31: "Cooperation with the supervisory authority",
    32: "Security of processing",
    33: "Notification of a personal data breach to the supervisory authority",
    34: "Communication of a personal data breach to the data subject",
    35: "Data protection impact assessment",
    36: "Prior consultation",
    37: "Designation of the data protection officer",
    38: "Position of the data protection officer",
    39: "Tasks of the data protection officer",
    40: "Codes of conduct",
    41: "Monitoring of approved codes of conduct",
    42: "Certification",
    43: "Certification bodies",
    44: "General principle for transfers",
    45: "Transfers on the basis of an adequacy decision",
    46: "Transfers subject to appropriate safeguards",
    47: "Binding corporate rules",
    48: "Transfers or disclosures not authorised by Union law",
    49: "Derogations for specific situations",
    50: "International cooperation for the protection of personal data",
    51: "Supervisory authority",
    52: "Independence",
    53: "General conditions for the members of the supervisory authority",
    54: "Rules on the establishment of the supervisory authority",
    55: "Competence",
    56: "Competence of the lead supervisory authority",
    57: "Tasks",
    58: "Powers",
    59: "Activity reports",
    60: "Cooperation between the lead supervisory authority and the other supervisory authorities",
    61: "Mutual assistance",
    62: "Joint operations of supervisory authorities",
    63: "Consistency mechanism",
    64: "Opinion of the Board",
    65: "Dispute resolution by the Board",
    66: "Urgency procedure",
    67: "Exchange of information",
    68: "European Data Protection Board",
    69: "Independence",
    70: "Tasks of the Board",
    71: "Reports",
    72: "Procedure",
    73: "Chair",
    74: "Tasks of the Chair",
    75: "Secretariat",
    76: "Confidentiality",
    77: "Right to lodge a complaint with a supervisory authority",
    78: "Right to an effective judicial remedy against a supervisory authority",
    79: "Right to an effective judicial remedy against a controller or processor",
    80: "Representation of data subjects",
    81: "Suspension of proceedings",
    82: "Right to compensation and liability",
    83: "General conditions for imposing administrative fines",
    84: "Penalties",
    85: "Processing and freedom of expression and information",
    86: "Processing and public access to official documents",
    87: "Processing of the national identification number",
    88: "Processing in the context of employment",
    89: "Safeguards and derogations relating to processing for archiving, research or statistical purposes",
    90: "Obligations of secrecy",
    91: "Existing data protection rules of churches and religious associations",
    92: "Exercise of the delegation",
    93: "Committee procedure",
    94: "Repeal of Directive 95/46/EC",
    95: "Relationship with Directive 2002/58/EC",
    96: "Relationship with previously concluded Agreements",
    97: "Commission reports",
    98: "Review of other Union legal acts on data protection",
    99: "Entry into force and application",
}


def _build_nodes() -> list[tuple[str, str, int, Optional[str]]]:
    """Build the full GDPR node list: 11 chapters + 99 articles."""
    nodes = []

    # Add chapters (level 1, no parent)
    for ch_num in sorted(_CHAPTER_TITLES.keys()):
        nodes.append((
            f"gdpr_ch_{ch_num}",
            _CHAPTER_TITLES[ch_num],
            1,
            None,
        ))

    # Add articles (level 2, parent = chapter)
    for art_num in range(1, 100):
        ch_num = _ARTICLE_TO_CHAPTER[art_num]
        nodes.append((
            f"gdpr_art_{art_num}",
            f"Article {art_num} - {_ARTICLE_TITLES[art_num]}",
            2,
            f"gdpr_ch_{ch_num}",
        ))

    return nodes


GDPR_NODES: list[tuple[str, str, int, Optional[str]]] = _build_nodes()

_SYSTEM_ROW = (
    "gdpr_articles",
    "GDPR Articles",
    "General Data Protection Regulation (EU) 2016/679 - Article Taxonomy",
    "2016/679",
    "European Union",
    "European Union (EUR-Lex)",
)


def _determine_level(code: str) -> int:
    """Return level: 1 for chapters, 2 for articles."""
    if code.startswith("gdpr_ch_"):
        return 1
    return 2


def _determine_parent(code: str) -> Optional[str]:
    """Return parent chapter code for articles; None for chapters."""
    if code.startswith("gdpr_ch_"):
        return None
    # Extract article number and look up chapter
    art_num = int(code.split("_")[-1])
    ch_num = _ARTICLE_TO_CHAPTER.get(art_num)
    if ch_num is None:
        return None
    return f"gdpr_ch_{ch_num}"


async def ingest_gdpr(conn) -> int:
    """Ingest GDPR article taxonomy.

    Hand-coded from EUR-Lex 2016/679 (open).
    Returns 110 (11 chapters + 99 articles).
    """
    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority, node_count)
           VALUES ($1, $2, $3, $4, $5, $6, 0)
           ON CONFLICT (id) DO UPDATE SET node_count = 0""",
        *_SYSTEM_ROW,
    )

    chapter_codes = {code for code, _, level, _ in GDPR_NODES if level == 1}

    rows = [
        (
            "gdpr_articles",
            code,
            title,
            level,
            parent,
            code.split("_")[1],       # sector_code = 'ch' or 'art'
            code not in chapter_codes, # is_leaf: articles are leaves, chapters are not
        )
        for code, title, level, parent in GDPR_NODES
    ]

    await conn.executemany(
        """INSERT INTO classification_node
               (system_id, code, title, level, parent_code, sector_code, is_leaf)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (system_id, code) DO NOTHING""",
        rows,
    )

    count = len(GDPR_NODES)
    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = 'gdpr_articles'",
        count,
    )

    return count
