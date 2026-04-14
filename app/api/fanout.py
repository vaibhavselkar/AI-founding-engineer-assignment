from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.models.schemas import FanOutRequest, FanOutResponse, FanOutError
from app.services.fanout_engine import generate_sub_queries, MODEL_NAME
from app.services.gap_analyzer import analyze_gaps

router = APIRouter()


@router.post("/generate")
async def generate_fanout(request: FanOutRequest):
    """
    Query Fan-Out Engine endpoint.
    Generates sub-queries using LLM and optionally
    performs gap analysis against existing content.
    """
    try:
        # Generate sub-queries using Gemini
        sub_queries = await generate_sub_queries(request.target_query)

        # If content provided — run gap analysis
        if request.existing_content:
            sub_queries, gap_summary = analyze_gaps(
                sub_queries,
                request.existing_content
            )
        else:
            gap_summary = None

        return FanOutResponse(
            target_query=request.target_query,
            model_used=MODEL_NAME,
            total_sub_queries=len(sub_queries),
            sub_queries=sub_queries,
            gap_summary=gap_summary
        )

    except RuntimeError as e:
        return JSONResponse(
            status_code=503,
            content=FanOutError(
                error="llm_unavailable",
                message="Fan-out generation failed. The LLM returned "
                        "an invalid response after 3 retries.",
                detail=str(e)
            ).model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=FanOutError(
                error="internal_error",
                message="An unexpected error occurred.",
                detail=str(e)
            ).model_dump()
        )