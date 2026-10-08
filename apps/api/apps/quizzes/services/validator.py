import logging
from typing import Any

from apps.quizzes.models import DifficultyLevel

logger = logging.getLogger(__name__)


class InvalidQuizQuestionError(Exception):
    """Raised when an AI-generated QCM question fails strict validation criteria."""

    pass


class QuizQuestionValidator:
    """Strict gatekeeper for AI-generated multiple choice questions.

    Rule: Never blindly trust LLM output.
    Enforces:
    1. Valid non-empty question text.
    2. Exactly 4 distinct answer options.
    3. Exactly ONE correct answer.
    4. Non-empty pedagogical explanation.
    5. Valid difficulty level (EASY, MEDIUM, HARD).
    6. Non-empty source/citation provenance.
    """

    VALID_DIFFICULTIES = {d.value for d in DifficultyLevel}

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
        text = raw_question.get("question") or raw_question.get("text")
        if not text or not isinstance(text, str) or not text.strip():
            raise InvalidQuizQuestionError("L'énoncé de la question est manquant ou vide.")
        text = text.strip()

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

        # Handle answers formatted either as objects [{"text": "...", "is_correct": true}]
        # or as strings with a separate "correct_answer" indicator
        correct_indicator = raw_question.get("correct_answer") or raw_question.get("correct_index")

        for idx, item in enumerate(raw_answers):
            if isinstance(item, dict):
                ans_text = item.get("text") or item.get("answer") or ""
                is_correct = bool(
                    item.get("is_correct") or item.get("correct") or (correct_indicator == idx)
                )
            elif isinstance(item, str):
                ans_text = item
                is_correct = correct_indicator == idx or correct_indicator == item
            else:
                raise InvalidQuizQuestionError(
                    f"Option #{idx + 1} invalide : format attendu texte ou objet."
                )

            if not isinstance(ans_text, str) or not ans_text.strip():
                raise InvalidQuizQuestionError(f"L'option de réponse #{idx + 1} est vide.")

            cleaned_text = ans_text.strip()
            lower_text = cleaned_text.lower()

            if lower_text in seen_texts:
                raise InvalidQuizQuestionError(
                    f"Options de réponse en doublon détectées : « {cleaned_text} »."
                )
            seen_texts.add(lower_text)

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
        explanation = raw_question.get("explanation") or raw_question.get("justification")
        if not explanation or not isinstance(explanation, str) or not explanation.strip():
            raise InvalidQuizQuestionError(
                "L'explication pédagogique de la bonne réponse est obligatoire."
            )
        explanation = explanation.strip()

        # 4. Validate Difficulty
        raw_diff = str(raw_question.get("difficulty") or default_difficulty).upper()
        if raw_diff not in self.VALID_DIFFICULTIES:
            raw_diff = default_difficulty

        # 5. Validate Source / Citation
        source = (
            raw_question.get("source")
            or raw_question.get("citation")
            or "Source documentaire analysée"
        )
        if not isinstance(source, str) or not source.strip():
            source = "Source documentaire"
        source = source.strip()

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

        Silently discards malformed questions and logs warnings.
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

        for idx, item in enumerate(raw_list):
            try:
                validated = self.validate_and_normalize(item, default_difficulty=default_difficulty)
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
