# PROMPT_LOG — Query Fan-Out Engine Prompt Iteration

## Overview

This document tracks my prompt engineering process
for the Query Fan-Out Engine (Feature 2).

The goal was to get Gemini to reliably return valid JSON
with exactly 6 sub-query types, at least 2 per type,
every single time — with no extra fields, no markdown,
and no hallucinated types.

---

## Attempt 1 — First Draft

### The Prompt
Generate 10-15 sub-queries for this query: "{target_query}"
Return them as JSON with type and query fields.
Types: comparative, feature_specific, use_case,
trust_signals, how_to, definitional.

### What Went Wrong

1. Gemini wrapped JSON in markdown backticks
   causing json.loads() to crash immediately

2. Sometimes returned only 7-8 sub-queries

3. Added extra fields like "description" and "priority"
   that broke Pydantic validation

4. One type was often missing entirely —
   trust_signals was the most commonly skipped

5. No example in the prompt so the model guessed format

6. Used wrong key name "queries" instead of "sub_queries"

### Failure Example

```json
Here are the sub-queries I generated:
{
  "queries": [
    {
      "type": "comparative",
      "query": "X vs Y",
      "priority": "high",
      "description": "Compare X to alternatives"
    }
  ]
}
```

### Lesson

Telling the model what NOT to do is not enough.
The model needs to see exactly what you want.

---

## Attempt 2 — Added Structure and Rules

### What I Changed

- Added: return ONLY valid JSON
- Added: no markdown, no backticks, no prose
- Specified minimum 2 per type explicitly
- Listed all 6 types with short descriptions
- Specified exact key name: sub_queries

### What Improved

- Correct key name sub_queries every time
- JSON was valid about 70 percent of the time

### What Still Went Wrong

- Model still occasionally returned markdown
- Some sub-queries were too generic and vague
- Model invented a 7th type called "pricing"
- Fewer than 10 sub-queries on some attempts

### Lesson

Rules alone are not enough.
The model needs an example to anchor the format.

---

## Attempt 3 — Added Concrete Example Output

### What I Changed

- Added a complete example of expected JSON output
- Added: do not add extra fields beyond type and query
- Added: do not invent new types beyond the 6 listed
- Made example queries specific and realistic
- Moved all instructions into a system message

### What Improved

- JSON was valid 90 percent of the time
- No extra fields in responses
- No invented types

### What Still Went Wrong

- Occasionally returned 9 sub-queries instead of 10
- Trust signals queries still sometimes generic

### Lesson

Concrete examples work better than rules.
But the minimum count needs explicit enforcement.

---

## Attempt 4 — Final Prompt

### What I Changed

- Added CRITICAL RULES section in caps for emphasis
- Added explicit: do not return fewer than 10
- Added retry logic in code — 3 attempts with backoff
- Added markdown stripping in parser as safety net
- Added Pydantic validation after parsing
- Made each type description more specific
- Fixed async bug — switched to generate_content_async

### Why This Works

- Role definition focuses the model on the task
- Type descriptions reduce ambiguity per type
- CRITICAL RULES in caps gets model attention
- Concrete example eliminates format guessing
- Retry logic handles remaining edge cases
- Markdown stripping catches edge cases in parser
- Pydantic validation ensures clean output to caller

---

## Final Prompt — Exact Code Used in Production

### System Message

This is the exact SYSTEM_PROMPT variable in fanout_engine.py:
You are a search query decomposition engine.
Your job is to take a target query and generate 10-15 sub-queries
that simulate how AI search engines like Perplexity or ChatGPT
decompose a query to build a comprehensive answer.
You MUST generate at least 2 sub-queries for EACH of these 6 types:

comparative - comparing the topic to alternatives
feature_specific - focusing on specific capabilities or features
use_case - real world applications and scenarios
trust_signals - reviews, case studies, credibility, proof points
how_to - procedural or instructional queries
definitional - conceptual or "what is" queries

CRITICAL RULES:

Return ONLY a valid JSON object — no markdown, no prose, no backticks
Every sub-query must have exactly two fields: "type" and "query"
The "type" field must be one of the 6 types listed above
Do not add any extra fields
Do not return fewer than 10 sub-queries total
Make sub-queries specific and realistic

EXAMPLE OUTPUT FORMAT:
{
"sub_queries": [
{"type": "comparative", "query": "X vs Y for Z use case"},
{"type": "comparative", "query": "X alternatives for small businesses"},
{"type": "feature_specific", "query": "X key features for enterprise"},
{"type": "feature_specific", "query": "X integration capabilities"},
{"type": "use_case", "query": "how companies use X for Y"},
{"type": "use_case", "query": "X for agency workflows at scale"},
{"type": "trust_signals", "query": "X customer reviews and ratings"},
{"type": "trust_signals", "query": "X case studies and success stories"},
{"type": "how_to", "query": "how to get started with X"},
{"type": "how_to", "query": "how to optimize X for better results"},
{"type": "definitional", "query": "what is X and how does it work"},
{"type": "definitional", "query": "what are the core concepts behind X"}
]
}

### User Message

This is the exact user_prompt variable in fanout_engine.py:
Generate 10-15 sub-queries for this target query: "{target_query}"
Remember:

Return ONLY valid JSON
At least 2 sub-queries per type
No markdown formatting
No extra fields in the JSON


### LLM Configuration

```python
model = genai.GenerativeModel("gemini-2.0-flash")

response = await model.generate_content_async(
    SYSTEM_PROMPT + "\n\n" + user_prompt,
    generation_config=genai.GenerationConfig(
        temperature=0.7,
        max_output_tokens=2048,
    )
)
```

Temperature 0.7 chosen to balance creativity
and consistency. Lower values produced too
repetitive sub-queries. Higher values produced
inconsistent JSON formatting.

---

## Async Bug — Critical Fix

During testing the API was returning 503 on every request
even with a valid prompt and API key.

Root cause: generate_content() is synchronous.
Calling it inside FastAPI's async event loop caused
an event loop conflict on every single request.

Fix: switched to generate_content_async() —
the proper async variant for use inside async functions.

This bug was invisible without logging.
Added logger.warning() in all three except blocks
so every failure is now diagnosable from server logs.

---

## Key Lessons From This Process

1. Show dont tell — a concrete example beats
   any amount of instructional text

2. CAPS for critical rules gets model attention
   and reduces rule violations significantly

3. Always strip markdown in parser as safety net
   even when you tell the model not to use it

4. Retry logic is essential for production LLM calls
   — even well-designed prompts fail occasionally

5. Validate with Pydantic before returning to caller
   — malformed responses should never reach the user

6. Naming the output key explicitly prevents
   the model from using wrong key names

7. Type descriptions reduce hallucination —
   vague type names lead to vague or wrong sub-queries

8. The async bug was invisible without logging —
   always add logger.warning in every except block
   so failures are diagnosable from server logs

9. Temperature matters — 0.7 was the sweet spot
   between creativity and JSON consistency

10. Prompt iteration is engineering work —
    document every failure and what you learned
    from it just like you would document a bug fix