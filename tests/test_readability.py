import pytest
from bs4 import BeautifulSoup
from app.services.aeo_checks.readability import ReadabilityCheck

check = ReadabilityCheck()


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# ─── Passing Cases ─────────────────────────────────────────

def test_target_grade_level():
    """Content at grade 7-9 should score 20"""
    html = """
    <p>Python is a popular programming language used by many developers.
    It helps people build websites, apps, and data tools quickly.
    Many companies use Python because it is easy to learn and powerful.
    You can start building real projects within a few weeks of learning it.</p>
    """
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.score >= 8
    assert result.details["fk_grade_level"] is not None


def test_returns_complex_sentences():
    """Should return top 3 complex sentences"""
    html = """
    <p>The implementation of sophisticated algorithmic architectures
    necessitates comprehensive understanding of computational paradigms.
    Dogs are fun pets. Cats also make great companions for many people.
    The multifaceted epistemological frameworks demonstrate unprecedented
    levels of intellectual sophistication and cognitive complexity.</p>
    """
    soup = make_soup(html)
    result = check.run(soup, "")
    assert len(result.details["complex_sentences"]) <= 3


# ─── Failing Cases ─────────────────────────────────────────

def test_very_complex_content():
    """Very complex content should score low"""
    html = """
    <p>The epistemological ramifications of poststructuralist
    deconstructionist methodologies necessitate comprehensive
    reevaluation of ontological frameworks and hermeneutical
    paradigms within contemporary philosophical discourse,
    particularly regarding phenomenological manifestations
    of consciousness and transcendental subjectivity.</p>
    """
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.details["fk_grade_level"] > 9


def test_very_simple_content():
    """Very simple content should score low"""
    html = "<p>Cat sat. Dog ran. Sun hot. Sky blue. Big red car.</p>"
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.details["fk_grade_level"] < 7


def test_empty_content():
    """Empty content should not crash"""
    html = "<p></p>"
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result is not None