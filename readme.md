# StudyAI — Smart Notes Summariser & Quiz Generator

## What is StudyAI?

StudyAI is a web application that takes any study material — lecture notes, textbook chapters, or any text — and instantly generates:

- A **structured summary** organised by topic with bullet points
- A **multiple-choice quiz** with adjustable difficulty (Easy / Medium / Hard) and question count
- A **key terms glossary** with definitions extracted from the content
- A **downloadable PDF** combining all three for offline revision

No login required. Works on mobile. Paste text or upload a PDF/TXT file.

---

## Project Structure

```
studyai/
├── backend/
│   ├── main.py           # FastAPI server — handles HTTP requests
│   ├── gemini.py         # Groq API integration + prompt engineering
│   ├── pdf_extract.py    # PDF text extraction using pdfplumber
│   ├── requirements.txt  # Python dependencies
│   ├── .env              # Your API keys (never commit this)
│   └── .env.example      # Template for environment variables
├── frontend/
│   └── index.html        # Complete single-file frontend (HTML + CSS + JS)
├── prompts/
│   └── master_prompt.md  # Prompt engineering documentation
├── samples/
│   └── ncert_excerpt.txt # Sample NCERT Class 10 text for testing/demo
└── README.md             # This file
```

---

## How to Run Locally

### Step 1 — Clone the repository

```bash
git clone https://github.com/amitshivhare7879/studyai.git
cd studyai
```

### Step 2 — Get a free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up with your Google or GitHub account
3. Go to **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_...`)

> Groq is free, works in India without restrictions, and gives 30 requests/minute + 500 requests/day — more than enough for a hackathon demo.

### Step 3 — Set up the backend

```bash
cd backend

# Install all Python dependencies
pip install -r requirements.txt

# Create your environment file in the backend folder
cp .env.example .env
# Open .env in any text editor and paste your Groq API key
# GROQ_API_KEY=gsk_your_key_here
```

### Step 4 — Start the backend server

```bash
uvicorn main:app --reload --port 5000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

Visit `http://localhost:5000` in your browser — you should see:
```json
{"status": "StudyAI API is running"}
```

### Step 5 — Open the frontend

Open a new terminal window (keep the backend running):

```bash
# Option A — Python simple server (recommended)
cd frontend
python -m http.server 3000
# Then open http://localhost:3000 in your browser

# Option B — Open directly
# Double-click index.html in your file explorer

# Option C — VS Code Live Server
# Right-click index.html → Open with Live Server
```

### Step 6 — Test it

1. Open `samples/ncert_excerpt.txt`, copy all the text
2. Paste it into the StudyAI text box
3. Select **Medium** difficulty, set questions to **5**
4. Click **Generate Summary & Quiz**
5. Wait ~5 seconds — your summary, quiz, and key terms appear
6. Click **Download PDF** to get the offline study kit

---

## How It Works — Full Technical Explanation

### System Architecture

```
Browser (index.html)
      |
      | HTTP POST /api/generate
      | FormData: { text, difficulty, num_questions, file? }
      ↓
FastAPI Server (main.py :5000)
      |
      |-- if file uploaded → pdf_extract.py → raw text
      |-- if text pasted  → use directly
      ↓
gemini.py
      |
      | builds prompt with text + difficulty + num_questions
      ↓
Groq API (cloud)
      |
      | llama-3.3-70b-versatile model
      | returns structured JSON
      ↓
Parse + validate JSON in gemini.py
      |
      ↓
JSON response → browser
      |
app.js renders:
  → Summary cards (tab 1)
  → Interactive MCQ quiz (tab 2)
  → Key terms glossary (tab 3)
  → jsPDF generates downloadable PDF (client-side, no server needed)
```

---

### File-by-File Explanation

#### `backend/main.py` — The Entry Point

FastAPI web server exposing one endpoint: `POST /api/generate`

When a request arrives it:
1. Checks if a file was uploaded or text was typed
2. If PDF file → passes bytes to `pdf_extract.py`
3. If TXT file → decodes bytes to string
4. If plain text → uses it directly
5. Validates text is at least 50 characters
6. Calls `generate_study_content()` from `gemini.py`
7. Returns the result as JSON

CORS middleware is enabled so the frontend (on a different port) can talk to the backend freely.

#### `backend/pdf_extract.py` — PDF Reader

Uses `pdfplumber` to open a PDF from raw bytes, loops through every page, and joins all extracted text into one string. Only works on text-based PDFs — scanned/image PDFs return empty string.

#### `backend/gemini.py` — The AI Brain

The most important file. Does two things:

**1. Prompt Engineering — `build_prompt()` function**

Constructs a careful instruction for the AI. The prompt:
- Specifies the exact JSON structure the AI must return
- Defines what Easy / Medium / Hard difficulty means
- Explicitly says "no markdown, no explanation, just raw JSON"
- Injects the user's text, difficulty, and question count
- Limits text to 8000 characters to stay within model context

**2. Calling Groq API — `generate_study_content()` function**

Sends two messages to the model:
- System: `"You are an expert study assistant. Always respond with valid JSON only."`
- User: the full built prompt

After getting the response it:
- Strips accidental markdown code fences using regex
- Parses the string as JSON
- Validates all three keys exist: `summary`, `quiz`, `key_terms`
- Returns `{ success: true, data: {...} }` or `{ success: false, error: "..." }`

#### `frontend/index.html` — The Complete UI

Single HTML file containing all HTML, CSS, and JavaScript. Key parts:

**Input** — textarea for pasting text + drag-and-drop file upload zone

**Controls** — difficulty buttons that set a variable, and a range slider for question count (3–10)

**Generate button** — calls `generate()` which builds a `FormData` object and sends a `fetch()` POST to the backend

**Three tabs:**
- Summary → `topic-card` divs with bullet points per topic
- Quiz → interactive MCQ cards with option buttons
- Key Terms → definition cards in a responsive grid

**MCQ Interaction** — when user clicks an option:
1. All options in that card are disabled
2. Correct option → green highlight
3. Wrong selection → red highlight
4. Explanation slides in below
5. Progress bar updates
6. When all answered → score summary appears

**PDF Download** — uses `jsPDF` loaded from CDN. Reads `currentData` from memory and draws text onto PDF pages. Entirely client-side, no server involved.

---

### How Difficulty Levels Work

Difficulty is **prompt engineering, not a code algorithm**.

In `build_prompt()`, each level is described explicitly to the AI:

| Level | Instruction to AI | Example question type |
|-------|------------------|----------------------|
| Easy | factual recall questions | "What is photosynthesis?" |
| Medium | comprehension and application | "Why does photosynthesis rate increase with light?" |
| Hard | analysis and inference | "What would happen if chlorophyll was removed? Justify." |

The LLM interprets these descriptions and generates appropriate questions. No hardcoded logic — the model's language understanding handles the calibration. This is more accurate than any rule-based system.

---

### The Master Prompt

The entire app depends on one well-designed prompt. Structure:

```
1. Role definition     → "You are an expert study assistant"
2. Output constraint   → "Return ONLY valid JSON, no markdown, no explanation"
3. Exact JSON schema   → full structure with all field names and types shown
4. Rules section       → difficulty meanings, topic count range, question count
5. The study text      → user's content (capped at 8000 chars)
```

All three outputs (summary + quiz + key_terms) are requested in one prompt because it is faster, cheaper, and keeps context consistent across all outputs.


## Deployment

### Backend → Render (Free)

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → **New Web Service** → connect repo
3. Settings:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port 10000`
4. Add environment variable: `GROQ_API_KEY` = your key
5. Deploy → copy your Render URL

### Frontend → Netlify (Free)

1. In `frontend/index.html`, find this line and update it:
   ```javascript
   : 'https://YOUR-RENDER-URL.onrender.com'
   ```
2. Go to [netlify.com](https://netlify.com) → **Deploy manually**
3. Drag and drop the `frontend/` folder
4. Your site is live instantly

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | FastAPI (Python) | HTTP server, request routing |
| AI | llama-3.3-70b via Groq | Text analysis, quiz generation |
| PDF extraction | pdfplumber | Extract text from uploaded PDFs |
| Frontend | HTML + CSS + Vanilla JS | UI and interactivity |
| PDF export | jsPDF (CDN) | Client-side PDF generation |
| Backend hosting | Render (free) | Cloud API deployment |
| Frontend hosting | Netlify (free) | Static site hosting |


## Common Issues

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot connect to server` | Backend not running | Run `uvicorn main:app --reload --port 5000` |
| `429 quota exceeded` | Groq rate limit | Wait 60 seconds and retry |
| `Generation failed: invalid format` | AI returned bad JSON | Retry — rare occurrence |
| `Text too short` | Input under 50 chars | Paste more content |
| PDF extraction returns empty | Scanned/image PDF | Copy-paste text manually instead |

