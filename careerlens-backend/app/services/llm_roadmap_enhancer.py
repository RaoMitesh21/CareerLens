"""
app/services/llm_roadmap_enhancer.py — LLM-Enhanced Learning Roadmap

Enhances the deterministic roadmap generator with contextual descriptions
and personalized learning suggestions using Llama 3 (via Hugging Face).

Features:
  - Supports both local inference (GPU) and Hugging Face API
  - Generates rich learning descriptions for each phase
  - Creates personalized action items based on skills
  - Recommends resources aligned with skill types
  - Tracks inference metrics for accuracy measurement

Model: ajosm/roadmap_generator (Llama-3-8B fine-tuned)
License: Apache 2.0
"""

from __future__ import annotations

import asyncio
import os
import json
import time
from typing import Dict, List, Optional
from enum import Enum

import requests
from dotenv import load_dotenv

load_dotenv()


class InferenceMode(str, Enum):
    """Inference execution mode."""
    LOCAL = "local"           # Use local GPU (requires CUDA)
    HF_API = "hf_api"        # Use Hugging Face Inference API
    MOCK = "mock"            # Mock mode for testing


class RoadmapEnhancer:
    """
    Enhances base roadmaps with LLM-generated descriptions and suggestions.
    
    Supports both local inference (fast, private) and Hugging Face API
    (scalable, cloud-based).
    """
    
    def __init__(
        self,
        mode: InferenceMode = InferenceMode.HF_API,
        hf_token: Optional[str] = None,
        model_id: str = "ajosm/roadmap_generator",
    ):
        """
        Initialize the roadmap enhancer.
        
        Args:
            mode: Inference mode (LOCAL, HF_API, or MOCK)
            hf_token: Hugging Face API token (required for HF_API mode)
            model_id: Model identifier on Hugging Face Hub
        """
        self.mode = mode
        self.model_id = model_id
        self.hf_token = hf_token or os.getenv("HUGGINGFACE_TOKEN")
        self.hf_router_chat_url = "https://router.huggingface.co/v1/chat/completions"
        # Use a provider-backed chat model for stable router inference.
        self.hf_chat_model = os.getenv("HF_CHAT_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        
        # For local inference
        self.tokenizer = None
        self.model = None
        self.device = None
        
        # Performance tracking
        self.metrics = {
            "total_calls": 0,
            "total_latency": 0.0,
            "avg_latency": 0.0,
        }
        
        # Initialize based on mode
        if mode == InferenceMode.LOCAL:
            self._init_local()
        elif mode == InferenceMode.HF_API and not self.hf_token:
            raise ValueError(
                "HUGGINGFACE_TOKEN required for HF_API mode"
            )
    
    def _init_local(self) -> None:
        """Initialize local GPU-based inference."""
        try:
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
            )
            import torch
            
            print(f"Loading {self.model_id} locally...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                device_map="auto",
                torch_dtype=torch.float16,
            )
            self.device = "cuda"
            print("✓ Local model loaded successfully")
        except ImportError as e:
            raise ImportError(
                "Local mode requires: pip install transformers torch"
            ) from e
    
    # ── Prompt Templates ────────────────────────────────────────

    @staticmethod
    def _level_guidance(level: str) -> str:
        """Return level-specific writing constraints for roadmap output."""
        if level == "beginner":
            return (
                "Audience profile: absolute beginner with little to no prior experience.\n"
                "Writing style: simple language, short sentences, no jargon.\n"
                "Task style: very small first steps, realistic weekly effort (5-7 hours/week).\n"
                "Content constraints:\n"
                "- Start with fundamentals before tools/frameworks.\n"
                "- Include beginner-safe actions (intro course, guided tutorial, tiny project).\n"
                "- Avoid advanced topics (system design, microservices, optimization) unless explicitly required.\n"
                "- Mention confidence-building milestones."
            )
        if level == "intermediate":
            return (
                "Audience profile: has base skills and some project experience.\n"
                "Writing style: practical and concise.\n"
                "Task style: focused gap-closing with medium complexity tasks."
            )
        return (
            "Audience profile: strong practitioner seeking polish/specialization.\n"
            "Writing style: concise and high-impact.\n"
            "Task style: advanced practice, depth, and leadership-oriented actions."
        )
    
    @staticmethod
    def _create_phase_prompt(
        phase_num: int,
        phase_title: str,
        skills: List[str],
        duration: str,
        role: str,
        level: str,
    ) -> str:
        """Create a focused prompt for phase enhancement."""
        skills_str = ", ".join(skills[:5])  # Top 5 skills
        level_guidance = RoadmapEnhancer._level_guidance(level)
        
        return f"""You are an expert career coach for {role} roles.

Generate an inspiring and actionable learning phase.

Phase {phase_num}: {phase_title}
Duration: {duration}
Level: {level}
Key Skills to Master: {skills_str}

{level_guidance}

Hard constraints:
- Make the content specific to the role "{role}" and the listed skills.
- Keep progression explicit: basic -> intermediate -> advanced outcomes.
- Avoid generic text like "learn fundamentals" without naming concrete skills.
- Objectives must be measurable and practical.
- Resources must directly support the listed skills.

Provide:
1. A 2-3 sentence engaging description of this phase
2. 4 followable step-by-step actions (clear sequence, each action starts with Step 1/2/3/4)
3. 3-4 specific, actionable learning objectives
4. 2-3 recommended learning resource types (e.g., courses, books, projects)

Keep response concise and motivating.
Return only valid JSON with this exact schema:
{{"description": "...", "actions": [...], "objectives": [...], "resources": [...]}}"""
    
    @staticmethod
    def _create_roadmap_prompt(
        role: str,
        level: str,
        total_phases: int,
        key_skills: List[str],
    ) -> str:
        """Create prompt for overall roadmap context."""
        skills_str = ", ".join(key_skills[:10])
        
        return f"""You are an expert career coach creating a personalized roadmap.

Role: {role}
Proficiency Level: {level}
Target Timeframe: {total_phases} phases
Core Skills to Develop: {skills_str}

Provide a motivational summary (2-3 sentences) for this career roadmap 
that explains the learning journey and end goal.

Format: {{"summary": "...", "motivation": "..."}}"""
    
    # ── Inference Methods ────────────────────────────────────────
    
    def _infer_local(self, prompt: str, max_tokens: int = 256) -> str:
        """Run inference using local GPU."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Local model not initialized")
        
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(self.device)
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
        )
        
        response = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True,
        )
        
        # Extract only the generated portion (after prompt)
        return response[len(prompt):].strip()
    
    def _infer_hf_api(self, prompt: str, max_tokens: int = 256) -> str:
        """Run inference using Hugging Face Router chat-completions API."""
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
            "temperature": 0.7,
            "top_p": 0.9,
        }
        
        response = requests.post(
            self.hf_router_chat_url,
            headers=headers,
            json=payload,
            timeout=30,
        )
        
        if response.status_code != 200:
            raise RuntimeError(
                f"Inference API error: {response.status_code} "
                f"{response.text}"
            )
        
        result = response.json()
        content = (
            result.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return content.strip() if isinstance(content, str) else str(content)
    
    def _infer_mock(self, prompt: str, **kwargs) -> str:
        """Mock inference for testing (no API calls)."""
        return json.dumps({
            "description": "Learn and master the fundamentals through "
                          "structured practice.",
            "actions": [
                "Step 1: Complete one guided lesson and take notes.",
                "Step 2: Practice with a small hands-on exercise.",
                "Step 3: Build one mini-project using the skills.",
                "Step 4: Review mistakes and document improvements.",
            ],
            "objectives": [
                "Complete online courses and tutorials",
                "Build small portfolio projects",
                "Join learning communities",
            ],
            "resources": [
                "Online learning platforms (Coursera, Udemy)",
                "Official documentation",
                "Practice repositories and coding challenges",
            ],
        })
    
    def _infer(self, prompt: str, max_tokens: int = 256) -> str:
        """Run inference based on configured mode."""
        if self.mode == InferenceMode.LOCAL:
            return self._infer_local(prompt, max_tokens)
        elif self.mode == InferenceMode.HF_API:
            return self._infer_hf_api(prompt, max_tokens)
        else:  # MOCK
            return self._infer_mock(prompt)
    
    # ── Parsing & Extraction ────────────────────────────────────────
    
    @staticmethod
    def _extract_json_from_response(response: str) -> Dict:
        """
        Extract JSON from LLM response.
        
        LLMs often wrap JSON in markdown code blocks or include extra text.
        This method robustly extracts the JSON object.
        """
        # Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end > start:
                return json.loads(response[start:end].strip())
        
        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end > start:
                try:
                    return json.loads(response[start:end].strip())
                except json.JSONDecodeError:
                    pass
        
        # Try finding JSON object patterns
        import re
        json_match = re.search(r'\{[^{}]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: return structured response
        return {
            "description": response[:200],
            "actions": [
                "Step 1: Complete one guided lesson for the phase skills.",
                "Step 2: Practice using targeted exercises and examples.",
                "Step 3: Build one mini-project using the same skills.",
                "Step 4: Review mistakes and document improvements.",
            ],
            "objectives": [
                "Understand core concepts for this phase.",
                "Apply concepts in practical exercises.",
                "Complete one small portfolio artifact.",
            ],
            "resources": [],
        }

    @staticmethod
    def _stringify_resource_item(item) -> str:
        """Convert model resource item (string/object) into UI-safe plain string."""
        if isinstance(item, str):
            return item.strip()

        if isinstance(item, dict):
            item_type = str(item.get("type", "Resource")).strip().title()
            title = str(item.get("title", "")).strip()
            platform = str(item.get("platform", "")).strip()
            author = str(item.get("author", "")).strip()
            description = str(item.get("description", "")).strip()

            parts: List[str] = []
            if item_type:
                parts.append(item_type)
            if title:
                parts.append(title)

            # Extra metadata in compact parentheses
            extras: List[str] = []
            if platform:
                extras.append(platform)
            if author:
                extras.append(author)
            if description:
                extras.append(description)

            base = ": ".join(parts) if parts else "Resource"
            if extras:
                return f"{base} ({'; '.join(extras)})"
            return base

        return str(item).strip()

    @staticmethod
    def _normalize_string_list(items, for_resources: bool = False) -> List[str]:
        """Ensure schema-safe List[str] for objectives/resources."""
        if items is None:
            return []

        if isinstance(items, str):
            return [items.strip()] if items.strip() else []

        normalized: List[str] = []
        if isinstance(items, list):
            for item in items:
                value = (
                    RoadmapEnhancer._stringify_resource_item(item)
                    if for_resources
                    else str(item).strip()
                )
                if value:
                    normalized.append(value)
        else:
            value = str(items).strip()
            if value:
                normalized.append(value)

        return normalized

    @staticmethod
    def _fallback_objectives(phase: Dict) -> List[str]:
        """Deterministic objectives when model output is missing/invalid."""
        skills = phase.get("skills_to_learn") or []
        actions = phase.get("suggested_actions") or []

        objectives: List[str] = []
        if skills:
            objectives.append(f"Learn and practice these core skills: {', '.join(skills[:4])}.")
        if actions:
            objectives.append(actions[0])
        objectives.append("Complete one small project and document your work in a portfolio.")
        objectives.append("Revise weekly and track progress with a checklist.")
        return objectives[:4]

    def _fallback_resources(self, phase: Dict, role: str) -> List[str]:
        """Deterministic occupation-wise resources when model output is missing/invalid."""
        role_lc = (role or "").lower()
        skills = [str(s).strip().lower() for s in (phase.get("skills_to_learn") or []) if str(s).strip()]

        def by_skill(skill: str) -> List[str]:
            if "python" in skill:
                return [
                    "Python Crash Course (Eric Matthes)",
                    "Real Python guided tutorials",
                ]
            if "sql" in skill:
                return [
                    "SQLBolt interactive SQL lessons",
                    "Mode SQL tutorial and exercises",
                ]
            if "machine learning" in skill or skill == "ml":
                return [
                    "Machine Learning Specialization by Andrew Ng (Coursera)",
                    "Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow",
                ]
            if "statistics" in skill or "probability" in skill:
                return [
                    "Khan Academy statistics and probability",
                    "Practical Statistics for Data Scientists",
                ]
            if "excel" in skill:
                return [
                    "Excel Skills for Business (Coursera)",
                    "Leila Gharani Excel practice tutorials",
                ]
            if "power bi" in skill:
                return [
                    "Microsoft Power BI learning path",
                    "Power BI guided dashboard projects",
                ]
            if "tableau" in skill:
                return [
                    "Tableau Desktop Specialist prep materials",
                    "Tableau Public hands-on project gallery",
                ]
            if "react" in skill:
                return [
                    "React official docs (react.dev)",
                    "Full Stack Open React modules",
                ]
            if "javascript" in skill or "web programming" in skill:
                return [
                    "The Odin Project JavaScript path",
                    "MDN JavaScript guide",
                ]
            if "html" in skill or "css" in skill:
                return [
                    "MDN HTML and CSS learning track",
                    "Frontend Mentor practical challenges",
                ]
            if "docker" in skill:
                return [
                    "Docker official getting-started guide",
                    "Dockerizing real apps tutorial series",
                ]
            if "git" in skill:
                return [
                    "Pro Git book (free)",
                    "GitHub flow and pull request tutorial",
                ]
            return []

        role_defaults: List[str]
        if "data scientist" in role_lc or "machine learning" in role_lc:
            role_defaults = [
                "Kaggle Learn tracks for Python, Pandas, and ML",
                "IBM Data Science Professional Certificate (Coursera)",
                "Scikit-learn official user guide",
            ]
        elif "data analyst" in role_lc or "analytics" in role_lc:
            role_defaults = [
                "Google Data Analytics Professional Certificate",
                "SQL practice on LeetCode or StrataScratch",
                "Power BI or Tableau end-to-end dashboard project course",
            ]
        elif "web" in role_lc or "frontend" in role_lc:
            role_defaults = [
                "The Odin Project full curriculum",
                "MDN web docs learning paths",
                "Frontend Mentor project challenges",
            ]
        elif "software" in role_lc or "developer" in role_lc or "backend" in role_lc:
            role_defaults = [
                "CS50x for programming foundations",
                "System Design Primer (GitHub)",
                "NeetCode or LeetCode roadmap for coding practice",
            ]
        else:
            role_defaults = [
                "Role-specific beginner-to-advanced course on Coursera",
                "Official documentation with hands-on examples",
                "Project-based learning repository",
            ]

        resources: List[str] = []
        for skill in skills[:4]:
            skill_resources = by_skill(skill)
            if skill_resources:
                resources.append(skill_resources[0])

        resources.extend(role_defaults)
        resources.append(f"One guided portfolio project focused on {role}")

        # De-duplicate while preserving order
        unique: List[str] = []
        seen = set()
        for item in resources:
            text = str(item).strip()
            key = text.lower()
            if text and key not in seen:
                seen.add(key)
                unique.append(text)
        return unique[:5]

    @staticmethod
    def _looks_generic_resources(resources: List[str]) -> bool:
        """Detect low-quality generic resource lists."""
        if not resources:
            return True

        generic_markers = [
            "online learning platform",
            "official documentation",
            "guided tutorial",
            "project-based practice repository",
            "beginner-friendly online course",
        ]

        score = 0
        for item in resources:
            text = str(item).lower()
            if any(marker in text for marker in generic_markers):
                score += 1

        return score >= max(1, len(resources) - 1)

    @staticmethod
    def _fallback_actions(phase: Dict) -> List[str]:
        """Deterministic followable actions when model output is missing/invalid."""
        actions = RoadmapEnhancer._normalize_string_list(
            phase.get("suggested_actions", []),
            for_resources=False,
        )

        if actions:
            # Ensure predictable Step format for frontend followability.
            out: List[str] = []
            for i, action in enumerate(actions[:4], start=1):
                text = action.strip()
                if text.lower().startswith("step "):
                    out.append(text)
                else:
                    out.append(f"Step {i}: {text}")
            return out

        return [
            "Step 1: Learn the core concept with one guided tutorial.",
            "Step 2: Practice with targeted exercises for this phase skills.",
            "Step 3: Build one mini-project and validate outputs.",
            "Step 4: Review gaps and update notes before next phase.",
        ]

    @staticmethod
    def _generic_default_actions() -> List[str]:
        """Default generic action set used by parser fallback."""
        return [
            "Step 1: Complete one guided lesson for the phase skills.",
            "Step 2: Practice using targeted exercises and examples.",
            "Step 3: Build one mini-project using the same skills.",
            "Step 4: Review mistakes and document improvements.",
        ]

    @staticmethod
    def _actions_from_objectives(objectives: List[str]) -> List[str]:
        """Create followable steps from objectives when model omits actions."""
        cleaned = [str(obj).strip() for obj in objectives if str(obj).strip()]
        if not cleaned:
            return []

        steps: List[str] = []
        for i, obj in enumerate(cleaned[:4], start=1):
            steps.append(f"Step {i}: {obj}")
        return steps
    
    # ── Public API ──────────────────────────────────────────────────
    
    async def enhance_phase(
        self,
        phase: Dict,
        role: str,
        level: str,
    ) -> Dict:
        """
        Enhance a single roadmap phase with LLM descriptions.
        
        Args:
            phase: Phase dict with keys: phase, title, duration, 
                   focus_area, skills_to_learn, suggested_actions
            role: Target occupation role
            level: Proficiency level (beginner/intermediate/advanced)
        
        Returns:
            Enhanced phase dict with AI-generated content:
              - enhanced_description: LLM-generated phase description
              - learning_objectives: Specific objectives for the phase
              - recommended_resources: Learning resource recommendations
        """
        start_time = time.time()
        
        try:
            # Create phase-specific prompt
            prompt = self._create_phase_prompt(
                phase["phase"],
                phase["title"],
                phase.get("skills_to_learn", []),
                phase.get("duration", "Varies"),
                role,
                level,
            )
            
            # Run inference
            response = await asyncio.to_thread(
                self._infer,
                prompt,
                256,
            )
            
            # Extract structured response
            enhancements = self._extract_json_from_response(response)

            description = enhancements.get("description", phase.get("title", ""))
            if not isinstance(description, str):
                description = str(description)

            objectives = self._normalize_string_list(
                enhancements.get("objectives", []),
                for_resources=False,
            )
            actions = self._normalize_string_list(
                enhancements.get("actions", []),
                for_resources=False,
            )
            resources = self._normalize_string_list(
                enhancements.get("resources", []),
                for_resources=True,
            )

            if not objectives:
                objectives = self._fallback_objectives(phase)
            if not actions:
                actions = self._actions_from_objectives(objectives)
            if not actions:
                actions = self._fallback_actions(phase)

            if len(actions) < 3:
                fallback_actions = self._fallback_actions(phase)
                for item in fallback_actions:
                    if item not in actions:
                        actions.append(item)
                    if len(actions) >= 4:
                        break

            # If parser-level generic defaults were used, prefer phase-aware actions.
            if actions[:4] == self._generic_default_actions():
                actions = self._fallback_actions(phase)
            if (not resources) or self._looks_generic_resources(resources):
                resources = self._fallback_resources(phase, role)

            # Keep only clearly followable actions and force Step prefix.
            followable_actions: List[str] = []
            for i, action in enumerate(actions[:4], start=1):
                text = str(action).strip()
                if not text:
                    continue
                if text.lower().startswith("step "):
                    followable_actions.append(text)
                else:
                    followable_actions.append(f"Step {i}: {text}")
            if not followable_actions:
                followable_actions = self._fallback_actions(phase)
            
            # Merge with original phase
            enhanced_phase = phase.copy()
            enhanced_phase.update({
                "enhanced_description": description,
                "suggested_actions": followable_actions,
                "learning_objectives": objectives,
                "recommended_resources": resources,
            })
            
            # Track metrics
            latency = time.time() - start_time
            self.metrics["total_calls"] += 1
            self.metrics["total_latency"] += latency
            self.metrics["avg_latency"] = (
                self.metrics["total_latency"] /
                self.metrics["total_calls"]
            )
            
            return enhanced_phase
            
        except Exception as e:
            # Fallback: keep roadmap usable even when inference fails.
            print(f"⚠️  Enhancement failed: {e}")
            fallback_phase = phase.copy()
            fallback_phase.update({
                "enhanced_description": phase.get("title", "Learning phase"),
                "learning_objectives": self._fallback_objectives(phase),
                "recommended_resources": self._fallback_resources(phase, role),
            })
            return fallback_phase
    
    async def enhance_roadmap(
        self,
        roadmap: Dict,
        role: str,
    ) -> Dict:
        """
        Enhance entire roadmap structure.
        
        Args:
            roadmap: Base roadmap dict with keys: level, title, 
                     summary, phases
            role: Target occupation role
        
        Returns:
            Enhanced roadmap with LLM descriptions for each phase
        """
        level = roadmap.get("level", "intermediate")
        
        # Enhance each phase concurrently
        enhanced_phases = await asyncio.gather(
            *[
                self.enhance_phase(phase, role, level)
                for phase in roadmap.get("phases", [])
            ]
        )
        
        # Create enhanced roadmap
        enhanced_roadmap = roadmap.copy()
        enhanced_roadmap["phases"] = enhanced_phases

        # Mark as AI enhanced only if at least one phase was actually enriched.
        is_enriched = any(
            bool(p.get("enhanced_description"))
            or bool(p.get("learning_objectives"))
            or bool(p.get("recommended_resources"))
            for p in enhanced_phases
        )
        enhanced_roadmap["ai_enhanced"] = is_enriched
        enhanced_roadmap["inference_mode"] = self.mode.value
        
        return enhanced_roadmap
    
    def get_metrics(self) -> Dict:
        """Return performance metrics."""
        return self.metrics.copy()


# ─────────────────────────────────────────────────────────────────────
# Async Interface for FastAPI Integration
# ─────────────────────────────────────────────────────────────────────

# Global enhancer instance (lazy-loaded)
_enhancer_instance: Optional[RoadmapEnhancer] = None


def get_enhancer(
    mode: InferenceMode = InferenceMode.HF_API,
) -> RoadmapEnhancer:
    """
    Get or create the global LLM enhancer instance.
    
    Using a singleton pattern for efficiency (model loading is expensive).
    """
    global _enhancer_instance
    
    if _enhancer_instance is None:
        _enhancer_instance = RoadmapEnhancer(mode=mode)
    
    return _enhancer_instance


async def enhance_roadmap_async(
    base_roadmap: Dict,
    role: str,
    mode: InferenceMode = InferenceMode.HF_API,
) -> Dict:
    """
    Convenience function for async roadmap enhancement.
    
    Usage in FastAPI:
        enhanced = await enhance_roadmap_async(roadmap, role)
    """
    enhancer = get_enhancer(mode)
    return await enhancer.enhance_roadmap(base_roadmap, role)
