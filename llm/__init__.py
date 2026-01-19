import json
from typing import Dict, List

from llm import prompts
from llm.openai_client import chat_completion, is_configured
from llm.stub import generate_query_bundle as stub_query_bundle
from llm.stub import generate_paper_cards as stub_paper_cards
from llm.stub import generate_review as stub_review
from llm.validator import validate_json


def _safe_llm_call(messages: List[Dict[str, str]]) -> Dict:
    result = chat_completion(messages)
    if result is None:
        raise ValueError("LLM not configured")
    return result


def generate_query_bundle(topic: str, round_num: int, strategy: str, rationale: str) -> Dict:
    if not is_configured():
        bundle = stub_query_bundle(topic, round_num, strategy, rationale)
        validate_json(bundle, "query_bundle.schema.json")
        return bundle

    messages = [
        {"role": "system", "content": prompts.QUERY_BUNDLE_PROMPT},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "topic": topic,
                    "round": round_num,
                    "strategy": strategy,
                    "rationale": rationale,
                }
            ),
        },
    ]
    try:
        bundle = _safe_llm_call(messages)
        validate_json(bundle, "query_bundle.schema.json")
        return bundle
    except Exception:
        bundle = stub_query_bundle(topic, round_num, strategy, rationale)
        validate_json(bundle, "query_bundle.schema.json")
        return bundle


def generate_paper_cards(topic: str, papers: List[Dict]) -> List[Dict]:
    if not is_configured():
        cards = stub_paper_cards(topic, papers)
        for card in cards:
            validate_json(card, "paper_card.schema.json")
        return cards

    messages = [
        {"role": "system", "content": prompts.PAPER_CARDS_PROMPT},
        {
            "role": "user",
            "content": json.dumps({"topic": topic, "papers": papers}),
        },
    ]
    try:
        cards = _safe_llm_call(messages)
        for card in cards:
            validate_json(card, "paper_card.schema.json")
        return cards
    except Exception:
        cards = stub_paper_cards(topic, papers)
        for card in cards:
            validate_json(card, "paper_card.schema.json")
        return cards


def generate_review(topic: str, papers: List[Dict], cards: List[Dict]) -> Dict:
    if not is_configured():
        review = stub_review(topic, papers, cards)
        validate_json(review, "review.schema.json")
        return review

    messages = [
        {"role": "system", "content": prompts.REVIEW_PROMPT},
        {
            "role": "user",
            "content": json.dumps({"topic": topic, "papers": papers, "cards": cards}),
        },
    ]
    try:
        review = _safe_llm_call(messages)
        validate_json(review, "review.schema.json")
        return review
    except Exception:
        review = stub_review(topic, papers, cards)
        validate_json(review, "review.schema.json")
        return review
