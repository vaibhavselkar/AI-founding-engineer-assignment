import pytest
from bs4 import BeautifulSoup
from app.services.aeo_checks.direct_answer import DirectAnswerCheck

check = DirectAnswerCheck()


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# ─── Passing Cases ─────────────────────────────────────────

def test_short_declarative_no_hedge():
    """Short clear declarative paragraph should score 20"""
    html = "<p>Python is a programming language that helps developers build software quickly and efficiently.</p>"
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.score == 20
    assert result.passed is True
    assert result.details["has_hedge_phrase"] is False


def test_declarative_exactly_60_words():
    """Exactly 60 words should pass"""
    words = " ".join(["word"] * 59)
    html = f"<p>Python is {words}.</p>"
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.score >= 12


# ─── Failing Cases ─────────────────────────────────────────

def test_too_many_words():
    """Paragraph over 90 words should score 0"""
    words = " ".join(["word"] * 91)
    html = f"<p>Python is a language. {words}</p>"
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.score == 0
    assert result.passed is False


def test_hedge_phrase_detected():
    """Hedge phrase should reduce score"""
    html = "<p>It depends on your use case and the tools you choose to work with every day.</p>"
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.details["has_hedge_phrase"] is True
    assert result.score <= 12


def test_between_61_and_90_words():
    """Paragraph between 61-90 words should score 8"""
    words = " ".join(["word"] * 70)
    html = f"<p>Python is a language {words}.</p>"
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.score == 8


def test_empty_paragraph():
    """Empty content should score 0"""
    html = "<p></p>"
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.score == 0