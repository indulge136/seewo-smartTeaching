---
name: homework-perception
description: Use when a user uploads jpg/png homework images and the backend must parse the image into TrustedQuestion JSON before grading, including OCR-like text extraction, handwriting understanding, question segmentation, student answer extraction, knowledge point inference, and confidence assessment.
---

# Homework Perception

Use this skill as the first stage after homework image upload. Convert the page into a single high-confidence `trusted_question` record for downstream grading skills.

## Stage Boundary

Only do perception and structuring. Do not grade, diagnose, tutor, recommend exercises, or generate feedback.

## Input Assumptions

- Accepted files: `jpg`, `jpeg`, `png`
- Source field: `file`
- Optional metadata: `subject`
- The image may contain printed text, handwriting, diagrams, teacher marks, partial crops, or multiple questions.

## Output Contract

Return JSON only. Preferred shape:

```json
{
  "trusted_question": {
    "subject": "math",
    "question": "question stem with key conditions, units, formulas, and diagram references",
    "student_answer": "visible student work, steps, final answer, and units",
    "knowledge": ["quadratic function", "maximum value"],
    "question_type": "calculation",
    "confidence": 0.92
  }
}
```

Batch mode is optional and only used when explicitly requested:

```json
{
  "trusted_question": {},
  "questions": []
}
```

## Extraction Priority

1. Read the full page before extracting any region.
2. Identify page structure in this order:
   - assignment title or worksheet header
   - question stem
   - options, blanks, or prompts
   - answer area
   - diagrams or figures
   - teacher marks or annotations
3. If the page contains multiple questions, select the first complete question in reading order unless batch mode is requested.
4. If the answer is visible but the stem is partially cropped, keep the visible context and lower confidence.
5. If the page contains a diagram-heavy question, describe the visible visual facts inside `question` or `student_answer` instead of omitting them.

## Normalization Rules

- `subject`: preserve the caller subject unless the image clearly contradicts it.
- `question`: preserve all key conditions, formulas, labels, symbols, and units.
- `student_answer`: preserve visible working, crossed-out text, and final answer.
- `knowledge`: short topic labels only.
- `question_type`: use a stable routing label.
- `confidence`: use a number from `0` to `1`.

## Question Type Map

Prefer one of these canonical labels:

- `objective`
- `multiple_choice`
- `fill_in_blank`
- `calculation`
- `reasoning`
- `essay`
- `short_answer`
- `mixed_visual_text`
- `unknown`

Use `objective` for fixed-answer questions with direct matching. Use `mixed_visual_text` when the visual content materially affects the answer. Use `unknown` only when the image is too unclear to classify.

## Subject Heuristics

- Math / physics: preserve equations, units, symbols, and intermediate reasoning traces.
- Chinese: preserve wording, paragraph boundaries, and prompt intent.
- English: preserve spelling, tense, grammar cues, and punctuation.
- Chemistry / biology: preserve element names, formulas, labels, and experimental notes.
- Diagrams: preserve labeled points, axes, arrows, dimensions, and relations.

## Confidence Rules

- `0.90-1.00`: whole question is clear and answer is readable.
- `0.70-0.89`: mostly clear with small crop or handwriting ambiguity.
- `0.40-0.69`: partial visibility or significant uncertainty.
- `0.00-0.39`: insufficient image quality.

## Guardrails

- Do not invent missing text, options, or answers.
- Do not silently fix the student's work.
- Do not use teacher marks as student answer unless clearly part of the work.
- Do not output Markdown or natural language outside JSON.
- Do not include the base64 image in the output.
