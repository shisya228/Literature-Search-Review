import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

import requests

ARXIV_API_URL = "http://export.arxiv.org/api/query"


def _parse_entry(entry: ET.Element) -> Dict:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    title = entry.findtext("atom:title", default="", namespaces=ns).strip().replace("\n", " ")
    summary = entry.findtext("atom:summary", default="", namespaces=ns).strip().replace("\n", " ")
    entry_id = entry.findtext("atom:id", default="", namespaces=ns).strip()
    authors = [author.findtext("atom:name", default="", namespaces=ns).strip() for author in entry.findall("atom:author", ns)]
    published = entry.findtext("atom:published", default="", namespaces=ns).strip()
    year = int(published[:4]) if published[:4].isdigit() else 1900

    links = entry.findall("atom:link", ns)
    pdf_url = None
    url = entry_id
    for link in links:
        rel = link.attrib.get("rel")
        href = link.attrib.get("href")
        if rel == "alternate" and href:
            url = href
        if link.attrib.get("title") == "pdf" and href:
            pdf_url = href

    categories = [cat.attrib.get("term") for cat in entry.findall("atom:category", ns) if cat.attrib.get("term")]

    return {
        "provider": "arxiv",
        "id": entry_id.split("/abs/")[-1] if "/abs/" in entry_id else entry_id,
        "title": title,
        "authors": [author for author in authors if author],
        "published_year": year,
        "abstract": summary,
        "url": url,
        "pdf_url": pdf_url,
        "categories": categories,
        "score": None,
    }


def search_arxiv(query: str, max_results: int = 20, start: int = 0) -> List[Dict]:
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
    }
    url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"
    start_time = time.time()
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    latency_ms = int((time.time() - start_time) * 1000)

    root = ET.fromstring(response.text)
    entries = root.findall("{http://www.w3.org/2005/Atom}entry")
    papers = [_parse_entry(entry) for entry in entries]

    return papers, latency_ms
