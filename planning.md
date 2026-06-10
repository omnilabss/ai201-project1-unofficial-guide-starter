# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

**Campus dining at the Georgia Institute of Technology.** The corpus covers the
three dining halls (Brittain, North Avenue, West Village — nicknamed "Willage"),
meal plans and meal-swipe rules, on-campus eateries and coffee shops, late-night
options, Tech Square, and nearby Midtown / West Midtown restaurants.

The *useful* version of this knowledge — which dining hall is actually worth it,
whether the meal plan pays off, where to eat at 2 a.m., what the menu says vs.
what's really served — lives in the student newspaper, fan blogs, a student-run
wiki, and review threads, not on the official dining website (which mostly lists
hours and markets an "all-you-can-eat experience"). It is scattered across many
pages, opinion-heavy, and goes stale as vendors and hours change every year, so
no single official source answers a plain-language question like the ones below.

---

## Documents

> Collected by `scripts/collect_documents.py`: it downloads each page's raw HTML
> (saved under `documents/raw/` for provenance) and extracts the article text to
> `documents/*.txt`, with metadata in `documents/sources.json`. **14 documents**
> collected. Notes: **Reddit blocks automated fetching** (HTTP 403), so the corpus
> leans on other authentic student voices instead; pages that are now JavaScript-only
> shells or bot-blocked (the Technique's new SPA, Niche, The Infatuation) were
> recovered from the **Internet Archive Wayback Machine** (`retrieved_via` in the
> manifest records which).

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | The Technique (GT student paper) | Beginner's guide to on-campus dining: 3 halls, Tech Green, CULC/Kaldi's, John Lewis Student Center vendors, Whistle Bistro | nique.net/life/2023/08/25/a-full-layout-of-on-campus-dining-at-tech/ (Wayback) → `documents/01-…txt` |
| 2 | The Technique (GT student paper) | Inside look at the dining halls & services; how Tech Dining is run | nique.net/life/2014/02/06/an-inside-look-at-techs-dining-halls-and-services/ (Wayback) → `02` |
| 3 | The Technique (opinion) | "Tech Dining rebrands, but does not improve" — student critique of quality/pricing | nique.net/opinions/2017/10/20/tech-dining-rebrands-but-does-not-improve/ (Wayback) → `03` |
| 4 | The Technique (opinion) | "Meal swipes in Tech Dining" — how swipes/declining-balance work and complaints | nique.net/opinions/2023/02/19/meal-swipes-in-tech-dining/ (Wayback) → `04` |
| 5 | The Technique (opinion) | "Late night dining" — what's open late and what isn't | nique.net/opinions/2012/03/02/late-night-dining/ (Wayback) → `05` |
| 6 | The Technique (news) | "Institute extends on-campus dining hours" — hours/policy change | nique.net/news/2021/10/29/institute-extends-on-campus-dining-hours/ (Wayback) → `06` |
| 7 | From The Rumble Seat (GT fan blog, SB Nation) | Opinionated "power rankings" of Tech dining experiences | fromtherumbleseat.com/2019/9/20/…tech-dining-experiences… → `07` |
| 8 | GTAE Aero Maker Space Wiki (student-run) | Student "Food Around Campus" wiki: halls, Student Center eateries, coffee, late-night, nearby | gtae.gitbook.io/ams/miscellaneous/food-around-campus → `08` |
| 9 | The Infatuation | "Where To Eat Near Georgia Tech" — curated nearby restaurants w/ descriptions & ratings | theinfatuation.com/atlanta/guides/where-to-eat-near-georgia-tech (Wayback) → `09` |
| 10 | Rambler Atlanta (local blog) | Top restaurants near campus in Midtown | rambleratlanta.com/resources/top-restaurants-near-campus/ → `10` |
| 11 | Rambler Atlanta (local blog) | Ultimate guide to GT meal plans (plan types & cost) | rambleratlanta.com/resources/guide-gt-meal-plans/ → `11` |
| 12 | PRKED (student-services blog) | GT meal plans: the ultimate student guide (plan comparison) | prked.com/post/georgia-tech-meal-plans-the-ultimate-student-guide → `12` |
| 13 | Niche | Real student opinions + polls + meal-plan cost / "Campus Food" grade | niche.com/colleges/georgia-institute-of-technology/campus-life/ (Wayback) → `13` |
| 14 | Georgia Tech Dining (official) | Official dining-halls page (the "official" counterpoint to student takes) | dining.gatech.edu/dining-locations/dining-halls → `14` |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What are Georgia Tech's three official dining halls, and which campus side is each on? | **Brittain** and **North Avenue** on East Campus; **West Village** on West Campus (nicknamed "Willage"). All are all-you-can-eat. (docs 1, 8, 14) |
| 2 | What do students call the West Village dining hall? | "**Willage**." (doc 1 — single, colloquial mention; a deliberate hard case for retrieval) |
| 3 | Where can I get coffee on campus near the CULC? | **Kaldi's Coffee**, on the 2nd floor of the Clough Undergraduate Learning Commons (CULC). Other on-campus coffee: Gold & Bold, Sideways Cafe. (docs 1, 8) |
| 4 | Roughly how much does a Georgia Tech meal plan cost? | First-year plans run **~$2,977/semester** (Everyday Unlimited / Flex, per the guides); Niche lists an **average ~$4,840/year**. (docs 11, 12, 13 — numbers are stated on different bases, so a good answer should note per-semester vs. per-year; a deliberate partial-accuracy trap) |
| 5 | What are some late-night food options on or near campus? | On/near campus: **The Missing T** (burgers/wings); at West Village, **WingZone** and **Starbucks** stay open latest (and don't take swipes); in Tech Square, **Waffle House** (24h) and **Insomnia Cookies**; **Sublime Doughnuts** (24/7) in West Midtown. (docs 5, 8, 9 — answer is scattered across sources, a deliberate multi-hop retrieval challenge) |

> Difficulty by design: Q2 tests a single OOV-ish nickname, Q4 has conflicting
> numeric bases across sources, and Q5 requires stitching facts from 3 documents —
> these are the questions most likely to expose retrieval or grounding failures.

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
