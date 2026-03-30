from groq import Groq
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def detect_length(text: str) -> str:
    words = len(text.split())
    if words < 300:
        return "short"
    elif words < 800:
        return "medium"
    else:
        return "long"

def get_summary_rules(length: str) -> str:
    if length == "short":
        return "- summary: Extract 2-4 topics. Each topic must have 2-4 bullet points. Cover ALL sections of the text."
    elif length == "medium":
        return "- summary: Extract 4-7 topics. Each topic must have 3-5 bullet points. Cover ALL sections of the text without skipping any concept."
    else:
        return "- summary: Extract 6-10 topics. Each topic must have 4-6 bullet points. You MUST cover the ENTIRE text from start to finish — do not stop at the introduction. Every major concept, law, formula, and principle mentioned must appear in at least one bullet point."

def get_keyterms_rules(length: str) -> str:
    if length == "short":
        return "- key_terms: Extract 4-6 important terms with precise definitions."
    elif length == "medium":
        return "- key_terms: Extract 7-10 important terms with precise definitions."
    else:
        return "- key_terms: Extract 10-15 important terms with precise definitions. Include all formulas, laws, and named concepts."

def get_difficulty_rules(difficulty: str) -> str:
    if difficulty == "Easy":
        return """- quiz difficulty: Easy — factual recall only.
  Questions must be directly answerable from a single sentence in the text.
  Example: "What are the two types of electric charges?" or "What does a gold-leaf electroscope detect?"
  All 4 options must be plausible but only one clearly correct."""

    elif difficulty == "Medium":
        return """- quiz difficulty: Medium — comprehension and application.
  Questions must require understanding a concept, not just recalling a fact.
  Include questions about HOW and WHY things work, relationships between concepts, and what would happen in a given scenario.
  Example: "Why does a charged rod attract small pieces of paper even though the paper is uncharged?"
  Do NOT ask questions whose answer is a single word from the text. Test understanding."""

    else:
        return """- quiz difficulty: Hard — analysis, inference, and multi-concept reasoning.
  Questions must require combining multiple concepts from the text to reason through.
  Include questions about comparing laws, predicting outcomes, identifying exceptions, applying formulas, and evaluating scenarios.
  Example: "A charge q is placed at the centre of a hollow conducting sphere. What is the electric field inside the sphere and why?"
  Questions should challenge even a student who has read the chapter carefully.
  Avoid any question that can be answered by recalling a single fact."""

def build_prompt(text: str, difficulty: str, num_questions: int) -> str:
    length = detect_length(text)
    summary_rules = get_summary_rules(length)
    keyterms_rules = get_keyterms_rules(length)
    difficulty_rules = get_difficulty_rules(difficulty)

    # For long texts, split into chunks and instruct model to cover all
    if length == "long":
        coverage_instruction = """
CRITICAL INSTRUCTION — FULL COVERAGE REQUIRED:
The text is long. You MUST read and summarise the ENTIRE text, not just the beginning.
Scan through the complete text first, identify ALL major sections and concepts, then write the summary.
If the text covers 10 topics, your summary must cover all 10 — not just the first 3.
Quiz questions must be drawn from ACROSS the entire text, not just the introduction.
"""
    else:
        coverage_instruction = "Cover all concepts present in the text."

    return f"""You are an expert study assistant and educator. Analyze the text below and return ONLY a valid JSON object — no markdown, no explanation, no code fences, just raw JSON.

{coverage_instruction}

The JSON must follow this exact structure:
{{
  "summary": [
    {{"topic": "Topic Name", "points": ["key point 1", "key point 2", "key point 3"]}}
  ],
  "quiz": [
    {{
      "question": "Clear question text?",
      "options": ["A. First option", "B. Second option", "C. Third option", "D. Fourth option"],
      "correct": "A",
      "explanation": "Brief explanation of why this is correct"
    }}
  ],
  "key_terms": [
    {{"term": "Term", "definition": "Clear and concise definition"}}
  ]
}}

Rules:
{summary_rules}
- quiz: Generate exactly {num_questions} questions.
{difficulty_rules}
- quiz: Spread questions ACROSS the entire text — do not take all questions from the introduction or a single section.
- quiz: Each question must test a DIFFERENT concept. No two questions should test the same fact.
- quiz: All 4 options must be plausible — avoid obviously wrong options that give away the answer.
{keyterms_rules}
- correct field must be just the letter: "A", "B", "C", or "D"
- Return ONLY the JSON. No preamble. No explanation.

Text to analyze:
{text[:12000]}
"""

async def generate_study_content(text: str, difficulty: str, num_questions: int):
    try:
        prompt = build_prompt(text, difficulty, num_questions)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert study assistant and educator. "
                        "Always respond with valid JSON only. No markdown, no explanation, no code fences. "
                        "When summarising long texts, you MUST cover the entire content — never stop at the introduction. "
                        "Quiz questions must span the full text and test real understanding, not trivial recall."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=6000,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

        data = json.loads(raw)

        if "summary" not in data or "quiz" not in data or "key_terms" not in data:
            raise ValueError("Missing required fields in response")

        return {"success": True, "data": data}

    except json.JSONDecodeError as e:
        return {"success": False, "error": f"AI returned invalid format. Please try again. ({str(e)})"}
    except Exception as e:
        return {"success": False, "error": f"Generation failed: {str(e)}"}