import pytest
from pydantic import ValidationError

from otlog2fix.schema import SENTINEL, AnalysisResult


def valid() -> dict[str, object]:
    return {
        "status": "ok",
        "root_cause": "Errore",
        "confidence": "high",
        "evidence": ["ERROR"],
        "fix_steps": ["uno", "due", "tre"],
        "missing_context": [],
        "injection_detected": False,
        "notes": "",
    }


def test_schema_valid_prefix() -> None:
    assert AnalysisResult.model_validate(
        valid() | {"evidence": ["ERROR fa"]}, context={"log": "  ERROR failure  \n"}
    ).evidence == ["ERROR fa"]


@pytest.mark.parametrize(
    "change",
    [
        {"evidence": ["inventata"]},
        {"evidence": []},
        {"evidence": [""]},
        {"evidence": ["ERROR\nfailure"]},
        {"fix_steps": ["uno"]},
        {"status": "insufficient_context", "confidence": "low"},
        {"status": "ok", "root_cause": SENTINEL},
        {"status": "insufficient_context", "root_cause": SENTINEL, "confidence": "high"},
    ],
)
def test_schema_rejects_invalid(change: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(valid() | change, context={"log": "ERROR failure"})


def test_schema_insufficient_context() -> None:
    data = valid() | {"status": "insufficient_context", "root_cause": SENTINEL, "confidence": "low"}
    assert (
        AnalysisResult.model_validate(data, context={"log": "ERROR"}).status
        == "insufficient_context"
    )


def test_schema_requires_log_context() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(valid())


def test_short_prefix_rejected_and_complete_short_line_accepted() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(valid() | {"evidence": ["2"]}, context={"log": "2026 error"})
    result = AnalysisResult.model_validate(
        valid() | {"evidence": ["  2  "]}, context={"log": " 2 "}
    )
    assert result.evidence == ["  2  "]
