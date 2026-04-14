import pytest
from bs4 import BeautifulSoup
from app.services.aeo_checks.htag_hierarchy import HTagHierarchyCheck

check = HTagHierarchyCheck()


def make_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# ─── Passing Cases ─────────────────────────────────────────

def test_valid_hierarchy():
    """Valid H1 H2 H3 structure should score 20"""
    html = """
    <h1>Main Title</h1>
    <h2>Section One</h2>
    <h3>Subsection</h3>
    <h2>Section Two</h2>
    """
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.score == 20
    assert result.passed is True
    assert result.details["violations"] == []


def test_h1_and_h2_only():
    """H1 followed by H2 only should score 20"""
    html = """
    <h1>Title</h1>
    <h2>Section</h2>
    <h2>Another Section</h2>
    """
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.score == 20


# ─── Failing Cases ─────────────────────────────────────────

def test_missing_h1():
    """Missing H1 should score 0"""
    html = """
    <h2>Section</h2>
    <h3>Subsection</h3>
    """
    soup = make_soup(html)
    result = check.run(soup, "")
    assert result.score == 0
    assert result.passed is False


def test_skipped_heading_level():
    """Skipping from H1 to H3 should create violation"""
    html = """
    <h1>Title</h1>
    <h3>Jumped to H3</h3>
    """
    soup = make_soup(html)
    result = check.run(soup, "")
    assert len(result.details["violations"]) > 0
    assert result.score < 20


def test_multiple_h1():
    """Multiple H1 tags should create violation"""
    html = """
    <h1>First Title</h1>
    <h1>Second Title</h1>
    <h2>Section</h2>
    """
    soup = make_soup(html)
    result = check.run(soup, "")
    assert len(result.details["violations"]) > 0


def test_tag_before_h1():
    """H2 appearing before H1 should create violation"""
    html = """
    <h2>Before Title</h2>
    <h1>Title</h1>
    <h2>Section</h2>
    """
    soup = make_soup(html)
    result = check.run(soup, "")
    assert len(result.details["violations"]) > 0