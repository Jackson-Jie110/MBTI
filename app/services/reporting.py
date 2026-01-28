from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "type_reports.json"


@lru_cache(maxsize=1)
def _load_type_reports() -> dict[str, Any]:
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


def _format_dimension_line(dim: str, info: dict[str, Any]) -> str:
    first = info.get("first_pole")
    second = info.get("second_pole")
    fp = info.get("first_percent")
    sp = info.get("second_percent")
    if first and second and fp is not None and sp is not None:
        stronger = second if int(sp) > int(fp) else first
        stronger_p = max(int(fp), int(sp))
        return f"- {dim}：更偏向 {stronger}（{stronger_p}%）"
    return f"- {dim}：数据不足"


def build_report(type_code: str, dimensions: dict[str, Any], *, boundary_notes: list[str]) -> str:
    reports = _load_type_reports()
    info = reports.get(type_code, {})

    title = info.get("title", "类型分析")
    summary = info.get("summary", "这是一个基于题目作答倾向的性格偏好分析结果。")
    strengths = info.get("strengths", [])
    blind_spots = info.get("blind_spots", [])
    advice = info.get("advice", [])
    suitable = info.get("suitable", [])

    lines: list[str] = []
    lines.append(f"# 你的类型：{type_code}（{title}）")
    lines.append("")
    lines.append("## 概览")
    lines.append(summary)
    lines.append("")
    lines.append("## 四维倾向")
    for dim in ["EI", "SN", "TF", "JP"]:
        if dim in dimensions:
            lines.append(_format_dimension_line(dim, dimensions[dim]))
    lines.append("")

    if boundary_notes:
        lines.append("## 边界提示")
        for note in boundary_notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("## 优势")
    for s in strengths:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## 盲点")
    for s in blind_spots:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## 建议")
    for s in advice:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## 适合方向")
    for s in suitable:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## 说明")
    lines.append("本测试仅用于自我了解与娱乐参考，不构成专业心理评估或诊断。")
    lines.append("")
    return "\n".join(lines)


def build_report_context(type_code: str, dimensions: dict[str, Any], *, boundary_notes: list[str]) -> dict[str, Any]:
    reports = _load_type_reports()
    info = reports.get(type_code, {})

    title = info.get("title", "类型分析")
    summary = info.get("summary", "这是一个基于题目作答倾向的性格偏好分析结果。")
    strengths = list(info.get("strengths", []))
    blind_spots = list(info.get("blind_spots", []))
    advice = list(info.get("advice", []))
    suitable = list(info.get("suitable", []))

    dim_items: list[dict[str, Any]] = []
    for dim in ["EI", "SN", "TF", "JP"]:
        d = dimensions.get(dim)
        if not d:
            continue
        first = d.get("first_pole")
        second = d.get("second_pole")
        fp = d.get("first_percent")
        sp = d.get("second_percent")
        if first and second and fp is not None and sp is not None:
            dim_items.append(
                {
                    "dimension": dim,
                    "first_pole": first,
                    "second_pole": second,
                    "first_percent": int(fp),
                    "second_percent": int(sp),
                }
            )

    return {
        "type_code": type_code,
        "title": title,
        "summary": summary,
        "dimensions": dim_items,
        "boundary_notes": list(boundary_notes),
        "strengths": strengths,
        "blind_spots": blind_spots,
        "advice": advice,
        "suitable": suitable,
        "disclaimer": "本测试仅用于自我了解与娱乐参考，不构成专业心理评估或诊断。",
    }
