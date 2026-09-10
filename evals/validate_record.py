"""
Validate one or more AdvisoryRecord JSON files against the week-1 schema.

Usage:
    python evals/validate_record.py evals/example_record.json
    python evals/validate_record.py data/records/*.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pydantic import ValidationError  # noqa: E402

from schemas.advisory import AdvisoryRecord  # noqa: E402


def main(paths: list) -> int:
    if not paths:
        print("Usage: python evals/validate_record.py <record.json> [...]")
        return 2
    failures = 0
    for p in paths:
        path = Path(p)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            record = AdvisoryRecord.model_validate(data)
            print("PASS  %s  (%d typologies, %d emergent, %d actors, %d indicators)" % (
                path.name, len(record.typologies), len(record.emergent_candidates),
                len(record.actors), len(record.indicators)))
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            failures += 1
            print("FAIL  %s" % path.name)
            print(str(exc))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
