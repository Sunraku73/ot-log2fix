from io import StringIO

from rich.console import Console

from otlog2fix.report import ReportMeta, markdown, render
from otlog2fix.schema import SENTINEL, AnalysisResult


def test_report_inert_markdown_and_fence() -> None:
    evidence = "ERROR ![img](http://evil) ```"
    result = AnalysisResult.model_validate(
        {
            "status": "ok",
            "root_cause": "![img](http://evil)",
            "confidence": "low",
            "evidence": [evidence],
            "fix_steps": ["a", "b", "c"],
            "missing_context": ["<a href=evil>"],
            "injection_detected": False,
            "notes": "[link](http://evil)",
        },
        context={"log": evidence},
    )
    md = markdown(
        result, ReportMeta("app.log", 2, 4, "ollama", "model", "2026-01-01T12:30:00+00:00")
    )
    assert "````text" in md
    assert "````text\n" + evidence + "\n````" in md
    assert "&lt;a href=evil&gt;" in md
    assert r"\[link\]\(http&#58;//evil\)" in md


def test_render_sentinel() -> None:
    result = AnalysisResult.model_validate(
        {
            "status": "insufficient_context",
            "root_cause": SENTINEL,
            "confidence": "low",
            "evidence": ["ERROR"],
            "fix_steps": ["a", "b", "c"],
            "missing_context": [],
            "injection_detected": False,
            "notes": "",
        },
        context={"log": "ERROR"},
    )
    out = StringIO()
    render(result, Console(file=out, force_terminal=True, color_system="standard", no_color=False))
    assert SENTINEL in out.getvalue()
    assert "\x1b[33m" in out.getvalue()


def test_metadata_partial_and_schemes() -> None:
    data = {
        "status": "ok",
        "root_cause": "12:30 ORA-01652: http://evil",
        "confidence": "low",
        "evidence": ["ERROR"],
        "fix_steps": ["a", "b", "c"],
        "missing_context": [],
        "injection_detected": False,
        "notes": "javascript:alert data:text/plain",
    }
    result = AnalysisResult.model_validate(data, context={"log": "ERROR"})
    meta = ReportMeta("example.log", 2, 4, "ollama", "model", "2026-11-14T12:30:00+00:00")
    text = markdown(result, meta)
    assert "Analisi parziale: chunk 2 di 4" in text
    assert "example.log" in text and "ollama" in text and "12:30" in text
    assert "ORA-01652:" in text
    assert "http://evil" not in text and "http&#58;//evil" in text
    assert "javascript&#58;" in text and "data&#58;" in text
    assert "Analisi parziale" not in markdown(result, ReportMeta("a", 1, 1, "p", "m", "UTC"))


def test_control_characters_are_safe_in_markdown_and_terminal() -> None:
    evidence = "ERROR " + "\x1b]8;;http://evil\x1b\\" + "payload"
    data = {
        "status": "ok",
        "root_cause": "problem\x1b[2J",
        "confidence": "low",
        "evidence": [evidence],
        "fix_steps": ["\x1b[2J", "b", "c"],
        "missing_context": ["x\x85y"],
        "injection_detected": False,
        "notes": "\x1b[2J",
    }
    result = AnalysisResult.model_validate(data, context={"log": evidence})
    md = markdown(result, ReportMeta("f", 1, 1, "p", "m", "UTC"))
    out = StringIO()
    render(result, Console(file=out, force_terminal=False, color_system=None))
    assert "\x1b" not in md and "\x1b" not in out.getvalue()
    assert "\ufffd]8;;http://evil\ufffd\\payload" in md
    assert "\ufffd[2J" in out.getvalue()
