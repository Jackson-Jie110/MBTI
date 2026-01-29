from __future__ import annotations

import html
import os
from typing import AsyncIterator


def _sse_data(text: str) -> str:
    safe = html.escape(text)
    safe = safe.replace("\n", "<br/>")
    return f"data: <span>{safe}</span>\n\n"


def _oob_inner_html(target_id: str, inner_html: str) -> str:
    return f"data: <div id=\"{html.escape(target_id)}\" hx-swap-oob=\"innerHTML\">{inner_html}</div>\n\n"


def _retry_ms(ms: int) -> str:
    return f"retry: {int(ms)}\n\n"


async def generate_report_stream(user_type: str, insights: list[str]) -> AsyncIterator[str]:
    yield _oob_inner_html("ai-content", "<div class='muted'>✨ 正在连接 AI 咨询师...</div>")

    try:
        base_url = os.getenv("MBTI_AI_BASE_URL")
        api_key = os.getenv("MBTI_AI_API_KEY")
        model = os.getenv("MBTI_AI_MODEL", "gpt-3.5-turbo")

        if not base_url or not api_key:
            raise ValueError("Vercel 环境变量未配置 (MBTI_AI_BASE_URL 或 MBTI_AI_API_KEY)")

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        insight_text = "\n".join([f"- {i}" for i in (insights or [])])
        system_prompt = (
            "你是一位专业的 MBTI 心理咨询师。请根据用户的类型和作答行为，给出一段温暖、有洞察力的性格分析与建议（300字以内）。"
            "请直接输出内容，不要带 Markdown 标题。"
        )
        user_prompt = f"用户类型：{user_type}\n\n关键行为洞察：\n{insight_text}\n\n请分析用户的性格矛盾点或独特优势。"

        current_text = ""
        yield _oob_inner_html("ai-content", "<div class='muted'>正在生成 AI 深度分析…</div>")

        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            timeout=20.0,
        )

        async for chunk in stream:
            text = ""
            try:
                text = chunk.choices[0].delta.content or ""
            except Exception:
                text = ""
            if not text:
                continue

            current_text += text
            safe_text = html.escape(current_text).replace("\n", "<br/>")
            yield _oob_inner_html("ai-content", safe_text)
    except Exception as e:
        error_msg = f"⚠️ 分析服务暂时不可用: {str(e)}"
        print(error_msg)
        yield _oob_inner_html("ai-content", f"<div class='muted btn danger'>{html.escape(error_msg)}</div>")
        yield _retry_ms(86_400_000)
        return

    # 正常结束：把重连间隔拉长，避免 HTMX/EventSource 反复重连触发重复生成
    yield _retry_ms(86_400_000)
