from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from html import unescape

import requests
from django.conf import settings

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

_SESSION = requests.Session()
_LAST_REQUEST_AT = 0.0


def _common_params() -> dict[str, str]:
    if not settings.NCBI_EMAIL:
        raise RuntimeError(".env 파일에 NCBI_EMAIL을 입력해주세요.")
    params = {
        "tool": settings.NCBI_TOOL_NAME,
        "email": settings.NCBI_EMAIL,
    }
    if settings.NCBI_API_KEY:
        params["api_key"] = settings.NCBI_API_KEY
    return params


def _request(method: str, url: str, **kwargs) -> requests.Response:
    global _LAST_REQUEST_AT
    min_interval = 0.11 if settings.NCBI_API_KEY else 0.35
    elapsed = time.monotonic() - _LAST_REQUEST_AT
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)

    headers = kwargs.pop("headers", {})
    headers.setdefault(
        "User-Agent",
        f"{settings.NCBI_TOOL_NAME}/1.0 "
        f"(contact: {settings.NCBI_EMAIL or 'not-configured'})",
    )
    response = _SESSION.request(
        method, url, headers=headers, timeout=60, **kwargs
    )
    _LAST_REQUEST_AT = time.monotonic()
    response.raise_for_status()
    return response


def _clean_title(value: object) -> str:
    text = unescape(str(value or "")).strip()
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split())


def search_recent_pubmed(keyword: str, days: int, max_results: int):
    keyword = keyword.strip()
    if not keyword:
        raise ValueError("검색어가 비어 있습니다.")

    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    params = {
        "db": "pubmed",
        "term": keyword,
        "retmode": "json",
        "retmax": max_results,
        "datetype": "edat",
        "mindate": start_date.strftime("%Y/%m/%d"),
        "maxdate": end_date.strftime("%Y/%m/%d"),
        "sort": "pub_date",
        **_common_params(),
    }
    result = _request("GET", ESEARCH_URL, params=params).json()["esearchresult"]
    return [str(pmid) for pmid in result.get("idlist", [])], start_date, end_date


def fetch_details(pmids: list[str]) -> dict[str, dict]:
    if not pmids:
        return {}

    data = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
        **_common_params(),
    }
    result = _request("POST", ESUMMARY_URL, data=data).json().get("result", {})
    details = {}

    for pmid in result.get("uids", []):
        item = result.get(str(pmid), {})
        authors = [
            str(author.get("name", "")).strip()
            for author in item.get("authors", [])
            if str(author.get("name", "")).strip()
        ]
        article_ids = item.get("articleids", [])
        doi = next(
            (
                str(identifier.get("value", ""))
                for identifier in article_ids
                if identifier.get("idtype") == "doi"
            ),
            "",
        )
        details[str(pmid)] = {
            "pmid": str(pmid),
            "title": _clean_title(item.get("title", "")),
            "authors": ", ".join(authors[:5])
            + (", et al." if len(authors) > 5 else ""),
            "journal": str(
                item.get("fulljournalname") or item.get("source") or ""
            ).strip(),
            "publication_date": str(item.get("pubdate", "")).strip(),
            "doi": doi.strip(),
            "pubmed_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }
    return details


def fetch_abstracts(pmids: list[str]) -> dict[str, str]:
    abstracts = {pmid: "" for pmid in pmids}
    if not pmids:
        return abstracts

    data = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
        **_common_params(),
    }
    root = ET.fromstring(_request("POST", EFETCH_URL, data=data).content)

    for article in root.findall("./PubmedArticle"):
        pmid_node = article.find("./MedlineCitation/PMID")
        if pmid_node is None or not pmid_node.text:
            continue

        parts = []
        for node in article.findall(
            "./MedlineCitation/Article/Abstract/AbstractText"
        ):
            text = " ".join("".join(node.itertext()).split())
            if not text:
                continue
            label = (
                node.attrib.get("Label")
                or node.attrib.get("NlmCategory")
                or ""
            ).strip()
            parts.append(f"{label}: {text}" if label else text)
        abstracts[pmid_node.text.strip()] = "\n\n".join(parts)

    return abstracts


def search_papers(keyword: str, days: int = 30, max_results: int = 10):
    pmids, start_date, end_date = search_recent_pubmed(
        keyword, days, max_results
    )
    details = fetch_details(pmids)
    abstracts = fetch_abstracts(pmids)
    papers = []

    for pmid in pmids:
        if pmid not in details:
            continue
        paper = details[pmid]
        paper["abstract"] = abstracts.get(pmid, "")
        papers.append(paper)

    return papers, start_date, end_date


def fetch_papers_by_pmids(pmids: list[str]) -> list[dict]:
    clean_pmids = [str(pmid).strip() for pmid in pmids if str(pmid).strip()]
    details = fetch_details(clean_pmids)
    abstracts = fetch_abstracts(clean_pmids)
    papers = []
    for pmid in clean_pmids:
        if pmid not in details:
            continue
        paper = details[pmid]
        paper["abstract"] = abstracts.get(pmid, "")
        papers.append(paper)
    return papers


def find_paper_for_extension(
    pmid: str = "",
    doi: str = "",
    title: str = "",
) -> dict | None:
    pmid = str(pmid or "").strip()
    doi = str(doi or "").strip()
    title = " ".join(str(title or "").split())

    if pmid:
        if not pmid.isdigit():
            raise ValueError("PMID 형식이 올바르지 않습니다.")
        papers = fetch_papers_by_pmids([pmid])
        return papers[0] if papers else None

    query = ""
    if doi:
        safe_doi = doi.replace('"', "")
        query = f'"{safe_doi}"[AID]'
    elif title:
        safe_title = title.replace('"', "")
        query = f'"{safe_title}"[Title]'
    else:
        return None

    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": 5,
        **_common_params(),
    }
    result = _request("GET", ESEARCH_URL, params=params).json().get(
        "esearchresult", {}
    )
    pmids = [str(value) for value in result.get("idlist", [])]
    papers = fetch_papers_by_pmids(pmids)
    if not papers:
        return None

    if doi:
        normalized = doi.lower().strip()
        exact = [paper for paper in papers if paper.get("doi", "").lower() == normalized]
        return exact[0] if exact else papers[0]

    normalized_title = re.sub(r"\W+", "", title).lower()
    exact = [
        paper
        for paper in papers
        if re.sub(r"\W+", "", paper.get("title", "")).lower()
        == normalized_title
    ]
    return exact[0] if exact else papers[0]
