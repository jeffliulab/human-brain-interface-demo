from src.anima.taskspec import (
    FiveFactors,
    IntentToken,
    PEARecord,
    Subtask,
    TaskSpec,
)


def test_intent_token_vocab_accepts_drink_water():
    tok = IntentToken(token="DRINK_WATER", confidence=0.9, source_text="I want water")
    assert tok.token == "DRINK_WATER"
    assert tok.requires_confirmation is False


def test_taskspec_round_trip():
    ts = TaskSpec(
        intent=IntentToken(token="DRINK_WATER", confidence=0.9),
        subtasks=[
            Subtask(name="locate_cup", type="locate"),
            Subtask(name="grasp_cup", type="grasp"),
            Subtask(name="lift_cup", type="lift"),
            Subtask(name="deliver_to_mouth", type="deliver"),
        ],
    )
    assert ts.device == "stretch_re3_mock"
    assert len(ts.subtasks) == 4
    data = ts.model_dump()
    restored = TaskSpec.model_validate(data)
    assert restored.intent.token == "DRINK_WATER"


def test_five_factors_defaults():
    ff = FiveFactors()
    assert ff.pea_count == 0
    assert 0.0 <= ff.goa <= 1.0


def test_pea_record_literal_outcome():
    rec = PEARecord(intent_token="DRINK_WATER", outcome="success")
    assert rec.outcome == "success"
