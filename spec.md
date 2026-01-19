# spec.md — Literature Search + Review Assistant (v0)

> Goal: build a usable v0 via “AI co-building workflow”.
> This spec is written as an acceptance-contract: **what must work**, **what is out of scope**, **how we will verify**.

---

## 0. Problem Statement

Researchers often start with a vague topic and spend lots of time:
- guessing keywords,
- iterating search queries manually,
- scanning abstracts,
- collecting papers,
- writing structured summaries,
- stitching them into a literature review.

We want a v0 tool that turns this into a **repeatable workflow** with:
- short feedback loops,
- human-in-the-loop selection,
- measurable retrieval quality.

---

## 1. User & Use Cases

### Primary user
- A humanities/social-science researcher (non-technical), writing a course paper / thesis section.

### Core use cases
1) **Topic → Query Bundle**
   - User enters a topic.
   - System produces a structured set of search queries and keyword variants.

2) **Search + Iteration**
   - System searches a provider (default: arXiv / OpenAlex / other pluggable provider).
   - User can request **broaden / narrow / shift-domain** iterations (max 2 rounds).

3) **Selection → Basket**
   - User selects papers from results into a “basket”.

4) **Paper Cards**
   - System generates structured summaries (“paper cards”) from abstracts (v0) and optionally full text (v1+).

5) **Literature Review Draft**
   - System generates a review draft from selected paper cards using a chosen outline mode.

---

## 2. Non-Goals (v0)

- No bulk crawling or automated downloading behind paywalls.
- No automatic PDF extraction pipeline (can be v1+).
- No promise of perfect citations; v0 uses best-effort metadata.
- No infinite query loops: iteration rounds are limited.
- No user accounts; local-only is acceptable for v0.

---

## 3. System Boundaries (v0)

### Data sources
- **Provider interface must be pluggable**.
- Default provider for v0: **arXiv API** (open access) OR another open metadata source.
- CNKI is **not** integrated as an API in v0. (If needed later, it will be “manual/open-link + human download”.)

### Human-in-the-loop
- The user chooses which papers to include.
- The system assists in query formulation and synthesis.

---

## 4. UX Requirements (v0 UI)

### Screens / panels (single-page is fine)
1) **Topic input**
   - Text input: `topic`
   - Button: `Generate Query Bundle`

2) **Query Bundle panel**
   - Displays structured query bundle.
   - Button: `Search`

3) **Results list**
   - Shows top results with:
     - title, authors, year, venue/source
     - abstract snippet (or full abstract if available)
     - primary link + pdf link (if available)
   - Each item has checkbox: `Add to Basket`

4) **Iteration controls**
   - Buttons:
     - `Broaden`
     - `Narrow`
     - `Shift Domain`
   - Each creates a new query bundle (round+1), then re-searches.
   - **Hard limit:** max 2 iteration rounds after initial search.

5) **Basket**
   - Shows selected papers.
   - Button: `Generate Paper Cards`

6) **Outputs**
   - Paper cards list (structured).
   - Button: `Generate Review Draft`
   - Review draft rendered as markdown.

---

## 5. Functional Requirements (Acceptance Criteria)

### A. Query Bundle Generation
**Given** a topic string  
**When** user clicks `Generate Query Bundle`  
**Then** the system outputs a `QueryBundle` object with:
- `core_terms` (2–6 items)
- `synonyms` (5–20 items)
- `narrow_terms` (0–10 items)
- `exclude_terms` (0–10 items)
- `domain_shift_terms` (0–10 items)
- `search_queries` (at least 3 ready-to-run query strings)

**And** all fields are present (can be empty lists where allowed).

### B. Search Results
**Given** a `QueryBundle`  
**When** user clicks `Search`  
**Then** the system returns a list of `Paper` items (Top-K, default K=20) with:
- stable `id` (provider ID)
- `title`
- `authors` (list)
- `published_year`
- `abstract` (may be empty but must exist)
- `url` (landing page)
- `pdf_url` (optional)

**And** results list renders within 3 seconds for typical queries (excluding network outage).

### C. Iteration (Broaden / Narrow / Shift)
**Given** an existing search round  
**When** user clicks one of iteration buttons  
**Then** system produces a new `QueryBundle`:
- `round = previous_round + 1`
- includes a short `rationale` string describing what changed
- updates `search_queries`

**And** re-searches automatically and updates results.

**Hard constraints**
- Maximum total rounds: `1 (initial) + 2 iterations = 3 rounds`.
- Must show the current round number in UI.

### D. Basket Selection
**Given** search results  
**When** user checks items and clicks `Add to Basket` (or auto-add on check)  
**Then** basket contains those papers with no duplicates (dedupe by `id`).

### E. Paper Cards (from Abstracts, v0)
**Given** basket with N papers (N≥1)  
**When** user clicks `Generate Paper Cards`  
**Then** system outputs `PaperCard` for each paper including:
- `one_line_takeaway`
- `research_question`
- `key_claims` (3–7 bullets)
- `evidence_or_method` (short)
- `keywords` (5–12)
- `limitations` (optional)
- `relevance_to_topic` (short)

### F. Review Draft
**Given** generated paper cards  
**When** user clicks `Generate Review Draft`  
**Then** system outputs a markdown document with:
- title
- intro paragraph
- 3–6 sections
- each section references (at least) the paper titles/years used
- a references list (best-effort metadata)

**Modes (v0 pick at least 1)**
- Theme-based outline (default)
Optional v1+: timeline-based / debate-map-based.

---

## 6. Contracts (Data Schemas)

The system must maintain stable JSON contracts to reduce “AI drift”.
Files:
- `contracts/query_bundle.schema.json`
- `contracts/paper.schema.json`
- `contracts/paper_card.schema.json`
- `contracts/review.schema.json`

At minimum, v0 must implement QueryBundle + Paper + PaperCard + Review.

---

## 7. Observability (must-have logging)

To support AI co-building and debugging, log these events:
- `topic_submitted`
- `query_bundle_generated`
- `search_started` (provider, round, K)
- `search_completed` (count, latency_ms)
- `iteration_requested` (type, round)
- `basket_updated` (size)
- `paper_cards_generated` (count, latency_ms)
- `review_generated` (sections, latency_ms)

Logs can be console logs in v0.

---

## 8. Measure Plan (v0 evaluation)

We evaluate whether “LLM expansion” helps vs direct search.

### Experiment
- Topics: 10 (realistic)
- A: direct search (no expansion), Top-20
- B: LLM-expanded search (max 2 rounds), Top-20
- Create pool = union(A,B) per topic, dedupe by paper id/title
- Human labels each pooled item: `relevant / partial / not_relevant`

### Metrics (report 3 numbers)
1) `Precision@20` (strict or lenient; choose one and be consistent)
2) `UniqueRelevant@20` (relevant papers found only in B, not in A)
3) `FirstRelevantRank` (position of first relevant result)

Artifacts:
- `eval/labels.csv` (topic_id, paper_id, label)
- `eval/report.md` (summary table)

---

## 9. Engineering Plan (suggested module breakdown)

- `ui/` — page layout + state machine
- `providers/` — arXiv/OpenAlex provider implementations
- `llm/` — prompts + JSON parsing + retries
- `contracts/` — JSON schema files
- `eval/` — labeling template + metrics script
- `examples/` — 1–2 sample topics with saved outputs

---

## 10. Definition of Done (v0)

v0 is done when:
- all Acceptance Criteria A–F pass on at least 2 example topics,
- iteration is capped and visible,
- basket → paper cards → review works end-to-end,
- eval pipeline can output the 3 metrics for a small topic set,
- repo contains spec + contracts + prompts + checklist for reuse.
