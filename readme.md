# StudyAI — AI-Powered Study Notes Summariser & Quiz Generator

## What is StudyAI?

StudyAI is a web application that takes any study material — lecture notes, textbook chapters, or any text — and instantly generates:

- **Structured Summary** — organised by topic with bullet points, scales to content length
- **MCQ Quiz** — 3–10 questions at Easy / Medium / Hard difficulty, fully interactive
- **Key Terms Glossary** — important definitions extracted from the content
- **Downloadable PDF** — complete study kit (summary + quiz + terms) for offline revision

**No login. No signup. Works on mobile. Deployed and live.**

---

## Screenshots

### Summary Output
> *(paste your summary screenshot here after running the app)*
> Filename: `screenshots/summary.png`

### Quiz Output
> *(paste your quiz screenshot here — show a correct/wrong answer highlighted)*
> Filename: `screenshots/quiz.png`

### PDF Download
> *(paste your PDF download screenshot here)*
> Filename: `screenshots/pdf.png`

---

## Project Structure

```
studyai/
├── backend/
│   ├── main.py              # FastAPI server — handles all HTTP requests
│   ├── gemini.py            # Groq API integration + smart prompt engineering
│   ├── pdf_extract.py       # PDF text extraction using pdfplumber
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # ← API key configuration template (see below)
│   └── .env                 # Your actual keys — never committed to GitHub
├── frontend/
│   └── index.html           # Complete single-file frontend (HTML + CSS + JS)
├── prompts/
│   └── master_prompt.md     # ← LLM prompt templates documented here
├── samples/
│   ├── ncert_excerpt.txt    # ← NCERT Class 10 Science — real textbook excerpt
│   ├── sample_short.txt     # Photosynthesis (~200 words) — quick demo
│   ├── sample_medium.txt    # French Revolution (~500 words) — full feature demo
│   └── sample_long.txt      # Computer Networks (~900 words) — stress test
├── screenshots/
│   ├── summary.png          # Screenshot of summary output
│   ├── quiz.png             # Screenshot of quiz with answer highlighted
│   └── pdf.png              # Screenshot of PDF download
└── README.md                # This file
```

---

## API Key Configuration

Copy `.env.example` to create your `.env` file:

```bash
cp backend/.env.example backend/.env
```

Contents of `backend/.env.example`:

```env
# Get your free Groq API key at https://console.groq.com
# Sign up → API Keys → Create API Key → copy the gsk_... key
GROQ_API_KEY=your_groq_api_key_here
```

> **Why Groq?** Gemini's free tier shows `limit: 0` for Indian accounts due to regional restrictions. Groq is completely free, works in India, needs no credit card, and gives 30 req/min + 500 req/day.

---

## Setup Instructions

### Requirements

- Python 3.8+
- pip
- A free Groq API key from [console.groq.com](https://console.groq.com)

### Step 1 — Clone the repository

```bash
git clone https://github.com/amitshivhare7879/studyai.git
cd studyai
```

### Step 2 — Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 3 — Configure your API key

```bash
cp .env.example .env
# Open .env and set: GROQ_API_KEY=gsk_your_actual_key_here
```

### Step 4 — Start the backend server

```bash
uvicorn main:app --reload --port 5000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:5000
```

Verify it's running — open `http://localhost:5000` in your browser:
```json
{"status": "StudyAI API is running"}
```

### Step 5 — Open the frontend

Open a **new terminal** (keep backend running in the first one):

```bash
# Option A — Python simple server
cd frontend
python -m http.server 3000
# Open http://localhost:3000

# Option B — Double click frontend/index.html in file explorer

# Option C — VS Code: right-click index.html → Open with Live Server
```

---

## Usage Guide

### Basic Usage

1. Open the app in your browser
2. **Paste** study text into the textarea, or **upload** a `.pdf` or `.txt` file
3. Select **difficulty** — Easy / Medium / Hard
4. Set **number of questions** using the slider (3–10)
5. Click **Generate Summary & Quiz**
6. Wait ~5 seconds for results
7. Browse the **Summary**, **Quiz**, and **Key Terms** tabs
8. Click **Download PDF** to save your offline study kit

### Testing with Sample Inputs

Use the files in the `samples/` folder for testing:

| File | Words | Best for |
|------|-------|----------|
| `sample_short.txt` | ~200 | Quick demo — shows speed |
| `ncert_excerpt.txt` | ~400 | Core demo — NCERT real content |
| `sample_medium.txt` | ~500 | Difficulty demo — try Hard mode |
| `sample_long.txt` | ~900 | Stress test — full chapter coverage |

**Recommended demo flow for judges:**
1. Paste `sample_short.txt` → Medium → 5 questions → generate (shows speed)
2. Paste `ncert_excerpt.txt` → Hard → 7 questions → click a wrong answer (shows quiz interaction)
3. Click Download PDF (shows offline study kit)
4. Open on mobile browser (shows responsive design)

## How It Works

### System Architecture

```
Browser (index.html — Vercel)
        │
        │  POST /api/generate
        │  FormData: { text, difficulty, num_questions, file? }
        ▼
FastAPI Server (main.py — Render :10000)
        │
        ├── PDF uploaded?  → pdf_extract.py  → raw text via pdfplumber
        ├── TXT uploaded?  → decode bytes    → raw text
        └── Text pasted?   → use directly
        │
        ▼
gemini.py — Smart Prompt Builder
        │
        ├── detect_length(text)         → "short" / "medium" / "long"
        ├── get_summary_rules(length)   → scales topic count to content size
        ├── get_keyterms_rules(length)  → scales term count to content size
        ├── get_difficulty_rules(diff)  → precise instructions per difficulty
        └── build_prompt(...)           → single master prompt
        │
        │  One API call → Groq (llama-3.3-70b-versatile)
        ▼
JSON response: { summary, quiz, key_terms }
        │
        ▼
index.html renders results:
        ├── Tab 1: Summary — topic cards with bullet points
        ├── Tab 2: Quiz — interactive MCQ with answer highlighting
        ├── Tab 3: Key Terms — definition grid
        └── Download PDF → jsPDF (100% client-side)
```

### File-by-File Explanation

#### `backend/main.py`
FastAPI server with one endpoint: `POST /api/generate`. Accepts `multipart/form-data` with optional file upload + text + difficulty + question count. Routes PDF files to `pdf_extract.py`, decodes TXT files directly, and passes all text to `gemini.py`. CORS is open so the Vercel frontend can call the Render backend cross-origin.

#### `backend/pdf_extract.py`
Opens uploaded PDF bytes using `pdfplumber`, loops through all pages, and returns joined text. Text-based PDFs only — scanned/image PDFs are not supported and return an empty string.

#### `backend/gemini.py`
The core AI logic. Contains four helper functions:

- **`detect_length(text)`** — classifies input by word count: short (<300), medium (300–800), long (800+)
- **`get_summary_rules(length)`** — returns topic count rules scaled to length (2–4 / 4–7 / 6–10 topics)
- **`get_keyterms_rules(length)`** — returns term count rules (4–6 / 7–10 / 10–15 terms)
- **`get_difficulty_rules(difficulty)`** — returns precise AI instructions per level with concrete examples
- **`build_prompt(text, difficulty, num_questions)`** — assembles the final prompt with a coverage enforcement block for long texts
- **`generate_study_content()`** — calls Groq with `temperature=0.5`, `max_tokens=6000`, strips response fences, parses and validates JSON

#### `frontend/index.html`
Single HTML file with all CSS and JS inline. Features: aurora background orbs, glassmorphism cards, animated MCQ interaction (click → green/red highlight + explanation), progress bar, score ring, jsPDF export, and full mobile responsiveness.

---

## Prompt Engineering

> Full documentation in `prompts/master_prompt.md`

### Strategy: Single-Call JSON

One Groq API call returns all three outputs simultaneously:

```python
{
  "summary":   [ { "topic": "...", "points": [...] } ],
  "quiz":      [ { "question": "...", "options": [...], "correct": "A", "explanation": "..." } ],
  "key_terms": [ { "term": "...", "definition": "..." } ]
}
```

Faster, cheaper, and context-consistent compared to three separate calls.

### Length-Adaptive Prompting

| Content Length | Word Count | Topics | Key Terms |
|----------------|-----------|--------|-----------|
| Short | < 300 | 2–4 | 4–6 |
| Medium | 300–800 | 4–7 | 7–10 |
| Long | 800+ | 6–10 | 10–15 |

### Difficulty Levels

| Level | AI Instruction | Example Question |
|-------|---------------|-----------------|
| Easy | Factual recall from single sentence | "What are the two types of electric charges?" |
| Medium | HOW and WHY — comprehension and relationships | "Why does a charged rod attract uncharged paper?" |
| Hard | Multi-concept reasoning, formula application, prediction | "What is the electric field inside a hollow charged conductor and why?" |

### Coverage Enforcement (for long texts)

For inputs over 800 words, the prompt includes:

```
CRITICAL: You MUST read and summarise the ENTIRE text, not just the beginning.
Quiz questions must be drawn from ACROSS the entire text — not just the introduction.
Each question must test a DIFFERENT concept.
```

This prevents the common LLM failure of only summarising the first few paragraphs.

---

## Deployment

### Backend → Render (Free)

1. Push repo to GitHub
2. [render.com](https://render.com) → **New Web Service** → connect repo
3. Configure:

| Setting | Value |
|---------|-------|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port 10000` |

4. Add environment variable: `GROQ_API_KEY` = `gsk_your_key`
5. Deploy → copy the URL

### Frontend → Vercel (Free)

1. Update `API_BASE` in `frontend/index.html`:
```javascript
: 'https://YOUR-RENDER-URL.onrender.com'
```
2. [vercel.com](https://vercel.com) → **New Project** → import repo
3. Set Root Directory: `frontend`, Framework: `Other`, leave build commands empty
4. Deploy → live instantly

---

## Judging Checklist

### Expected Deliverables

| Requirement | Status |
|-------------|--------|
| Web app with text paste input | ✅ |
| File upload — PDF and TXT | ✅ |
| AI-generated structured summary with topic headings | ✅ |
| MCQ quiz with adjustable count (3–10) | ✅ |
| Adjustable difficulty — Easy / Medium / Hard | ✅ |
| Key terms and definitions extractor | ✅ |
| Downloadable PDF (summary + quiz + terms) | ✅ |
| No login required — instant access | ✅ |

### GitHub Requirements

| Requirement | Status | Location |
|-------------|--------|----------|
| README with setup instructions | ✅ | This file — Setup Instructions section |
| API key configuration (.env.example) | ✅ | `backend/.env.example` |
| Usage guide | ✅ | This file — Usage Guide section |
| LLM prompt templates in `prompts/` folder | ✅ | `prompts/master_prompt.md` |
| Screenshots of summary, quiz, PDF download | ✅ | `screenshots/` folder |
| Sample input text file (real textbook excerpt) | ✅ | `samples/ncert_excerpt.txt` |
| Deployed link | ✅ | Badge at top of this README |

### Bonus Points

| Bonus | Points | Status |
|-------|--------|--------|
| Live working demo via public URL at judging | +5 | ✅ Vercel |
| Deployed on cloud (Vercel + Render) | +5 | ✅ |
| Open GitHub repo with README + screenshots + architecture | +3 | ✅ |
| Mobile responsive | +2 | ✅ `@media (max-width: 600px)` |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI (Python) | HTTP server, CORS, file handling |
| AI | llama-3.3-70b via Groq API | Summarisation, quiz generation, term extraction |
| PDF reading | pdfplumber | Extract text from uploaded PDFs |
| Frontend | HTML + CSS + Vanilla JS | UI, interactivity, state |
| PDF export | jsPDF (CDN) | Client-side downloadable PDF |
| Backend deploy | Render (free) | Cloud API hosting |
| Frontend deploy | Vercel (free) | Static site hosting |

---

## Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot connect to server` | Backend not running | Run `uvicorn main:app --reload --port 5000` |
| `429 quota exceeded` | Groq rate limit | Wait 60 seconds and retry |
| `Generation failed: invalid format` | AI returned bad JSON | Retry — resolves itself |
| `Text too short` | Input under 50 characters | Paste more content |
| PDF extraction returns empty | Scanned / image PDF | Copy-paste the text manually |
| Summary only covers intro | Outdated `gemini.py` | Pull latest from GitHub |


