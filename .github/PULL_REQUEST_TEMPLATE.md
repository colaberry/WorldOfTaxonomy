## Summary

<!-- One sentence: what does this PR add or fix? -->

## Type

- [ ] New classification system
- [ ] Bug fix
- [ ] Frontend change
- [ ] API change
- [ ] Documentation
- [ ] Other: ___

---

## For new classification systems - checklist

- [ ] Test file written FIRST and confirmed failing (Red) before any implementation
- [ ] All three tests pass (Green): `test_ingest_creates_system`, `test_ingest_creates_nodes`, `test_idempotent`
- [ ] System registered in `world_of_taxonomy/__main__.py` (dispatch block + choices list)
- [ ] Dispatch block follows the standard pattern (so auto-ingest-on-merge can detect it):
      `if target in ("<target>", "all"):` immediately followed by `from world_of_taxonomy.ingest.<module> import ...`
- [ ] `python3 -c "import ast; ast.parse(open('world_of_taxonomy/__main__.py').read()); print('OK')"` passes
- [ ] `CLAUDE.md` systems table updated with new row
- [ ] `DATA_SOURCES.md` updated with source URL and license
- [ ] No em-dash characters (U+2014) anywhere in changed files
- [ ] Full test suite passes: `python3 -m pytest tests/ -q`

> **Production data load:** when this PR merges, the
> [`Auto ingest on merge`](../actions/workflows/auto-ingest-on-merge.yml)
> workflow detects the newly-added ingester file, maps it to its CLI
> target, runs `python -m world_of_taxonomy ingest <target>` against the
> prod database, and busts the Next.js ISR cache. You do **not** need to
> dispatch `ingest-refresh.yml` manually. If the auto-ingest run fails
> (check the Actions tab on this PR's merge commit), retry with:
>
> ```bash
> gh workflow run auto-ingest-on-merge.yml \
>   -f added_files="world_of_taxonomy/ingest/<module>.py" \
>   --repo colaberry/WorldOfTaxonomy
> ```

## System details (if applicable)

| Field | Value |
|-------|-------|
| System ID | |
| Display name | |
| Region | |
| Codes ingested | |
| Source URL | |
| License | |
| Derived from | (NACE / ISIC / standalone) |

---

## Testing

```bash
# How to verify this PR works
python3 -m pytest tests/test_ingest_<system>.py -v
```
