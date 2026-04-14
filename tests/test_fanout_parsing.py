import pytest
import json
from app.models.schemas import SubQuery


# ─── Mock LLM Response Parser Tests ────────────────────────

def parse_llm_response(raw_text: str) -> list[SubQuery]:
    """Simulate the parsing logic from fanout_engine"""
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    parsed = json.loads(raw_text)

    if "sub_queries" not in parsed:
        raise ValueError("Missing 'sub_queries' key")

    valid_types = {
        "comparative", "feature_specific", "use_case",
        "trust_signals", "how_to", "definitional"
    }

    sub_queries = []
    for item in parsed["sub_queries"]:
        if "type" not in item or "query" not in item:
            continue
        if item["type"] not in valid_types:
            continue
        sub_queries.append(SubQuery(
            type=item["type"],
            query=item["query"]
        ))

    return sub_queries


# ─── Passing Cases ─────────────────────────────────────────

def test_valid_json_response():
    """Valid JSON response should parse correctly"""
    mock_response = json.dumps({
        "sub_queries": [
            {"type": "comparative", "query": "X vs Y"},
            {"type": "comparative", "query": "X alternatives"},
            {"type": "feature_specific", "query": "X features"},
            {"type": "feature_specific", "query": "X capabilities"},
            {"type": "use_case", "query": "X for enterprise"},
            {"type": "use_case", "query": "X for small business"},
            {"type": "trust_signals", "query": "X reviews"},
            {"type": "trust_signals", "query": "X case studies"},
            {"type": "how_to", "query": "how to use X"},
            {"type": "how_to", "query": "how to set up X"},
            {"type": "definitional", "query": "what is X"},
            {"type": "definitional", "query": "X explained"}
        ]
    })
    result = parse_llm_response(mock_response)
    assert len(result) == 12
    assert all(isinstance(sq, SubQuery) for sq in result)


def test_markdown_wrapped_json():
    """JSON wrapped in markdown backticks should parse correctly"""
    mock_response = """```json
{
  "sub_queries": [
    {"type": "comparative", "query": "X vs Y"},
    {"type": "feature_specific", "query": "X features"}
  ]
}
```"""
    result = parse_llm_response(mock_response)
    assert len(result) == 2


# ─── Failing Cases ─────────────────────────────────────────

def test_invalid_json_raises_error():
    """Invalid JSON should raise JSONDecodeError"""
    with pytest.raises(json.JSONDecodeError):
        parse_llm_response("this is not json at all")


def test_missing_sub_queries_key():
    """Missing sub_queries key should raise ValueError"""
    mock_response = json.dumps({"wrong_key": []})
    with pytest.raises(ValueError):
        parse_llm_response(mock_response)


def test_invalid_type_filtered_out():
    """Invalid sub-query types should be filtered out"""
    mock_response = json.dumps({
        "sub_queries": [
            {"type": "comparative", "query": "X vs Y"},
            {"type": "invalid_type", "query": "should be filtered"},
            {"type": "how_to", "query": "how to use X"}
        ]
    })
    result = parse_llm_response(mock_response)
    assert len(result) == 2
    assert all(sq.type != "invalid_type" for sq in result)
