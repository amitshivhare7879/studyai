# Prompt Engineering — StudyAI

## Master Prompt Strategy

We use a **single-call JSON prompt** — one Gemini API call returns all three outputs (summary, quiz, key terms) simultaneously. This is faster, cheaper, and avoids inconsistency between separate calls.

## The Prompt

```
You are an expert study assistant. Analyze the text below and return ONLY a valid JSON object — no markdown, no explanation, no code fences, just raw JSON.

The JSON must follow this exact structure:
{
  "summary": [
    {"topic": "Topic Name", "points": ["key point 1", "key point 2"]}
  ],
  "quiz": [
    {
      "question": "Clear question text?",
      "options": ["A. First option", "B. Second option", "C. Third option", "D. Fourth option"],
      "correct": "A",
      "explanation": "Brief explanation of why this is correct"
    }
  ],
  "key_terms": [
    {"term": "Term", "definition": "Clear and concise definition"}
  ]
}

Rules:
- summary: Group into logical topics (3-6 topics). Each topic must have 2-5 bullet points.
- quiz: Generate exactly {num_questions} questions at {difficulty} difficulty level.
  - Easy: factual recall questions
  - Medium: comprehension and application questions
  - Hard: analysis and inference questions
- key_terms: Extract 5-10 important terms with definitions.
- correct field must be just the letter: "A", "B", "C", or "D"
- Return ONLY the JSON. No preamble. No explanation.

Text to analyze:
{text}
```

## Why This Works

1. **JSON-only instruction** — explicitly tells the model no markdown, no fences
2. **Exact structure** — providing the JSON template reduces hallucination
3. **Explicit rules section** — separates content rules from format rules
4. **Difficulty mapping** — explicit description of what each level means prevents vague output
5. **Text limit** — capped at 8000 chars to stay within context and ensure focused output

## Error Handling

- Strip markdown fences with regex before parsing (Gemini sometimes adds them despite instructions)
- Validate all three keys exist in the parsed object
- Return user-friendly error messages on failure