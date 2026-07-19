---
name: homework-diagnosis
description: Use when a grading result must be turned into error causes, knowledge points, ability tags, and student profile changes after homework grading.
---

# Homework Diagnosis

Use this skill as the third stage after grading. Turn the grading result into a compact diagnosis payload for the next teaching workflow.

## Stage Boundary

Only analyze errors and map them to knowledge and ability signals. Do not generate exercises, feedback paragraphs, or teaching plans.

## Typical Inputs

- `trusted_question.question`
- `trusted_question.student_answer`
- `trusted_question.knowledge`
- `trusted_question.question_type`
- `grading.score`
- `grading.judgement`
- `grading.process_score`
- `grading.result_score`
- `grading.comments`

## Output Contract

Return valid JSON only:

```json
{
  "error_causes": [
    {
      "kind": "concept_misunderstanding",
      "evidence": "wrong theorem or formula",
      "severity": "high"
    },
    {
      "kind": "calculation_error",
      "evidence": "sign slip in the second step",
      "severity": "medium"
    }
  ],
  "knowledge_points": ["quadratic function"],
  "ability_tags": [
    {
      "kind": "concept_understanding",
      "level": "weak"
    },
    {
      "kind": "process_expression",
      "level": "medium"
    }
  ],
  "student_profile_delta": {
    "mastery_trend": "stable",
    "high_frequency_error": "incomplete expression"
  }
}
```

## Fixed Field Template

Use these stable enumerations:

### error_causes.kind

- `concept_misunderstanding`
- `calculation_error`
- `reasoning_process_error`
- `expression_format_issue`
- `unit_error`
- `visual_interpretation_error`

### ability_tags.kind

- `concept_understanding`
- `process_expression`
- `calculation_accuracy`
- `logical_reasoning`
- `unit_awareness`
- `visual_reading`

### ability_tags.level

- `strong`
- `medium`
- `weak`

### error_causes.severity

- `low`
- `medium`
- `high`

## Diagnosis Procedure

1. Read the extracted question and the grading result together.
2. Decide which fixed error kind best matches the evidence.
3. Map each error to one or more knowledge points.
4. Map each error to one or more ability tags.
5. Summarize student trend in `student_profile_delta`.

## Student Profile Delta

Keep this small and machine-readable:

- `mastery_trend`: `improving`, `stable`, or `declining`
- `high_frequency_error`: short repeated error pattern
- Optional extra keys only if they are directly supported by evidence

## Guardrails

- Do not stop at correct or incorrect.
- Do not generate personalized practice or follow-up teaching content.
- Do not invent hidden mistakes.
- Do not make the diagnosis verbose.
