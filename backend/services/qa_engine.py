"""Rule-based QA engine for nutrition label questions."""

from __future__ import annotations

import os
import re
import requests

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


def _is_extraction_question(question: str) -> bool:
    nutrients = (
        r"sugar|fat|protein|carb|carbs|carbohydrate|sodium|salt|fiber|fibre|calories?|energy|"
        r"cholesterol|calcium|potassium|iron|saturated\s+fat|sat\s+fat|trans\s+fat|added\s+sugar|added\s+sugars"
    )
    extraction_markers = (
        r"\bhow much\b",
        r"\bhow many\b",
        r"\bwhat(?:'s| is) the (?:amount|value|count)\b",
        rf"\bhow much\s+(?:{nutrients})\b",
        rf"\btotal\s+(?:{nutrients})\b",
        rf"\b(?:{nutrients})\b\s*(?:amount|value|count)\b",
        rf"^(?:{nutrients})\??$",
        rf"^(?:how much|how many)\s+(?:{nutrients})\??$",
        r"\bingredients?\b",
    )
    return any(re.search(pattern, question) for pattern in extraction_markers)


def _is_reasoning_question(question: str) -> bool:
    reasoning_markers = (
        "is it",
        "is this",
        "does it",
        "do i",
        "should i",
        "good for me",
        "healthy",
        "health",
        "recommend",
        "better",
        "free",
        "low sugar",
        "high sugar",
        "contains sugar",
        "zero sugar",
        "sugar-free",
        "sugar free",
        "fat-free",
        "fat free",
    )
    return any(marker in question for marker in reasoning_markers)


def _classify_question_type(question: str) -> str:
    if _is_extraction_question(question) and not _is_reasoning_question(question):
        return "extraction"
    return "reasoning"


def _is_nutrient_status_question(question: str) -> bool:
    status_markers = (
        "sugar free",
        "sugar-free",
        "zero sugar",
        "no sugar",
        "free of sugar",
        "fat free",
        "fat-free",
        "zero fat",
        "low sugar",
        "high sugar",
        "low fat",
        "high fat",
    )
    return any(marker in question for marker in status_markers)


def _is_nutrient_summary_question(question: str) -> bool:
    summary_markers = (
        "what nutrients are there",
        "what nutrients are present",
        "what nutrients does it contain",
        "list nutrients",
        "nutrition information",
        "nutrients are there",
    )
    return any(marker in question for marker in summary_markers)


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

    if profile.cholesterol_mg is not None and profile.cholesterol_mg >= 20:
        insights.append("cholesterol present")

    if profile.calcium_mg is not None and profile.calcium_mg >= 100:
        insights.append("calcium present")

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
        "cholesterol": profile.cholesterol_mg if profile.cholesterol_mg is not None else "Not found",
        "calcium": profile.calcium_mg if profile.calcium_mg is not None else "Not found",
    }


def _map_extraction_confidence(level: str) -> float:
    if level == "high":
        return 0.9
    if level == "medium":
        return 0.78
    return 0.62


def _answer_about_sugar(profile: NutritionProfile) -> tuple[str, str]:
    if profile.sugar_per_serving_g is not None and profile.sugar_per_100g_g is not None:
        return (
            f"The label lists {profile.sugar_per_serving_g:g} g of sugar per serving and {profile.sugar_per_100g_g:g} g per 100 g.",
            "sugar",
        )
    if profile.sugar_g is None:
        return "I could not determine the sugar amount from the label text.", "sugar"
    return f"The label indicates about {profile.sugar_g:g} g of sugar.", "sugar"


def _answer_about_sugar_status(profile: NutritionProfile) -> tuple[str, str]:
    sugar_value = profile.sugar_per_serving_g if profile.sugar_per_serving_g is not None else profile.sugar_g
    if sugar_value is None:
        return "I could not determine whether the product is sugar free from the label text.", "sugar_status"
    if sugar_value <= 0:
        return "Yes, it appears sugar free (0 g sugar).", "sugar_status"
    return f"No, it is not sugar free. It contains about {sugar_value:g} g of sugar.", "sugar_status"


def _format_nutrient_value(label: str, value: float | int, unit: str) -> str:
    numeric_value = float(value)
    value_text = f"{int(numeric_value)}" if numeric_value.is_integer() else f"{numeric_value:g}"
    return f"- {label}: {value_text} {unit}"


def _build_nutrient_summary(profile: NutritionProfile) -> str:
    lines: list[str] = []

    def add_line(label: str, value: float | int | None, unit: str) -> None:
        if value is not None:
            lines.append(_format_nutrient_value(label, value, unit))

    add_line("Calories", profile.calories_per_serving if profile.calories_per_serving is not None else profile.calories, "kcal")
    add_line("Protein", profile.protein_per_serving_g if profile.protein_per_serving_g is not None else profile.protein_g, "g")
    add_line("Fat", profile.fat_per_serving_g if profile.fat_per_serving_g is not None else profile.fat_g, "g")
    add_line("Saturated Fat", profile.saturated_fat_per_serving_g if profile.saturated_fat_per_serving_g is not None else profile.saturated_fat_g, "g")
    add_line("Trans Fat", profile.trans_fat_per_serving_g if profile.trans_fat_per_serving_g is not None else profile.trans_fat_g, "g")
    add_line("Carbohydrates", profile.carbs_per_serving_g if profile.carbs_per_serving_g is not None else profile.carbs_g, "g")
    add_line("Added Sugars", profile.sugar_added_per_serving_g if profile.sugar_added_per_serving_g is not None else profile.sugar_added_g, "g")
    add_line("Total Sugars", profile.sugar_per_serving_g if profile.sugar_per_serving_g is not None else profile.sugar_g, "g")
    add_line("Fiber", profile.fiber_per_serving_g if profile.fiber_per_serving_g is not None else profile.fiber_g, "g")
    add_line("Sodium", profile.sodium_per_serving_mg if profile.sodium_per_serving_mg is not None else profile.sodium_mg, "mg")
    add_line("Cholesterol", profile.cholesterol_per_serving_mg if profile.cholesterol_per_serving_mg is not None else profile.cholesterol_mg, "mg")
    add_line("Calcium", profile.calcium_per_serving_mg if profile.calcium_per_serving_mg is not None else profile.calcium_mg, "mg")
    add_line("Potassium", profile.potassium_per_serving_mg if profile.potassium_per_serving_mg is not None else profile.potassium_mg, "mg")
    add_line("Iron", profile.iron_per_serving_mg if profile.iron_per_serving_mg is not None else profile.iron_mg, "mg")

    if not lines:
        return "I could not determine any nutrient values from the label text."

    return "Based on the nutrition information provided, here are the nutrients I found:\n" + "\n".join(lines)


def _answer_about_calories(profile: NutritionProfile) -> tuple[str, str]:
    if profile.calories_per_serving is not None and profile.calories_per_100g is not None:
        return (
            f"The label lists {profile.calories_per_serving} kcal per serving and {profile.calories_per_100g} kcal per 100 g.",
            "calories",
        )
    if profile.calories_per_serving is not None:
        return (f"The label indicates about {profile.calories_per_serving} kcal per serving.", "calories")
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
    question_type = _classify_question_type(normalized_question)
    strict_qwen = os.getenv("QWEN_STRICT", "true").lower() == "true"
    direct_fact_question = question_type == "extraction" or _is_nutrient_summary_question(normalized_question)

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

    enable_llm = (
        os.getenv("ENABLE_LLM", "false").lower() == "true" or
        os.getenv("ENABLE_QWEN", "false").lower() == "true"
    )
    llm_provider = os.getenv("LLM_PROVIDER", "qwen").lower().strip()

    if enable_llm and not direct_fact_question:
        try:
            context = (
                "You are CaloriQ, a friendly and professional nutrition AI assistant. "
                "Analyze the nutrition details and answer the user's question.\n"
                "Guidelines:\n"
                "- Keep the response concise, engaging, and easy to read on a mobile screen.\n"
                "- Use clean bullet points and emojis to summarize facts.\n"
                "- Bold important numbers or warnings.\n"
                "- Never mention system variables (like profile_dict, raw text, OCR, VLM, JSON).\n\n"
                f"Nutrition Facts: {profile_dict}\n"
                f"Ingredients: {', '.join(profile.ingredients) if profile.ingredients else 'None'}\n"
                f"Raw Label Text: {profile.raw_text}\n"
                f"User Question: {question}\n"
                "Answer:"
            )
            vlm_answer = None
            source_name = "qwen_vlm"

            if llm_provider == "gemini":
                gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
                if not gemini_key:
                    raise QaEngineError("GEMINI_API_KEY environment variable is missing")
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={gemini_key}"
                response = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": context}]}]},
                    headers={"Content-Type": "application/json"},
                    timeout=15,
                )
                response.raise_for_status()
                res_data = response.json()
                vlm_answer = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                source_name = "gemini"
            else:
                qwen = QwenModel(
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                    model=os.getenv("QWEN_MODEL", "qwen2.5:3b"),
                    request_timeout_sec=float(os.getenv("QWEN_TIMEOUT_SEC", "6")),
                )
                vlm_answer = qwen.call(context)
                source_name = "qwen_vlm"

            if vlm_answer:
                return QaResponse(
                    answer=vlm_answer,
                    confidence=_map_extraction_confidence(calculate_confidence(profile_dict)),
                    insights=sorted(dict.fromkeys(base_insights + health_insights + all_diet_recommendations)),
                    question_type=question_type,
                    detected_intent=source_name,
                    source=source_name,
                    health_score=(int(health.get("score")) if wants_health_context and isinstance(health.get("score"), (int, float)) else None),
                    health_label=(str(health.get("label")) if wants_health_context and health.get("label") else None),
                    diet_recommendations=all_diet_recommendations if wants_health_context else [],
                )
            if strict_qwen:
                raise QaEngineError(f"{llm_provider} returned an empty response")
        except Exception as exc:
            if strict_qwen:
                raise QaEngineError(f"{llm_provider} is unavailable: {exc}") from exc
            # If Ollama/Qwen is unavailable, continue with deterministic fallback.
            pass

    answer = "I could not determine the answer from the label text."
    intent = "general"

    if _is_nutrient_summary_question(normalized_question):
        answer = _build_nutrient_summary(profile)
        intent = "nutrient_summary"
        question_type = "extraction"
    elif any(keyword in normalized_question for keyword in ("cholesterol",)):
        intent = "cholesterol"
        if profile.cholesterol_per_serving_mg is not None and profile.cholesterol_per_100g_mg is not None:
            answer = (
                f"The label lists {profile.cholesterol_per_serving_mg:g} mg of cholesterol per serving "
                f"and {profile.cholesterol_per_100g_mg:g} mg per 100 g."
            )
        elif profile.cholesterol_mg is None:
            answer = "I could not determine the cholesterol amount from the label text."
        else:
            answer = f"The label indicates about {profile.cholesterol_mg:g} mg of cholesterol."
        question_type = "extraction"
    elif any(keyword in normalized_question for keyword in ("calcium",)):
        intent = "calcium"
        if profile.calcium_per_serving_mg is not None and profile.calcium_per_100g_mg is not None:
            answer = (
                f"The label lists {profile.calcium_per_serving_mg:g} mg of calcium per serving "
                f"and {profile.calcium_per_100g_mg:g} mg per 100 g."
            )
        elif profile.calcium_mg is None:
            answer = "I could not determine the calcium amount from the label text."
        else:
            answer = f"The label indicates about {profile.calcium_mg:g} mg of calcium."
        question_type = "extraction"
    elif any(keyword in normalized_question for keyword in ("potassium",)):
        intent = "potassium"
        if profile.potassium_per_serving_mg is not None and profile.potassium_per_100g_mg is not None:
            answer = (
                f"The label lists {profile.potassium_per_serving_mg:g} mg of potassium per serving "
                f"and {profile.potassium_per_100g_mg:g} mg per 100 g."
            )
        elif profile.potassium_mg is None:
            answer = "I could not determine the potassium amount from the label text."
        else:
            answer = f"The label indicates about {profile.potassium_mg:g} mg of potassium."
        question_type = "extraction"
    elif any(keyword in normalized_question for keyword in ("iron",)):
        intent = "iron"
        if profile.iron_per_serving_mg is not None and profile.iron_per_100g_mg is not None:
            answer = (
                f"The label lists {profile.iron_per_serving_mg:g} mg of iron per serving "
                f"and {profile.iron_per_100g_mg:g} mg per 100 g."
            )
        elif profile.iron_mg is None:
            answer = "I could not determine the iron amount from the label text."
        else:
            answer = f"The label indicates about {profile.iron_mg:g} mg of iron."
        question_type = "extraction"

    if any(keyword in normalized_question for keyword in ("sugar free", "sugar-free", "zero sugar", "no sugar", "free of sugar")):
        answer, intent = _answer_about_sugar_status(profile)
        question_type = "reasoning"
    elif any(keyword in normalized_question for keyword in ("calorie", "calories", "energy")):
        intent = "calories"
        if profile.calories_per_serving is not None and profile.calories_per_100g is not None:
            answer = (
                f"The label lists {profile.calories_per_serving:g} kcal per serving and {profile.calories_per_100g:g} kcal per 100 g."
            )
        else:
            answer, intent = _answer_about_calories(profile)
    elif any(keyword in normalized_question for keyword in ("total sugar", "sugar")):
        if profile.sugar_per_serving_g is not None and profile.sugar_per_100g_g is not None:
            answer = (
                f"The label lists {profile.sugar_per_serving_g:g} g of sugar per serving "
                f"and {profile.sugar_per_100g_g:g} g per 100 g."
            )
        else:
            answer, intent = _answer_about_sugar(profile)
        intent = "sugar"
    elif any(keyword in normalized_question for keyword in ("healthy", "health", "good for me", "is this good")):
        intent = "health"
        score = health.get("score")
        label = health.get("label")
        answer = (
            f"Based on extracted nutrition values, health score is {int(score)}/10 ({label})."
            if isinstance(score, (int, float)) and label
            else "I could not confidently determine a health score from the detected nutrition fields."
        )
    elif _is_fitness_goal_question(normalized_question):
        answer, intent = _answer_fitness_goal(profile)
    elif any(keyword in normalized_question for keyword in ("gluten", "peanut", "peanuts", "soy", "dairy", "allergen", "allergy", "contains")):
        answer, intent, allergen_insights = _answer_about_allergens(profile, normalized_question)
        dynamic_insights.extend(allergen_insights)
    elif any(keyword in normalized_question for keyword in ("fat", "low fat", "fat content")):
        intent = "fat"
        if profile.fat_per_serving_g is not None and profile.fat_per_100g_g is not None:
            answer = (
                f"The label lists {profile.fat_per_serving_g:g} g of fat per serving "
                f"and {profile.fat_per_100g_g:g} g per 100 g."
            )
        elif profile.fat_g is None:
            answer = "I could not determine the fat amount from the label text."
        else:
            answer = f"The label indicates about {profile.fat_g:g} g of fat."
    elif any(keyword in normalized_question for keyword in ("protein", "protein content")):
        intent = "protein"
        if profile.protein_per_serving_g is not None and profile.protein_per_100g_g is not None:
            answer = (
                f"The label lists {profile.protein_per_serving_g:g} g of protein per serving "
                f"and {profile.protein_per_100g_g:g} g per 100 g."
            )
        elif profile.protein_g is None:
            answer = "I could not determine the protein amount from the label text."
        else:
            answer = f"The label indicates about {profile.protein_g:g} g of protein."
    elif any(keyword in normalized_question for keyword in ("carb", "carbs", "carbohydrate")):
        intent = "carbohydrate"
        if profile.carbs_per_serving_g is not None and profile.carbs_per_100g_g is not None:
            answer = (
                f"The label lists {profile.carbs_per_serving_g:g} g of carbohydrate per serving "
                f"and {profile.carbs_per_100g_g:g} g per 100 g."
            )
        elif profile.carbs_g is None:
            answer = "I could not determine the carbohydrate amount from the label text."
        else:
            answer = f"The label indicates about {profile.carbs_g:g} g of carbohydrate."
    elif any(keyword in normalized_question for keyword in ("saturated fat", "sat fat")):
        intent = "saturated_fat"
        if profile.saturated_fat_per_serving_g is not None and profile.saturated_fat_per_100g_g is not None:
            answer = (
                f"The label lists {profile.saturated_fat_per_serving_g:g} g of saturated fat per serving "
                f"and {profile.saturated_fat_per_100g_g:g} g per 100 g."
            )
        elif profile.saturated_fat_g is None:
            answer = "I could not determine the saturated fat amount from the label text."
        else:
            answer = f"The label indicates about {profile.saturated_fat_g:g} g of saturated fat."
        question_type = "extraction"
    elif any(keyword in normalized_question for keyword in ("trans fat",)):
        intent = "trans_fat"
        if profile.trans_fat_per_serving_g is not None and profile.trans_fat_per_100g_g is not None:
            answer = (
                f"The label lists {profile.trans_fat_per_serving_g:g} g of trans fat per serving "
                f"and {profile.trans_fat_per_100g_g:g} g per 100 g."
            )
        elif profile.trans_fat_g is None:
            answer = "I could not determine the trans fat amount from the label text."
        else:
            answer = f"The label indicates about {profile.trans_fat_g:g} g of trans fat."
        question_type = "extraction"
    elif any(keyword in normalized_question for keyword in ("sodium", "salt")):
        intent = "sodium"
        if profile.sodium_per_serving_mg is not None and profile.sodium_per_100g_mg is not None:
            answer = (
                f"The label lists {profile.sodium_per_serving_mg:g} mg of sodium per serving "
                f"and {profile.sodium_per_100g_mg:g} mg per 100 g."
            )
        elif profile.sodium_mg is None:
            answer = "I could not determine the sodium amount from the label text."
        else:
            answer = f"The label indicates about {profile.sodium_mg:g} mg of sodium."
    elif any(keyword in normalized_question for keyword in ("fiber", "fibre")):
        intent = "fiber"
        if profile.fiber_per_serving_g is not None and profile.fiber_per_100g_g is not None:
            answer = (
                f"The label lists {profile.fiber_per_serving_g:g} g of fiber per serving "
                f"and {profile.fiber_per_100g_g:g} g per 100 g."
            )
        elif profile.fiber_g is None:
            answer = "I could not determine the fiber amount from the label text."
        else:
            answer = f"The label indicates about {profile.fiber_g:g} g of fiber."
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
        question_type=question_type,
        detected_intent=intent,
        source="rule_based",
        health_score=(int(health.get("score")) if wants_health_context and isinstance(health.get("score"), (int, float)) else None),
        health_label=(str(health.get("label")) if wants_health_context and health.get("label") else None),
        diet_recommendations=all_diet_recommendations if wants_health_context else [],
    )
