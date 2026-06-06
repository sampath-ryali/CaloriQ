"""Advanced nutrition inference utilities migrated from the VLM project."""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Any, Optional

import requests


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextNormalizer:
    """Normalize OCR text for nutrition extraction."""

    @staticmethod
    def normalize(text: str) -> str:
        """Clean and normalize text."""

        text = " ".join(text.split())
        text = text.lower()
        text = re.sub(r"[^\w\s\d./-]", "", text)
        return text

    @staticmethod
    def extract_value(text: str) -> Optional[float]:
        """Extract numeric value from text."""

        match = re.search(r"(\d+\.?\d*)", text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None


class NutritionExtractor:
    """Extract nutrition values from OCR text using regex patterns."""

    PATTERNS = {
        "calories": [
            r"\bcalories?\b\s*(?:[:\-]|is)?\s*(\d{1,4}(?:\.\d+)?)\b",
            r"\benergy\b\s*(?:[:\-]|is)?\s*(\d{1,4}(?:\.\d+)?)\s*(?:kcal|cal)?\b",
            r"\b(\d{1,4}(?:\.\d+)?)\s*(?:kcal|cal)\b",
        ],
        "protein": [
            r"\bprotein(?:e)?\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*g\b",
        ],
        "fat": [
            r"\b(?:total\s+)?fats?\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*g\b",
        ],
        "saturated_fat": [
            r"\b(?:saturated\s+fat|sat\.?\s*fat)\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*g\b",
        ],
        "trans_fat": [
            r"\btrans\s+fat\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*g\b",
        ],
        "carbs": [
            r"\bcarb(?:ohydrate)?s?\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*g\b",
        ],
        "sodium": [
            r"\bsodium\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*mg\b",
            r"\bsalt\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*(?:mg|g)?\b",
        ],
        "fiber": [
            r"\b(?:dietary\s+)?fiber\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*g\b",
        ],
        "sugar": [
            r"\bsugars?\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*g\b",
        ],
        "sugar_added": [
            r"\b(?:added\s+sugars?|added\s+sugar)\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*g\b",
        ],
        "cholesterol": [
            r"\bcholesterol\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*mg\b",
        ],
        "calcium": [
            r"\bcalcium\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*mg\b",
        ],
        "potassium": [
            r"\bpotassium\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*mg\b",
        ],
        "iron": [
            r"\biron\b\s*(?:[:\-]|is)?\s*(\d+(?:\.\d+)?)\s*mg\b",
        ],
    }

    def extract(self, ocr_text: str) -> dict[str, Any]:
        """Extract nutrition values from OCR text."""

        normalized = TextNormalizer.normalize(ocr_text)
        result: dict[str, Any] = {}

        for field, patterns in self.PATTERNS.items():
            value = None
            for pattern in patterns:
                match = re.search(pattern, normalized, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        break
                    except (ValueError, IndexError):
                        continue

            result[field] = value if value is not None else "Not found"

        return result


def analyze_health(data: dict[str, Any]) -> dict[str, Any]:
    """Analyze nutrition data and return health score with insights."""

    def safe_extract(value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if value == "Not found":
            return None
        try:
            return float(str(value))
        except Exception:
            return None

    protein = safe_extract(data.get("protein", "Not found"))
    carbs = safe_extract(data.get("carbs", "Not found"))
    fat = safe_extract(data.get("fat", "Not found"))
    sodium = safe_extract(data.get("sodium", "Not found"))
    calories = safe_extract(data.get("calories", "Not found"))

    score = 5
    insights: list[str] = []

    if protein is not None and protein > 15:
        score += 2
        insights.append("High protein content")
    elif protein is not None and protein > 8:
        score += 1
        insights.append("Good protein level")
    elif protein is not None and protein < 3:
        insights.append("Low protein content")

    if carbs is not None and carbs > 50:
        score -= 2
        insights.append("High carbohydrate content")
    elif carbs is not None and carbs > 30:
        score -= 1
        insights.append("Moderate carbs")

    if fat is not None and fat > 20:
        score -= 1
        insights.append("High fat content")
    elif fat is not None and fat < 3:
        insights.append("Low fat (may be too lean)")

    if sodium is not None and sodium > 600:
        score -= 2
        insights.append("High sodium - limit intake")
    elif sodium is not None and sodium > 300:
        score -= 1
        insights.append("Moderate sodium level")

    if calories is not None and calories > 400:
        insights.append("High calorie per serving")
    elif calories is not None and calories < 50:
        insights.append("Very low calorie")

    if not insights:
        insights.append("Not enough nutrition fields were detected for strong health conclusions")

    score = max(1, min(10, score))

    if score >= 8:
        health_label = "Excellent"
    elif score >= 6:
        health_label = "Good"
    elif score >= 4:
        health_label = "Moderate"
    else:
        health_label = "Poor"

    return {
        "score": score,
        "label": health_label,
        "insights": insights,
    }


def recommend_diet(data: dict[str, Any]) -> list[str]:
    """Recommend suitable diets based on nutrition content."""

    def safe_extract(value: Any) -> float | None:
        if isinstance(value, (int, float)):
            return float(value)
        if value == "Not found":
            return None
        try:
            return float(str(value))
        except Exception:
            return None

    protein = safe_extract(data.get("protein", "Not found"))
    carbs = safe_extract(data.get("carbs", "Not found"))
    fat = safe_extract(data.get("fat", "Not found"))
    sodium = safe_extract(data.get("sodium", "Not found"))

    recommendations: list[str] = []

    if carbs is not None and fat is not None and carbs < 5 and fat > 5:
        recommendations.append("✓ Keto-friendly")

    if protein is not None and carbs is not None and protein > 15 and carbs >= 20:
        recommendations.append("✓ Good for muscle gain")

    if sodium is not None and sodium < 200:
        recommendations.append("✓ Low sodium (heart-friendly)")

    if protein is not None and protein > 20:
        recommendations.append("✓ High protein (fitness-focused)")

    if protein is not None and fat is not None and protein > 5 and fat > 2:
        recommendations.append("✓ Could be vegetarian-friendly")

    if carbs is not None and carbs < 20:
        recommendations.append("✓ Diabetic-friendly (low carbs)")

    if not recommendations:
        recommendations.append("○ Balanced - suitable for general diet")

    return recommendations


def calculate_confidence(data: dict[str, Any]) -> str:
    """Calculate extraction confidence based on fields found."""

    key_fields = ["calories", "protein", "fat", "carbs", "sodium", "fiber", "sugar", "cholesterol", "calcium"]
    found_fields = sum(
        1
        for field in key_fields
        if data.get(field) != "Not found" and data.get(field) is not None
    )

    if found_fields >= 5:
        return "high"
    if found_fields >= 3:
        return "medium"
    return "low"


class QwenModel:
    """Interface to Qwen model via Ollama API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:3b",
        request_timeout_sec: float = 6.0,
    ):
        self.base_url = base_url
        self.model = model
        self.endpoint = f"{base_url}/api/generate"
        self.tags_endpoint = f"{base_url}/api/tags"
        self.version_endpoint = f"{base_url}/api/version"
        self.request_timeout_sec = request_timeout_sec

    def ensure_ready(self) -> None:
        """Verify that Ollama is reachable and the configured model is available."""

        version_response = requests.get(self.version_endpoint, timeout=self.request_timeout_sec)
        version_response.raise_for_status()

        tags_response = requests.get(self.tags_endpoint, timeout=self.request_timeout_sec)
        tags_response.raise_for_status()
        payload = tags_response.json()
        models = payload.get("models", [])

        if not any(str(item.get("name", "")).strip() == self.model for item in models if isinstance(item, dict)):
            raise RuntimeError(f"Qwen model '{self.model}' is not available in Ollama")

    def call(self, prompt: str, temperature: float = 0.7) -> str:
        """Call Qwen model via Ollama API, fallback to free Hugging Face API if unavailable."""

        # Try Ollama first
        try:
            response = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False,
                },
                timeout=self.request_timeout_sec,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
        except Exception:
            # Fallback to HuggingFace Inference API (Free & runs Qwen2.5)
            logger.info("Ollama unreachable. Falling back to free HuggingFace API...")
            try:
                models = [
                    "Qwen/Qwen2.5-7B-Instruct",
                    "Qwen/Qwen2.5-1.5B-Instruct",
                    "Qwen/Qwen2.5-72B-Instruct"
                ]
                headers = {"Content-Type": "application/json"}
                hf_token = os.getenv("HF_TOKEN")
                if hf_token:
                    headers["Authorization"] = f"Bearer {hf_token}"
                
                for model_id in models:
                    hf_url = "https://router.huggingface.co/v1/chat/completions"
                    logger.info("Trying Hugging Face model: %s", model_id)
                    for attempt in range(3):
                        try:
                            res = requests.post(
                                hf_url,
                                json={
                                    "model": model_id,
                                    "messages": [{"role": "user", "content": prompt}],
                                    "temperature": temperature,
                                    "max_tokens": 256
                                },
                                headers=headers,
                                timeout=15,
                            )
                            if res.status_code == 200:
                                payload = res.json()
                                choices = payload.get("choices", [])
                                if choices:
                                    content = choices[0].get("message", {}).get("content", "")
                                    return content.strip()
                            elif res.status_code == 503:
                                logger.info("Model %s is loading. Retrying in 3 seconds...", model_id)
                                time.sleep(3)
                            else:
                                logger.error("Model %s returned code %s: %s", model_id, res.status_code, res.text)
                                break
                        except Exception as e:
                            logger.error("Request to model %s failed: %s", model_id, e)
                            break
            except Exception as hf_exc:
                logger.error("Hugging Face fallback failed: %s", hf_exc)
        
        return ""


def answer_questions(
    data: dict[str, Any],
    questions: list[str],
    use_qwen: bool = False,
    qwen_model: Optional[QwenModel] = None,
) -> dict[str, Any]:
    """Answer questions about nutrition using rules or Qwen LLM."""

    strict_qwen = os.getenv("QWEN_STRICT", "true").lower() == "true"

    def safe_extract(value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if value == "Not found":
            return 0.0
        try:
            return float(str(value))
        except Exception:
            return 0.0

    answers: dict[str, Any] = {}
    calories = safe_extract(data.get("calories", 0))
    protein = safe_extract(data.get("protein", 0))
    fat = safe_extract(data.get("fat", 0))
    carbs = safe_extract(data.get("carbs", 0))
    sodium = safe_extract(data.get("sodium", 0))

    for question in questions:
        q_lower = question.lower()

        if "calor" in q_lower:
            answers[question] = {"answer": f"{int(calories)} kcal", "method": "rule-based"}
        elif "protein" in q_lower:
            answers[question] = {"answer": f"{protein:.1f}g", "method": "rule-based"}
        elif "fat" in q_lower and "saturated" not in q_lower:
            answers[question] = {"answer": f"{fat:.1f}g", "method": "rule-based"}
        elif "carb" in q_lower:
            answers[question] = {"answer": f"{carbs:.1f}g", "method": "rule-based"}
        elif "sodium" in q_lower or "salt" in q_lower:
            answers[question] = {"answer": f"{int(sodium)}mg", "method": "rule-based"}
        elif "healthy" in q_lower:
            health = analyze_health(data)
            answers[question] = {
                "answer": f"Score: {health['score']}/10 ({health['label']})",
                "insights": health["insights"],
                "method": "rule-based",
            }
        else:
            if use_qwen and qwen_model:
                context = f"""
                Nutrition Facts:
                - Calories: {calories} kcal
                - Protein: {protein}g
                - Fat: {fat}g
                - Carbs: {carbs}g
                - Sodium: {sodium}mg

                Question: {question}
                Answer concisely:
                """
                if strict_qwen:
                    qwen_model.ensure_ready()
                qwen_answer = qwen_model.call(context)
                answers[question] = {
                    "answer": qwen_answer if qwen_answer else "Unable to answer",
                    "method": "qwen" if qwen_answer else ("error" if strict_qwen else "fallback"),
                }
            else:
                answers[question] = {
                    "answer": "Question not supported",
                    "method": "unsupported",
                }

    return answers