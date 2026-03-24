"""
LLM enhancer for analysis summary and personalized resume tips.

This service enriches analysis output with:
- llm_insights.analytics_summary
- llm_insights.tips
- llm_insights.priority_actions

It is resilient by design:
- If inference fails, deterministic fallback content is returned.
- Output is always schema-safe (strings/lists of strings).
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Dict, List, Optional

import requests

from app.services.llm_roadmap_enhancer import InferenceMode


class AnalysisEnhancer:
    """Generate LLM-powered analytics summary and resume tips."""

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
    def _create_prompt(analysis: Dict) -> str:
        role = str(analysis.get("role", "target role"))
        overall = analysis.get("overall_score", 0)
        core = analysis.get("core_match", 0)
        secondary = analysis.get("secondary_match", 0)
        bonus = analysis.get("bonus_match", 0)

        strengths = ", ".join((analysis.get("strengths") or [])[:8])
        high_gaps = [
            item.get("skill", "")
            for item in (analysis.get("improvement_priority") or [])
            if str(item.get("priority", "")).lower() == "high"
        ]
        missing_focus = ", ".join([s for s in high_gaps[:8] if s])

        return f"""You are an expert resume coach.

Analyze this profile for role: {role}
Scores:
- Overall: {overall}
- Core: {core}
- Secondary: {secondary}
- Bonus: {bonus}

Top strengths: {strengths or 'Not enough data'}
High-priority skill gaps: {missing_focus or 'Not enough data'}

Return only valid JSON with this exact schema:
{{
  \"analytics_summary\": \"2-4 concise sentences with practical interpretation of score and role-readiness\",
  \"tips\": [\"4-6 concrete resume + preparation tips tailored to this profile\"],
  \"priority_actions\": [\"4-6 followable actions in action-verb style\"]
}}

Constraints:
- Keep content specific to the role and listed gaps.
- Avoid generic filler.
- Keep language simple and practical.
"""

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
                    "content": "You are an expert career coach. Return concise valid JSON only.",
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

        result = response.json()
        content = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return content.strip() if isinstance(content, str) else str(content)

    @staticmethod
    def _infer_mock(_prompt: str, **_kwargs) -> str:
        return json.dumps(
            {
                "analytics_summary": (
                    "Your profile has promising alignment for the role, but core skill coverage "
                    "still needs improvement to become interview-ready."
                ),
                "tips": [
                    "Add 2-3 quantified achievements using relevant tools from the target role.",
                    "Highlight one project that demonstrates end-to-end problem solving.",
                    "Move your strongest role-matching skills to the top of your skills section.",
                    "Use role-specific keywords in project bullets and resume summary.",
                ],
                "priority_actions": [
                    "Build one portfolio project focused on a high-priority missing skill.",
                    "Write STAR-format bullets for your latest project experience.",
                    "Practice interview questions for top missing core skills weekly.",
                    "Update your resume with measurable outcomes before next applications.",
                ],
            }
        )

    def _infer(self, prompt: str, max_tokens: int = 320) -> str:
        if self.mode == InferenceMode.HF_API:
            return self._infer_hf_api(prompt, max_tokens=max_tokens)
        return self._infer_mock(prompt)

    @staticmethod
    def _extract_json_from_response(response: str) -> Dict:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                try:
                    return json.loads(response[start:end].strip())
                except json.JSONDecodeError:
                    pass

        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                try:
                    return json.loads(response[start:end].strip())
                except json.JSONDecodeError:
                    pass

        match = re.search(r"\{[\s\S]*\}", response)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return {}

    @staticmethod
    def _normalize_str_list(items) -> List[str]:
        if items is None:
            return []
        if isinstance(items, str):
            cleaned = items.strip()
            return [cleaned] if cleaned else []
        if not isinstance(items, list):
            return [str(items).strip()] if str(items).strip() else []

        output: List[str] = []
        for item in items:
            value = str(item).strip()
            if value:
                output.append(value)
        return output

    @staticmethod
    def _fallback_tips(analysis: Dict) -> List[str]:
        role = str(analysis.get("role", "target role"))
        tips: List[str] = []

        top_missing = [
            item.get("skill", "")
            for item in (analysis.get("improvement_priority") or [])
            if item.get("skill")
        ]

        if top_missing:
            tips.append(f"Prioritize these missing skills for {role}: {', '.join(top_missing[:4])}.")
        tips.append("Quantify impact in your resume using numbers (time saved, growth, performance).")
        tips.append("Add one role-relevant project with tools and outcomes clearly listed.")
        tips.append("Align your resume summary with the exact wording of the target role.")
        tips.append("Practice explaining trade-offs and decisions in your recent projects.")
        return tips[:6]

    @staticmethod
    def _fallback_priority_actions(analysis: Dict) -> List[str]:
        actions: List[str] = []
        for item in (analysis.get("improvement_priority") or [])[:6]:
            skill = str(item.get("skill", "")).strip()
            if skill:
                actions.append(f"Build and document one mini project using {skill}.")

        if len(actions) < 4:
            actions.extend(
                [
                    "Rewrite your top 3 resume bullets in STAR format with measurable impact.",
                    "Solve 10 role-relevant practical problems and track weak areas.",
                    "Create a weekly study plan covering one core gap at a time.",
                    "Update your portfolio readme with outcomes, stack, and challenges.",
                ]
            )

        deduped: List[str] = []
        seen = set()
        for item in actions:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped[:6]

    def enhance(self, analysis: Dict) -> Dict:
        enhanced = dict(analysis)

        fallback_summary = str(analysis.get("analysis_summary", "")).strip()
        fallback_tips = self._fallback_tips(analysis)
        fallback_actions = self._fallback_priority_actions(analysis)

        insights = {
            "analytics_summary": fallback_summary,
            "tips": fallback_tips,
            "priority_actions": fallback_actions,
        }

        try:
            prompt = self._create_prompt(analysis)
            raw = self._infer(prompt)
            parsed = self._extract_json_from_response(raw)

            llm_summary = str(parsed.get("analytics_summary", "")).strip()
            llm_tips = self._normalize_str_list(parsed.get("tips"))
            llm_actions = self._normalize_str_list(parsed.get("priority_actions"))

            if llm_summary:
                insights["analytics_summary"] = llm_summary

            if llm_tips:
                merged_tips = llm_tips + [tip for tip in fallback_tips if tip not in llm_tips]
                insights["tips"] = merged_tips[:6]

            if llm_actions:
                merged_actions = llm_actions + [a for a in fallback_actions if a not in llm_actions]
                insights["priority_actions"] = merged_actions[:6]

        except Exception:
            pass

        enhanced["llm_insights"] = insights
        return enhanced


async def enhance_analysis_async(
    base_analysis: Dict,
    mode: InferenceMode = InferenceMode.HF_API,
) -> Dict:
    """Async wrapper to run analysis enhancement off the event loop."""
    enhancer = AnalysisEnhancer(mode=mode)
    return await asyncio.to_thread(enhancer.enhance, base_analysis)
