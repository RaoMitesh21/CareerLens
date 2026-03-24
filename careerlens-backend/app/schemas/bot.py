"""Schemas for CareerLens hybrid assistant bot."""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=2000)


class BotChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1200)
    history: List[ChatMessage] = Field(default_factory=list)
    context: Optional[Dict[str, Any]] = None


class BotChatResponse(BaseModel):
    intent: Literal["career_coach", "roadmap_assistant", "recruiter_helper", "general"]
    reply: str
    action_items: List[str] = Field(default_factory=list)
    suggested_prompts: List[str] = Field(default_factory=list)
    source: Literal["llm", "fallback"] = "fallback"
