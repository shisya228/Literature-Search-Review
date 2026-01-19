# Literature Search + Review Assistant (v0)

A minimal Streamlit app to generate search queries, retrieve papers from arXiv, curate a basket, generate paper cards from abstracts, and draft a literature review. The app defaults to a local stub LLM mode that produces deterministic JSON matching the contracts.

## Features
- Topic → Query bundle → Search → Iteration (broaden/narrow/shift domain, max 2 rounds)
- arXiv provider integration (pluggable provider layer)
- Human-in-the-loop paper selection and basket management
- Paper cards generated from abstracts (v0)
- Theme-based literature review draft with markdown rendering
- JSON schema validation against `/contracts`
- Console logging for key events

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
streamlit run app.py
```

## Optional LLM Mode
Set `OPENAI_API_KEY` (and optionally `BASE_URL` / `OPENAI_MODEL`) to enable OpenAI-compatible generation. If the LLM output fails schema validation, the app falls back to stub mode.

```bash
export OPENAI_API_KEY="your_key"
export BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o-mini"
```

## Examples
See `examples/` for a sample topic and saved outputs (query bundle, papers, paper cards, review).

## Evaluation
Templates live under `eval/` with a CSV labeling stub and report outline.
