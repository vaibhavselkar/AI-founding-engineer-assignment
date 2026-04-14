import os
import json
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from app.models.schemas import SubQuery

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-2.5-flash"
MAX_RETRIES = 3

# ─── Prompt Template ───────────────────────────────────────

SYSTEM_PROMPT = """
You are a search query decomposition engine.
Your job is to take a target query and generate 10-15 sub-queries
that simulate how AI search engines like Perplexity or ChatGPT
decompose a query to build a comprehensive answer.

You MUST generate at least 2 sub-queries for EACH of these 6 types:
1. comparative - comparing the topic to alternatives
2. feature_specific - focusing on specific capabilities or features
3. use_case - real world applications and scenarios
4. trust_signals - reviews, case studies, credibility, proof points
5. how_to - procedural or instructional queries
6. definitional - conceptual or "what is" queries

CRITICAL RULES:
- Return ONLY a valid JSON object — no markdown, no prose, no backticks
- Every sub-query must have exactly two fields: "type" and "query"
- The "type" field must be one of the 6 types listed above
- Do not add any extra fields
- Do not return fewer than 10 sub-queries total
- Make sub-queries specific and realistic

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
"""


async def generate_sub_queries(target_query: str) -> list[SubQuery]:
    """
    Call Gemini LLM to generate sub-queries.
    Retries up to MAX_RETRIES times on failure.
    """
    model = genai.GenerativeModel(MODEL_NAME)

    user_prompt = f"""
Generate 10-15 sub-queries for this target query: "{target_query}"

Remember:
- Return ONLY valid JSON
- At least 2 sub-queries per type
- No markdown formatting
- No extra fields in the JSON
"""

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await model.generate_content_async(
                SYSTEM_PROMPT + "\n\n" + user_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            )

            raw_text = response.text.strip()

            # Clean markdown if model wraps in backticks
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            # Parse JSON
            parsed = json.loads(raw_text)

            # Validate structure
            if "sub_queries" not in parsed:
                raise ValueError("Missing 'sub_queries' key in response")

            sub_queries_raw = parsed["sub_queries"]

            if len(sub_queries_raw) < 10:
                raise ValueError(
                    f"Only {len(sub_queries_raw)} sub-queries returned, expected 10+"
                )

            # Validate and build SubQuery objects
            valid_types = {
                "comparative", "feature_specific", "use_case",
                "trust_signals", "how_to", "definitional"
            }

            sub_queries = []
            for item in sub_queries_raw:
                if "type" not in item or "query" not in item:
                    continue
                if item["type"] not in valid_types:
                    continue
                sub_queries.append(SubQuery(
                    type=item["type"],
                    query=item["query"]
                ))

            if len(sub_queries) < 10:
                raise ValueError(
                    f"Only {len(sub_queries)} valid sub-queries after validation"
                )

            return sub_queries

        except json.JSONDecodeError as e:
            last_error = f"JSONDecodeError on attempt {attempt}: {str(e)}"
        except ValueError as e:
            last_error = str(e)
        except Exception as e:
            last_error = str(e)

        # Exponential backoff between retries
        if attempt < MAX_RETRIES:
            await asyncio.sleep(2 ** attempt)

    raise RuntimeError(
        f"LLM returned an invalid response after {MAX_RETRIES} retries. "
        f"Last error: {last_error}"
    )