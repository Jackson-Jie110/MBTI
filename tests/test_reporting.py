from __future__ import annotations


def test_report_has_required_sections():
    from app.services.reporting import build_report

    report = build_report(
        "INTJ",
        {"EI": {"first_pole": "E", "second_pole": "I", "first_percent": 40, "second_percent": 60}},
        boundary_notes=[],
    )
    assert "优势" in report
    assert "盲点" in report
    assert "建议" in report
    assert "适合" in report


def test_report_context_has_sections():
    from app.services.reporting import build_report_context

    ctx = build_report_context(
        "INTJ",
        {"EI": {"first_pole": "E", "second_pole": "I", "first_percent": 40, "second_percent": 60}},
        boundary_notes=["E/I 接近边界"],
    )
    assert ctx["type_code"] == "INTJ"
    assert ctx["strengths"]
    assert ctx["blind_spots"]
    assert ctx["advice"]
    assert ctx["suitable"]
