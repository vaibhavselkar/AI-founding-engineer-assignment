import httpx
from bs4 import BeautifulSoup
from typing import Tuple

# Tags to strip as boilerplate
BOILERPLATE_TAGS = ["nav", "footer", "header", "aside", "script", "style"]

async def fetch_url(url: str) -> str:
    """Fetch HTML content from a URL"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            return response.text
    except httpx.TimeoutException:
        raise ValueError(f"Connection timeout after 10s")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"HTTP {e.response.status_code} error")
    except Exception as e:
        raise ValueError(str(e))


def strip_boilerplate(html: str) -> BeautifulSoup:
    """Parse HTML and remove boilerplate tags"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in BOILERPLATE_TAGS:
        for element in soup.find_all(tag):
            element.decompose()
    return soup


def extract_first_paragraph(soup: BeautifulSoup) -> str:
    """Extract first paragraph from parsed HTML"""
    # Try first <p> tag
    first_p = soup.find("p")
    if first_p and first_p.get_text(strip=True):
        return first_p.get_text(strip=True)

    # Fallback — get all text and split by double newline
    full_text = soup.get_text(separator="\n", strip=True)
    paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
    if paragraphs:
        return paragraphs[0]

    return ""


def extract_plain_text(soup: BeautifulSoup) -> str:
    """Extract all plain text from parsed HTML"""
    return soup.get_text(separator=" ", strip=True)


def extract_htags(soup: BeautifulSoup) -> list:
    """Extract all H tags in DOM order"""
    return [
        tag.name
        for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    ]


async def parse_input(input_type: str, input_value: str) -> Tuple[BeautifulSoup, str]:
    """
    Main entry point.
    Returns (soup, raw_html_or_text)
    """
    if input_type == "url":
        html = await fetch_url(input_value)
        soup = strip_boilerplate(html)
        return soup, html

    elif input_type == "text":
        # Wrap plain text in basic HTML if no tags present
        if "<" not in input_value:
            wrapped = f"<html><body><p>{input_value}</p></body></html>"
        else:
            wrapped = input_value
        soup = strip_boilerplate(wrapped)
        return soup, wrapped

    else:
        raise ValueError(f"Invalid input_type: {input_type}. Use 'url' or 'text'")