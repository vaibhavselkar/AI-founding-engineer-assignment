from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.models.schemas import SubQuery, GapSummary

# Load model once at module level for performance
# Using all-MiniLM-L6-v2 for speed over accuracy
# In production all-mpnet-base-v2 would be more accurate
# but is 5x slower — for this use case speed wins
MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# Similarity threshold
# 0.72 is provided as starting point
# After testing: values below 0.65 produce too many false positives
# Values above 0.80 are too strict and miss relevant coverage
# 0.72 balances precision and recall well for this use case
SIMILARITY_THRESHOLD = 0.72


def chunk_content(text: str) -> list[str]:
    """
    Split content into sentence level chunks.
    Filters out chunks that are too short to be meaningful.
    """
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = [s.strip() for s in sentences if len(s.split()) >= 5]
    return chunks if chunks else [text]


def analyze_gaps(
    sub_queries: list[SubQuery],
    existing_content: str
) -> tuple[list[SubQuery], GapSummary]:
    """
    Compare sub-queries against content using
    sentence embeddings and cosine similarity.

    Returns updated sub_queries with covered/similarity_score
    and a GapSummary.
    """

    # Chunk the content
    content_chunks = chunk_content(existing_content)

    # Vectorize content chunks
    content_embeddings = MODEL.encode(
        content_chunks,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    # Vectorize all sub-queries at once for efficiency
    sub_query_texts = [sq.query for sq in sub_queries]
    query_embeddings = MODEL.encode(
        sub_query_texts,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    # Compute cosine similarity matrix
    # Shape: (num_queries, num_chunks)
    similarity_matrix = cosine_similarity(
        query_embeddings,
        content_embeddings
    )

    # Update sub-queries with coverage info
    updated_queries = []
    covered_types = set()
    missing_types = set()

    for i, sub_query in enumerate(sub_queries):
        # Max similarity across all content chunks
        max_similarity = float(np.max(similarity_matrix[i]))
        is_covered = max_similarity >= SIMILARITY_THRESHOLD

        updated_query = SubQuery(
            type=sub_query.type,
            query=sub_query.query,
            covered=is_covered,
            similarity_score=round(max_similarity, 2)
        )
        updated_queries.append(updated_query)

        if is_covered:
            covered_types.add(sub_query.type)
        else:
            missing_types.add(sub_query.type)

    # Build gap summary
    covered_count = sum(1 for sq in updated_queries if sq.covered)
    total_count = len(updated_queries)
    coverage_percent = round(
        (covered_count / total_count) * 100, 1
    ) if total_count > 0 else 0.0

    gap_summary = GapSummary(
        covered=covered_count,
        total=total_count,
        coverage_percent=coverage_percent,
        covered_types=sorted(list(covered_types)),
        missing_types=sorted(list(missing_types))
    )

    return updated_queries, gap_summary