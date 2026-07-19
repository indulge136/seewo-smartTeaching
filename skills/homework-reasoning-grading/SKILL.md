---
name: homework-reasoning-grading
description: Use when grading calculation, reasoning, math, physics, or process-based homework that requires evaluating solution steps, intermediate logic, process score, and final result after TrustedQuestion extraction.
---

# Homework Reasoning Grading

Use this skill when the answer depends on process, not only a final fact lookup.

## Stage Boundary

Grade the method, the intermediate steps, and the final result. Do not do diagnosis, tutoring, or feedback generation here.

## Typical Inputs

- `trusted_question.question`
- `trusted_question.student_answer`
- `trusted_question.knowledge`
- `trusted_question.question_type`
- Optional reference answer or rubric when available

## Output Contract

Return valid JSON only:

```json
{
  "score": 82,
  "max_score": 100,
  "judgement": "partially_correct",
  "process_score": 32,
  "result_score": 50,
  "comments": [
    {
      "kind": "concept",
      "status": "ok",
      "detail": "formula choice is correct"
    },
    {
      "kind": "process",
      "status": "warn",
      "detail": "one intermediate step is missing"
    },
    {
      "kind": "calculation",
      "status": "warn",
      "detail": "sign error in the second step"
    },
    {
      "kind": "result",
      "status": "warn",
      "detail": "final unit is missing"
    },
    {
      "kind": "format",
      "status": "ok",
      "detail": "answer format is readable"
    }
  ]
}
```

## Fixed Comment Template

Always structure `comments` as an array of short objects with these fields:

- `kind`: one of `concept`, `process`, `calculation`, `result`, `format`
- `status`: one of `ok`, `warn`, `error`
- `detail`: short evidence-based text

Keep the array small. Prefer one item per dimension, and omit a dimension only when it is not relevant.

The downstream diagnosis stage should map the `process` comment to the `process_expression` ability tag when the method is valid but not fully expressed.

## What to Check

1. Concept selection
2. Formula or theorem usage
3. Intermediate calculation
4. Logical sequence
5. Final result and unit

## Scoring Rules

- Give process credit if the solving method is valid even when the final answer is wrong.
- Penalize missing units, wrong signs, skipped steps, or unclear logic separately.
- Split scoring when the task is clearly process-based:
  - `process_score` for reasoning and method
  - `result_score` for the final answer
- Use `judgement` values such as:
  - `correct`
  - `partially_correct`
  - `incorrect`
  - `ungradable`

## Reasoning Subtypes

- `calculation`: arithmetic, algebra, geometry, functions, equations
- `physics`: force, motion, circuit, energy, experimental reasoning
- `proof_or_reasoning`: derivation, logical explanation, multi-step argument

## Guardrails

- Do not over-penalize handwriting ambiguity.
- Do not invent steps that are not visible.
- Do not silently fix incorrect reasoning.
- Do not generate personalized teaching advice.
- Keep comments short, specific, and evidence-based.
