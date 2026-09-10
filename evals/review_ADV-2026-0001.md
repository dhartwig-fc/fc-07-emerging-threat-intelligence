# Week 1 review: ADV-2026-0001 against the FATF/Egmont TBML report

Reviewed 2026-09-10. Record: `data/records/ADV-2026-0001.json` (gitignored).
Source: `data/advisories/fatf-tbml-2020.pdf`, sha256 `0969e498…f6828`, 66 PDF
pages. Run: `agents/extract_advisory.py`, model `claude-sonnet-5`, 3m08s,
single turn, no tools. Fixture library: `data/typologies.json` (8 entries).

## Headline

The record is honest and the schema is where reality disagreed. Every one of
the 17 citations is a real sentence from the document. Zero fabrications. But
**0 of 17 land on the page they name**, because the schema never said what a
page number is and the agent picked the printed folio for 15 of them and the
PDF index for 2. That inconsistency, not any hallucination, is the week 1 defect.

## What was checked and how

| Check | Method | Result |
|---|---|---|
| Schema validity | `evals/validate_record.py` | PASS |
| Every citation quote exists verbatim on its page | `evals/check_citations.py`, whitespace/quote-normalised | 0 exact, 11 wrong page, 6 not found |
| The 6 not found | locate by 45-char fragment, print source text | all 6 present; pypdf splits words (`collus ion`, `t o believe`) and the agent silently repaired the spacing |
| Page convention | read printed folio on 8 sampled PDF pages | folio = PDF index − 2, constant across the document |
| Source URL | search PDF front matter | verbatim from the "Citing reference" on PDF page 2 |
| Publication date | search PDF | document says only "December 2020"; record's `2020-12-01` is invented precision (site says 9 December) |
| 14 jurisdictions | count mentions and case "Box" pages | all 14 appear in case boxes |
| Missed jurisdictions | same, inverted | Hong Kong, India, China, Switzerland, Brazil have case boxes and are absent |
| Emergent candidates vs the GOVERNED library | grep fc-04 README and typology docs | none of the 5 exist in fc-04; genuinely emergent |
| Fixture IDs vs the governed library | compare fc-04 README | **fixture is wrong**: fc-04 has TBML001 Over Invoicing, TBML002 Under Invoicing, TBML003 Multiple Invoicing, TBML004 Phantom Shipping, TBML005 False Description |

## Findings, ranked by what they cost

### 1. `Citation.page` is ambiguous and the agent proved it — schema

The field says "1-based page number in the source document". This document
prints folio 3 on PDF page 5. The agent cited the folio 15 times and the PDF
index twice (OCGs on p5, the ABF mirror-statistics indicator on p26). Nothing
in the schema or prompt told it which to use, so it used both.

Proposed fix, `schemas/advisory.py`, bump to 1.1.0:

- Rename the description to "1-based PDF page index, matching the `=== PAGE n ===`
  marker the agent was shown. NOT the printed folio."
- Add `printed_folio: Optional[str]` so the human-readable reference is kept
  without ambiguity.
- In `extract_advisory.py`, state the rule in `SYSTEM_PROMPT` in one line.

The week 4 reviewer subagent must run the check in `evals/check_citations.py`; it is
the mechanical half of "no citation, no fact" and it caught this in one run.

### 2. Quotes are "verbatim modulo pypdf" — reviewer design, not schema

Six quotes failed exact match because pypdf inserts spaces inside words. The
agent's text was the correct English; the extractor's was not. A verbatim
check must normalise whitespace INSIDE words, or the reviewer will reject
honest citations on every born-digital FATF PDF. Do not "fix" this by loosening
to fuzzy match on meaning; strip whitespace and compare.

### 3. `published_on: date` forces precision the source does not state — schema

The report says "December 2020". The record says `2020-12-01`, which is the
PDF's creation timestamp and not a claim the document makes. Either allow
`YYYY-MM` precision or add `published_on_precision: day | month | year`.
Under rule 3 a day the source never states is an uncited fact.

### 4. The fixture library contradicts the governed one — data, week 2

`data/typologies.json` says TBML002 = Phantom shipments. fc-04 says TBML002 =
Under Invoicing and TBML004 = Phantom Shipping. So the record's TBML002 link
is right against the fixture and wrong against the Knowledge Centre. The FATF
sentence on over- AND under-invoicing should, in governed terms, link both
TBML001 and TBML002. This is exactly what week 2 exists to fix: replace the
fixture with the real export before any record is treated as intel. Until
then every `typology_id` in `data/records/` is fixture-scoped.

### 5. Actors are categories, not actors — schema

OCGs, PMLs and TF networks are extracted as `actor_type: organisation` /
`network`. They are threat-actor CLASSES. The report names no designated
party, which the agent said honestly in `extraction_notes`. Either add
`ActorType.CATEGORY` (or `THREAT_ACTOR_CLASS`) or instruct that a category is
not an actor and belongs in the summary. Week 3's resolver will otherwise try
to resolve "Organised Criminal Groups" against an entity fixture.

### 6. Jurisdiction recall is partial — prompt, low priority

14 of at least 19 case-box countries. Hong Kong, India, China, Switzerland and
Brazil were missed. The agent's note says jurisdictions "reflect countries with
named case studies", which was its rule, applied incompletely. Score it in
week 3; do not tune the prompt for it now (rule 5).

## What was right

- Typology recall on the document's own taxonomy is complete: the four
  "traditional" techniques and the four newer cash-integration methods it
  lists on PDF pages 28–33 are all present, plus TBTF.
- Emergent flagging worked as designed and was conservative: services-based
  ML was explicitly excluded because the source says it is distinct.
- Desk routing (trade, FIU liaison, correspondent, general) is defensible.
- `document_sha256` and `page_count` are correct; the agent copied them
  rather than guessing.
- `extraction_notes` reads like a reviewer note, which is what it is for.

## Rerun under schema 1.1.0 (same day)

Findings 1, 3 and 5 were applied: `Citation.page` is the PDF index with
`printed_folio` beside it, `published_on_precision` was added with a validator
that refuses a stated day under month precision, and `ActorType.CATEGORY` was
added. Three lines went into the agent's system prompt. The 1.0.0 record is
kept at `data/records/ADV-2026-0001.schema-1.0.0.json` for the diff.

| | 1.0.0 run | 1.1.0 run |
|---|---|---|
| Citations on the page they name | 0 of 17 | **14 of 15** (10 exact, 4 modulo pypdf spacing) |
| Wrong page | 11 | 1 (an indicator cited p14, found on p16) |
| Not in document | 6, all pypdf spacing | 0 |
| `printed_folio` matches the page | n/a | 15 of 15 |
| `published_on` | 2020-12-01, day | 2020-12-01, **month** |
| Actor types | organisation ×2, network | category ×3 |

The one residual wrong page is the kind of error the week 4 reviewer exists
to reject; the checker catches it and exits 1, so the record is not clean.

**Run-to-run variance is the new finding.** Same document, same model, same
prompt apart from three lines: indicators went 7 to 5 with three dropped and
one new, Colombia left the jurisdictions, and correspondent desk became fraud
desk. Typologies and actors were stable. A single extraction is not a stable
measurement, which is what week 3's golden set and `evals/score.py` are for.
Do not tune the prompt against one run (rule 5).

## Week 2 addendum: the governed library is in, and the search tool is the next defect

Finding 4 closed the same day. `tools/import_fc10_doctrine.py` exports fc-10's
committed `indexes/doctrine_library.json` (57 typologies, all authored, five
families) into `data/typologies.json`; deterministic, provenance pinned to the
fc-10 commit and file hash. Schema 1.2.0 widens `typology_id` to allow one
trailing letter because the governed library carries `TBML002U` for
under-invoicing. TBML001 and TBML002 export with no indicators because fc-04's
doctrine for them has no indicators heading; nothing was invented.

Against the real library, the week-1 record's `TBML002` link is now visibly
wrong (governed `TBML002` is "Over Invoicing (Cross-Domain)"; phantom shipping
is `TBML004`), which is what week 2's tool-grounded rerun exists to correct.

**New finding 7: `knowledge_centre_search_typologies` will mislead the agent.**
It is token overlap with no stemming and no floor. Measured on the real library
with week-1 phrases:

| Query | Top result | Should be |
|---|---|---|
| phantom shipments no product is moved at all | BA001 Structuring, 0.40 | TBML004 Phantom Shipping ("shipments" does not match "shipping") |
| Black Market Peso Exchange drug cartels | BA007 Cash Intensive Activity, 0.17 | "No matches", it is emergent |
| misrepresentation of the price of goods invoice over-invoicing | TBML002U Under Invoicing, 0.83 | TBML001, which scored 0.67 |
| vessels disable AIS ship-to-ship transfer | SAN002 / PAT008 Shadow Fleet, 0.71 | correct |

The plan defers embedding search to week 3, but the agent is grounded on this
tool in week 2 step 3. A weak match reported as a match is worse than no match:
the agent will link BMPE to cash-intensive activity and mark it non-emergent.
Fix in tool design, not prompt: a score floor below which the tool says "no
match, treat as emergent", and label-token stemming at minimum.

**Finding 7 closed the same day, measured.** `evals/search_probes.py` holds 12
phrases with expected answers, written before the change: 8 of 12 missed on the
token-overlap search. The replacement (`rank_typologies` in the server) uses
stemmed tokens truncated to six characters, inverse document frequency across
the 57 records so common words stop dominating, a 2× label bonus, and a floor
of 0.25 below which the tool reports no match and names the closest sub-floor
candidate as "not a match". After: 12 of 12. Emergent phrases top out at 0.12;
the weakest true match is 0.48.

Mutation-verified: floor forced to 0 misses both emergent probes; stemming
disabled misses two; restored, clean. Two of my probes were corrected during
the work because they were badly posed, not because the scorer failed them:
one named both a shared director and a shared address, one expected a single
winner where the library has two Shadow Fleet entries (SAN002, PAT008).

Two limits, recorded rather than fixed:

- TBML001 and TBML002 tie on every over-invoicing query because fc-10's
  TBML002 borrows TBML001's doctrine verbatim. The tool now appends
  "doctrine authored as TBML001" from the export's provenance field, so the
  agent can prefer the code the doctrine was written for. Data, not code.
- A short query that names only a label ("controlled by the same director")
  ties PAT001, PAT007 and SAN001 at 1.00. The agent sees all three with
  labels; that is the honest answer for three stems.

## Week 2 step 3: the agent grounded on tools, same document

`agents/extract_advisory.py` now passes the Knowledge Centre server via
`mcp_servers`, allows the four `knowledge_centre_*` tools, and carries no
library in the prompt. A typology_id can only come from a tool result, and
that is enforced in code: the propose tool refuses unknown ids, and
`_refuse_unknown_ids` raises if the returned record names one anyway. The
prompt says the same thing, which is advice, not governance.

Run: `claude-sonnet-5`, 49 turns, 6m45s, $1.14, 43 Knowledge Centre calls
(19 search, 8 get, 12 propose). Week-1 record kept at
`data/records/ADV-2026-0001.week1-schema-1.1.0.json`.

| | Week 1, fixture in prompt | Week 2, tools |
|---|---|---|
| Typologies resolved to library ids | 2, one of them wrong in governed terms | **7**: TBML001, 002U, 003, 004, 005, 008, 009 |
| Emergent | 5 | 5 |
| Proposals in the review queue | 0 | 12, one per typology, reconciled both ways |
| Ids outside the library | n/a | 0 |
| Citations on the page they name | 14 of 15 | **5 of 21** |

**What improved.** Under-invoicing resolved to TBML002U, third-party invoice
settlement to TBML008, multiple invoicing and false description of goods to
TBML003 and TBML005, none of which the fixture had. The agent saw that
TBML002's doctrine is borrowed from TBML001 and did not link it, and it
read the search's "no match" as emergent five times, including
services-based ML, which week 1 had excluded by judgement. Every proposal in
`data/proposals.jsonl` is `pending_review`; nothing wrote to the library.

**What regressed, and why it matters more than the win.** In 15 of 21
citations the agent swapped the two page fields: the PDF index went into
`printed_folio` and the folio into `page`. Both numbers were correct; the
assignment was not. Week 1's rerun got this right 14 of 15 times on the same
prompt line. Under 49 turns of tool traffic the prompt rule stopped holding.
That is the difference between advice and governance made visible: the id
rule is enforced in code and held; the page rule is prose and did not. The
checker caught it and exits 1.

The durable fix is structural, deliberately not applied before the golden set
exists: put the folio in the page marker the agent reads
(`=== PAGE 28 · printed 26 ===`) so the mapping is where the text is, and
have the week-4 reviewer swap or reject. Recorded, not tuned.

**Two environment findings.** The Claude Code registration from step 1 leaked
into the SDK run: the CLI loaded the folder's registered `knowledge-centre`
alongside the SDK's `knowledge_centre`, so the model saw two copies and hit
four permission denials on the hyphenated one. `strict_mcp_config=True` maps
to the CLI's `--strict-mcp-config` and fixes it; verified with a one-tool
probe, zero denials. And fc-10's export marks TBML002U as "authored as
TBML002" because its writeup lives under `typologies/TBML002/`, while TBML002
itself is "authored as TBML001". The chain is an fc-10 curator artefact; the
agent saw through it and said so in `extraction_notes`. Worth an fc-10 fix so
the hint is not misleading for the one under-invoicing code.

## Week 1 status

- [x] Extraction run on a real advisory, record validates
- [x] Record read against the PDF, every citation located
- [x] Schema changed for findings 1, 3 and 5, `SCHEMA_VERSION` 1.1.0,
      `evals/example_record.json` updated, mutation-checked both ways
- [x] Rerun under 1.1.0: citations land, folios verified
- [ ] Week 0 scaffold and this week's files committed (still untracked)
