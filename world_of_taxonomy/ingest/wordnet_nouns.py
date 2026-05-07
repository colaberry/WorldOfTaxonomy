"""WordNet noun hypernym tree ingester.

Source: NLTK's WordNet 3.1 corpus (Princeton WordNet).
The Princeton WordNet noun database contains ~82,115 synsets organized
into a hypernym tree rooted at entity.n.01. The tree comes natively
from the publisher; descriptions are the synset glosses (100% coverage).

Hierarchy: hypernym chains rooted at entity.n.01. Instance synsets
(proper nouns like Aristotle.n.01) use instance_hypernyms instead of
hypernyms; both are treated as valid parent edges. Multi-hypernym
synsets (~1.7%) keep the first listed hypernym as the canonical
hierarchy edge; alternative parents are noted in the description.

Verbs, adjectives, and adverbs are NOT ingested. The hypernym relation
is only well-defined for nouns and verbs in WordNet, and verbs are
queued for a follow-up if they prove valuable.

License: WordNet License (Princeton WordNet, BSD-style); the NLTK
wrapper preserves the original license terms.

Verdict against the WoT inclusion policy:
    1. Published and externally maintained: yes (Princeton, since 1985)
    2. Stable identifiers: yes (synset IDs like 'dog.n.01')
    3. Enumerated/hierarchical: yes (single rooted tree at entity.n.01)
    4. Practical size: yes (~82K, well under 500K cap)
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

from world_of_taxonomy.ingest.hash_util import sha256_of_file


# ── Provenance constants ─────────────────────────────────────────

_SYSTEM_ROW = (
    "wordnet_nouns",
    "WordNet (Nouns)",
    "Princeton WordNet 3.1 - Noun Hypernym Tree",
    "3.1",
    "Global",
    "Princeton University",
)
_SOURCE_URL = "https://wordnet.princeton.edu/"
_DATA_PROVENANCE = "official_download"
_LICENSE = "WordNet License (BSD-style)"
_EXPECTED_MIN = 70_000

CHUNK = 1000
ENTITY_ROOT = "entity.n.01"


# ── Parser ──────────────────────────────────────────────────────


def parse_wordnet_nouns() -> List[Tuple[str, str, int, Optional[str], Optional[str]]]:
    """Parse WordNet's noun hypernym tree into WoT node tuples.

    Returns: list of (code, title, level, parent_code, description).

    Reads from the NLTK WordNet corpus (lazy-loaded on first access).
    Filters to noun synsets only. Treats both hypernyms and
    instance_hypernyms as valid parent edges; first listed is canonical.
    Multi-parent synsets get alternatives appended to the description.
    """
    from nltk.corpus import wordnet as wn

    synsets = list(wn.all_synsets("n"))
    primary_parent: Dict[str, Optional[str]] = {}
    extra_parents: Dict[str, List[str]] = defaultdict(list)
    title_of: Dict[str, str] = {}
    desc_of: Dict[str, str] = {}

    for s in synsets:
        code = s.name()
        # Title from the first lemma name, with underscores -> spaces.
        # Falls back to the synset code base if no lemmas (rare).
        lemmas = s.lemma_names()
        title = lemmas[0].replace("_", " ") if lemmas else code.split(".", 1)[0].replace("_", " ")
        title_of[code] = _clean(title)
        desc_of[code] = _clean(s.definition() or "")
        # Combine hypernyms + instance_hypernyms; preserve order
        parents = [h.name() for h in s.hypernyms()] + [
            h.name() for h in s.instance_hypernyms()
        ]
        if parents:
            primary_parent[code] = parents[0]
            if len(parents) > 1:
                extra_parents[code] = parents[1:]
        else:
            primary_parent[code] = None

    # Sanity: every parent reference should resolve to a code we have.
    valid_codes = set(primary_parent)
    for code in list(primary_parent):
        p = primary_parent[code]
        if p is not None and p not in valid_codes:
            primary_parent[code] = None
        extra_parents[code] = [x for x in extra_parents.get(code, []) if x in valid_codes]

    # Append extra parents to description for the multi-parent synsets.
    for code, extras in extra_parents.items():
        if not extras:
            continue
        base = desc_of.get(code, "") or ""
        suffix = f" Also a hyponym of: {', '.join(extras)}."
        desc_of[code] = (base + suffix).strip()

    # BFS from roots to compute level.
    level: Dict[str, int] = {}
    children_of: Dict[str, List[str]] = defaultdict(list)
    for code, parent in primary_parent.items():
        if parent is not None:
            children_of[parent].append(code)
    roots = [c for c, p in primary_parent.items() if p is None]
    queue = deque(roots)
    for r in roots:
        level[r] = 1
    while queue:
        cur = queue.popleft()
        for child in children_of.get(cur, []):
            if child not in level:
                level[child] = level[cur] + 1
                queue.append(child)
    for code in primary_parent:
        level.setdefault(code, 1)

    nodes: List[Tuple[str, str, int, Optional[str], Optional[str]]] = []
    for code in primary_parent:
        nodes.append((
            code,
            title_of.get(code, code),
            level.get(code, 1),
            primary_parent.get(code),
            desc_of.get(code) or None,
        ))
    nodes.sort(key=lambda r: (r[2], r[0]))
    return nodes


def _clean(s: str) -> str:
    if not s:
        return s
    return s.replace("\u2014", "-").replace("\n", " ").strip()


# ── Ingestion ────────────────────────────────────────────────────


async def ingest_wordnet_nouns(conn) -> int:
    """Ingest WordNet noun hypernym tree.

    Args:
        conn: asyncpg connection.

    Returns:
        Number of nodes ingested.
    """
    nodes = parse_wordnet_nouns()
    if len(nodes) < _EXPECTED_MIN:
        raise ValueError(
            f"Parsed only {len(nodes)} WordNet noun synsets, expected >= "
            f"{_EXPECTED_MIN}. NLTK corpus may be incomplete."
        )

    # No source file hash since the data lives in the NLTK package; record
    # the WordNet release version instead by hashing a deterministic
    # signature (count + root + first 100 codes joined).
    sig = f"v3.1|n={len(nodes)}|" + "|".join(n[0] for n in nodes[:100])
    import hashlib
    file_hash = hashlib.sha256(sig.encode("utf-8")).hexdigest()

    sid, short_name, full_name, ver, region, authority = _SYSTEM_ROW

    await conn.execute(
        """INSERT INTO classification_system
               (id, name, full_name, version, region, authority,
                source_url, source_date, data_provenance, license,
                source_file_hash, node_count)
           VALUES ($1,$2,$3,$4,$5,$6,$7,CURRENT_DATE,$8,$9,$10,0)
           ON CONFLICT (id) DO UPDATE SET
                name=$2, full_name=$3, version=$4, region=$5, authority=$6,
                source_url=$7, source_date=CURRENT_DATE, data_provenance=$8,
                license=$9, source_file_hash=$10, node_count=0""",
        sid, short_name, full_name, ver, region, authority,
        _SOURCE_URL, _DATA_PROVENANCE, _LICENSE, file_hash,
    )

    await conn.execute(
        "DELETE FROM classification_node WHERE system_id = $1", sid
    )

    records = [
        (sid, code, title, description, level, parent)
        for code, title, level, parent, description in nodes
    ]

    count = 0
    for i in range(0, len(records), CHUNK):
        batch = records[i : i + CHUNK]
        await conn.executemany(
            """INSERT INTO classification_node
                   (system_id, code, title, description, level, parent_code)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            batch,
        )
        count += len(batch)

    await conn.execute(
        "UPDATE classification_system SET node_count = $1 WHERE id = $2",
        count, sid,
    )

    print(f"  Ingested {count} WordNet noun synsets")
    return count
