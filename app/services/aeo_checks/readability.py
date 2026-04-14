import textstat
from bs4 import BeautifulSoup
from app.services.aeo_checks.base import BaseCheck
from app.models.schemas import CheckResult
from app.services.content_parser import extract_plain_text


class ReadabilityCheck(BaseCheck):
    """
    Check C — Snippet Readability Scorer
    Tests if content is readable at Flesch-Kincaid Grade Level 7-9
    Target range is complex enough to be credible,
    simple enough to be extractable by AI systems.
    """

    def run(self, soup, plain_text: str) -> CheckResult:

        # Extract clean plain text
        clean_text = extract_plain_text(soup)

        # Calculate Flesch-Kincaid Grade Level
        fk_grade = textstat.flesch_kincaid_grade(clean_text)

        # Find 3 most complex sentences
        complex_sentences = self._get_complex_sentences(clean_text)

        # Calculate score
        score = self._calculate_score(fk_grade)

        # Recommendation
        recommendation = self._get_recommendation(fk_grade)

        return CheckResult(
            check_id="readability",
            name="Snippet Readability",
            passed=7.0 <= fk_grade <= 9.0,
            score=score,
            max_score=20,
            details={
                "fk_grade_level": round(fk_grade, 1),
                "target_range": "7-9",
                "complex_sentences": complex_sentences,
            },
            recommendation=recommendation,
        )

    def _get_complex_sentences(self, text: str) -> list:
        """
        Find the 3 most complex sentences.
        Complexity = syllable count / word count per sentence.
        """
        if not text:
            return []

        # Split into sentences using basic splitting
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.split()) > 3]

        # Score each sentence by syllables per word
        scored = []
        for sentence in sentences:
            words = sentence.split()
            if not words:
                continue
            syllables = textstat.syllable_count(sentence)
            complexity = syllables / len(words)
            scored.append((complexity, sentence))

        # Sort by complexity descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return top 3 sentences truncated to 100 chars
        return [
            s[:100] + "..." if len(s) > 100 else s
            for _, s in scored[:3]
        ]

    def _calculate_score(self, fk_grade: float) -> int:
        """Calculate score based on FK grade level"""
        if 7.0 <= fk_grade <= 9.0:
            return 20
        elif fk_grade in [6.0, 10.0] or (6.0 <= fk_grade < 7.0) or (9.0 < fk_grade <= 10.0):
            return 14
        elif (5.0 <= fk_grade < 6.0) or (10.0 < fk_grade <= 11.0):
            return 8
        else:
            return 0

    def _get_recommendation(self, fk_grade: float) -> str | None:
        """Return actionable recommendation"""
        if 7.0 <= fk_grade <= 9.0:
            return None
        elif fk_grade > 9.0:
            return (
                f"Content reads at Grade {round(fk_grade, 1)}. "
                "Shorten sentences and replace technical jargon "
                "with plain language to reach Grade 7-9."
            )
        else:
            return (
                f"Content reads at Grade {round(fk_grade, 1)}. "
                "Add more detail and technical depth "
                "to reach Grade 7-9."
            )