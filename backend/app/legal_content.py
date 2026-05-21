"""Load first-party legal copy from legacy HTML exports in the repo."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from app.settings import settings

# API slug -> file under legacy/
LEGACY_SLUG_FILES: dict[str, str] = {
    "terms": "Terms.html",
    "faq": "faq.html",
    "privacy": "privacy.html",
    "legal": "legal.html",
}

DISCLOSURE_FRAGMENT_ID = "term1005"


def repo_root() -> Path:
    return settings.resolved_funnel_config().parent.parent


def legacy_dir() -> Path:
    return repo_root() / "legacy"


def _read_legacy_file(name: str) -> str:
    path = legacy_dir() / name
    if not path.is_file():
        raise FileNotFoundError(f"Legacy legal file missing: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def _strip_chrome(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(["script", "link", "nav", "iframe"]):
        tag.decompose()
    for tag in soup.find_all(class_=lambda c: c and "navbar" in c):
        tag.decompose()


def _rewrite_links(container: BeautifulSoup) -> None:
    """Point in-site legacy paths at our /legal routes where possible."""
    mapping = {
        "/faq.html": "/legal/faq",
        "faq.html": "/legal/faq",
        "/privacy.html": "/legal/privacy",
        "privacy.html": "/legal/privacy",
        "/legal.html": "/legal/legal",
        "legal.html": "/legal/legal",
    }
    for a in container.find_all("a", href=True):
        href = a["href"]
        if href in mapping:
            a["href"] = mapping[href]
        elif href.startswith("/") and not href.startswith("//") and ".html" in href:
            # Leave other legacy marketing links as-is (external site paths)
            pass


def extract_container_html(raw_html: str) -> tuple[str, str]:
    soup = BeautifulSoup(raw_html, "html.parser")
    _strip_chrome(soup)
    # Terms.html: main copy lives in col-sm-8
    col = soup.select_one("div.col-sm-8")
    container = col or soup.select_one("div.container.narrow") or soup.select_one("div.container")
    if not container:
        body = soup.body
        if not body:
            return "Legal", raw_html
        _rewrite_links(body)
        title = soup.title.string.strip() if soup.title and soup.title.string else "Legal"
        return title, str(body)
    _rewrite_links(container)
    header = container.select_one(".txtheader, .terms-title, #terms-summary .terms-title")
    if header:
        title = header.get_text(strip=True)
    elif container.select_one("#terms-summary"):
        title = "Key Summary of Terms and Conditions"
    else:
        title = "Legal"
    return title, str(container)


def extract_disclosure_html() -> tuple[str, str]:
    raw = _read_legacy_file("Terms.html")
    soup = BeautifulSoup(raw, "html.parser")
    _strip_chrome(soup)
    block = soup.find(id=DISCLOSURE_FRAGMENT_ID)
    if not block:
        raise FileNotFoundError("Disclosure section term1005 not found in Terms.html")
    _rewrite_links(block)
    return (
        "Disclosure Statement to Consumers",
        f'<div class="legal-legacy disclosure">{block.decode_contents()}</div>',
    )


def extract_terms_summary_html() -> tuple[str, str]:
    """Key summary + link to full terms (wizard agreements step)."""
    raw = _read_legacy_file("Terms.html")
    soup = BeautifulSoup(raw, "html.parser")
    _strip_chrome(soup)
    summary = soup.select_one("#terms-summary")
    intro = soup.select_one("#term0001")
    parts: list[str] = []
    if summary:
        parts.append(str(summary))
    if intro:
        parts.append(str(intro))
    parts.append(
        '<p class="legal-full-terms-link"><a href="/legal/terms" id="enrollment-view-full-terms">'
        "View the full terms and conditions</a></p>"
    )
    return ("UTILITYnet Terms and Conditions", '<div class="legal-legacy terms">' + "".join(parts) + "</div>")


def load_legal_document(slug: str) -> dict[str, str]:
    if slug == "disclosure":
        title, html = extract_disclosure_html()
        return {"slug": slug, "title": title, "format": "html", "body": html}
    if slug == "terms-summary":
        title, html = extract_terms_summary_html()
        return {"slug": slug, "title": title, "format": "html", "body": html}
    filename = LEGACY_SLUG_FILES.get(slug)
    if not filename:
        raise FileNotFoundError(f"Unknown legal slug: {slug}")
    raw = _read_legacy_file(filename)
    title, html = extract_container_html(raw)
    return {
        "slug": slug,
        "title": title,
        "format": "html",
        "body": f'<div class="legal-legacy">{html}</div>',
    }
