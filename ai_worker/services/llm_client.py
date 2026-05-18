"""Gọi API Gemini hoặc OpenAI."""

from __future__ import annotations

import logging

from ai_worker.settings import settings

logger = logging.getLogger(__name__)


def complete_chat(system_prompt: str, user_prompt: str) -> str:
    provider = (settings.llm_provider or "gemini").strip().lower()
    if provider == "openai":
        return _openai_complete(system_prompt, user_prompt)
    return _gemini_complete(system_prompt, user_prompt)


def _openai_complete(system_prompt: str, user_prompt: str) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("Thiếu OPENAI_API_KEY trong .env")
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError("Cài đặt: pip install openai") from e

    client = OpenAI(api_key=settings.openai_api_key)
    r = client.chat.completions.create(
        model=settings.llm_model_openai,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return (r.choices[0].message.content or "").strip()


def _gemini_complete(system_prompt: str, user_prompt: str) -> str:
    if not settings.gemini_api_key:
        raise RuntimeError("Thiếu GEMINI_API_KEY trong .env (hoặc đổi LLM_PROVIDER=openai)")
    try:
        import google.generativeai as genai
    except ImportError as e:
        raise RuntimeError("Cài đặt: pip install google-generativeai") from e

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.llm_model_gemini, system_instruction=system_prompt)
    r = model.generate_content(user_prompt)
    return (getattr(r, "text", None) or "").strip()
