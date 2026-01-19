import json
import time
from typing import Dict, List

import streamlit as st

from llm import generate_query_bundle, generate_paper_cards, generate_review
from providers.arxiv import search_arxiv
from llm.validator import validate_json


st.set_page_config(page_title="Literature Search + Review Assistant", layout="wide")


def log_event(event: str, **payload) -> None:
    print(json.dumps({"event": event, **payload}))


def init_state() -> None:
    defaults = {
        "topic": "",
        "query_bundle": None,
        "round": 1,
        "results": [],
        "basket": [],
        "paper_cards": [],
        "review": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_markdown(review: Dict) -> str:
    lines = [f"# {review['title']}", "", review["abstract"], ""]
    for section in review["sections"]:
        lines.append(f"## {section['heading']}")
        lines.append(section["content_markdown"])
        lines.append("")
    lines.append("## References")
    for ref in review["references"]:
        lines.append(f"- {ref['citation_text']}")
    return "\n".join(lines)


def add_to_basket(selected_ids: List[str]) -> None:
    existing = {paper["id"]: paper for paper in st.session_state.basket}
    for paper in st.session_state.results:
        if paper["id"] in selected_ids:
            existing[paper["id"]] = paper
    st.session_state.basket = list(existing.values())
    log_event("basket_updated", size=len(st.session_state.basket))


init_state()

st.title("Literature Search + Review Assistant (v0)")

st.header("1) Topic Input")

with st.form("topic_form"):
    topic = st.text_input("Topic", value=st.session_state.topic, placeholder="e.g., climate adaptation narratives")
    submitted = st.form_submit_button("Generate Query Bundle")

if submitted and topic:
    st.session_state.topic = topic
    st.session_state.round = 1
    log_event("topic_submitted", topic=topic)
    bundle = generate_query_bundle(topic, round_num=1, strategy="initial", rationale="Initial query formulation.")
    validate_json(bundle, "query_bundle.schema.json")
    st.session_state.query_bundle = bundle
    log_event("query_bundle_generated", round=1)

st.header("2) Query Bundle")
if st.session_state.query_bundle:
    st.json(st.session_state.query_bundle)

    if st.button("Search"):
        query = st.session_state.query_bundle["search_queries"][0]
        log_event("search_started", provider="arxiv", round=st.session_state.round, k=20)
        papers, latency_ms = search_arxiv(query, max_results=20)
        for paper in papers:
            validate_json(paper, "paper.schema.json")
        st.session_state.results = papers
        log_event("search_completed", count=len(papers), latency_ms=latency_ms)

st.header("3) Results")
if st.session_state.results:
    selected_ids = []
    for paper in st.session_state.results:
        with st.container():
            cols = st.columns([0.1, 0.9])
            with cols[0]:
                checked = st.checkbox("", key=f"select_{paper['id']}")
            with cols[1]:
                st.subheader(paper["title"])
                st.caption(", ".join(paper["authors"]))
                st.write(f"Year: {paper['published_year']} | Categories: {', '.join(paper['categories'])}")
                st.write(paper["abstract"])
                st.markdown(f"[Link]({paper['url']})")
                if paper["pdf_url"]:
                    st.markdown(f"[PDF]({paper['pdf_url']})")
            if checked:
                selected_ids.append(paper["id"])
    if st.button("Add to Basket"):
        add_to_basket(selected_ids)

st.header("4) Iteration (Max 2)")
iteration_cols = st.columns(3)

def handle_iteration(strategy: str) -> None:
    if not st.session_state.query_bundle:
        st.warning("Generate a query bundle first.")
        return
    if st.session_state.round >= 3:
        st.warning("Maximum iterations reached.")
        return
    st.session_state.round += 1
    rationale_map = {
        "broaden": "Expanding scope with broader terminology.",
        "narrow": "Narrowing scope with constraints.",
        "shift_domain": "Shifting to adjacent domain vocabulary.",
    }
    rationale = rationale_map[strategy]
    log_event("iteration_requested", type=strategy, round=st.session_state.round)
    bundle = generate_query_bundle(
        st.session_state.topic,
        round_num=st.session_state.round,
        strategy=strategy,
        rationale=rationale,
    )
    validate_json(bundle, "query_bundle.schema.json")
    st.session_state.query_bundle = bundle
    log_event("query_bundle_generated", round=st.session_state.round)
    query = bundle["search_queries"][0]
    log_event("search_started", provider="arxiv", round=st.session_state.round, k=20)
    papers, latency_ms = search_arxiv(query, max_results=20)
    for paper in papers:
        validate_json(paper, "paper.schema.json")
    st.session_state.results = papers
    log_event("search_completed", count=len(papers), latency_ms=latency_ms)

with iteration_cols[0]:
    if st.button("Broaden"):
        handle_iteration("broaden")
with iteration_cols[1]:
    if st.button("Narrow"):
        handle_iteration("narrow")
with iteration_cols[2]:
    if st.button("Shift Domain"):
        handle_iteration("shift_domain")

st.caption(f"Current round: {st.session_state.round}")

st.header("5) Basket")
if st.session_state.basket:
    for paper in st.session_state.basket:
        st.write(f"- {paper['title']} ({paper['published_year']})")
else:
    st.write("No papers selected yet.")

if st.button("Generate Paper Cards"):
    if not st.session_state.basket:
        st.warning("Add papers to the basket first.")
    else:
        start = time.time()
        cards = generate_paper_cards(st.session_state.topic, st.session_state.basket)
        for card in cards:
            validate_json(card, "paper_card.schema.json")
        st.session_state.paper_cards = cards
        log_event("paper_cards_generated", count=len(cards), latency_ms=int((time.time() - start) * 1000))

st.header("6) Paper Cards")
if st.session_state.paper_cards:
    st.json(st.session_state.paper_cards)

if st.button("Generate Review Draft"):
    if not st.session_state.paper_cards:
        st.warning("Generate paper cards first.")
    else:
        start = time.time()
        review = generate_review(st.session_state.topic, st.session_state.basket, st.session_state.paper_cards)
        validate_json(review, "review.schema.json")
        st.session_state.review = review
        log_event("review_generated", sections=len(review["sections"]), latency_ms=int((time.time() - start) * 1000))

st.header("7) Review Draft")
if st.session_state.review:
    st.markdown(render_markdown(st.session_state.review))
