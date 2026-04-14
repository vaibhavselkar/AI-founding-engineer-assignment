import spacy
from app.services.aeo_checks.base import BaseCheck
from app.models.schemas import CheckResult
from app.services.content_parser import extract_first_paragraph

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Hedge phrases that reduce score
HEDGE_PHRASES = [
    "it depends",
    "may vary",
    "in some cases",
    "this varies",
    "generally speaking",
]


class DirectAnswerCheck(BaseCheck):
    """
    Check A — Direct Answer Detection
    Tests if first paragraph answers query in 60 words or less
    with a clear declarative statement and no hedge phrases.
    """

    def run(self, soup, plain_text: str) -> CheckResult:

        # Extract first paragraph
        first_para = extract_first_paragraph(soup)

        # Word count
        word_count = len(first_para.split())

        # Hedge phrase detection
        lower_para = first_para.lower()
        has_hedge = any(phrase in lower_para for phrase in HEDGE_PHRASES)

        # Declarative check using spaCy
        is_declarative = self._is_declarative(first_para)

        # Score calculation
        score = self._calculate_score(word_count, has_hedge, is_declarative)

        # Recommendation
        recommendation = self._get_recommendation(
            word_count, has_hedge, is_declarative
        )

        return CheckResult(
            check_id="direct_answer",
            name="Direct Answer Detection",
            passed=score >= 20,
            score=score,
            max_score=20,
            details={
                "word_count": word_count,
                "threshold": 60,
                "is_declarative": is_declarative,
                "has_hedge_phrase": has_hedge,
            },
            recommendation=recommendation,
        )

    def _is_declarative(self, text: str) -> bool:
        """
        Use spaCy dependency parser to check
        if text has subject + root verb = declarative sentence
        """
        if not text:
            return False

        doc = nlp(text[:500])  # Limit to first 500 chars for speed

        for sent in doc.sents:
            has_subject = any(
                token.dep_ in ("nsubj", "nsubjpass")
                for token in sent
            )
            has_root_verb = any(
                token.dep_ == "ROOT" and token.pos_ == "VERB"
                for token in sent
            )
            if has_subject and has_root_verb:
                return True

        return False

    def _calculate_score(
        self,
        word_count: int,
        has_hedge: bool,
        is_declarative: bool
    ) -> int:
        """Calculate score based on word count, hedge, declarative"""
        if word_count <= 60 and not has_hedge and is_declarative:
            return 20
        elif word_count <= 60 and (has_hedge or not is_declarative):
            return 12
        elif 61 <= word_count <= 90:
            return 8
        else:
            return 0

    def _get_recommendation(
        self,
        word_count: int,
        has_hedge: bool,
        is_declarative: bool
    ) -> str | None:
        """Return actionable recommendation"""
        if word_count > 90:
            return (
                f"Your opening paragraph is {word_count} words. "
                "Trim it to under 60 words with a direct, "
                "declarative answer."
            )
        if word_count > 60:
            return (
                f"Opening paragraph is {word_count} words. "
                "Aim for 60 words or fewer."
            )
        if has_hedge:
            return (
                "Remove hedge phrases like 'it depends' or "
                "'may vary' from your opening paragraph."
            )
        if not is_declarative:
            return (
                "Opening paragraph should be a clear declarative "
                "statement with a subject and verb."
            )
        return None