from pathlib import Path
from typing import Any


SKILL_TOOL_DESCRIPTIONS: dict[str, str] = {
    "HomeworkPerceptionSkill": "\u8bfb\u53d6 jpg/png \u4f5c\u4e1a\u56fe\u7247\uff0c\u8f93\u51fa TrustedQuestion JSON\uff0c\u53ea\u505a\u611f\u77e5\u7ed3\u6784\u5316\u3002",
    "ObjectiveSkill": "\u5904\u7406\u5ba2\u89c2\u9898\u3001\u9009\u62e9\u9898\u3001\u586b\u7a7a\u9898\uff0c\u505a\u7b54\u6848\u5339\u914d\u3001\u5355\u4f4d\u68c0\u67e5\u548c\u786e\u5b9a\u6027\u5224\u5206\u3002",
    "ReasoningSkill": "\u5904\u7406\u6570\u5b66/\u7269\u7406/\u8ba1\u7b97/\u63a8\u7406\u9898\uff0c\u8bc4\u4f30\u6b65\u9aa4\u3001\u8fc7\u7a0b\u5206\u548c\u7ed3\u679c\u5206\u3002",
    "RubricSkill": "\u5904\u7406\u4f5c\u6587\u3001\u7b80\u7b54\u3001\u5f00\u653e\u9898\uff0c\u6309 Rubric \u7ef4\u5ea6\u505a\u8bed\u4e49\u8bc4\u4ef7\u3002",
    "VisionSkill": "\u5904\u7406\u56fe\u6587\u6df7\u5408\u3001\u51e0\u4f55\u56fe\u3001\u5b9e\u9a8c\u56fe\u3001\u7535\u8def\u56fe\u7b49\u89c6\u89c9\u63a8\u7406\u9898\u3002",
    "HomeworkDiagnosisSkill": "\u8bfb\u53d6\u611f\u77e5\u548c\u5224\u5206\u7ed3\u679c\uff0c\u8f93\u51fa\u9519\u8bef\u539f\u56e0\u3001\u77e5\u8bc6\u70b9\u3001\u80fd\u529b\u6807\u7b7e\u548c\u5b66\u751f\u753b\u50cf\u589e\u91cf\u3002",
}

SKILL_FILE_SLUGS: dict[str, str] = {
    "HomeworkPerceptionSkill": "homework-perception",
    "ObjectiveSkill": "homework-objective-grading",
    "ReasoningSkill": "homework-reasoning-grading",
    "RubricSkill": "homework-rubric-grading",
    "VisionSkill": "homework-vision-grading",
    "HomeworkDiagnosisSkill": "homework-diagnosis",
}


def route_grading_skill(question: dict[str, Any]) -> dict[str, str]:
    question_type = str(question.get("question_type", "")).lower()
    subject = str(question.get("subject", "")).lower()

    if any(keyword in question_type for keyword in ["\u5ba2\u89c2", "\u9009\u62e9", "\u586b\u7a7a", "objective"]):
        return {"skill": "ObjectiveSkill", "reason": "\u5ba2\u89c2\u9898\u91c7\u7528\u7b54\u6848\u5339\u914d\u3001\u5355\u4f4d\u8f6c\u6362\u548c\u683c\u5f0f\u5224\u65ad\u3002"}

    if any(keyword in question_type for keyword in ["\u4f5c\u6587", "\u7b80\u7b54", "\u5f00\u653e", "rubric", "essay"]):
        return {"skill": "RubricSkill", "reason": "\u5f00\u653e\u9898\u91c7\u7528\u591a\u7ef4 Rubric \u8bed\u4e49\u8bc4\u4ef7\u3002"}

    if any(keyword in question_type for keyword in ["\u56fe", "\u56fe\u6587", "\u51e0\u4f55", "\u7535\u8def", "\u5b9e\u9a8c", "vision"]):
        return {"skill": "VisionSkill", "reason": "\u56fe\u6587\u6df7\u5408\u9898\u9700\u8981\u7406\u89e3\u56fe\u5f62\u3001\u5b9e\u9a8c\u56fe\u6216\u7535\u8def\u56fe\u3002"}

    if any(keyword in question_type for keyword in ["\u8ba1\u7b97", "\u63a8\u7406", "\u8fc7\u7a0b", "reasoning"]):
        return {"skill": "ReasoningSkill", "reason": "\u63a8\u7406\u9898\u9700\u8981\u7406\u89e3\u6b65\u9aa4\u3001\u903b\u8f91\u548c\u4e2d\u95f4\u8fc7\u7a0b\u3002"}

    if any(keyword in subject for keyword in ["\u6570\u5b66", "\u7269\u7406", "math", "physics"]):
        return {"skill": "ReasoningSkill", "reason": "\u6570\u7406\u5b66\u79d1\u9ed8\u8ba4\u8fdb\u5165\u63a8\u7406\u6279\u6539\u80fd\u529b\u3002"}

    return {"skill": "RubricSkill", "reason": "\u672a\u8bc6\u522b\u9898\u578b\u65f6\u91c7\u7528\u901a\u7528 Rubric \u8bc4\u4ef7\u3002"}


def load_skill_instruction(skill_name: str) -> str:
    slug = SKILL_FILE_SLUGS.get(skill_name)
    if not slug:
        return SKILL_TOOL_DESCRIPTIONS.get(skill_name, "")

    repo_root = Path(__file__).resolve().parents[3]
    skill_paths = [
        repo_root / "skills" / slug / "SKILL.md",
        repo_root / ".agents" / "skills" / slug / "SKILL.md",
    ]
    skill_path = next((path for path in skill_paths if path.exists()), None)
    if skill_path is None:
        return SKILL_TOOL_DESCRIPTIONS.get(skill_name, "")

    return skill_path.read_text(encoding="utf-8")


def build_skill_action_instruction(skill_name: str) -> str:
    return f"Skill Instruction for {skill_name}:\n{load_skill_instruction(skill_name)}"
