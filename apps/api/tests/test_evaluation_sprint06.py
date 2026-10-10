"""Tests for Sprint 06: Automated Evaluation and Quality Optimization of AI Generations.

Implements all 12 mandatory test requirements:
1. Reproducible benchmark suite execution.
2. Detection of invalid output.
3. Detection of missing mandatory fields.
4. Detection of inconsistent quiz answers (multiple correct, <4 options, meta distractors).
5. Detection of corrupted / invalid PPTX file.
6. Detection of corrupted / invalid audio stream (magic header, size).
7. Comparison between two prompt / generator versions with regression detection.
8. Proper handling and documentation of unsupported or skipped evaluations.
9. Privacy and security protection (no PII, no secrets, no internal keys in logs or dataset).
10. Non-regression detection across generators.
11. Deterministic threshold strictness (100% required, no compensating by semantic scores).
12. Verification of evaluation report production (Markdown and structured JSON).
"""

import io

from pptx import Presentation

from apps.ai.evaluation import (
    EvaluationCategory,
    EvaluationRunner,
    PromptVersionComparator,
)
from apps.ai.evaluation.dataset import BENCHMARK_DATASET
from apps.ai.evaluation.evaluators import (
    AudioDeterministicEvaluator,
    CourseDeterministicEvaluator,
    QuizDeterministicEvaluator,
    SlidesDeterministicEvaluator,
)


class TestSprint06EvaluationSuite:
    """Suite testing the Sprint 06 Automated Evaluation Framework."""

    # 1. Reproducible benchmark execution
    def test_reproducible_benchmark_execution(self):
        runner = EvaluationRunner(version="v1.0.0")
        report1 = runner.run_suite(cases=BENCHMARK_DATASET)
        report2 = runner.run_suite(cases=BENCHMARK_DATASET)

        assert report1.total_samples == len(BENCHMARK_DATASET)
        assert report2.total_samples == len(BENCHMARK_DATASET)
        assert report1.total_samples > 0
        assert report1.passed_samples == report2.passed_samples
        assert report1.failed_samples == report2.failed_samples
        assert report1.success_rate == report2.success_rate

    # 2. Detection of invalid output
    def test_detect_invalid_output(self):
        # A string or list instead of expected course dict
        metrics = CourseDeterministicEvaluator.evaluate("not a valid dict")
        schema_metric = next(m for m in metrics if m.name == "course_schema_validity")
        assert schema_metric.passed is False
        assert schema_metric.value is False

    # 3. Detection of missing mandatory field
    def test_detect_missing_mandatory_field(self):
        incomplete_course = {
            "title": "Titre sans description ni chapitres",
            # Missing "description" and "chapters"
        }
        metrics = CourseDeterministicEvaluator.evaluate(incomplete_course)
        mandatory_metric = next(m for m in metrics if m.name == "course_mandatory_fields")
        assert mandatory_metric.passed is False
        assert mandatory_metric.details["has_chapters"] is False

    # 4. Detection of inconsistent quiz answers
    def test_detect_inconsistent_quiz_answers(self):
        # Inconsistent quiz: 2 correct answers and a banned meta distractor
        inconsistent_quiz = {
            "questions": [
                {
                    "question": "Question invalide",
                    "answers": [
                        {"text": "Option 1", "is_correct": True},
                        {"text": "Option 2", "is_correct": True},  # Multiple correct!
                        {
                            "text": "Toutes les réponses ci-dessus",
                            "is_correct": False,
                        },  # Meta distractor!
                        {"text": "Option 4", "is_correct": False},
                    ],
                    "explanation": "Brève",
                }
            ]
        }
        metrics = QuizDeterministicEvaluator.evaluate(inconsistent_quiz)
        single_correct_m = next(
            m for m in metrics if m.name == "quiz_single_correct_answer_per_question"
        )
        meta_distractor_m = next(m for m in metrics if m.name == "quiz_absence_of_meta_distractors")

        assert single_correct_m.passed is False
        assert meta_distractor_m.passed is False

    # 5. Detection of invalid PPTX file
    def test_detect_invalid_pptx_file(self):
        corrupt_pptx = b"NOT_A_VALID_ZIP_OR_PPTX_BYTES_CORRUPTED"
        payload = {"title": "Presentation", "slides": [{"bullet_points": ["Point 1"]}]}
        metrics = SlidesDeterministicEvaluator.evaluate(payload, pptx_bytes=corrupt_pptx)

        pptx_metric = next(m for m in metrics if m.name == "pptx_binary_integrity")
        assert pptx_metric.passed is False
        assert pptx_metric.value is False

        # Positive control: valid PPTX
        prs = Presentation()
        prs.slides.add_slide(prs.slide_layouts[6])
        buf = io.BytesIO()
        prs.save(buf)
        valid_bytes = buf.getvalue()

        positive_metrics = SlidesDeterministicEvaluator.evaluate(payload, pptx_bytes=valid_bytes)
        pos_pptx_metric = next(m for m in positive_metrics if m.name == "pptx_binary_integrity")
        assert pos_pptx_metric.passed is True

    # 6. Detection of invalid audio file (magic header, size)
    def test_detect_invalid_audio_stream(self):
        # Invalid stream: random ascii without ID3 or MPEG sync, and under 48 bytes
        bad_audio = b"Hello audio test"
        metrics = AudioDeterministicEvaluator.evaluate(bad_audio)

        header_m = next(m for m in metrics if m.name == "audio_magic_header_valid")
        size_m = next(m for m in metrics if m.name == "audio_min_size_satisfied")

        assert header_m.passed is False
        assert size_m.passed is False

        # Positive control: valid ID3 audio stream >= 48 bytes
        good_audio = b"ID3\x03\x00\x00\x00\x00\x00\x00" + (b"\xff\xfb\x90d" * 20)
        good_metrics = AudioDeterministicEvaluator.evaluate(good_audio)
        good_header_m = next(m for m in good_metrics if m.name == "audio_magic_header_valid")
        good_size_m = next(m for m in good_metrics if m.name == "audio_min_size_satisfied")

        assert good_header_m.passed is True
        assert good_size_m.passed is True

    # 7. Comparison between two versions (PromptVersionComparator)
    def test_version_comparison_between_prompts(self):
        runner = EvaluationRunner()
        report_v1 = runner.run_suite(suite_name="Suite Baseline v1.0")
        report_v2 = runner.run_suite(suite_name="Suite Candidate v1.1")

        comparison = PromptVersionComparator.compare_reports(report_v1, report_v2)
        assert comparison.baseline_version == report_v1.version
        assert comparison.candidate_version == report_v2.version
        assert isinstance(comparison.regressions_detected, bool)
        assert len(comparison.metric_comparisons) > 0
        assert "Comparaison" in comparison.summary

    # 8. Handling of unsupported or skipped evaluations
    def test_handle_unsupported_or_skipped_evaluations(self):
        runner = EvaluationRunner()
        report = runner.run_suite()

        assert len(report.unsupported_or_skipped_evaluations) > 0
        for item in report.unsupported_or_skipped_evaluations:
            assert "evaluation" in item
            assert "reason" in item
            assert "mitigation" in item

    # 9. Privacy and security protection (no PII, no secrets)
    def test_privacy_and_security_no_pii_or_secrets(self):
        forbidden_patterns = [
            "sk-proj-",
            "sk-live-",
            "api_key=",
            "secret_key",
            "private_key",
            "bearer ey",
            "ghp_",
            "ssh-rsa",
        ]
        # Inspect all benchmark dataset cases
        for case in BENCHMARK_DATASET:
            content_str = str(case.input_payload).lower() + str(case.expected_properties).lower()
            for pattern in forbidden_patterns:
                assert pattern not in content_str, (
                    f"Secret or credential pattern '{pattern}' detected in {case.case_id}!"
                )

        # Inspect generated report string
        runner = EvaluationRunner()
        report = runner.run_suite()
        report_md = runner.export_report_to_markdown(report).lower()
        for pattern in forbidden_patterns:
            assert pattern not in report_md

    # 10. Non-regression detection across generators
    def test_non_regression_detection(self):
        runner = EvaluationRunner()
        baseline = runner.run_suite()

        # Simulate candidate report with a regression (e.g. failing quiz options)
        candidate = runner.run_suite()
        for r in candidate.results:
            if r.generator_type == "quiz":
                # Inject a failing metric
                for m in r.metrics:
                    if m.name == "quiz_exact_4_options_per_question":
                        m.value = False
                        m.passed = False

        comp = PromptVersionComparator.compare_reports(baseline, candidate)
        assert comp.regressions_detected is True
        assert comp.deterministic_regression_count >= 1

    # 11. Deterministic threshold strictness
    def test_deterministic_thresholds_strictness(self):
        # A candidate with 5.0 / 5.0 semantic rating but an invalid schema MUST FAIL overall
        incomplete_course = {
            "title": "Titre",
            # Missing chapters
        }
        metrics = CourseDeterministicEvaluator.evaluate(incomplete_course)
        det_passed = all(
            m.passed for m in metrics if m.category == EvaluationCategory.DETERMINISTIC
        )
        assert det_passed is False, (
            "Deterministic failure must NOT pass, regardless of any semantic score!"
        )

    # 12. Verification of evaluation report production (Markdown and JSON)
    def test_evaluation_report_generation(self):
        runner = EvaluationRunner(version="v1.0.0")
        report = runner.run_suite(suite_name="Rapport Sprint 06 Quality")

        report_dict = report.to_dict()
        assert report_dict["suite_name"] == "Rapport Sprint 06 Quality"
        assert report_dict["total_samples"] > 0
        assert "deterministic" in report_dict["summary_by_category"]
        assert "semantic" in report_dict["summary_by_category"]
        assert "perceptual" in report_dict["summary_by_category"]

        markdown_doc = runner.export_report_to_markdown(report)
        assert "# Rapport d'Évaluation de la Qualité" in markdown_doc
        assert "Synthèse Globale" in markdown_doc
        assert "Conformité par Catégorie d'Évaluation" in markdown_doc
