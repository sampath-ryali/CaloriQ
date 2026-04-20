"""Rule-based QA engine for nutrition label questions."""

from __future__ import annotations

import os
import re

from models.nutrition_profile import NutritionProfile
from models.qa_response import QaResponse
from services.advanced_inference import QwenModel, analyze_health, calculate_confidence, recommend_diet


class QaEngineError(Exception):
    """Raised when question answering fails."""


ALLERGEN_KEYWORDS = {
    "gluten": {"gluten", "wheat", "barley", "rye", "triticale", "malt"},
    "peanuts": {"peanut", "peanuts"},
    "soy": {"soy", "soya", "soybean", "soybeans", "lecithin (soy)"},
    "dairy": {"milk", "dairy", "whey", "casein", "lactose", "cheese", "butter", "cream"},
}


def _normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", (question or "").strip().lower())


def _contains_any(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _detect_allergens(profile: NutritionProfile) -> list[str]:
    ingredient_text = " ".join(profile.ingredients).lower()
    detected = []
    for allergen, keywords in ALLERGEN_KEYWORDS.items():
        if _contains_any(ingredient_text, keywords):
            detected.append(allergen)
    return detected


def _summarize_nutrition(profile: NutritionProfile) -> list[str]:
    insights: list[str] = []

    if profile.calories is not None:
        if profile.calories >= 400:
            insights.append("high calorie product")
        elif profile.calories <= 120:
            insights.append("low calorie product")

    if profile.sugar_g is not None:
        if profile.sugar_g >= 20:
            insights.append("high sugar content")
        elif profile.sugar_g <= 5:
            insights.append("low sugar content")

    if profile.fat_g is not None and profile.fat_g <= 3:
        insights.append("low fat product")

    if profile.protein_g is not None and profile.protein_g >= 10:
        insights.append("high protein content")

    return insights


def _confidence_from_coverage(profile: NutritionProfile, question: str, answer: str) -> float:
    known_fields = sum(
        1
        for value in (profile.calories, profile.sugar_g, profile.fat_g, profile.protein_g)
        if value is not None
    )
    base = 0.45 + min(known_fields, 4) * 0.1
    if answer != "I could not determine the answer from the label text.":
        base += 0.1
    if _normalize_question(question) in {"what is the calorie count", "how many calories"} and profile.calories is not None:
        base += 0.1
    return round(min(base, 0.99), 2)


def _profile_to_inference_dict(profile: NutritionProfile) -> dict[str, float | str]:
    return {
        "calories": profile.calories if profile.calories is not None else "Not found",
        "protein": profile.protein_g if profile.protein_g is not None else "Not found",
        "fat": profile.fat_g if profile.fat_g is not None else "Not found",
        "carbs": profile.carbs_g if profile.carbs_g is not None else "Not found",
        "sodium": profile.sodium_mg if profile.sodium_mg is not None else "Not found",
        "fiber": profile.fiber_g if profile.fiber_g is not None else "Not found",
        "sugar": profile.sugar_g if profile.sugar_g is not None else "Not found",
    }


def _map_extraction_confidence(level: str) -> float:
    if level == "high":
        return 0.9
    if level == "medium":
        return 0.78
    return 0.62


def _answer_about_sugar(profile: NutritionProfile) -> tuple[str, str]:
    if profile.sugar_g is None:
        return "I could not determine the sugar amount from the label text.", "sugar"
    return f"The label indicates about {profile.sugar_g:g} g of sugar.", "sugar"


def _answer_about_calories(profile: NutritionProfile) -> tuple[str, str]:
    if profile.calories is None:
        return "I could not determine the calories from the label text.", "calories"
    return f"The label indicates about {profile.calories} calories.", "calories"


def _answer_about_allergens(profile: NutritionProfile, question: str) -> tuple[str, str, list[str]]:
    allergens = _detect_allergens(profile)
    targeted = [allergen for allergen in ALLERGEN_KEYWORDS if allergen in question]

    if targeted:
        matches = [allergen for allergen in targeted if allergen in allergens]
        if matches:
            return f"The ingredient list suggests the product may contain {', '.join(matches)}.", "allergens", [
                f"possible allergens detected: {', '.join(matches)}"
            ]
        return f"I did not find direct evidence of {', '.join(targeted)} in the ingredient list.", "allergens", [
            "no targeted allergen keywords detected"
        ]

    if allergens:
        return f"Potential allergens detected: {', '.join(allergens)}.", "allergens", [
            f"detected allergens: {', '.join(allergens)}"
        ]
    return "No common allergens were detected from the parsed ingredient list.", "allergens", ["no common allergens detected"]


def _is_fitness_goal_question(question: str) -> bool:
    goal_terms = (
        "muscle gain",
        "gain muscle",
        "fat loss",
        "lose fat",
        "weight loss",
        "cutting",
        "bulk",
        "bulking",
        "recomp",
        "based on these macros",
    )
    return any(term in question for term in goal_terms)


def _answer_fitness_goal(profile: NutritionProfile) -> tuple[str, str]:
    gain_score = 0
    loss_score = 0
    reasons: list[str] = []

    if profile.protein_g is not None:
        if profile.protein_g >= 20:
            gain_score += 2
            reasons.append("high protein supports muscle gain")
        elif profile.protein_g >= 10:
            gain_score += 1
            reasons.append("moderate protein can support training")
        else:
            loss_score += 1
            reasons.append("low protein is less ideal for muscle gain")

    if profile.calories is not None:
        if profile.calories <= 200:
            loss_score += 2
            reasons.append("lower calories favor fat loss")
        elif profile.calories <= 350:
            loss_score += 1
            reasons.append("moderate calories can fit fat-loss plans")
        elif profile.calories >= 400:
            gain_score += 1
            reasons.append("higher calories can support muscle gain")

    if profile.fat_g is not None:
        if profile.fat_g <= 8:
            loss_score += 1
            reasons.append("low fat can help calorie control")
        elif profile.fat_g >= 20:
            gain_score += 1
            reasons.append("higher fat increases energy density")

    if profile.carbs_g is not None:
        if profile.carbs_g <= 20:
            loss_score += 1
            reasons.append("lower carbs may help a cut")
        elif profile.carbs_g >= 40:
            gain_score += 1
            reasons.append("higher carbs can support training fuel")

    if profile.sodium_mg is not None and profile.sodium_mg > 500:
        reasons.append("sodium is relatively high, so watch overall daily intake")

    if gain_score > loss_score + 1:
        verdict = "This profile leans more toward muscle gain than fat loss."
    elif loss_score > gain_score + 1:
        verdict = "This profile leans more toward fat loss than muscle gain."
    else:
        verdict = "This profile looks mixed between fat loss and muscle gain goals."

    if reasons:
        return f"{verdict} Key factors: {', '.join(reasons[:3])}.", "fitness_goal"
    return (
        "I could not confidently classify this for muscle gain versus fat loss due to missing macro values.",
        "fitness_goal",
    )


def answer_question(profile: NutritionProfile, question: str) -> QaResponse:
    """Answer nutrition questions using VLM first, then deterministic fallback rules."""

    normalized_question = _normalize_question(question)
    if not normalized_question:
        raise QaEngineError("Question is required")

    profile_dict = _profile_to_inference_dict(profile)
    health = analyze_health(profile_dict)
    all_diet_recommendations = recommend_diet(profile_dict)
    health_insights = [str(item) for item in health.get("insights", [])]

    base_insights = _summarize_nutrition(profile)
    dynamic_insights: list[str] = []

    wants_health_context = any(
        keyword in normalized_question
        for keyword in (
            "healthy",
            "health",
            "diet",
            "recommend",
            "fitness",
            "good for me",
            "is this good",
        )
    )

    if os.getenv("ENABLE_QWEN", "false").lower() == "true":
        try:
            qwen = QwenModel(
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                model=os.getenv("QWEN_MODEL", "qwen2.5:3b"),
                request_timeout_sec=float(os.getenv("QWEN_TIMEOUT_SEC", "6")),
            )
            vlm_answer = qwen.call(f"Nutrition: {profile_dict}. Question: {question}")
            if vlm_answer:
                return QaResponse(
                    answer=vlm_answer,
                    confidence=_map_extraction_confidence(calculate_confidence(profile_dict)),
                    insights=sorted(dict.fromkeys(base_insights + health_insights + all_diet_recommendations)),
                    detected_intent="qwen_vlm",
                    source="qwen_vlm",
                    health_score=(int(health.get("score")) if wants_health_context and isinstance(health.get("score"), (int, float)) else None),
                    health_label=(str(health.get("label")) if wants_health_context and health.get("label") else None),
                    diet_recommendations=all_diet_recommendations if wants_health_context else [],
                )
        except Exception:
            # If Ollama/Qwen is unavailable, continue with deterministic fallback.
            pass

    answer = "I could not determine the answer from the label text."
    intent = "general"

    if any(keyword in normalized_question for keyword in ("calorie", "calories", "energy")):
        answer, intent = _answer_about_calories(profile)
    elif any(keyword in normalized_question for keyword in ("healthy", "health", "good for me", "is this good")):
        intent = "health"
        score = health.get("score")
        label = health.get("label")
        answer = (
            f"Based on extracted nutrition values, health score is {int(score)}/10 ({label})."
            if isinstance(score, (int, float)) and label
            else "I could not confidently determine a health score from the detected nutrition fields."
        )
    elif any(keyword in normalized_question for keyword in ("sugar", "sweet")):
        answer, intent = _answer_about_sugar(profile)
    elif _is_fitness_goal_question(normalized_question):
        answer, intent = _answer_fitness_goal(profile)
    elif any(keyword in normalized_question for keyword in ("gluten", "peanut", "peanuts", "soy", "dairy", "allergen", "allergy", "contains")):
        answer, intent, allergen_insights = _answer_about_allergens(profile, normalized_question)
        dynamic_insights.extend(allergen_insights)
    elif any(keyword in normalized_question for keyword in ("fat", "low fat", "fat content")):
        intent = "fat"
        if profile.fat_g is None:
            answer = "I could not determine the fat amount from the label text."
        else:
            answer = f"The label indicates about {profile.fat_g:g} g of fat."
    elif any(keyword in normalized_question for keyword in ("protein", "protein content")):
        intent = "protein"
        if profile.protein_g is None:
            answer = "I could not determine the protein amount from the label text."
        else:
            answer = f"The label indicates about {profile.protein_g:g} g of protein."
    elif any(keyword in normalized_question for keyword in ("ingredient", "ingredients", "made of", "contains")):
        intent = "ingredients"
        if profile.ingredients:
            answer = f"The ingredients listed are: {', '.join(profile.ingredients)}."
        else:
            answer = "I could not determine the ingredients from the label text."

    confidence = _confidence_from_coverage(profile, normalized_question, answer)
    if any(marker in answer.lower() for marker in ("could not determine", "no common allergens", "did not find direct evidence")):
        confidence = min(confidence, 0.58)

    combined_insights = sorted(
        dict.fromkeys(
            base_insights + (health_insights if wants_health_context else []) + dynamic_insights
        )
    )

    return QaResponse(
        answer=answer,
        confidence=confidence,
        insights=combined_insights,
        detected_intent=intent,
        source="rule_based",
        health_score=(int(health.get("score")) if wants_health_context and isinstance(health.get("score"), (int, float)) else None),
        health_label=(str(health.get("label")) if wants_health_context and health.get("label") else None),
        diet_recommendations=all_diet_recommendations if wants_health_context else [],
    )
