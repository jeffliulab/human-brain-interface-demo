"""Export TaskSpec and related Pydantic models as JSON Schema files.

Run: uv run python scripts/export_schemas.py
Outputs to: ../shared/schemas/
"""

import json
from pathlib import Path

from src.anima.taskspec import FiveFactors, IntentToken, PEARecord, TaskSpec

OUT_DIR = Path(__file__).resolve().parents[2] / "shared" / "schemas"

MODELS = {
    "taskspec": TaskSpec,
    "intent_token": IntentToken,
    "five_factors": FiveFactors,
    "pea_record": PEARecord,
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, model in MODELS.items():
        schema = model.model_json_schema()
        path = OUT_DIR / f"{name}.json"
        path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
