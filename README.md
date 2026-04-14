# AEGIS — Answer Engine & Generative Intelligence Suite

A content intelligence API that scores and improves content
for AEO (Answer Engine Optimization) and GEO
(Generative Engine Optimization) — helping content teams
understand how likely their content is to be cited by AI
search engines like ChatGPT, Perplexity, and Google AI Mode.

---

## The Problem This Solves

In 2026 users don't click ten blue links anymore.
They get one AI-generated answer.
If your content isn't structured for AI extraction
it simply doesn't get cited.

AEGIS scores your content across two dimensions:

AEO — Is your content structured so AI can extract
clean direct answers?

GEO — Does your content cover the sub-topics that
AI systems actually look for when generating answers?

---

## Quick Start

### 1. Clone the repository
git clone https://github.com/vaibhavselkar/AI-founding-engineer-assignment
cd AI-founding-engineer-assignment

### 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

### 3. Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

### 4. Create .env file
GEMINI_API_KEY=your_gemini_api_key_here
Get your free key at: aistudio.google.com

### 5. Run the server
uvicorn app.main:app --reload

### 6. Open API docs
http://localhost:8000/docs

### 7. Open Frontend UI
Open index.html in your browser for a visual interface
to test the AEO Content Scorer interactively.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| GEMINI_API_KEY | Yes | Gemini API key from aistudio.google.com |

---

## API Endpoints

### POST /api/aeo/analyze

Scores content for AEO readiness across 3 checks.
Accepts a URL or raw text/HTML.

Request with URL:
```json
{
  "input_type": "url",
  "input_value": "https://example.com/article"
}
```

Request with text:
```json
{
  "input_type": "text",
  "input_value": "<h1>Title</h1><p>Your content here</p>"
}
```

Response:
```json
{
  "aeo_score": 76.7,
  "band": "Needs Improvement",
  "checks": [
    {
      "check_id": "direct_answer",
      "name": "Direct Answer Detection",
      "passed": false,
      "score": 12,
      "max_score": 20,
      "details": {
        "word_count": 15,
        "threshold": 60,
        "is_declarative": false,
        "has_hedge_phrase": false
      },
      "recommendation": "Opening paragraph should be a clear declarative statement with a subject and verb."
    }
  ]
}
```

Score Bands:
- 85-100: AEO Optimized
- 65-84: Needs Improvement
- 40-64: Significant Gaps
- 0-39:  Not AEO Ready

---

### POST /api/fanout/generate

Generates sub-queries using Gemini LLM and optionally
performs semantic gap analysis against existing content.

Request:
```json
{
  "target_query": "best AI writing tool for SEO",
  "existing_content": "Optional article text for gap analysis"
}
```

Response:
```json
{
  "target_query": "best AI writing tool for SEO",
  "model_used": "gemini-2.0-flash",
  "total_sub_queries": 12,
  "sub_queries": [...],
  "gap_summary": {
    "covered": 2,
    "total": 12,
    "coverage_percent": 16.7,
    "covered_types": ["feature_specific"],
    "missing_types": ["comparative", "trust_signals", "how_to", "definitional"]
  }
}
```

---

## Project Structure
aegis-assignment/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── api/
│   │   ├── aeo.py                 # AEO scoring endpoint
│   │   └── fanout.py              # Fan-out engine endpoint
│   ├── services/
│   │   ├── content_parser.py      # URL fetch + HTML parsing
│   │   ├── fanout_engine.py       # Gemini LLM + prompt logic
│   │   ├── gap_analyzer.py        # Embeddings + cosine similarity
│   │   └── aeo_checks/
│   │       ├── base.py            # Abstract BaseCheck class
│   │       ├── direct_answer.py   # Check A: 60 word first para
│   │       ├── htag_hierarchy.py  # Check B: H1 H2 H3 structure
│   │       └── readability.py     # Check C: FK grade level
│   └── models/
│       └── schemas.py             # Pydantic request/response models
├── tests/
│   ├── test_direct_answer.py
│   ├── test_htag_hierarchy.py
│   ├── test_readability.py
│   └── test_fanout_parsing.py
├── index.html                     # Frontend UI for visual testing
├── README.md
├── PROMPT_LOG.md
├── requirements.txt
└── .env

---

## What I Completed vs Skipped

### Completed
- Feature 1 — AEO Content Scorer (all 3 checks)
- Feature 2 — Query Fan-Out Engine with Gemini 2.0 Flash
- Semantic gap analysis with sentence-transformers
- Unit tests for all 3 AEO checks
- LLM response parsing tests with mocked data
- Retry logic with exponential backoff (3 attempts)
- Async fix — switched to generate_content_async
- Pydantic validation on all requests and responses
- Error handling on all endpoints (422, 503, 500)
- Frontend HTML UI for visual testing
- PROMPT_LOG documenting 4 prompt iterations

### Skipped
- Brand Monitor module (out of scope for assignment)
- GEO Optimizer module (out of scope for assignment)
- Async sentence-transformer inference
  (CPU bound — kept sync, would use thread pool in production)

---

## Key Technical Decisions

### 1. LLM JSON Reliability

Gemini sometimes wraps JSON in markdown backticks
and returns extra fields not in the schema.

My solution has three layers:
- Strip markdown backticks in parser before json.loads()
- Validate parsed JSON against Pydantic schema
- Retry up to 3 times with exponential backoff (2s, 4s, 8s)
- Return 503 with clear error message after max retries

Critical async bug fixed: The original sync generate_content()
called inside FastAPI's async event loop caused event loop
conflicts on every request. Fixed by switching to
generate_content_async() — the proper async variant.

### 2. Embedding Model Choice

Chose all-MiniLM-L6-v2 over all-mpnet-base-v2.

Reasoning:
- 5x faster inference
- Acceptable accuracy trade-off for this use case
- For a real-time scoring API latency beats marginal accuracy

In production with a dedicated GPU and async inference
I would switch to all-mpnet-base-v2.

### 3. Similarity Threshold — Why 0.72

Kept 0.72 after manual testing on real content.

Below 0.65: too many false positives —
unrelated content marked as covered.

Above 0.80: too strict —
genuinely relevant coverage marked as missing.

In production I would A/B test this threshold against
human-labeled coverage data to find the optimal value.

### 4. Content Parsing Robustness

No clear first paragraph: falls back to splitting
full text by double newline.

JavaScript-heavy pages: httpx fetches rendered HTML.
If page returns empty content the API returns 422.

Pages behind login: httpx raises HTTP 403
caught and returned as 422 with clear message.

### 5. Async vs Sync Design

LLM calls: async using generate_content_async (I/O bound)
URL fetching: async using httpx AsyncClient (I/O bound)
Sentence-transformers: sync (CPU bound — acceptable for now)
spaCy: sync (CPU bound)

### 6. Failure Modes

LLM timeout: caught, retried 3 times, returns 503
URL fetch timeout: 10 second timeout, returns 422
Invalid JSON: retried with exponential backoff
Empty content: each check handles gracefully, returns 0

---

## Running Tests
pytest tests/ -v

---

## What I Would Improve With More Time

1. Redis caching for URL fetches and embeddings
   to avoid re-processing the same content

2. Async sentence-transformer inference using
   asyncio.get_event_loop().run_in_executor()
   to prevent blocking the event loop

3. Tune the 0.72 threshold against human-labeled
   coverage data rather than manual testing

4. Add rate limiting per API key

5. Add streaming endpoint for real-time scoring feedback

6. Deploy on AWS Lambda with API Gateway

7. Implement the GEO Optimizer module

---

## Time Spent

Approximately 7 hours total:
- 1 hour: Reading assignment and planning architecture
- 2 hours: Feature 1 — AEO Content Scorer
- 2 hours: Feature 2 — Fan-out Engine and gap analysis
- 1 hour: Tests, debugging async bug, retry logic
- 1 hour: Frontend UI, README, PROMPT_LOG

## One Decision I Am Least Confident About

The 0.72 similarity threshold.
It was chosen through manual testing on a small sample
of content. In production this needs to be validated
against real data with human-labeled ground truth.

## One Thing I Would Improve With Another 2 Hours

Add async sentence-transformer inference using
a thread pool executor. Currently the embedding step
is synchronous and blocks the event loop during
gap analysis on long documents.