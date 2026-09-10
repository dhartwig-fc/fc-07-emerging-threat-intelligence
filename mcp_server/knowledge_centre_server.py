"""
NEXUS Track 2 · Threat Intelligence · Slice 1
Week 2 skeleton: the Knowledge Centre exposed as an MCP server.
Works on MCP Python SDK 2.x (MCPServer) and 1.x (FastMCP).

Governance lives here, not in the prompt. The extraction agent can only touch
the typology library through these tools. Proposals are written to a staging
file for human review; nothing writes to the library itself.

Run locally (stdio transport, the default for Claude Desktop and Claude Code):
    python mcp_server/knowledge_centre_server.py

Register in Claude Code:
    claude mcp add knowledge-centre -- python "$PWD/mcp_server/knowledge_centre_server.py"
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

try:
    # MCP Python SDK 2.x: FastMCP was renamed to MCPServer
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # MCP Python SDK 1.x
    from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent.parent
TYPOLOGY_PATH = Path(os.environ.get("NEXUS_TYPOLOGY_PATH", ROOT / "data" / "typologies.json"))
PROPOSALS_PATH = Path(os.environ.get("NEXUS_PROPOSALS_PATH", ROOT / "data" / "proposals.jsonl"))

mcp = FastMCP("knowledge_centre_mcp")


# ---------------------------------------------------------------------------
# Library access (read-only)
# ---------------------------------------------------------------------------

def _load_library() -> dict:
    with open(TYPOLOGY_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _typologies() -> List[dict]:
    return _load_library().get("typologies", [])


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class ListTypologiesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    family: Optional[str] = Field(
        None,
        description="Filter by family such as tbml, sanctions, correspondent_banking. Omit for all.",
    )
    limit: int = Field(50, ge=1, le=200, description="Maximum rows to return")


class GetTypologyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    typology_id: str = Field(..., pattern=r"^[A-Z]{2,6}\d{3}$", description="Knowledge Centre ID such as TBML001")


class SearchTypologiesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., min_length=3, max_length=300, description="Free-text phrase from the advisory")
    limit: int = Field(5, ge=1, le=20)


class ProposeLinkInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    advisory_id: str = Field(..., pattern=r"^ADV-\d{4}-\d{4}$")
    typology_id: Optional[str] = Field(
        None,
        pattern=r"^[A-Z]{2,6}\d{3}$",
        description="Existing typology to link. Omit when proposing an emergent typology.",
    )
    emergent_label: Optional[str] = Field(None, min_length=3, max_length=120)
    rationale: str = Field(..., min_length=20, max_length=1000, description="Why this link holds, citing page numbers")
    confidence: str = Field(..., pattern=r"^(high|medium|low)$")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="knowledge_centre_list_typologies",
    annotations={"title": "List typologies", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def list_typologies(params: ListTypologiesInput) -> str:
    """
    List typologies in the governed Knowledge Centre library.

    Returns id, family and label for each typology, optionally filtered by family.
    Use this first to learn the valid typology_id values before proposing a link.
    Never invent a typology_id that this tool did not return.
    """
    rows = _typologies()
    if params.family:
        rows = [r for r in rows if r.get("family") == params.family.lower()]
    rows = rows[: params.limit]
    if not rows:
        return "No typologies found for family %r. Call without a filter to see all families." % params.family
    lines = ["%s | %s | %s" % (r["typology_id"], r["family"], r["label"]) for r in rows]
    return "typology_id | family | label\n" + "\n".join(lines)


@mcp.tool(
    name="knowledge_centre_get_typology",
    annotations={"title": "Get typology", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def get_typology(params: GetTypologyInput) -> str:
    """
    Return the full doctrine record for one typology by ID, including its summary
    and known indicators. Use this to confirm a match before proposing a link.
    """
    for r in _typologies():
        if r["typology_id"] == params.typology_id:
            return json.dumps(r, indent=2)
    return "Typology %s not found. Use knowledge_centre_list_typologies to see valid IDs." % params.typology_id


@mcp.tool(
    name="knowledge_centre_search_typologies",
    annotations={"title": "Search typologies", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def search_typologies(params: SearchTypologiesInput) -> str:
    """
    Keyword search across typology labels, summaries and indicators.

    Deliberately simple in slice 1 (token overlap). Week 3 swaps this for an
    embedding index without changing the tool contract. Returns ranked matches
    with a score so the agent can decide whether a typology is emergent.
    """
    terms = set(t for t in params.query.lower().split() if len(t) > 2)
    scored = []
    for r in _typologies():
        haystack = " ".join([r["label"], r.get("summary", "")] + r.get("indicators", [])).lower()
        hits = sum(1 for t in terms if t in haystack)
        if hits:
            scored.append((hits / max(len(terms), 1), r))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return "No matches. Treat as a possible emergent typology and propose it with emergent_label."
    out = ["score | typology_id | label"]
    for score, r in scored[: params.limit]:
        out.append("%.2f | %s | %s" % (score, r["typology_id"], r["label"]))
    return "\n".join(out)


@mcp.tool(
    name="knowledge_centre_propose_link",
    annotations={"title": "Propose advisory link", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
async def propose_link(params: ProposeLinkInput) -> str:
    """
    Propose that an advisory be pinned to a typology, or propose an emergent typology.

    This never writes to the library. It appends to a review queue that a human
    approves in week 5. Exactly one of typology_id or emergent_label must be given.
    """
    if bool(params.typology_id) == bool(params.emergent_label):
        return "Rejected: provide exactly one of typology_id or emergent_label."
    if params.typology_id and not any(r["typology_id"] == params.typology_id for r in _typologies()):
        return "Rejected: %s is not in the library. Use emergent_label if this is new." % params.typology_id

    record = {
        "proposed_at": datetime.now(timezone.utc).isoformat(),
        "advisory_id": params.advisory_id,
        "typology_id": params.typology_id,
        "emergent_label": params.emergent_label,
        "rationale": params.rationale,
        "confidence": params.confidence,
        "status": "pending_review",
    }
    PROPOSALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROPOSALS_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    return "Accepted into review queue: %s -> %s" % (
        params.advisory_id,
        params.typology_id or "EMERGENT(%s)" % params.emergent_label,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
