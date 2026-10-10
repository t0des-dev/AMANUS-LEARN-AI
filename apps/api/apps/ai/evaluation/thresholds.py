"""Acceptance Thresholds for Deterministic, Semantic, and Perceptual Metrics (Sprint 06).

Rule: Deterministic thresholds are hard binary constraints (100% compliance required).
Critical errors (schema, missing fields, security isolation) CANNOT be offset by high semantic scores.
"""

from typing import Any

ACCEPTANCE_THRESHOLDS: dict[str, dict[str, Any]] = {
    # 1. Course & Documents
    "course": {
        "deterministic": {
            "schema_validity": 1.0,  # 100% valid JSON matching contract
            "mandatory_fields_present": 1.0,  # title, chapters, lessons/sections
            "non_empty_content": 1.0,  # 0 empty strings or null titles
            "minimum_chapter_count": 1,  # At least 1 chapter
            "monotonic_ordering": 1.0,  # Sequential indices without duplicates
        },
        "semantic": {
            "min_citation_rate": 0.60,  # >= 60% of factual lessons contain chunk references [1], [2]
            "max_ngram_redundancy": 0.25,  # <= 25% tri-gram overlap between adjacent sections
            "language_conformity_rate": 0.85,  # >= 85% keywords matching target language (FR, AR, EN)
        },
        "perceptual": {
            "pedagogical_clarity_score": 3.5,  # >= 3.5 / 5.0 on human or calibrated rubric
        },
    },
    # 2. Slides & Presentations
    "slides": {
        "deterministic": {
            "schema_validity": 1.0,  # 100% valid presentation schema
            "slide_count_compliance": 1.0,  # Matches requested count (+/- 0)
            "mandatory_slide_fields": 1.0,  # title, slide_number, bullet_points
            "max_bullets_per_slide": 6,  # Max 6 bullets
            "max_chars_per_bullet": 160,  # Max 160 chars per bullet to avoid overflow
            "pptx_binary_validity": 1.0,  # PPTX file opens cleanly with OpenXML parser
            "widescreen_aspect_ratio": 1.0,  # 16:9 widescreen dimensions (13.33 x 7.5 inches)
        },
        "semantic": {
            "structure_progression": 0.80,  # Progression index (Intro -> Body -> Conclusion)
            "max_slide_redundancy": 0.20,  # <= 20% bullet repetition across deck
        },
        "perceptual": {
            "visual_overflow_rate": 0.00,  # 0% slides overflowing visual container
            "contrast_legibility_score": 4.0,  # >= 4.0 / 5.0
        },
    },
    # 3. Audio & Text-to-Speech
    "audio": {
        "deterministic": {
            "valid_magic_header": 1.0,  # ID3 or MPEG sync word (0xFFFB/F3/F2)
            "min_file_size_bytes": 48,  # Reject empty or stub byte streams
            "text_preservation_fidelity": 1.0,  # 100% words preserved across chunk segmentation
            "zero_word_duplication": 1.0,  # 0 duplicate words injected at chunk seams
        },
        "semantic": {
            "natural_pause_ratio": 0.70,  # Chunks broken strictly on sentences/paragraphs
        },
        "perceptual": {
            "min_words_per_minute": 110,  # Natural lecture pace
            "max_words_per_minute": 180,
            "intelligibility_score": 4.0,  # >= 4.0 / 5.0 on listening calibration
        },
    },
    # 4. Quizzes & Assessments
    "quiz": {
        "deterministic": {
            "schema_validity": 1.0,  # Valid QCM structure
            "exact_option_count": 4,  # Exactly 4 distinct choices per question
            "single_correct_answer": 1.0,  # Exactly 1 choice with is_correct=True
            "valid_difficulty_level": 1.0,  # EASY, MEDIUM, or HARD
            "non_empty_explanation": 1.0,  # Explanation present and > 10 chars
            "absence_of_meta_distractors": 1.0,  # 0 "All of the above" or "None of the above"
            "distinct_options_per_question": 1.0,  # 0 identical options
            "scoring_accuracy": 1.0,  # 100% correct score calculation on attempt
        },
        "semantic": {
            "explanation_justification_rate": 0.80,  # Explication mentions why correct answer is right
            "distractor_plausibility_index": 0.75,  # Distractor length variation ratio <= 2.5
        },
        "perceptual": {
            "learner_fairness_rating": 4.0,  # >= 4.0 / 5.0
        },
    },
    # 5. Orchestration & Pipeline
    "orchestration": {
        "deterministic": {
            "lifecycle_transition_validity": 1.0,  # Only valid transitions in TaskLifecycleStatus
            "multi_tenant_isolation": 1.0,  # 100% denial of cross-tenant task inspection
            "concurrency_lock_acquisition": 1.0,  # Lock properly blocks parallel executions (HTTP 409)
            "idempotency_consistency": 1.0,  # Same inputs produce identical task fingerprint
            "cache_invalidation_cleanliness": 1.0,  # Document update purges cached generation
        },
        "semantic": {
            "task_completion_success_rate": 0.95,  # >= 95% task success under standard conditions
        },
        "perceptual": {
            "user_progress_feedback_clarity": 4.0,
        },
    },
}
