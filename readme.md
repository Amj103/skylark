📘 DECISION LOG — Skylark BI Agent

This document records major architectural and technical decisions made during the development of Skylark BI Agent to maintain clarity, traceability, and future scalability.

✅ [2026-02-25] Use Offline Local LLM (Phi-3 GGUF via llama.cpp)

Context
The application needed private, offline inference for business intelligence queries without sending sensitive Monday.com data to external APIs.

Decision
Use:

llama_cpp + Phi-3-mini-4k-instruct-q4.gguf

downloaded via hf_hub_download() and loaded locally.

Reasoning

Protect business data privacy

Reduce API cost

Maintain offline capability

Allow deployment inside Hugging Face Spaces CPU runtime

Impact

Increased startup time (model download)

Higher RAM usage

Full local control over AI responses

✅ [2026-02-25] Adopt Semantic Routing Agent

Context
Users may ask about either:

Deals pipeline

Work orders

Hardcoding logic would reduce flexibility.

Decision

Introduce extract_intent() LLM-based routing.

Reasoning

Enables natural language interaction

Simplifies UI logic

Allows future expansion to more data sources

Impact

Two-stage AI pipeline:

Intent extraction

Leadership update generation

✅ [2026-02-25] Implement Anti-Hallucination Prompting

Context
Business dashboards require accurate numeric outputs.

Decision

Add strict system prompt rules:

Use ONLY RAW DATA
NEVER invent numbers

Reasoning

Prevent fabricated pipeline values

Maintain trust for BI reporting

Impact

More reliable summaries

Slightly less creative language output

✅ [2026-02-25] Dynamic Column Detection for Monday Data

Context
Monday boards may change column names.

Decision

Use dynamic matching:

'sector' in column name
'deal value' in column name

instead of fixed schema.

Reasoning

Makes app resilient to schema drift

Reduces maintenance

Impact

More flexible data ingestion

Slightly higher runtime processing

✅ [2026-02-25] Streamlit Conversational UI

Context

Wanted ChatGPT-style interaction instead of traditional dashboard filters.

Decision

Use:

st.chat_input
st.session_state.messages

Reasoning

Founder-friendly interface

Natural BI querying

Better UX for non-technical users

Impact

Stateful conversation flow

Clear separation of UI and agent logic

✅ [2026-02-25] Caching Strategy for Performance

Decision

Use:

@st.cache_resource → LLM loading
@st.cache_data(ttl=600) → Monday API

Reasoning

Prevent repeated model loading

Reduce API calls

Improve Space performance

🚀 Future Decisions (Planned)

Add streaming token output

Merge intent + response into single LLM call

Add analytics memory layer

Optimize CPU inference settings

🧠 Why this Decision Log is valuable

Since your project is basically a Founder BI Copilot, this file:

✅ shows architectural maturity
✅ helps future collaborators
✅ looks VERY strong in a portfolio or startup pitch

If you want, I can also create a second file for your Space called:

ARCHITECTURE.md

which visually explains your system like this:

User → Streamlit UI → Routing Agent → Monday API → Leadership Generator → Response

It will make your Space look seriously professional.