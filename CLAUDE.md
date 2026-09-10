# CLAUDE.md · fc-08-emerging-threat-intelligence

Project memory for Claude Code. Read `PLAN.md` for the full six-week plan.

## What this repo is now

Home of NEXUS Track 2 · Threat Intelligence · Slice 1 ("intel extraction"). An agentic pipeline that ingests regulator and industry advisories, extracts a governed `AdvisoryRecord`, resolves it against the Knowledge Centre through MCP tools, flags emergent typologies and routes desk digests, with every fact cited to page and paragraph.

The pre-existing folders (`analytics-opportunities/`, `intelligence/`, `roadmap/`, `threats/`) are the domain content this slice feeds. Do not restructure them.

## Stack and versions (verified 10 Sep 2026)

- Python 3.14 in `.venv` (activate with `. .venv/bin/activate`)
- `claude-agent-sdk` 0.2.x, `mcp` 2.2.x (**MCPServer**, not FastMCP; client results are snake_case: `init.server_info`, `init.protocol_version`, annotations `read_only_hint`), `pydantic` 2.13, `pypdf` 6
- The Agent SDK drives the `claude` CLI, whose login is SEPARATE from the desktop app. Check `claude auth status` first. fatf-gafi.org blocks curl; fetch advisories through a real browser
- The Agent SDK drives the Claude Code CLI; it must be installed and signed in
- macOS, Bash 3.2. No `declare -A`, no `mapfile`. Full-file replacements only, never partial snippets or edit-in-place instructions

## Layout

```
PLAN.md                            six-week plan and definition of done
schemas/advisory.py                AdvisoryRecord contract (schema v1.0.0) — the treaty
mcp_server/knowledge_centre_server.py   Knowledge Centre as MCP tools (read-only + propose)
agents/extract_advisory.py         week-1 single-advisory extraction agent
data/typologies.json               GOVERNED export of fc-10's doctrine library (57 typologies); never hand-edit
tools/import_fc10_doctrine.py      regenerates it from fc-10's indexes/doctrine_library.json; deterministic, provenance = fc-10 commit + sha256
data/advisories/                   source PDFs (gitignored)
data/records/                      validated AdvisoryRecord JSON (gitignored)
data/proposals.jsonl               review queue written by the MCP server (gitignored)
evals/example_record.json          golden record proving the schema
evals/validate_record.py           validator for any record
evals/check_citations.py           proves every citation quote exists on the PDF page it names
evals/review_ADV-2026-0001.md      week-1 review: what the first real run got wrong and why
setup.sh                           bootstrap + smoke tests
```

## Non-negotiable rules

1. `schemas/advisory.py` is the contract. Change it deliberately, bump `SCHEMA_VERSION`, update `evals/example_record.json` in the same commit.
2. Governance lives in tools and schemas, not prompts. The agent must never name a `typology_id` that a `knowledge_centre_*` tool did not return.
3. No citation, no fact. Every typology, actor and indicator carries at least one `Citation` with page and verbatim quote.
4. Nothing writes to the Knowledge Centre. `knowledge_centre_propose_link` appends to a review queue; a human approves.
5. Evaluate before improving. Build the golden set before touching prompt wording.
6. Keep single-file deliverables copy-and-paste ready. Reliability over cleverness.

## Commands

```bash
. .venv/bin/activate
python evals/validate_record.py evals/example_record.json
python agents/extract_advisory.py data/advisories/<file>.pdf --advisory-id ADV-2026-0001
python evals/validate_record.py data/records/ADV-2026-0001.json
claude mcp add knowledge-centre -- "$PWD/.venv/bin/python" "$PWD/mcp_server/knowledge_centre_server.py"
```

## Status

- [x] Week 0: repo scaffolded, schema validates, MCP server imports on mcp 2.2.0
- [x] Week 1 (2026-09-10): FATF TBML 2020 extracted twice; schema argued with and bumped to 1.1.0 (PDF page index + printed_folio, published_on_precision, ActorType.CATEGORY). Review and numbers in `evals/review_ADV-2026-0001.md`; citation checker in `evals/check_citations.py`. Nothing committed yet.
- [~] Week 2 (started 2026-09-10): MCP server registered (`claude mcp get knowledge-centre` shows Connected) and driven over stdio by a client; fixture replaced by the governed fc-10 export (schema 1.2.0 widens typology_id to allow TBML002U). Agent wired via `mcp_servers` with `strict_mcp_config=True` (the folder's `claude mcp add` registration otherwise loads too and causes permission denials); library removed from the prompt; `_refuse_unknown_ids` guards in code. Tool-grounded run: 7 library ids + 5 emergent, 12 proposals, $1.14, 49 turns. Citation page/folio SWAPPED in 15 of 21 under tool load: prompt advice does not hold; structural fix deferred to the golden set. Week 2 DONE except commit. Search tool rewritten (stemmed IDF + label bonus + floor 0.25); `evals/search_probes.py` went 8-of-12 missing to 12-of-12, mutation-verified. Run it after ANY change to the library or the scorer.
- [ ] Week 3: 20-advisory golden set and `evals/score.py`
- [ ] Week 4: fetcher / extractor / classifier / reviewer subagents
- [ ] Week 5: hooks, telemetry, `review.py` gate, desk digests
- [ ] Week 6: publish slice 1 on `future-capabilities.html`, tag `fc08-threatintel-slice1-v1.0.0`

## Journal

Engineering journal lives in `~/fc_vision_notes_dhartwig` (2026 entries). Filenames describe what happened that day. First entry to write: the mcp 1.x → 2.x rename hit on day one and how it was handled.

## Related repos

- `fc-10-repo`: governed platform, consumer of this slice's output via the MCP contract
- `dan-hartwig-portfolio/projects/nexus/`: public NEXUS site where slice 1 is published in week 6
