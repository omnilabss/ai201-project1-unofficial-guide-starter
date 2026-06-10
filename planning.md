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

**Chunk size:** ~700 characters (≈175 tokens), hard-capped at 900 (≈225 tokens).

**Overlap:** ~100 characters (≈25 tokens), carried as whole trailing lines/sentences — not a blind mid-word character slice.

**Method:** Greedy line-then-sentence packing. The extracted text comes out
line-delimited (one line per original block element — a paragraph, a heading, a
list item), *not* separated by blank lines, so I pack consecutive lines into a
chunk until the next line would push it past the target, then start a new chunk.
If a single line is already longer than the cap (rare — a few of the meal-plan
guide's paragraphs), I fall back to splitting that line on sentence boundaries
(`. `). Overlap is the last line(s)/sentence(s) of the previous chunk, re-prepended.

**Reasoning:** The real constraint is the embedding model, not taste. `all-MiniLM-L6-v2`
truncates input at 256 tokens and silently drops everything past it, so a chunk
*must* stay under that or its tail never gets embedded — and the tail is exactly
where a price or a caveat tends to sit. At ~4 chars/token, 900 chars is ~225
tokens, and I keep margin because the dense stuff in this corpus (`$2,977`, `CULC`,
`Willage`) tokenizes to more than four characters apiece.

Within that ceiling, 700 fits the *shape* of these documents. I measured them: the
Technique opinion columns are ~150-character sentence-lines, while the Infatuation,
Rambler, and GTAE-wiki docs are lists where one entry is a short name line plus a
~300-character blurb. A 700-char chunk holds one full restaurant entry (sometimes
two adjacent ones), or a claim plus its supporting sentences from an opinion piece
— which is the unit a person is actually asking about. Packing whole *lines* rather
than cutting at a fixed offset is what keeps an entry's name attached to its blurb.

I avoided the two failure extremes deliberately. Too large (say one 2,000-char
chunk per section): it loses its tail to truncation, and its single vector is the
average of several unrelated restaurants, so it matches every food query weakly and
the LLM gets a wall of mostly-irrelevant text. Too small (say 200 chars): it splits
"`$2,977`" away from "Everyday Unlimited," or a restaurant's name away from why it's
good, so a retrieved chunk names a thing without the fact about it. I'll know I got
it wrong if top-k starts returning one giant chunk spanning four restaurants (too
large) or chunks like "Kaldi's is on the second floor" with no idea what Kaldi's is
(too small).

**Preprocessing before chunking:** normalize whitespace and unicode (smart quotes
and em-dashes → ASCII); drop the masthead/byline lines the extractor kept on the
Technique pages (author, date, "Opinions"); strip the housing/dorms boilerplate that
leads the Niche page (doc 13) before its food section. The thin official page (doc 14)
stays as-is — it's a useful "official line" counterpoint. Every chunk carries its
source metadata (`doc id`, `title`, `url`, `retrieved_via`) pulled from
`sources.json`, which is what makes citation possible downstream.

**Estimated chunk count:** ~110–140 chunks across the 14 documents (76,840 chars at
~600 net chars/chunk after overlap). Exact count reported in the README after M3.

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via `sentence-transformers` — 384-dimensional,
runs locally on CPU, free, no API key or rate limit. Its 256-token input cap is the
constraint that drove the chunk size above. I'll embed the query with the same model
and use cosine distance.

**Top-k:** 5. At ~700 chars/chunk that's ~3,500 characters (~900 tokens) of context —
plenty for `llama-3.3-70b`, and enough to cover the questions whose answers are spread
across documents (the late-night question pulls from ~3 sources; the dining-halls
question appears in 3). k=2 would starve those multi-source questions. k=12 would drag
in off-topic chunks — a Midtown restaurant two miles away when someone asked about
*on-campus* food, or the Niche housing boilerplate — and tempt the model to merge
contradictory figures. On top of top-k I'll apply a cosine-distance threshold and drop
chunks past it, so a question with no real answer in the corpus returns few or zero
chunks instead of five weak ones (that feeds the "abstain when ungrounded" behavior in
generation).

Semantic search is the point here: it matches on meaning, not keywords, so "where can
I grab coffee" lands on "Kaldi's Coffee, on the second floor of the CULC" even though
they share no words. The flip side — and a real risk for this corpus — is that it also
matches on vibe, so "good food" happily returns every positive restaurant blurb whether
or not it's on campus. The distance threshold and metadata are how I keep that in check.

**Production tradeoff reflection:** If cost weren't a constraint, the first thing I'd buy
isn't accuracy — it's **context length**. MiniLM's 256-token cap is what forced the
small-chunk design; a model with an 8k-token window (OpenAI `text-embedding-3-small`/
`-large`, Voyage, Cohere embed v3) would let me embed a whole short opinion column or a
whole restaurant section as one unit and drop most of the chunking gymnastics. Second,
**domain accuracy**: MiniLM is a tiny general-purpose model and fumbles GT-specific
jargon ("Willage," "NAV," "CULC") that a larger model trained on more web text would
place correctly — directly relevant to the nickname question. **Multilingual** support I
wouldn't pay for: this corpus is English, so it's wasted capacity unless international
-student threads enter later. On **local vs. API**: local MiniLM is instant, private,
free, and re-embeds the whole corpus in seconds, which is right for a small corpus that
updates rarely; an API embedder adds per-call latency, real cost, a network dependency,
and ships campus data off-box, so I'd only switch at a scale or quality bar this project
doesn't have. If I were actually shipping this, I'd A/B MiniLM against
`text-embedding-3-small` on these five questions first — it's cheap, 1536-dim, 8k
context, and probably the sweet spot before reaching for a large model.

---

## Evaluation Plan

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

1. **Stale and conflicting facts across a 2012–2026 corpus.** The documents span
   fourteen years — the 2012 late-night piece, the 2017 "rebrands" critique, the 2023
   meal-swipe rules, the 2026 official page. Hours, prices, and vendors all changed in
   that window, so "how much is the meal plan" has `$2,977`/semester, `$4,840`/year, and
   older numbers all sitting in the corpus at once (this is the eval question I expect to
   come back partially accurate). The danger is the model averaging them into one wrong
   figure, or quoting 2012 hours as if they're current. Mitigation: keep source title and
   date in each chunk's metadata, and write the system prompt to attribute and flag
   disagreement/recency rather than silently reconcile.

2. **Silent truncation at the embedding step.** If cleaning or chunking lets a chunk
   drift past ~256 tokens, MiniLM cuts the tail off before embedding — and the tail is
   often where the actual answer lives (a price, an exception, "…but it doesn't take meal
   swipes"). It fails quietly: no error, just a chunk whose vector doesn't represent its
   own ending. Mitigation: the 900-char hard cap, plus a token-length assertion in the
   chunker that logs or skips anything over the limit.

3. **Off-topic retrieval from "restaurant-shaped" noise.** The Infatuation and Rambler
   docs are full of Midtown/West Midtown spots a mile or two off campus, and the Niche
   page carries housing/dorm content. Semantic search will cheerfully return a great-but-
   far restaurant for "where can I eat on campus," or a dorm-quality line for a food
   query. Mitigation: strip the Niche housing block during ingestion, lean on the
   distance threshold, and tag chunks on-campus vs. nearby in metadata if it proves
   necessary.

4. **Jargon and nicknames the embedder doesn't know.** "Willage" shows up exactly once,
   glossed in doc 1; "NAV" and "CULC" are used as if everyone knows them. If the single
   chunk that defines the term isn't in the top-k, the system can't connect "Willage" →
   West Village, and a small general-purpose embedder may not place the slang near its
   referent in the first place. This is the failure case I most expect to have to write up.

---

## Architecture

```
Ingestion  →  Chunking  →  Embed + Store  →  Retrieval  →  Generation
(requests +   (~700 char    (all-MiniLM-     (top-k=5,     (Groq
 html.parser,  chunks,       L6-v2  →         ChromaDB      llama-3.3-70b,
 Wayback)      100 overlap)  ChromaDB)        search)       cited answer)
```

User question → embed (same model) → retrieve top-5 chunks → feed as context to the LLM → grounded answer + sources.

---

## AI Tool Plan

I'm working with **Claude (Claude Code in the terminal)**. The pattern is the same at
every stage: hand it the relevant section of this file as the spec, let it generate the
module, then verify against a concrete check before moving on. The spec is the contract;
the five eval questions are the acceptance test. The ingestion script (M1) was already
built this way.

**Milestone 3 — Ingestion and chunking:**
- *Give it:* the Documents section, the `sources.json` schema, the two cleaning notes
  (strip Niche housing boilerplate, leave the thin official doc), and the full Chunking
  Strategy section (700/100, 900-char cap, line→sentence packing).
- *Expect:* `ingest.py` that loads `documents/*.txt`, normalizes whitespace/unicode and
  strips the masthead/byline + Niche housing lines, plus a `chunk_text()` doing the greedy
  line/sentence packing with overlap, each chunk carrying its source metadata.
- *Verify:* print a chunk-length histogram and assert nothing exceeds 256 tokens; grep the
  chunks to confirm the "Willage" sentence and a full Infatuation restaurant entry each
  land intact inside one chunk (no boundary splits).

**Milestone 4 — Embedding and retrieval:**
- *Give it:* the Retrieval Approach section.
- *Expect:* `index.py` that embeds chunks with `all-MiniLM-L6-v2` and persists them to a
  ChromaDB collection with metadata, and `search(query, k=5)` returning chunks + metadata
  + distances with the distance threshold applied.
- *Verify:* run the five eval questions through retrieval only (no LLM yet) and check each
  returns its expected source doc(s) in the top-5 — if Q5 doesn't pull docs 5/8/9, that's a
  retrieval bug to fix before it ever reaches generation.

**Milestone 5 — Generation and interface:**
- *Give it:* the grounding requirement plus a system prompt I'll draft that restricts the
  model to the retrieved context and requires inline source citations.
- *Expect:* `answer.py` calling Groq `llama-3.3-70b-versatile` with the retrieved chunks as
  context, returning an answer + a Sources list, and a small CLI (`python ask.py "question"`).
- *Verify:* ask an out-of-corpus question ("what are the gym hours?") and confirm it abstains
  instead of inventing an answer; on a real question, confirm every factual claim traces back
  to a cited chunk.
