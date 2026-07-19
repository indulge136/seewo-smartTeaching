import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.grading.normalization import normalize_qwen_result


def test_normalize_qwen_result_coerces_string_based_skill_outputs() -> None:
    raw_result = {
        "choices": [
            {
                "message": {
                    "content": """
                    {
                      "trusted_question": {
                        "subject": "数学",
                        "question": "12 的 1/3 是多少",
                        "student_answer": "4",
                        "knowledge": ["分数"],
                        "question_type": "计算题",
                        "confidence": 0.9
                      },
                      "grading": {
                        "score": 80,
                        "max_score": 100,
                        "judgement": "partially_correct",
                        "process_score": 30,
                        "result_score": 50,
                        "comments": ["过程清晰", "结果正确"]
                      },
                      "diagnosis": {
                        "error_causes": ["单位缺失"],
                        "knowledge_points": ["分数"],
                        "ability_tags": ["process_expression"],
                        "student_profile_delta": {"mastery_trend": "stable"}
                      }
                    }
                    """
                }
            }
        ]
    }

    stages = normalize_qwen_result(raw_result, "数学")

    assert stages.grading.comments[0].kind == "comment"
    assert stages.grading.comments[0].detail == "过程清晰"
    assert stages.diagnosis.error_causes[0].kind == "issue"
    assert stages.diagnosis.error_causes[0].evidence == "单位缺失"
    assert stages.diagnosis.ability_tags[0].kind == "process_expression"
    assert stages.diagnosis.ability_tags[0].level == "unknown"
