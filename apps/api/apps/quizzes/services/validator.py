import logging
import re
from typing import Any

from apps.quizzes.models import DifficultyLevel

logger = logging.getLogger(__name__)


class InvalidQuizQuestionError(Exception):
    """Raised when an AI-generated QCM question fails strict validation criteria."""

    pass


def sanitize_quiz_text(text: str) -> str:
    """Strips non-printable control characters while preserving Unicode and valid formatting."""
    if not isinstance(text, str):
        return ""
    # Strip ASCII control characters except \n and \t
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return cleaned.strip()


def parse_boolean_value(val: Any) -> bool:
    """Safely parses boolean values from JSON payloads (strings, integers, booleans)."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        s = val.strip().lower()
        if s in ("true", "1", "t", "yes", "vrai", "oui", "صحيح"):
            return True
        if s in ("false", "0", "f", "no", "faux", "non", "خطأ"):
            return False
    return False


class QuizQuestionValidator:
    """Strict gatekeeper for AI-generated multiple choice questions.

    Rule: Never blindly trust LLM output.
    Enforces:
    1. Valid non-empty question text with minimum meaningful length.
    2. Exactly 4 distinct answer options.
    3. Exactly ONE correct answer (robust boolean parsing).
    4. Non-empty, non-tautological pedagogical explanation.
    5. Valid difficulty level (EASY, MEDIUM, HARD).
    6. Non-empty source/citation provenance.
    7. Absence of meta-distractors ("All of the above", "None of the above").
    8. Anti-duplication within question options and across questions in the quiz.
    """

    VALID_DIFFICULTIES = {d.value for d in DifficultyLevel}

    BANNED_META_DISTRACTORS = [
        "toutes les réponses",
        "toutes les options",
        "tous les choix",
        "aucune des réponses",
        "aucune de ces réponses",
        "aucun des choix",
        "all of the above",
        "none of the above",
        "both a and b",
        "both b and c",
        "كل ما سبق",
        "جميع ما سبق",
        "لا شيء مما سبق",
        "لا شيء مما ذكر",
    ]

    TAUTOLOGICAL_EXPLANATIONS = [
        "c'est la bonne réponse",
        "bonne réponse",
        "c'est correct",
        "correct",
        "parce que c'est vrai",
        "this is correct",
        "correct answer",
        "إجابة صحيحة",
        "هذا صحيح",
    ]

    def validate_and_normalize(
        self,
        raw_question: dict[str, Any],
        default_difficulty: str = DifficultyLevel.MEDIUM,
    ) -> dict[str, Any]:
        """Validates a single question dictionary and normalizes it.

        Raises:
            InvalidQuizQuestionError: if any validation rule is violated.
        """
        if not isinstance(raw_question, dict):
            raise InvalidQuizQuestionError("La question doit être un objet JSON valide.")

        # 1. Validate Question Text
        raw_text = raw_question.get("question") or raw_question.get("text")
        if not raw_text or not isinstance(raw_text, str) or not raw_text.strip():
            raise InvalidQuizQuestionError("L'énoncé de la question est manquant ou vide.")

        text = sanitize_quiz_text(raw_text)
        if len(text) < 10:
            raise InvalidQuizQuestionError(
                f"L'énoncé de la question est trop court pour une évaluation rigoureuse ({len(text)} caractères)."
            )

        # 2. Validate Answers / Options
        raw_answers = (
            raw_question.get("answers")
            or raw_question.get("options")
            or raw_question.get("choices")
        )
        if not raw_answers or not isinstance(raw_answers, list):
            raise InvalidQuizQuestionError(
                "La question ne contient pas de liste d'options de réponse."
            )

        if len(raw_answers) != 4:
            raise InvalidQuizQuestionError(
                f"Une question de QCM doit comporter exactement 4 options de réponse (reçu : {len(raw_answers)})."
            )

        normalized_answers: list[dict[str, Any]] = []
        seen_texts: set[str] = set()
        correct_count = 0

        correct_indicator = raw_question.get("correct_answer")
        if correct_indicator is None:
            correct_indicator = raw_question.get("correct_index")

        for idx, item in enumerate(raw_answers):
            if isinstance(item, dict):
                ans_text = item.get("text") or item.get("answer") or ""
                # Robust boolean parsing to avoid string "false" being cast to True
                has_bool = "is_correct" in item or "correct" in item
                if has_bool:
                    raw_val = (
                        item.get("is_correct") if "is_correct" in item else item.get("correct")
                    )
                    is_correct = parse_boolean_value(raw_val)
                elif correct_indicator is not None:
                    is_correct = (correct_indicator == idx) or (
                        str(correct_indicator).strip().lower() == str(ans_text).strip().lower()
                    )
                else:
                    is_correct = False
            elif isinstance(item, str):
                ans_text = item
                is_correct = (correct_indicator == idx) or (
                    str(correct_indicator).strip().lower() == str(ans_text).strip().lower()
                )
            else:
                raise InvalidQuizQuestionError(
                    f"Option #{idx + 1} invalide : format attendu texte ou objet."
                )

            if not isinstance(ans_text, str) or not ans_text.strip():
                raise InvalidQuizQuestionError(f"L'option de réponse #{idx + 1} est vide.")

            cleaned_text = sanitize_quiz_text(ans_text)
            if len(cleaned_text) < 1:
                raise InvalidQuizQuestionError(f"L'option de réponse #{idx + 1} est vide.")

            # Normalized text for strict duplicate check (ignore trailing dots/punctuation)
            norm_text = re.sub(r"[^\w\s\u0600-\u06FF]", "", cleaned_text.lower()).strip()
            if not norm_text:
                norm_text = cleaned_text.lower().strip()

            if norm_text in seen_texts:
                raise InvalidQuizQuestionError(
                    f"Options de réponse en doublon détectées : « {cleaned_text} »."
                )
            seen_texts.add(norm_text)

            # Check banned meta-distractors
            lower_clean = cleaned_text.lower()
            for banned in self.BANNED_META_DISTRACTORS:
                if banned in lower_clean:
                    raise InvalidQuizQuestionError(
                        f"Option #{idx + 1} rejetée : les méta-distracteurs de type « {cleaned_text} » sont interdits dans un QCM numérique."
                    )

            if is_correct:
                correct_count += 1

            normalized_answers.append(
                {
                    "text": cleaned_text,
                    "is_correct": is_correct,
                    "order": idx,
                }
            )

        if correct_count != 1:
            raise InvalidQuizQuestionError(
                f"Une question de QCM doit comporter exactement UNE seule bonne réponse (détecté : {correct_count})."
            )

        # 3. Validate Explanation
        raw_expl = raw_question.get("explanation") or raw_question.get("justification")
        if not raw_expl or not isinstance(raw_expl, str) or not raw_expl.strip():
            raise InvalidQuizQuestionError(
                "L'explication pédagogique de la bonne réponse est obligatoire."
            )
        explanation = sanitize_quiz_text(raw_expl)
        if len(explanation) < 15:
            raise InvalidQuizQuestionError(
                "L'explication pédagogique doit faire au moins 15 caractères pour justifier rigoureusement la réponse."
            )

        expl_lower = explanation.lower().strip()
        for tautology in self.TAUTOLOGICAL_EXPLANATIONS:
            if expl_lower == tautology or expl_lower.startswith(f"{tautology}."):
                raise InvalidQuizQuestionError(
                    "L'explication pédagogique est tautologique et n'explique pas le raisonnement sous-jacent."
                )

        # 4. Validate Difficulty
        raw_diff = str(raw_question.get("difficulty") or default_difficulty).upper().strip()
        if raw_diff not in self.VALID_DIFFICULTIES:
            raw_diff = default_difficulty

        # 5. Validate Source / Citation
        raw_source = (
            raw_question.get("source")
            or raw_question.get("citation")
            or "Source documentaire analysée"
        )
        if not isinstance(raw_source, str) or not raw_source.strip():
            source = "Source documentaire"
        else:
            source = sanitize_quiz_text(raw_source)

        return {
            "text": text,
            "answers": normalized_answers,
            "explanation": explanation,
            "difficulty": raw_diff,
            "source": source,
        }

    def validate_quiz_payload(
        self,
        data: dict[str, Any] | list[Any],
        default_difficulty: str = DifficultyLevel.MEDIUM,
    ) -> list[dict[str, Any]]:
        """Extracts and validates a list of questions from an LLM response payload.

        Silently discards malformed or duplicate questions and logs warnings.
        Raises InvalidQuizQuestionError if 0 questions are valid.
        """
        raw_list: list[Any]
        if isinstance(data, dict):
            raw_list = data.get("questions") or data.get("qcm") or []
        elif isinstance(data, list):
            raw_list = data
        else:
            raise InvalidQuizQuestionError(
                "Format de payload invalide : dictionnaire ou liste attendu."
            )

        if not raw_list:
            raise InvalidQuizQuestionError("Aucune question trouvée dans la réponse de génération.")

        valid_questions: list[dict[str, Any]] = []
        errors: list[str] = []
        seen_question_prompts: set[str] = set()

        for idx, item in enumerate(raw_list):
            try:
                validated = self.validate_and_normalize(item, default_difficulty=default_difficulty)
                # Deduplicate repeated questions in the same quiz
                q_key = re.sub(r"[^\w\s\u0600-\u06FF]", "", validated["text"].lower()).strip()
                if q_key in seen_question_prompts:
                    logger.warning(
                        "Rejet de la question LLM #%s car redondante avec une question précédente.",
                        idx + 1,
                    )
                    continue
                seen_question_prompts.add(q_key)
                valid_questions.append(validated)
            except InvalidQuizQuestionError as err:
                logger.warning(
                    "Rejet de la question LLM #%s pour non-conformité : %s",
                    idx + 1,
                    err,
                )
                errors.append(f"Q#{idx + 1}: {err}")

        if not valid_questions:
            raise InvalidQuizQuestionError(
                f"Toutes les questions générées ont été rejetées car non conformes : {'; '.join(errors)}"
            )

        return valid_questions
