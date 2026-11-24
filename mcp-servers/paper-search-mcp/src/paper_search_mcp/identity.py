"""Stable identifiers; titles are matching evidence, never automatic merge keys."""

import re
from urllib.parse import unquote, urlparse


def normalize_ref(value: str) -> str:
    value = value.strip()
    if value.startswith(("https://", "http://")):
        url = urlparse(value)
        host = (url.hostname or "").lower()
        path = url.path.strip("/")
        if host in ("doi.org", "dx.doi.org"):
            value = "doi:" + unquote(path)
        elif host in ("arxiv.org", "www.arxiv.org", "export.arxiv.org"):
            value = "arxiv:" + re.sub(r"^(abs|pdf|src|e-print)/", "", unquote(path))
            value = re.sub(r"\.pdf$", "", value)
        elif host == "openalex.org":
            value = "openalex:" + path
        elif host in ("semanticscholar.org", "www.semanticscholar.org") and "/paper/" in url.path:
            value = "s2:" + path.split("/")[-1]
        else:
            if url.scheme not in ("https", "http") or not host or url.username:
                raise ValueError("Invalid paper URL")
            value = "url:" + url._replace(fragment="").geturl()
    if re.match(r"^10\.\d{4,9}/\S+$", value, re.I):
        value = "doi:" + value
    if re.match(r"^(\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?$", value, re.I):
        value = "arxiv:" + value
    if ":" not in value:
        raise ValueError("Use a DOI, arXiv ID, supported URL or namespaced external ID")
    scheme, ident = value.split(":", 1)
    scheme = {"semantic_scholar": "s2", "arxivid": "arxiv"}.get(scheme.lower(), scheme.lower())
    if (
        scheme not in ("doi", "arxiv", "s2", "openalex", "scholar", "scholar_cites", "url")
        or not ident
    ):
        raise ValueError("Unsupported or empty identifier")
    if any(c.isspace() for c in ident):
        raise ValueError("Identifiers cannot contain whitespace")
    if scheme in ("doi", "s2"):
        ident = unquote(ident).lower()
    if scheme == "arxiv":
        ident = unquote(ident)
        if re.search(r"v0\d*$", ident):
            raise ValueError("Invalid arXiv revision")
        ident = re.sub(r"v\d+$", "", ident)
        if not re.fullmatch(r"(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})", ident, re.I):
            raise ValueError("Invalid arXiv identifier")
    if scheme == "doi" and not re.fullmatch(r"10\.\d{4,9}/\S+", ident):
        raise ValueError("Invalid DOI")
    if scheme == "openalex":
        ident = ident.upper()
        if not re.fullmatch(r"W\d+", ident):
            raise ValueError(
                "OpenAlex paper refs must identify works; use entity_ref for authors/institutions"
            )
    if scheme == "url":
        parsed = urlparse(ident)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username:
            raise ValueError("Invalid paper URL")
    return f"{scheme}:{ident}"


def version_from_ref(value: str) -> str | None:
    value = value.strip()
    try:
        if not normalize_ref(value).startswith("arxiv:"):
            return None
    except ValueError:
        return None
    path = urlparse(value).path if value.startswith(("http://", "https://")) else value
    match = re.search(r"(v[1-9]\d*)(?:\.pdf)?/?$", unquote(path))
    return match.group(1) if match else None


def title_key(value: str) -> str:
    return re.sub(r"\W+", " ", value.casefold()).strip()


def canonical_ref(refs: list[str]) -> str:
    if not refs:
        raise ValueError("Paper has no stable external identifier")
    priority = {
        "arxiv": 0,
        "doi": 1,
        "s2": 2,
        "openalex": 3,
        "scholar": 4,
        "scholar_cites": 5,
        "url": 6,
    }
    return min(refs, key=lambda r: (priority[r.split(":")[0]], r))
