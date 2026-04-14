from pydantic import BaseModel
from typing import Optional, List

# ─── AEO Request ───────────────────────────────────────────

class AEORequest(BaseModel):
    input_type: str  # "url" or "text"
    input_value: str

# ─── AEO Check Detail Models ───────────────────────────────

class DirectAnswerDetails(BaseModel):
    word_count: int
    threshold: int = 60
    is_declarative: bool
    has_hedge_phrase: bool

class HTagDetails(BaseModel):
    violations: List[str]
    h_tags_found: List[str]

class ReadabilityDetails(BaseModel):
    fk_grade_level: float
    target_range: str = "7-9"
    complex_sentences: List[str]

# ─── AEO Check Result ──────────────────────────────────────

class CheckResult(BaseModel):
    check_id: str
    name: str
    passed: bool
    score: int
    max_score: int
    details: dict
    recommendation: Optional[str]

# ─── AEO Response ──────────────────────────────────────────

class AEOResponse(BaseModel):
    aeo_score: float
    band: str
    checks: List[CheckResult]

# ─── AEO Error ─────────────────────────────────────────────

class AEOError(BaseModel):
    error: str
    message: str
    detail: Optional[str]

# ─── Fan-out Request ───────────────────────────────────────

class FanOutRequest(BaseModel):
    target_query: str
    existing_content: Optional[str] = None

# ─── Fan-out Sub Query ─────────────────────────────────────

class SubQuery(BaseModel):
    type: str
    query: str
    covered: Optional[bool] = None
    similarity_score: Optional[float] = None

# ─── Fan-out Gap Summary ───────────────────────────────────

class GapSummary(BaseModel):
    covered: int
    total: int
    coverage_percent: float
    covered_types: List[str]
    missing_types: List[str]

# ─── Fan-out Response ──────────────────────────────────────

class FanOutResponse(BaseModel):
    target_query: str
    model_used: str
    total_sub_queries: int
    sub_queries: List[SubQuery]
    gap_summary: Optional[GapSummary] = None

# ─── Fan-out Error ─────────────────────────────────────────

class FanOutError(BaseModel):
    error: str
    message: str
    detail: Optional[str]