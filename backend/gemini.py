from groq import Groq
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def build_prompt(text: str, difficulty: str, num_questions: int) -> str:
    return f"""You are an expert study assistant. Analyze the text below and return ONLY a valid JSON object — no markdown, no explanation, no code fences, just raw JSON.

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
- summary: Group into logical topics (3-6 topics). Each topic must have 2-5 bullet points.
- quiz: Generate exactly {num_questions} questions at {difficulty} difficulty level.
  - Easy: factual recall questions
  - Medium: comprehension and application questions  
  - Hard: analysis and inference questions
- key_terms: Extract 5-10 important terms with definitions.
- correct field must be just the letter: "A", "B", "C", or "D"
- Return ONLY the JSON. No preamble. No explanation.

Text to analyze:
{text[:8000]}
"""

async def generate_study_content(text: str, difficulty: str, num_questions: int):
    try:
        prompt = build_prompt(text, difficulty, num_questions)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert study assistant. Always respond with valid JSON only. No markdown, no explanation, no code fences."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
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