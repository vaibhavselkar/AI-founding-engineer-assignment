from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.models.schemas import AEORequest, AEOResponse, AEOError
from app.services.content_parser import parse_input, extract_plain_text
from app.services.aeo_checks.direct_answer import DirectAnswerCheck
from app.services.aeo_checks.htag_hierarchy import HTagHierarchyCheck
from app.services.aeo_checks.readability import ReadabilityCheck

router = APIRouter()

# Initialize checks
checks = [
    DirectAnswerCheck(),
    HTagHierarchyCheck(),
    ReadabilityCheck(),
]


@router.post("/analyze")
async def analyze_content(request: AEORequest):
    """
    AEO Content Scorer endpoint.
    Accepts URL or text and returns AEO readiness score.
    """
    try:
        # Parse input
        soup, raw = await parse_input(
            request.input_type,
            request.input_value
        )

        # Extract plain text
        plain_text = extract_plain_text(soup)

        # Run all checks
        results = []
        raw_score = 0

        for check in checks:
            result = check.run(soup, plain_text)
            results.append(result)
            raw_score += result.score

        # Normalize to 100
        aeo_score = round((raw_score / 60) * 100, 1)

        # Determine band
        band = get_band(aeo_score)

        return AEOResponse(
            aeo_score=aeo_score,
            band=band,
            checks=results
        )

    except ValueError as e:
        return JSONResponse(
            status_code=422,
            content=AEOError(
                error="url_fetch_failed",
                message="Could not retrieve content from the provided URL.",
                detail=str(e)
            ).model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=AEOError(
                error="internal_error",
                message="An unexpected error occurred.",
                detail=str(e)
            ).model_dump()
        )


def get_band(score: float) -> str:
    """Return score band label"""
    if score >= 85:
        return "AEO Optimized ✅"
    elif score >= 65:
        return "Needs Improvement 🟡"
    elif score >= 40:
        return "Significant Gaps 🔴"
    else:
        return "Not AEO Ready ⛔"