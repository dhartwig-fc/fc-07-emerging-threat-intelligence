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

## Week 1 status

- [x] Extraction run on a real advisory, record validates
- [x] Record read against the PDF, every citation located
- [x] Schema changed for findings 1, 3 and 5, `SCHEMA_VERSION` 1.1.0,
      `evals/example_record.json` updated, mutation-checked both ways
- [x] Rerun under 1.1.0: citations land, folios verified
- [ ] Week 0 scaffold and this week's files committed (still untracked)
