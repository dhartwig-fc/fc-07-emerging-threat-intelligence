"""
Probe set for knowledge_centre_search_typologies against the governed library.

Usage:
    python evals/search_probes.py

Each probe is a phrase an advisory might contain and the typology the search
must rank first, or None when the right answer is "no match, treat as
emergent". Exit 1 on any miss. Written BEFORE the search was changed (week 2,
2026-09-10) and it failed 4 of 12 on the token-overlap version; keep it failing
on any regression rather than editing the expectations.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcp_server import knowledge_centre_server as s  # noqa: E402

# (phrase, expected top typology_id or None for "no match")
PROBES = [
    ("misrepresentation of the price of goods on the invoice, over-invoicing to transfer value", "TBML001"),
    ("under-invoicing: goods invoiced below market value so the importer receives the difference", "TBML002U"),
    ("phantom shipments where no product is moved at all", "TBML004"),
    ("the same consignment invoiced multiple times to different banks", "TBML003"),
    ("goods falsely described on the bill of lading to disguise their true nature", "TBML005"),
    # the library carries two Shadow Fleet entries (sanctions SAN002, network PAT008); either is right
    ("vessels disable AIS and conduct ship-to-ship transfers of sanctioned cargo", ("SAN002", "PAT008")),
    ("funds leave an account, pass through intermediaries and return to the originator, round-tripping", "BA004"),
    ("matched buy and sell orders that produce no change in beneficial ownership", "CM005"),
    ("two companies are controlled by the same director", "PAT001"),
    ("Black Market Peso Exchange used by drug cartels to launder proceeds", None),
    ("surrogate shoppers purchasing luxury goods on behalf of wealthier individuals", None),
    ("cash-intensive retail business with deposits far above peers", "BA007"),
]


async def run() -> int:
    misses = 0
    for phrase, expected in PROBES:
        text = await s.search_typologies(s.SearchTypologiesInput(query=phrase, limit=3))
        lines = text.splitlines()
        if lines and lines[0].startswith("score"):
            top = lines[1].split("|")[1].strip() if len(lines) > 1 else None
            top_score = lines[1].split("|")[0].strip() if len(lines) > 1 else ""
        else:
            top, top_score = None, "-"
        ok = top in expected if isinstance(expected, tuple) else top == expected
        misses += not ok
        print("%s  %-9s got %-9s %s  | %s" % ("OK  " if ok else "MISS", str(expected), str(top), top_score, phrase[:60]))
    print()
    print("probes: %d | misses: %d" % (len(PROBES), misses))
    if len(PROBES) == 0:
        return 1
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))
