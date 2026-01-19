import hashlib
import itertools
from typing import List, Dict


def _tokenize(text: str) -> List[str]:
    return [token.strip().lower() for token in text.replace("/", " ").replace("-", " ").split() if token.strip()]


def _unique(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _pad_list(items: List[str], min_len: int, filler_prefix: str) -> List[str]:
    if len(items) >= min_len:
        return items
    needed = min_len - len(items)
    items.extend([f"{filler_prefix} {i + 1}" for i in range(needed)])
    return items


def generate_query_bundle(topic: str, round_num: int, strategy: str, rationale: str) -> Dict:
    tokens = _tokenize(topic)
    core_terms = _unique(tokens[:6])
    core_terms = _pad_list(core_terms, 2, "core")

    synonyms = _unique(tokens + [f"{token} study" for token in tokens])
    synonyms = _pad_list(synonyms, 5, "synonym")

    narrow_terms = ["case study", "qualitative", "quantitative"] if strategy == "narrow" else []
    exclude_terms = ["survey", "review"] if strategy == "narrow" else []
    domain_shift_terms = ["policy", "ethics", "history"] if strategy == "shift_domain" else []

    queries = [
        " AND ".join(core_terms[:2]),
        " OR ".join(synonyms[:3]),
        f"{topic} {strategy}".strip(),
    ]
    search_queries = _unique([q.strip() for q in queries if q.strip()])
    search_queries = _pad_list(search_queries, 3, "query")

    return {
        "topic": topic,
        "round": round_num,
        "strategy": strategy,
        "rationale": rationale,
        "core_terms": core_terms,
        "synonyms": synonyms,
        "narrow_terms": narrow_terms,
        "exclude_terms": exclude_terms,
        "domain_shift_terms": domain_shift_terms,
        "search_queries": search_queries,
    }


def _hash_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def generate_paper_cards(topic: str, papers: List[Dict]) -> List[Dict]:
    cards = []
    for index, paper in enumerate(papers):
        abstract = paper.get("abstract", "").strip()
        first_sentence = abstract.split(".")[0] if abstract else "Summary unavailable"
        keywords = _unique(_tokenize(paper["title"]) + _tokenize(topic))
        keywords = _pad_list(keywords, 5, "keyword")
        claims = [
            f"Addresses {topic} through {paper['title']}",
            f"Highlights {keywords[0]} and {keywords[1]}",
            "Provides evidence from the abstract",
        ]
        cards.append(
            {
                "paper_id": paper["id"],
                "title": paper["title"],
                "one_line_takeaway": f"{first_sentence.strip()}." if first_sentence else "Key insights summarized.",
                "research_question": f"How does this work inform {topic}?",
                "key_claims": claims,
                "evidence_or_method": paper.get("abstract", "Abstract-based synthesis."),
                "keywords": keywords[:12],
                "limitations": None,
                "relevance_to_topic": f"Connects {paper['title']} to {topic} for review synthesis.",
            }
        )
    return cards


def generate_review(topic: str, papers: List[Dict], cards: List[Dict]) -> Dict:
    paper_ids = [paper["id"] for paper in papers]
    sections = []
    headings = ["Background and Definitions", "Methods and Approaches", "Key Findings and Gaps"]
    for heading in headings:
        sections.append(
            {
                "heading": heading,
                "content_markdown": f"This section synthesizes insights on **{topic}** across selected papers.",
                "paper_ids": paper_ids[: max(1, len(paper_ids))],
            }
        )

    references = []
    for paper in papers:
        authors = ", ".join(paper.get("authors", [])[:3])
        citation = f"{authors} ({paper['published_year']}). {paper['title']}."
        references.append(
            {
                "paper_id": paper["id"],
                "citation_text": citation.strip(),
                "url": paper.get("url"),
            }
        )

    return {
        "topic": topic,
        "mode": "theme",
        "title": f"Literature Review: {topic}",
        "abstract": f"This review summarizes recent work on {topic} based on selected abstracts.",
        "sections": sections,
        "references": references,
    }
