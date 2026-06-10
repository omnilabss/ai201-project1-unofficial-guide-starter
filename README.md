# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

**Campus dining at the Georgia Institute of Technology** — the dining halls
(Brittain, North Avenue, and West Village, which students call "Willage"), meal
plans and meal-swipe rules, on-campus eateries and coffee shops, late-night food,
Tech Square, and nearby Midtown restaurants.

This knowledge is valuable but hard to find through official channels because the
honest version of it — *which* dining hall is worth the walk, whether the meal plan
actually pays off, what's really open at 2 a.m., and how the served food compares to
the posted menu — isn't in the course catalog or on the official dining site (which
markets an "all-you-can-eat experience" and lists hours). It's spread across the
student newspaper, a GT fan blog, a student-run wiki, and student review threads,
it's opinion-heavy, and it goes stale every year as vendors and hours change. This
system makes that scattered student knowledge searchable and answerable with citations.

---

## Document Sources

14 documents collected with `scripts/collect_documents.py` (raw HTML saved under
`documents/raw/` for provenance; extracted text in `documents/*.txt`; metadata in
`documents/sources.json`). **Notable collection constraints:** Reddit blocks
automated fetching (HTTP 403), so the corpus uses other authentic student voices;
sources that are now JavaScript-only or bot-blocked were recovered from the Internet
Archive Wayback Machine (marked *(archive)* below).

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | The Technique — "A full layout of on-campus dining at Tech" | Student newspaper *(archive)* | nique.net/life/2023/08/25/a-full-layout-of-on-campus-dining-at-tech/ → `documents/01-…txt` |
| 2 | The Technique — "An inside look at Tech's Dining Halls and Services" | Student newspaper *(archive)* | nique.net/life/2014/02/06/an-inside-look-at-techs-dining-halls-and-services/ → `02` |
| 3 | The Technique — "Tech Dining rebrands, but does not improve" | Student newspaper, opinion *(archive)* | nique.net/opinions/2017/10/20/tech-dining-rebrands-but-does-not-improve/ → `03` |
| 4 | The Technique — "Meal swipes in Tech Dining" | Student newspaper, opinion *(archive)* | nique.net/opinions/2023/02/19/meal-swipes-in-tech-dining/ → `04` |
| 5 | The Technique — "Late night dining" | Student newspaper, opinion *(archive)* | nique.net/opinions/2012/03/02/late-night-dining/ → `05` |
| 6 | The Technique — "Institute extends on-campus dining hours" | Student newspaper, news *(archive)* | nique.net/news/2021/10/29/institute-extends-on-campus-dining-hours/ → `06` |
| 7 | From The Rumble Seat — "Power Rankings: Tech Dining Experiences" | GT fan blog (SB Nation), opinion | fromtherumbleseat.com/2019/9/20/20874335/…tech-dining-experiences… → `07` |
| 8 | GTAE Aero Maker Space Wiki — "Food Around Campus" | Student-run wiki | gtae.gitbook.io/ams/miscellaneous/food-around-campus → `08` |
| 9 | The Infatuation — "Where To Eat Near Georgia Tech" | Food guide *(archive)* | theinfatuation.com/atlanta/guides/where-to-eat-near-georgia-tech → `09` |
| 10 | Rambler Atlanta — "Top Restaurants Near Georgia Tech" | Local blog | rambleratlanta.com/resources/top-restaurants-near-campus/ → `10` |
| 11 | Rambler Atlanta — "Ultimate Guide to GT Meal Plans" | Local blog | rambleratlanta.com/resources/guide-gt-meal-plans/ → `11` |
| 12 | PRKED — "Georgia Tech Meal Plans: The Ultimate Student Guide" | Student-services blog | prked.com/post/georgia-tech-meal-plans-the-ultimate-student-guide → `12` |
| 13 | Niche — "Georgia Tech Campus Life" (food reviews/polls) | Student reviews aggregator *(archive)* | niche.com/colleges/georgia-institute-of-technology/campus-life/ → `13` |
| 14 | Georgia Tech Dining — "Dining Halls" | Official | dining.gatech.edu/dining-locations/dining-halls → `14` |

---

## Chunking Strategy

Implemented in [src/ingest.py](src/ingest.py): it loads `documents/*.txt`, finishes
cleaning each one, then splits it with greedy line-then-sentence packing.

**Chunk size:** ~700 characters (~175 tokens) target, hard-capped at 900 (~225 tokens).
The cap exists because `all-MiniLM-L6-v2` truncates input at 256 tokens and silently
drops the rest — so a chunk has to fit under that or its tail never gets embedded. After
building, the true maximum is **224 tokens** (verified with the MiniLM tokenizer,
truncation disabled — its default 128-token truncation otherwise hides over-long chunks).

**Overlap:** ~100 characters, carried as whole trailing lines/sentences (never a mid-word
slice), and capped so the carried text can't push a chunk over 900.

**Preprocessing before chunking:** unicode normalization (smart quotes/dashes → ASCII,
non-breaking spaces removed) and HTML-entity unescaping; per-source boilerplate removal —
strip the Technique byline/date lines, the related-article and "Advertiser Content" tails
on the fan blog and meal-plan guides, the repeated "Earn 3x points with your sapphire card"
ad line in the Infatuation guide, author bios/CTAs, and bare URL/date lines; and the Niche
page is sliced down to just its Food block (the rest is housing/safety/greek-life). Every
chunk keeps its source metadata (doc id, title, url) from `documents/sources.json` for
later citation.

**Why these choices fit your documents:** the corpus mixes short opinion columns
(~150-char sentence-lines) with list-style guides where one entry is a name line plus a
~300-char blurb. Packing whole lines (falling back to sentences only when a line exceeds
the cap) keeps a restaurant entry — name, metadata, blurb, rating — or a single argument
together in one chunk, instead of stranding a name without the fact about it.

**Final chunk count:** **157** across the 14 documents — median 639 chars, mean 599,
max 894 — comfortably inside the healthy 50–2,000 range. (A touch above the ~110–140 I
estimated in planning.md: the list-heavy guides produce more, smaller entries than I'd
guessed.) No empty chunks, no HTML artifacts, no sub-150-char fragments.

---

## Embedding Model

Implemented in [src/index.py](src/index.py).

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` (384-dim, runs locally on
CPU, free, no API key). The 157 chunks are embedded and stored in a persistent **ChromaDB**
collection configured for **cosine** distance (`hnsw:space: cosine`), each with its source
metadata (doc id, title, url). Queries are embedded with the same model; `search()` returns
the top-k chunks with distances and supports a `max_distance` cutoff so the generation step
can abstain when nothing relevant comes back.

I tested retrieval before adding any LLM — running 3+ of the eval questions and checking
both relevance and that the expected source document showed up. All five passed: every
question retrieved at least one expected source, with top-result cosine distances of
**0.17–0.29** (well under the 0.5 bar). The lower-ranked results occasionally pull in
"restaurant-shaped" noise (e.g., a Taco Mac chunk for the coffee query), which is the
off-topic-retrieval risk I flagged in planning.md — but the #1 result was on-topic in
every case.

**Production tradeoff reflection:** If cost weren't a constraint, the first upgrade I'd
buy is **context length**, not raw accuracy — MiniLM truncates at 256 tokens, which is what
forced the small-chunk design; an 8k-context embedder (OpenAI `text-embedding-3-small`/
`-large`, Voyage, Cohere v3) would let me embed a whole short opinion column or restaurant
section as one unit. Second, **domain accuracy**: MiniLM is a tiny general model and can
fumble GT jargon ("Willage", "NAV", "CULC"); a larger model placed those better. I'd skip
**multilingual** (English-only corpus). On **local vs. API**: local MiniLM is instant,
private, and free, which suits a small corpus that updates rarely — an API embedder adds
latency, cost, and ships data off-box, only worth it at a scale/quality bar this project
doesn't have. Realistically I'd A/B MiniLM vs. `text-embedding-3-small` on the five eval
questions before paying for anything bigger.

> Environment note: the local `.venv` lives on an iCloud-synced Desktop, and with the disk
> ~99% full the heavy `torch` import intermittently hung on evicted-file reads. The fix is
> environmental (free disk space and/or keep the project off iCloud), not code.

---

## Grounded Generation

Implemented in [src/answer.py](src/answer.py) using Groq `llama-3.3-70b-versatile`
at `temperature=0`.

**System prompt grounding instruction:** the model is given the numbered retrieved
chunks and these rules (verbatim from `SYSTEM` in `src/answer.py`):

> You are The Unofficial Guide to Georgia Tech campus dining. Answer the question
> using ONLY the information in the numbered sources the user provides. Rules:
> - Use only facts stated in the sources. Do not add anything from your own knowledge
>   or assumptions.
> - If the sources do not contain enough information to answer, reply with exactly:
>   "I don't have enough information on that." and nothing else.
> - Cite the sources you use inline with their [S#] labels.
> - Be concise, and report what students actually say. If the sources disagree (for
>   example different prices or different years), say so rather than picking one silently.

Grounding isn't only the prompt — it's enforced structurally too: the context is *only*
the top-k retrieved chunks (the model never sees the full corpus or the open web); a
`max_distance` cutoff drops weak matches; and **if retrieval returns nothing, the system
abstains without calling the LLM at all**. `temperature=0` keeps it from improvising.
Tested end-to-end: an out-of-corpus question ("CRC gym hours") returns the exact abstain
string, and the meal-plan-cost question correctly reports that the retrieved sources don't
give a full price rather than inventing one from training knowledge.

**How source attribution is surfaced in the response:** programmatically, not on the
model's good behaviour. After generation, `ask()` parses the `[S#]` labels the model cited,
maps them back to those chunks' metadata (title, source, URL) from `sources.json`, and
de-duplicates by document — falling back to all retrieved sources if the model cited none,
and to none if it abstained. Both interfaces render this as a "Retrieved from" list under
the answer.

**Query interface:** two front-ends over the same `ask()` function —
- Web UI: `python app.py` → open `http://localhost:7860` (Gradio; question box + Ask
  button, answer and "Retrieved from" panels, example questions).
- CLI: `python ask.py "is the meal plan worth it?"` (one-shot) or `python ask.py`
  (interactive REPL — the embedding model loads once and stays warm).

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
