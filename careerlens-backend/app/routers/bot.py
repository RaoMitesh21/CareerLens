"""Hybrid assistant bot routes."""

from __future__ import annotations

import asyncio
import os

from fastapi import APIRouter

from app.schemas.bot import BotChatRequest, BotChatResponse
from app.services.bot_assistant import bot_reply_async
from app.services.llm_roadmap_enhancer import InferenceMode

router = APIRouter(prefix="/bot", tags=["Bot"])


def _resolve_inference_mode() -> InferenceMode:
    mode_raw = os.getenv("INFERENCE_MODE", "mock").strip().lower()
    mode_map = {
        "mock": InferenceMode.MOCK,
        "hf_api": InferenceMode.HF_API,
        "local": InferenceMode.LOCAL,
    }
    return mode_map.get(mode_raw, InferenceMode.MOCK)


@router.post("/chat", response_model=BotChatResponse, summary="Hybrid assistant chat")
def chat_with_bot(request: BotChatRequest):
    mode = _resolve_inference_mode()

    history_payload = [m.model_dump() for m in request.history]

    try:
        result = asyncio.run(
            bot_reply_async(
                message=request.message,
                history=history_payload,
                context=request.context,
                mode=mode,
            )
        )
    except Exception:
        # Guaranteed response shape even on runtime failure
        result = {
            "intent": "general",
            "reply": "I can help with resume strategy, roadmap planning, and recruiter-style feedback. Ask me one specific goal and I will break it down.",
            "action_items": [
                "Share your target role and current score.",
                "Ask for a 7-day action plan from your roadmap.",
                "Ask for interview prep on one weak skill.",
            ],
            "suggested_prompts": [
                "Give me a 7-day upskilling plan",
                "What skill should I focus on first?",
                "How can I improve my resume this week?",
            ],
            "source": "fallback",
        }

    return result
