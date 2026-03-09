# PROMPTS.md — Vera Chatbot: Prompt Engineering Design Decisions

## Overview

This document explains the prompt engineering decisions made when building Vera —
an agentic RAG chatbot for Verité Research publications. Every design choice below
was deliberate, tested, and reflects a specific reason.

---

## 1. Persona Design — "Vera"

The chatbot is named **Vera**, derived naturally from "Verité". The name signals
trustworthiness and professionalism while remaining approachable.

The system prompt opens by establishing Vera's identity clearly:

```
You are Vera, a knowledgeable research assistant for Verité Research — a Sri Lankan
think tank producing independent analysis on economics, politics, finance, and
governance in South and Southeast Asia.
```

**Why anchor identity at the top?**
In long conversations, LLMs can drift from their persona. Placing the identity
statement first ensures it is prioritised in the model's attention. Vera's personality
is defined as warm, precise, and intellectually curious — never speculating beyond
what the documents support.

---

## 2. Intent Classification System

Every user message is classified before any action is taken. A **separate
zero-temperature Gemini call** acts as a classifier, returning exactly one of
five labels:

| Label | Action |
|-------|--------|
| `GREETING` | Respond naturally. No search. |
| `MEMORY` | Answer from conversation history. No search. |
| `VERITE_SEARCH` | Hybrid search → cite sources. |
| `OUT_OF_SCOPE` | Polite decline and redirect. |
| `BORDERLINE` | Define concept briefly + search Verité content. |

**Why a separate classifier call?**
Combining classification and answering in one prompt produces inconsistent routing.
A dedicated zero-temperature classifier is deterministic — it always returns a clean
label. The answering LLM can then focus entirely on generating a quality response.

**Why zero temperature for the classifier?**
Classification is a routing decision, not a creative task. Temperature 0.0 eliminates
randomness and ensures the same message always gets the same label.

**Why include conversation history in the classifier?**
The last 4 turns are passed to the classifier so it can detect memory-answerable
follow-ups. Without this, a follow-up like "Tell me more about that" would always
trigger a new search — wasting tokens and producing inconsistent context.

---

## 3. Handling Borderline Questions

**Example**: *"What is forced labour?"* or *"What is corruption?"*

These are general concepts that are directly central to Verité's research areas.
The deliberate choice is:

> **Briefly define the concept, then ground the answer in Verité's specific findings.**

**Why not refuse?**
Refusing would make Vera unhelpfully rigid. A user asking "What is forced labour?"
is almost certainly interested in Verité's research on the topic — refusing wastes
their intent.

**Why not just define without searching?**
Answering from general knowledge alone ignores the knowledge base entirely, defeating
the purpose of the RAG system.

**The combined approach** — brief definition + Verité-specific findings — maximises
usefulness while keeping Vera firmly on-topic.

Other borderline examples handled the same way:
- *"What is debt restructuring?"* → define + show Verité's economic coverage
- *"What is corruption?"* → define + show Verité's governance findings
- *"What is the RTI Act?"* → define + show Verité's transparency research

---

## 4. Search Decision Logic

The agent only calls the retriever when intent is `VERITE_SEARCH` or `BORDERLINE`.

**This avoids:**
- Unnecessary latency on greetings and small talk
- Re-searching for facts already established in the session
- Irrelevant context being injected into the prompt

**The classifier checks conversation history** so memory-answerable follow-ups
never trigger a new search. For example:

```
User: "What does Verité say about budget allocations?"
Vera: [searches, answers with sources]

User: "Can you summarise that?"
Classifier: MEMORY  ← answered from history, no new search
Vera: [summarises from conversation context]
```

---

## 5. Hybrid Search Design

Two retrievers are combined using LangChain's `EnsembleRetriever`:

- **FAISS vector search** — 60% weight — captures semantic similarity
- **BM25 keyword search** — 40% weight — catches exact terminology and proper nouns

**Why hybrid over vector-only?**
Verité publications contain precise terminology — acronyms like CIABOC, UNCAC,
RTI Act, ACA — that vector search alone can miss. BM25 catches these exact matches
while vector search handles paraphrased or conceptual queries.

**Why 60/40 weighting?**
Vector search handles the majority of natural language queries well. BM25 is given
40% weight as a strong supporting signal — enough to surface exact matches without
dominating semantic relevance.

---

## 6. Citation Format

When answering from retrieved content, Vera is instructed to end with a
**Sources section** listing document title and page number. In the UI, these
appear as clickable chips that open a source side panel showing the exact chunk.

This design choice was deliberate:
- Builds trust — users can verify every claim
- Meets the assignment requirement for source attribution
- Shows transparency in AI-generated answers

---

## 7. Memory Architecture

### Short-term (within session)
`ConversationBufferWindowMemory` keeps the last 10 turns in RAM.
Passed as conversation history to both the classifier and the answer prompt.

### Long-term (across sessions)
A SQLite store persists exchanges per `user_id`. On session start, the 10 most
recent past exchanges are loaded and injected into the system prompt as context:

```
Long-term context about this user (if any):
Previous session context:
User: I am researching private sector corruption in Sri Lanka
Vera: Verité's report Gaps in the Guardrails identifies nine key gaps...
```

This allows Vera to personalise responses and remember research interests across
sessions without storing full chat logs in the LLM context window.

---

## 8. Out-of-Scope Handling

The refusal message is warm and redirecting, not dismissive:

```
"I'm Vera, and I'm here specifically to help with Verité Research publications.
That topic falls outside what I can assist with — but if you have questions about
Verité's work on economics, governance, labour, or South Asian policy, I'd love
to help!"
```

**Why this wording?**
A curt refusal damages the conversational experience. The chosen phrasing:
- Reaffirms Vera's identity and purpose
- Acknowledges the user's message without being rude
- Actively invites them back to relevant topics

---

## 9. System Prompt Structure

The full system prompt follows this order intentionally:

```
1. Identity      ← who Vera is (anchors persona)
2. Personality   ← how Vera communicates
3. Rules         ← numbered, strict, easy for the model to follow
4. Long-term ctx ← personalisation for returning users
```

Rules are numbered rather than bulleted because numbered lists have been shown
to improve instruction-following in LLMs — the model treats them as an ordered
checklist rather than loose guidelines.

---

## 10. Known Limitations & Future Improvements

### User Identity
Currently uses an anonymous browser-based ID stored in localStorage. This means:
- Long-term memory works on the same browser ✓
- Clearing browser data resets memory
- Different devices = different memory

In production, this would be replaced with proper authentication (OAuth, JWT tokens)
to enable true cross-device persistent memory and eliminate any risk of ID collisions
between users sharing the same browser.

### Chunking Strategy
Fixed chunk size of 500 characters with 100-character overlap works well for most
Verité publications. For future improvement, semantic chunking (splitting at natural
topic boundaries rather than character count) would improve retrieval quality for
longer, densely structured reports.

### Embedding Model
HuggingFace `sentence-transformers/all-MiniLM-L6-v2` was chosen for its speed and
zero API cost — it runs fully locally. For production, a larger model such as
`all-mpnet-base-v2` or a domain-specific legal/policy embedding model would improve
retrieval accuracy for Verité's technical publications.