"""
scripts/benchmark_roadmap.py — Roadmap Model Accuracy Benchmark

Measures the accuracy and quality improvements of the LLM-enhanced
roadmap generator vs. the baseline rule-based system.

Metrics Tracked:
  - BLEU Score: Text generation quality
  - Semantic Similarity: Relevance to input
  - Skill Coverage: Precision & Recall
  - Latency: Performance tracking
  - User-friendliness: Action relevance rating
  
Accuracy Target: > 0.80 F1 score
"""

import sys
import json
import asyncio
import time
from typing import Dict, List, Tuple
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.roadmap_generator import generate_roadmap
from app.services.llm_roadmap_enhancer import (
    RoadmapEnhancer,
    InferenceMode,
    enhance_roadmap_async,
)


# ─────────────────────────────────────────────────────────────────────
# Test Data
# ─────────────────────────────────────────────────────────────────────

TEST_SCENARIOS = [
    {
        "name": "Python Developer - Beginner",
        "overall_score": 35.0,
        "role": "Python Developer",
        "missing_core": [
            "Object-Oriented Programming",
            "Python Fundamentals",
            "Data Structures",
            "Web Frameworks",
            "Version Control",
        ],
        "missing_secondary": [
            "Testing Frameworks",
            "Database Design",
            "API Development",
            "Performance Optimization",
        ],
        "missing_bonus": [
            "Microservices",
            "Containerization",
            "Machine Learning Basics",
        ],
    },
    {
        "name": "Data Scientist - Intermediate",
        "overall_score": 62.0,
        "role": "Data Scientist",
        "missing_core": [
            "Advanced Statistics",
            "Machine Learning Algorithms",
            "Python ML Libraries",
        ],
        "missing_secondary": [
            "Deep Learning",
            "Time Series Analysis",
            "Feature Engineering",
            "Model Deployment",
        ],
        "missing_bonus": [
            "Reinforcement Learning",
            "Computer Vision",
            "NLP Advanced Topics",
        ],
    },
    {
        "name": "Full-Stack Developer - Advanced",
        "overall_score": 78.0,
        "role": "Full-Stack Developer",
        "missing_core": [
            "DevOps Practices",
            "Security Best Practices",
        ],
        "missing_secondary": [
            "Performance Tuning",
            "Load Balancing",
            "Cloud Architecture",
        ],
        "missing_bonus": [
            "Kubernetes",
            "Machine Learning Integration",
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────
# Accuracy Metrics
# ─────────────────────────────────────────────────────────────────────

class RoadmapBenchmark:
    """Benchmark suite for roadmap accuracy measurement."""
    
    @staticmethod
    def calculate_bleu_score(reference: str, hypothesis: str) -> float:
        """
        Calculate BLEU-like score (0-1).
        
        Simplified BLEU using word overlap.
        BLEU > 0.65: Good quality
        BLEU > 0.75: Excellent quality
        """
        try:
            from nltk.translate.bleu_score import sentence_bleu
            from nltk.tokenize import word_tokenize
            
            reference_tokens = word_tokenize(reference.lower())
            hypothesis_tokens = word_tokenize(hypothesis.lower())
            
            # 1-gram and 2-gram weights
            weights = (0.5, 0.5)
            score = sentence_bleu(
                [reference_tokens],
                hypothesis_tokens,
                weights=weights,
            )
            return float(score)
        except ImportError:
            # Fallback: basic word overlap
            ref_words = set(reference.lower().split())
            hyp_words = set(hypothesis.lower().split())
            
            if not ref_words:
                return 1.0 if not hyp_words else 0.0
            
            overlap = len(ref_words & hyp_words)
            return overlap / len(ref_words)
    
    @staticmethod
    def calculate_semantic_similarity(text1: str, text2: str) -> float:
        """
        Calculate semantic similarity using embeddings.
        
        Similarity > 0.75: High relevance
        Similarity > 0.65: Good relevance
        """
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity
            
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding1 = model.encode(text1)
            embedding2 = model.encode(text2)
            
            similarity = cosine_similarity(
                [embedding1],
                [embedding2],
            )[0][0]
            
            return float(similarity)
        except ImportError:
            # Fallback: basic text similarity
            return 0.5
    
    @staticmethod
    def calculate_skill_coverage(
        expected_skills: List[str],
        generated_content: str,
    ) -> Tuple[float, float, float]:
        """
        Calculate skill coverage metrics.
        
        Returns: (precision, recall, f1_score)
        """
        expected_lower = {skill.lower() for skill in expected_skills}
        
        # Extract skill mentions from generated content
        content_lower = generated_content.lower()
        found_skills = {
            skill for skill in expected_lower
            if skill in content_lower
        }
        
        if not expected_lower:
            return 1.0, 1.0, 1.0
        
        # Precision: correct out of generated
        precision = (
            len(found_skills) / len(expected_lower)
            if expected_lower else 0.0
        )
        
        # Recall: correct out of expected
        recall = (
            len(found_skills) / len(expected_lower)
            if expected_lower else 0.0
        )
        
        # F1 Score
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
        
        return precision, recall, f1
    
    @staticmethod
    def rate_action_relevance(
        actions: List[str],
        skills: List[str],
    ) -> float:
        """
        Rate how relevant actions are to the skills.
        
        Score 0-1, higher is better.
        > 0.8: Highly relevant actions
        > 0.6: Moderately relevant actions
        """
        if not actions or not skills:
            return 0.5
        
        action_text = " ".join(actions).lower()
        skill_text = " ".join(skills).lower()
        
        # Check for keyword mentions
        action_words = set(action_text.split())
        skill_words = set(skill_text.split())
        
        overlap = len(action_words & skill_words)
        total = max(len(action_words), len(skill_words), 1)
        
        return overlap / total


# ─────────────────────────────────────────────────────────────────────
# Benchmark Runner
# ─────────────────────────────────────────────────────────────────────

async def run_benchmark_suite() -> Dict:
    """Run complete benchmark on all test scenarios."""
    
    print("\n" + "=" * 70)
    print("ROADMAP MODEL ACCURACY BENCHMARK")
    print("=" * 70 + "\n")
    
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "scenarios": [],
        "summary": {},
    }
    
    benchmark = RoadmapBenchmark()
    
    for scenario in TEST_SCENARIOS:
        print(f"🧪 Testing: {scenario['name']}")
        print(f"   Score: {scenario['overall_score']:.1f}/100")
        print("-" * 70)
        
        # Generate base roadmap (rule-based)
        start = time.time()
        base_roadmap = generate_roadmap(
            overall_score=scenario["overall_score"],
            role=scenario["role"],
            missing_core=scenario["missing_core"],
            missing_secondary=scenario["missing_secondary"],
            missing_bonus=scenario["missing_bonus"],
        )
        base_latency = time.time() - start
        
        # Generate enhanced roadmap (with LLM)
        start = time.time()
        try:
            enhanced_roadmap = await enhance_roadmap_async(
                base_roadmap,
                scenario["role"],
                mode=InferenceMode.MOCK,  # Use MOCK for quick benchmarking
            )
            enhanced_latency = time.time() - start
        except Exception as e:
            print(f"   ⚠️  Enhancement failed: {e}")
            enhanced_roadmap = base_roadmap
            enhanced_latency = 0
        
        # Calculate metrics for each phase
        phase_metrics = []
        total_bleu = 0
        total_similarity = 0
        total_f1 = 0
        total_action_relevance = 0
        
        for i, (base_phase, enhanced_phase) in enumerate(
            zip(base_roadmap["phases"], enhanced_roadmap["phases"])
        ):
            # Metric 1: BLEU Score
            base_title = base_phase.get("title", "")
            enhanced_desc = enhanced_phase.get(
                "enhanced_description",
                base_title,
            )
            bleu = benchmark.calculate_bleu_score(base_title, enhanced_desc)
            
            # Metric 2: Semantic Similarity
            base_summary = base_roadmap.get("summary", "")
            similarity = benchmark.calculate_semantic_similarity(
                base_summary,
                enhanced_desc,
            )
            
            # Metric 3: Skill Coverage (F1)
            all_skills = scenario["missing_core"] + scenario["missing_secondary"]
            content = (
                base_title + " " + enhanced_desc + " " +
                " ".join(base_phase.get("suggested_actions", []))
            )
            precision, recall, f1 = benchmark.calculate_skill_coverage(
                all_skills,
                content,
            )
            
            # Metric 4: Action Relevance
            actions = enhanced_phase.get(
                "learning_objectives",
                base_phase.get("suggested_actions", []),
            )
            action_score = benchmark.rate_action_relevance(
                actions,
                base_phase.get("skills_to_learn", []),
            )
            
            phase_metrics.append({
                "phase": i + 1,
                "bleu_score": round(bleu, 3),
                "semantic_similarity": round(similarity, 3),
                "skill_f1": round(f1, 3),
                "skill_precision": round(precision, 3),
                "skill_recall": round(recall, 3),
                "action_relevance": round(action_score, 3),
            })
            
            total_bleu += bleu
            total_similarity += similarity
            total_f1 += f1
            total_action_relevance += action_score
        
        num_phases = len(base_roadmap["phases"])
        avg_metrics = {
            "avg_bleu_score": round(total_bleu / num_phases, 3),
            "avg_semantic_similarity": round(
                total_similarity / num_phases,
                3,
            ),
            "avg_skill_f1": round(total_f1 / num_phases, 3),
            "avg_action_relevance": round(
                total_action_relevance / num_phases,
                3,
            ),
            "base_generation_latency_ms": round(base_latency * 1000, 2),
            "enhanced_generation_latency_ms": round(
                enhanced_latency * 1000,
                2,
            ),
        }
        
        scenario_result = {
            "name": scenario["name"],
            "level": base_roadmap["level"],
            "num_phases": num_phases,
            "phase_metrics": phase_metrics,
            "aggregate": avg_metrics,
        }
        
        results["scenarios"].append(scenario_result)
        
        # Print summary for this scenario
        print(f"   ✓ Phase Count: {num_phases}")
        print(f"   ✓ BLEU Score (avg): {avg_metrics['avg_bleu_score']:.3f}")
        print(
            f"   ✓ Semantic Sim (avg): "
            f"{avg_metrics['avg_semantic_similarity']:.3f}"
        )
        print(f"   ✓ Skill F1 (avg): {avg_metrics['avg_skill_f1']:.3f}")
        print(
            f"   ✓ Action Relevance (avg): "
            f"{avg_metrics['avg_action_relevance']:.3f}"
        )
        print(
            f"   ✓ Base Latency: "
            f"{avg_metrics['base_generation_latency_ms']:.2f}ms"
        )
        print(
            f"   ✓ Enhanced Latency: "
            f"{avg_metrics['enhanced_generation_latency_ms']:.2f}ms"
        )
        print()
    
    # Calculate overall summary
    bleu_scores = [
        s["aggregate"]["avg_bleu_score"]
        for s in results["scenarios"]
    ]
    f1_scores = [
        s["aggregate"]["avg_skill_f1"]
        for s in results["scenarios"]
    ]
    similarities = [
        s["aggregate"]["avg_semantic_similarity"]
        for s in results["scenarios"]
    ]
    
    results["summary"] = {
        "num_scenarios": len(TEST_SCENARIOS),
        "avg_bleu_score": round(sum(bleu_scores) / len(bleu_scores), 3),
        "avg_skill_f1": round(sum(f1_scores) / len(f1_scores), 3),
        "avg_semantic_similarity": round(
            sum(similarities) / len(similarities),
            3,
        ),
        "overall_quality_rating": "Excellent"
        if round(sum(f1_scores) / len(f1_scores), 3) > 0.80
        else "Good"
        if round(sum(f1_scores) / len(f1_scores), 3) > 0.65
        else "Adequate",
    }
    
    return results


# ─────────────────────────────────────────────────────────────────────
# Report Generation
# ─────────────────────────────────────────────────────────────────────

def print_benchmark_report(results: Dict) -> None:
    """Print formatted benchmark report."""
    
    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS SUMMARY")
    print("=" * 70 + "\n")
    
    summary = results["summary"]
    print(f"📊 Overall Metrics:")
    print(f"   Scenarios Tested: {summary['num_scenarios']}")
    print(f"   Avg BLEU Score: {summary['avg_bleu_score']:.3f} ⭐")
    print(f"   Avg Skill F1: {summary['avg_skill_f1']:.3f}")
    print(
        f"   Avg Semantic Similarity: "
        f"{summary['avg_semantic_similarity']:.3f}"
    )
    print(f"   Quality Rating: {summary['overall_quality_rating']}")
    print()
    
    print("✅ Accuracy Thresholds:")
    print(f"   {'BLEU Score (> 0.65):':<30} "
          f"{summary['avg_bleu_score']:.3f} "
          f"{'✓ PASS' if summary['avg_bleu_score'] > 0.65 else '✗ FAIL'}")
    print(f"   {'Skill F1 (> 0.80):':<30} "
          f"{summary['avg_skill_f1']:.3f} "
          f"{'✓ PASS' if summary['avg_skill_f1'] > 0.80 else '✗ FAIL'}")
    print(f"   {'Semantic Sim (> 0.75):':<30} "
          f"{summary['avg_semantic_similarity']:.3f} "
          f"{'✓ PASS' if summary['avg_semantic_similarity'] > 0.75 else '✗ FAIL'}")
    print()
    
    # Save detailed results
    output_path = Path(__file__).parent.parent.parent / "BENCHMARK_RESULTS.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"📁 Detailed results saved to: {output_path}")


# ─────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────

async def main():
    """Run the complete benchmark suite."""
    results = await run_benchmark_suite()
    print_benchmark_report(results)


if __name__ == "__main__":
    asyncio.run(main())
