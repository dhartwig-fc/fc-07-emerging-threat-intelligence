"""
NEXUS Track 2 · Threat Intelligence · Slice 1
Week 1 agent: one advisory PDF in, one validated AdvisoryRecord out.

Usage:
    python agents/extract_advisory.py path/to/advisory.pdf --advisory-id ADV-2026-0001

Week 1 runs without the MCP server. Week 2 passes the Knowledge Centre
server in via `mcp_servers` so the agent looks up real typology IDs instead of
guessing. The schema contract does not change between the two weeks.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.advisory import AdvisoryRecord  # noqa: E402

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query  # noqa: E402

SYSTEM_PROMPT = """You are an intel extraction agent for a financial-crime threat-intelligence desk.
You read regulator and industry advisories and reduce them to a governed record.

Rules:
- Extract only what the document states. Never add typologies, actors or indicators from your own knowledge.
- Every typology, actor and indicator must carry at least one citation with page number and verbatim quote.
- Citation page is the n in the "=== PAGE n ===" marker above the text, never the number printed on the page. Put the printed number in printed_folio.
- published_on_precision says how much of the date the document states. "December 2020" is 2020-12-01 with precision month.
- A class of actor the document describes (organised crime groups, professional money launderers) is actor_type category, not organisation.
- If a typology is not in the known library, mark it emergent and leave typology_id null.
- Prefer fewer, well-cited items over many weakly supported ones.
- Jurisdictions are ISO 3166-1 alpha-2 codes.
- Put caveats for the human reviewer in extraction_notes.
"""


def pdf_to_pages(path: Path) -> list:
    reader = PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append("=== PAGE %d ===\n%s" % (i, text.strip()))
    return pages


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_prompt(advisory_id: str, path: Path, pages: list, known_typologies: list) -> str:
    library = "\n".join("%s | %s | %s" % (t["typology_id"], t["family"], t["label"]) for t in known_typologies)
    return (
        "Advisory ID to use: %s\n"
        "Document SHA-256: %s\n"
        "Page count: %d\n\n"
        "Known typology library (id | family | label):\n%s\n\n"
        "Document text follows. Produce the AdvisoryRecord.\n\n%s"
        % (advisory_id, sha256_of(path), len(pages), library, "\n\n".join(pages))
    )


async def extract(path: Path, advisory_id: str, model: str) -> AdvisoryRecord:
    pages = pdf_to_pages(path)
    with open(ROOT / "data" / "typologies.json", "r", encoding="utf-8") as fh:
        known = json.load(fh)["typologies"]

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        model=model,
        max_turns=3,
        allowed_tools=[],
        output_format={"type": "json_schema", "schema": AdvisoryRecord.model_json_schema()},
    )

    structured = None
    async for message in query(prompt=build_prompt(advisory_id, path, pages, known), options=options):
        if isinstance(message, ResultMessage):
            if message.is_error:
                raise RuntimeError("Agent run failed: %s" % (message.errors or message.result))
            structured = message.structured_output

    if structured is None:
        raise RuntimeError("Agent returned no structured output")
    return AdvisoryRecord.model_validate(structured)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a governed AdvisoryRecord from one PDF")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--advisory-id", required=True, help="Governed ID, for example ADV-2026-0001")
    parser.add_argument("--model", default="claude-sonnet-4-5", help="Model alias or ID")
    parser.add_argument("--out", type=Path, default=None, help="Where to write the JSON record")
    args = parser.parse_args()

    if not args.pdf.exists():
        print("PDF not found: %s" % args.pdf, file=sys.stderr)
        return 2

    record = asyncio.run(extract(args.pdf, args.advisory_id, args.model))

    out = args.out or (ROOT / "data" / "records" / ("%s.json" % args.advisory_id))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(record.model_dump_json(indent=2), encoding="utf-8")

    print("Wrote %s" % out)
    print("Typologies: %d (emergent: %d) | Actors: %d | Indicators: %d | Desks: %s" % (
        len(record.typologies),
        len(record.emergent_candidates),
        len(record.actors),
        len(record.indicators),
        ", ".join(d.value for d in record.suggested_desks),
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
