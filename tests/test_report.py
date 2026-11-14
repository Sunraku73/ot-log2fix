from io import StringIO

from rich.console import Console

from otlog2fix.report import markdown, render
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
    md = markdown(result)
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
