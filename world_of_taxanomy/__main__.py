"""CLI entry point for WorldOfTaxanomy.

Usage:
    python -m world_of_taxanomy init
    python -m world_of_taxanomy ingest {naics,isic,crosswalk,all}
    python -m world_of_taxanomy browse <system_id> [code]
    python -m world_of_taxanomy search <query> [--system SYSTEM] [--limit N]
    python -m world_of_taxanomy equiv <system_id> <code> [--target TARGET]
    python -m world_of_taxanomy stats
"""

import argparse
import sys


def _run(coro):
    """Run an async coroutine synchronously."""
    import asyncio
    return asyncio.run(coro)


# ── Commands ──────────────────────────────────────────────────


def cmd_init(args):
    """Initialize the database schema."""
    from world_of_taxanomy.db import init_db
    print("Initializing database schema...")
    _run(init_db())
    print("Done. Tables created.")


def cmd_reset(args):
    """Drop and recreate all tables."""
    from world_of_taxanomy.db import reset_db
    print("Resetting database (dropping all tables)...")
    _run(reset_db())
    print("Done. Fresh schema ready.")


def cmd_ingest(args):
    """Ingest classification data."""
    from world_of_taxanomy.db import get_pool, close_pool

    async def _ingest():
        pool = await get_pool()
        async with pool.acquire() as conn:
            target = args.target

            if target in ("naics", "all"):
                from world_of_taxanomy.ingest.naics import ingest_naics_2022
                print("\n── NAICS 2022 ──")
                await ingest_naics_2022(conn)

            if target in ("isic", "all"):
                from world_of_taxanomy.ingest.isic import ingest_isic_rev4
                print("\n── ISIC Rev 4 ──")
                await ingest_isic_rev4(conn)

            if target in ("crosswalk", "all"):
                from world_of_taxanomy.ingest.crosswalk import ingest_crosswalk
                print("\n── Crosswalk (NAICS ↔ ISIC) ──")
                await ingest_crosswalk(conn)

        await close_pool()

    _run(_ingest())
    print("\nIngestion complete.")


def cmd_browse(args):
    """Browse classification hierarchy."""
    from world_of_taxanomy.db import get_pool, close_pool

    async def _browse():
        pool = await get_pool()
        async with pool.acquire() as conn:
            if args.code:
                # Show specific node and its children
                from world_of_taxanomy.query.browse import get_node, get_children, get_ancestors
                node = await get_node(conn, args.system_id, args.code)
                ancestors = await get_ancestors(conn, args.system_id, args.code)
                children = await get_children(conn, args.system_id, args.code)

                # Print breadcrumb
                if len(ancestors) > 1:
                    breadcrumb = " → ".join(f"{a.code}" for a in ancestors)
                    print(f"Path: {breadcrumb}")
                    print()

                # Print node
                leaf_marker = " 🍂" if node.is_leaf else ""
                print(f"[{node.code}] {node.title}{leaf_marker}")
                print(f"  System: {node.system_id} | Level: {node.level} | Sector: {node.sector_code}")

                if children:
                    print(f"\n  Children ({len(children)}):")
                    for child in children:
                        leaf = " 🍂" if child.is_leaf else ""
                        print(f"    [{child.code}] {child.title}{leaf}")
            else:
                # Show system roots
                from world_of_taxanomy.query.browse import get_system, get_roots
                try:
                    system = await get_system(conn, args.system_id)
                    print(f"\n{system.name} — {system.full_name}")
                    print(f"  Region: {system.region} | Version: {system.version}")
                    print(f"  Nodes: {system.node_count}")
                except Exception:
                    pass

                roots = await get_roots(conn, args.system_id)
                print(f"\nTop-level codes ({len(roots)}):")
                for root in roots:
                    print(f"  [{root.code}] {root.title}")

        await close_pool()

    _run(_browse())


def cmd_search(args):
    """Search classification codes."""
    from world_of_taxanomy.db import get_pool, close_pool

    async def _search():
        pool = await get_pool()
        async with pool.acquire() as conn:
            from world_of_taxanomy.query.search import search_nodes
            results = await search_nodes(
                conn, args.query,
                system_id=args.system,
                limit=args.limit,
            )

            if not results:
                print(f"No results for '{args.query}'")
                return

            print(f"Search results for '{args.query}' ({len(results)} found):\n")
            for node in results:
                print(f"  [{node.system_id}] {node.code} — {node.title}")

        await close_pool()

    _run(_search())


def cmd_equiv(args):
    """Show equivalences for a code."""
    from world_of_taxanomy.db import get_pool, close_pool

    async def _equiv():
        pool = await get_pool()
        async with pool.acquire() as conn:
            if args.target:
                from world_of_taxanomy.query.equivalence import translate_code
                results = await translate_code(
                    conn, args.system_id, args.code, args.target,
                )
            else:
                from world_of_taxanomy.query.equivalence import get_equivalences
                results = await get_equivalences(conn, args.system_id, args.code)

            if not results:
                print(f"No equivalences for {args.system_id}:{args.code}")
                return

            print(f"Equivalences for {args.system_id}:{args.code}:\n")
            for eq in results:
                arrow = "→"
                match_label = f"({eq.match_type})"
                target_title = f" — {eq.target_title}" if eq.target_title else ""
                print(f"  {arrow} [{eq.target_system}] {eq.target_code}{target_title} {match_label}")

        await close_pool()

    _run(_equiv())


def cmd_stats(args):
    """Show database statistics."""
    from world_of_taxanomy.db import get_pool, close_pool

    async def _stats():
        pool = await get_pool()
        async with pool.acquire() as conn:
            from world_of_taxanomy.query.browse import get_systems
            from world_of_taxanomy.query.equivalence import get_crosswalk_stats

            systems = await get_systems(conn)
            crosswalk = await get_crosswalk_stats(conn)

            print("╔═══════════════════════════════════════════════╗")
            print("║        WorldOfTaxanomy — Statistics           ║")
            print("╚═══════════════════════════════════════════════╝\n")

            print("Classification Systems:")
            for s in systems:
                print(f"  • {s.name:20s}  {s.node_count:>6,} nodes  ({s.region})")

            total_nodes = sum(s.node_count for s in systems)
            print(f"\n  Total nodes: {total_nodes:,}")

            if crosswalk:
                print("\nCrosswalk Edges:")
                total_edges = 0
                for cw in crosswalk:
                    print(f"  • {cw['source_system']:15s} → {cw['target_system']:15s}"
                          f"  {cw['edge_count']:>5,} edges"
                          f"  ({cw['exact_count']} exact, {cw['partial_count']} partial)")
                    total_edges += cw["edge_count"]
                print(f"\n  Total edges: {total_edges:,}")

        await close_pool()

    _run(_stats())


def cmd_serve(args):
    """Start the FastAPI server."""
    import uvicorn
    from world_of_taxanomy.api.app import create_app
    from world_of_taxanomy.db import get_pool, close_pool

    app = create_app()

    @app.on_event("startup")
    async def startup():
        app.state.pool = await get_pool()
        print("Database pool ready.")

    @app.on_event("shutdown")
    async def shutdown():
        await close_pool()
        print("Database pool closed.")

    print(f"\nStarting WorldOfTaxanomy API server...")
    print(f"  http://{args.host}:{args.port}")
    print(f"  Docs: http://{args.host}:{args.port}/docs\n")
    uvicorn.run(app, host=args.host, port=args.port)


# ── Argument Parser ───────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="world_of_taxanomy",
        description="WorldOfTaxanomy — Unified Industry Classification Knowledge Graph",
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # init
    sub.add_parser("init", help="Initialize database schema")

    # reset
    sub.add_parser("reset", help="Drop and recreate all tables")

    # ingest
    p_ingest = sub.add_parser("ingest", help="Ingest classification data")
    p_ingest.add_argument(
        "target",
        choices=["naics", "isic", "crosswalk", "all"],
        help="What to ingest",
    )

    # browse
    p_browse = sub.add_parser("browse", help="Browse classification hierarchy")
    p_browse.add_argument("system_id", help="Classification system ID (e.g., naics_2022)")
    p_browse.add_argument("code", nargs="?", help="Node code to inspect")

    # search
    p_search = sub.add_parser("search", help="Search classification codes")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--system", help="Filter by system ID")
    p_search.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    # equiv
    p_equiv = sub.add_parser("equiv", help="Show equivalences for a code")
    p_equiv.add_argument("system_id", help="Source system ID")
    p_equiv.add_argument("code", help="Source code")
    p_equiv.add_argument("--target", help="Target system ID (optional filter)")

    # stats
    sub.add_parser("stats", help="Show database statistics")

    # serve
    p_serve = sub.add_parser("serve", help="Start the API server")
    p_serve.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "reset": cmd_reset,
        "ingest": cmd_ingest,
        "browse": cmd_browse,
        "search": cmd_search,
        "equiv": cmd_equiv,
        "stats": cmd_stats,
        "serve": cmd_serve,
    }

    try:
        commands[args.command](args)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
