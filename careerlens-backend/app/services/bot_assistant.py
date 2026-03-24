"""Hybrid assistant bot service for CareerLens.

Combines three behaviors:
- Career coach (resume and skill gap guidance)
- Roadmap assistant (month/phase planning help)
- Recruiter helper (candidate evaluation prompts)

Uses HF Router when available, with deterministic fallback for reliability.
"""

from __future__ import annotations

import asyncio
import json
import os
from enum import Enum
from typing import Dict, List, Optional, Tuple

import requests

from app.services.llm_roadmap_enhancer import InferenceMode


class BotIntent(str, Enum):
    CAREER_COACH = "career_coach"
    ROADMAP_ASSISTANT = "roadmap_assistant"
    RECRUITER_HELPER = "recruiter_helper"
    GENERAL = "general"


class HybridBotAssistant:
    def __init__(
        self,
        mode: InferenceMode = InferenceMode.HF_API,
        hf_token: Optional[str] = None,
    ):
        self.mode = mode
        self.hf_token = hf_token or os.getenv("HUGGINGFACE_TOKEN")
        self.hf_router_chat_url = "https://router.huggingface.co/v1/chat/completions"
        self.hf_chat_model = os.getenv("HF_CHAT_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    @staticmethod
    def detect_intent(message: str) -> BotIntent:
        text = (message or "").lower()

        if ("mix" in text or "mixture" in text or "combine" in text or "all" in text) and (
            "coach" in text or "roadmap" in text or "recruit" in text
        ):
            return BotIntent.GENERAL

        recruiter_keys = [
            "candidate", "shortlist", "hire", "recruit", "interview", "screening",
            "compare resumes", "selection", "job fit",
        ]
        roadmap_keys = [
            "roadmap", "month", "phase", "plan", "timeline", "next step", "week",
            "what should i do", "learning path",
        ]
        coach_keys = [
            "resume", "cv", "skill gap", "improve", "tips", "score", "strength",
            "missing skills", "prepare",
        ]

        recruiter_hit = any(k in text for k in recruiter_keys)
        roadmap_hit = any(k in text for k in roadmap_keys)
        coach_hit = any(k in text for k in coach_keys)

        if (1 if recruiter_hit else 0) + (1 if roadmap_hit else 0) + (1 if coach_hit else 0) > 1:
            return BotIntent.GENERAL

        if recruiter_hit:
            return BotIntent.RECRUITER_HELPER
        if roadmap_hit:
            return BotIntent.ROADMAP_ASSISTANT
        if coach_hit:
            return BotIntent.CAREER_COACH
        return BotIntent.GENERAL

    @staticmethod
    def _extract_context(context: Optional[Dict]) -> Tuple[Dict, Dict]:
        context = context or {}
        analysis = context.get("analysis") if isinstance(context.get("analysis"), dict) else {}
        roadmap = context.get("roadmap") if isinstance(context.get("roadmap"), dict) else {}
        return analysis, roadmap

    @staticmethod
    def _context_summary(analysis: Dict, roadmap: Dict) -> str:
        role = analysis.get("role") or "unknown"
        overall = analysis.get("overall_score", "n/a")
        core = analysis.get("core_match", "n/a")
        missing = analysis.get("missing_skills") or []
        strengths = analysis.get("strengths") or []

        phases = roadmap.get("phases") if isinstance(roadmap.get("phases"), list) else []
        timeline = roadmap.get("timeline_months", "n/a")
        first_phase = phases[0] if phases else {}

        first_phase_title = first_phase.get("title", "n/a")
        first_phase_skills = ", ".join((first_phase.get("skills_to_learn") or [])[:5])

        return (
            f"Role: {role}\n"
            f"Overall score: {overall}\n"
            f"Core match: {core}\n"
            f"Top strengths: {', '.join(strengths[:5]) if strengths else 'n/a'}\n"
            f"Top missing skills: {', '.join(missing[:8]) if missing else 'n/a'}\n"
            f"Roadmap timeline months: {timeline}\n"
            f"First phase: {first_phase_title}\n"
            f"First phase skills: {first_phase_skills or 'n/a'}"
        )

    @staticmethod
    def _intent_instruction(intent: BotIntent) -> str:
        if intent == BotIntent.CAREER_COACH:
            return (
                "Mode: Career Coach. Give practical resume and upskilling guidance. "
                "Explain score/gaps simply and suggest concrete actions."
            )
        if intent == BotIntent.ROADMAP_ASSISTANT:
            return (
                "Mode: Roadmap Assistant. Focus on month-by-month or phase-by-phase plan. "
                "Prioritize immediate next actions and realistic weekly workload."
            )
        if intent == BotIntent.RECRUITER_HELPER:
            return (
                "Mode: Recruiter Helper. Summarize candidate fit, major risks, and interview focus areas. "
                "Keep tone objective and structured."
            )
        return (
            "Mode: General Assistant. Blend career coaching and roadmap guidance based on user context."
        )

    def _build_prompt(self, message: str, intent: BotIntent, history: List[Dict], analysis: Dict, roadmap: Dict) -> str:
        compact_history = []
        for item in history[-8:]:
            role = str(item.get("role", "user"))
            content = str(item.get("content", "")).strip()
            if content:
                compact_history.append(f"{role}: {content}")

        history_block = "\n".join(compact_history) if compact_history else "No prior history"
        context_block = self._context_summary(analysis, roadmap)
        intent_instruction = self._intent_instruction(intent)

        return f"""You are CareerLens Hybrid Assistant.

{intent_instruction}

Context snapshot:
{context_block}

Conversation history:
{history_block}

User message:
{message}

Response rules:
- Keep reply concise and clear.
- Provide actionable, role-specific guidance.
- Avoid generic filler.
- If user asks for steps, make steps explicit.
- If relevant context is missing, state assumption briefly.

Return only valid JSON with schema:
{{
  "reply": "short helpful response",
  "action_items": ["3-6 concrete actions"],
  "suggested_prompts": ["2-4 follow-up prompts"]
}}"""

    def _infer_hf_api(self, prompt: str, max_tokens: int = 320) -> str:
        if not self.hf_token:
            raise RuntimeError("HUGGINGFACE_TOKEN is required for HF API mode")

        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.hf_chat_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a practical career assistant. Return only valid JSON.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "max_tokens": max_tokens,
            "temperature": 0.5,
            "top_p": 0.9,
        }

        response = requests.post(
            self.hf_router_chat_url,
            headers=headers,
            json=payload,
            timeout=30,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Inference API error: {response.status_code} {response.text}")

        data = response.json()
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return content.strip() if isinstance(content, str) else str(content)

    @staticmethod
    def _infer_mock(_prompt: str, **_kwargs) -> str:
        return json.dumps(
            {
                "reply": "You are on a good path. Focus on top missing skills and execute one portfolio action this week.",
                "action_items": [
                    "Pick one high-priority missing skill and complete one guided module.",
                    "Implement one mini-project and publish it with a short readme.",
                    "Update resume bullets with measurable outcomes.",
                ],
                "suggested_prompts": [
                    "Give me a 7-day plan from my roadmap",
                    "Which missing skill should I learn first and why?",
                    "Create interview questions for my weakest area",
                ],
            }
        )

    def _infer(self, prompt: str, max_tokens: int = 320) -> str:
        if self.mode == InferenceMode.HF_API:
            return self._infer_hf_api(prompt, max_tokens=max_tokens)
        return self._infer_mock(prompt)

    @staticmethod
    def _extract_json(raw: str) -> Dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        if "```json" in raw:
            start = raw.find("```json") + 7
            end = raw.find("```", start)
            if end > start:
                try:
                    return json.loads(raw[start:end].strip())
                except json.JSONDecodeError:
                    pass

        if "```" in raw:
            start = raw.find("```") + 3
            end = raw.find("```", start)
            if end > start:
                try:
                    return json.loads(raw[start:end].strip())
                except json.JSONDecodeError:
                    pass

        # Fallback parse-free structure
        return {"reply": raw.strip()}

    @staticmethod
    def _to_list(value, limit: int) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            value = [str(value)]

        out: List[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                out.append(text)
        return out[:limit]

    @staticmethod
    def _fallback(intent: BotIntent, analysis: Dict, roadmap: Dict) -> Dict:
        role = analysis.get("role") or "target role"
        missing = analysis.get("missing_skills") or []
        phases = roadmap.get("phases") if isinstance(roadmap.get("phases"), list) else []
        first_phase = phases[0] if phases else {}

        if intent == BotIntent.ROADMAP_ASSISTANT:
            phase_title = first_phase.get("title", "Phase 1")
            phase_skills = ", ".join((first_phase.get("skills_to_learn") or [])[:4]) or "foundational skills"
            return {
                "reply": f"Start with {phase_title}. Focus first on {phase_skills}, then complete one mini project this month.",
                "action_items": [
                    "Allocate 5-7 hours this week for learning and practice.",
                    "Finish one tutorial covering the top phase skill.",
                    "Build one mini project and share it in your portfolio.",
                    "Review progress at end of week and plan next week.",
                ],
                "suggested_prompts": [
                    "Make this into a 7-day checklist",
                    "Which project should I build first?",
                    "How do I track monthly progress?",
                ],
            }

        if intent == BotIntent.RECRUITER_HELPER:
            top_gaps = ", ".join(missing[:4]) if missing else "no major gaps detected"
            return {
                "reply": f"Candidate fit for {role} is moderate. Key risk areas: {top_gaps}.",
                "action_items": [
                    "Ask scenario-based questions around top missing skills.",
                    "Evaluate depth using one practical task or case.",
                    "Probe impact with STAR-format follow-up questions.",
                    "Compare against must-have role criteria before shortlist.",
                ],
                "suggested_prompts": [
                    "Generate 5 interview questions for this candidate",
                    "Summarize hire risk in 3 bullets",
                    "Give a shortlist recommendation",
                ],
            }

        # Career coach + general fallback
        top_missing = ", ".join(missing[:4]) if missing else "core role skills"
        return {
            "reply": f"To improve your fit for {role}, prioritize {top_missing} and show practical project outcomes.",
            "action_items": [
                "Pick one missing skill and complete one guided learning module.",
                "Create one project artifact demonstrating that skill.",
                "Rewrite resume bullets with impact metrics.",
                "Practice interview answers for top weak areas.",
            ],
            "suggested_prompts": [
                "What should I improve first this week?",
                "Turn this into daily tasks",
                "Review my resume strategy for this role",
            ],
        }

    def reply(self, message: str, history: List[Dict], context: Optional[Dict]) -> Dict:
        intent = self.detect_intent(message)
        analysis, roadmap = self._extract_context(context)

        fallback = self._fallback(intent, analysis, roadmap)
        result = {
            "intent": intent.value,
            "reply": fallback["reply"],
            "action_items": fallback["action_items"],
            "suggested_prompts": fallback["suggested_prompts"],
            "source": "fallback",
        }

        try:
            prompt = self._build_prompt(message, intent, history, analysis, roadmap)
            raw = self._infer(prompt)
            parsed = self._extract_json(raw)

            llm_reply = str(parsed.get("reply", "")).strip()
            llm_actions = self._to_list(parsed.get("action_items"), 6)
            llm_prompts = self._to_list(parsed.get("suggested_prompts"), 4)

            if llm_reply:
                result["reply"] = llm_reply
                result["source"] = "llm"
            if llm_actions:
                result["action_items"] = llm_actions
            if llm_prompts:
                result["suggested_prompts"] = llm_prompts

        except Exception:
            pass

        return result


async def bot_reply_async(
    message: str,
    history: List[Dict],
    context: Optional[Dict],
    mode: InferenceMode = InferenceMode.HF_API,
) -> Dict:
    """Async wrapper for bot replies."""
    assistant = HybridBotAssistant(mode=mode)
    return await asyncio.to_thread(assistant.reply, message, history, context)
