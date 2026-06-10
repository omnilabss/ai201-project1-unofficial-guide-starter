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

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**

**Overlap:**

**Why these choices fit your documents:**

**Final chunk count:**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

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
