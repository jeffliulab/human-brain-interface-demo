"""Parser tests — mock the LLM so these run without an API key."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from src.anima import l1_parser
from src.anima.taskspec import TaskSpec


def _fake_llm_response(args: dict) -> MagicMock:
    tool_call = MagicMock()
    tool_call.function.arguments = json.dumps(args)
    msg = MagicMock()
    msg.tool_calls = [tool_call]
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_parse_drink_water_fills_full_plan():
    fake_args = {
        "intent_token": "DRINK_WATER",
        "intent_confidence": 0.9,
        "requires_confirmation": False,
        "alternatives": [],
        "subtasks": [],  # force the safety fill-in
        "constraints": {},
    }
    with patch.object(l1_parser, "get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = _fake_llm_response(
            fake_args
        )
        ts: TaskSpec = l1_parser.parse("我想喝水", drift=0.05)
    assert ts.intent.token == "DRINK_WATER"
    assert len(ts.subtasks) == 4
    assert ts.subtasks[0].type == "locate"
    assert ts.intent.requires_confirmation is False


def test_parse_low_confidence_forces_confirmation():
    fake_args = {
        "intent_token": "GRASP",
        "intent_confidence": 0.55,
        "requires_confirmation": False,
        "alternatives": [{"token": "LIFT", "confidence": 0.4}],
        "subtasks": [{"name": "grasp_obj", "type": "grasp"}],
        "constraints": {},
    }
    with patch.object(l1_parser, "get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = _fake_llm_response(
            fake_args
        )
        ts = l1_parser.parse("动一下", drift=0.05)
    assert ts.intent.requires_confirmation is True
    assert len(ts.intent.alternatives) == 1


def test_parse_invalid_token_maps_to_unknown():
    fake_args = {
        "intent_token": "TELEPORT",  # not in vocab
        "intent_confidence": 0.8,
        "subtasks": [{"name": "do_thing", "type": "grasp"}],
        "constraints": {},
    }
    with patch.object(l1_parser, "get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = _fake_llm_response(
            fake_args
        )
        ts = l1_parser.parse("瞬移", drift=0.05)
    assert ts.intent.token == "UNKNOWN"
