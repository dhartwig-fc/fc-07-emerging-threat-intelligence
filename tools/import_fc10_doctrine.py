"""
NEXUS Track 2 · Threat Intelligence · Slice 1
Week 2: replace the fixture typology library with the governed FC10 export.

Usage:
    python tools/import_fc10_doctrine.py <path/to/fc-10/indexes/doctrine_library.json>

Reads fc-10's committed doctrine library (57 typologies, curated from the
toolkit doctrine writeups by fc-10's doctrine_curator) and writes
data/typologies.json in the shape the Knowledge Centre MCP server reads:
typology_id, family, label, summary, indicators, plus the fields the
get_typology tool is allowed to show an agent.

Deterministic: same input file, same output bytes. Provenance is the fc-10
commit that produced the library and the sha256 of the file read, never a
timestamp.

What it will NOT do: invent an indicator for a typology whose doctrine has
none. Those export with an empty list and are named on stderr.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "typologies.json"

# fc-10 family label -> schemas.advisory.TypologyFamily value. Every fc-10
# family must map; an unmapped family is an error, not "other".
FAMILY_MAP = {
    "Network Intelligence": "network",
    "TBML": "tbml",
    "Correspondent Banking": "correspondent_banking",
    "Sanctions": "sanctions",
    "Capital Markets": "capital_markets",
}

_WS = re.compile(r"\s+")


def _one_paragraph(text: str, limit: int = 600) -> str:
    """First paragraph of a doctrine prose field, whitespace-normalised."""
    first = (text or "").strip().split("\n\n", 1)[0]
    first = _WS.sub(" ", first).strip()
    return first[:limit].rstrip()


def _indicators(rec: dict) -> list:
    items = []
    for group in rec.get("risk_indicators") or []:
        for item in group.get("items") or []:
            item = _WS.sub(" ", item).strip()
            if item and item not in items:
                items.append(item)
    for item in rec.get("red_flags") or []:
        item = _WS.sub(" ", item).strip()
        if item and item not in items:
            items.append(item)
    return items


def _fc10_commit(library_path: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(library_path.parent), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def convert(library_path: Path) -> dict:
    raw = library_path.read_bytes()
    lib = json.loads(raw)
    unmapped = sorted({t["family"] for t in lib["typologies"]} - set(FAMILY_MAP))
    if unmapped:
        raise SystemExit("fc-10 families with no FC08 mapping: %s" % unmapped)

    typologies = []
    empty = []
    for t in sorted(lib["typologies"], key=lambda r: r["code"]):
        indicators = _indicators(t)
        if not indicators:
            empty.append(t["code"])
        entry = {
            "typology_id": t["code"],
            "family": FAMILY_MAP[t["family"]],
            "label": t["name"],
            "summary": _one_paragraph(t.get("description", "")),
            "indicators": indicators,
        }
        if t.get("intelligence_question"):
            entry["intelligence_question"] = _one_paragraph(t["intelligence_question"], 400)
        prov = t.get("provenance") or {}
        if prov.get("file"):
            entry["doctrine_file"] = prov["file"]
        if prov.get("authored_as"):
            entry["doctrine_authored_as"] = prov["authored_as"]
        typologies.append(entry)

    if empty:
        print("no indicators in doctrine, exported empty: %s" % ", ".join(empty), file=sys.stderr)

    return {
        "version": "fc10-%s" % _fc10_commit(library_path),
        "source": {
            "repository": "fc-10-intelligence-repository-layer",
            "file": "indexes/doctrine_library.json",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "library_schema_version": lib.get("schema_version"),
            "typology_count": len(typologies),
        },
        "note": "Governed export from fc-10's doctrine library. Regenerate with tools/import_fc10_doctrine.py; never hand-edit.",
        "typologies": typologies,
    }


def main(argv: list) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    library_path = Path(argv[0]).resolve()
    if not library_path.exists():
        print("not found: %s" % library_path, file=sys.stderr)
        return 2
    out = convert(library_path)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    fams = {}
    for t in out["typologies"]:
        fams[t["family"]] = fams.get(t["family"], 0) + 1
    print("Wrote %s: %d typologies from %s (%s)" % (OUT, len(out["typologies"]), out["version"], out["source"]["sha256"][:12]))
    print("families: " + ", ".join("%s=%d" % kv for kv in sorted(fams.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
