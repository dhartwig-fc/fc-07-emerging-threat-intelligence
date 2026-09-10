"""
Week-1 review helper: does every citation in an AdvisoryRecord point at text that
actually exists on the page it names?

Usage:
    python check_citations.py <record.json> <advisory.pdf>

This is the mechanical half of "read the record against the PDF". It does NOT
judge whether the typology mapping is right; it only proves each quote is real.
The plan's week-4 reviewer subagent does the same check inside the pipeline.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace("­", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def main(record_path: str, pdf_path: str) -> int:
    record = json.loads(Path(record_path).read_text(encoding="utf-8"))
    pages = [norm(p.extract_text() or "") for p in PdfReader(pdf_path).pages]
    all_text = " ".join(pages)

    # pypdf splits words ("collus ion", "t o believe") on born-digital FATF PDFs. A
    # second tier compares with ALL whitespace removed, so an honest quote whose only
    # difference is the extractor's spacing is OK-SPACING rather than MISSING. This
    # is deliberately not a fuzzy match on meaning.
    tight_pages = [p.replace(" ", "") for p in pages]
    tight_all = "".join(tight_pages)

    checked = 0
    exact = 0
    spacing = 0
    off_page = 0
    missing = 0
    for section in ("typologies", "actors", "indicators"):
        for item in record.get(section, []):
            label = item.get("label") or item.get("name") or item.get("description", "")[:60]
            for c in item.get("citations", []):
                checked += 1
                q = norm(c["quote"])
                tq = q.replace(" ", "")
                page_idx = c["page"] - 1
                in_range = 0 <= page_idx < len(pages)
                on_page = in_range and q in pages[page_idx]
                on_page_tight = in_range and tq in tight_pages[page_idx]
                anywhere = tq in tight_all
                if on_page:
                    exact += 1
                    status = "OK       "
                elif on_page_tight:
                    spacing += 1
                    status = "OK-SPACING"
                elif anywhere:
                    off_page += 1
                    where = [i + 1 for i, p in enumerate(tight_pages) if tq in p]
                    status = "OFF-PAGE  (found on %s)" % where
                else:
                    missing += 1
                    status = "MISSING  "
                print("%s p%-3d %-10s %s" % (status, c["page"], section[:10], label[:60]))
                if not (on_page or on_page_tight):
                    print("           quote: %r" % c["quote"][:140])

    print()
    print("citations checked: %d | exact on page: %d | on page modulo pypdf spacing: %d | "
          "right quote wrong page: %d | not in document: %d"
          % (checked, exact, spacing, off_page, missing))
    if checked == 0:
        print("FAIL: no citations examined; a record with nothing to check is not a pass")
        return 1
    return 0 if missing == 0 and off_page == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
