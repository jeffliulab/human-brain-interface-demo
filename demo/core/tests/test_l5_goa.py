import tempfile
from pathlib import Path
from unittest.mock import patch

from src.anima import l5_assessment
from src.anima.l5_assessment import compute_pre_goa
from src.anima.taskspec import IntentToken


def test_pre_goa_formula():
    # ita=0.9 × p_plan=0.95 × p_skill=0.91 = 0.7780...
    assert abs(compute_pre_goa(0.9) - 0.9 * 0.95 * 0.91) < 1e-9


def test_pre_goa_clamped():
    assert compute_pre_goa(-0.5) == 0.0
    assert compute_pre_goa(2.0) == 1.0  # 2.0*0.95*0.91 = 1.729 → clamped


def test_log_pea_appends():
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "pea.jsonl"
        with patch.object(l5_assessment, "PEA_LOG", log_path):
            assert l5_assessment.pea_count() == 0
            intent = IntentToken(
                token="DRINK_WATER",
                confidence=0.9,
                source_text="我想喝水",
            )
            rec = l5_assessment.log_pea(intent, "success")
            assert rec.intent_token == "DRINK_WATER"
            assert l5_assessment.pea_count() == 1
            l5_assessment.log_pea(intent, "success")
            assert l5_assessment.pea_count() == 2
