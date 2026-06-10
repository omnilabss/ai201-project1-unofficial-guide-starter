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

## Sample Chunks

Five representative chunks from `chunks.json`, each labeled with its chunk id and source
document. Each is a complete, retrievable thought on its own.

**[03-2] — source: doc 03, "Tech Dining rebrands, but does not improve" (The Technique)**
> Currently, Dining operates exactly two full service dining halls on campus, both located
> on East. At either of these locations, students with meal plans can get unlimited food for
> a single meal swipe. Unfortunately, no full-service dining hall exists on West Campus. …
> West used to have a dining hall, Woodruff, until it was closed in favor of a 'dining
> commons' … West Village provides students with exactly $9 per meal swipe.

**[08-1] — source: doc 08, "Food Around Campus" (GTAE student wiki)**
> North Avenue & West Village Dining Halls. NAV and West Village serve a wide selection of
> food. Both halls feature pizza, hot food stations, and a salad bar. … To check West Village
> "Willage"'s dining hall hours, click … These websites also feature the rotating menus of
> the two biggest dining areas on campus.

**[09-3] — source: doc 09, "Where To Eat Near Georgia Tech" (The Infatuation)**
> Hankook Taqueria / Mexican / West Midtown / $$$$ … During lunchtime hours, you'll have to
> be quick on your feet to scoop up a table … their delicious Mexican-Korean mash-up is one
> of the most inventive taco plays in the city. The crispy shrimp option … 7.7

**[12-3] — source: doc 12, "GT Meal Plans: The Ultimate Student Guide" (PRKED)**
> Dining Dollars: This is like a prepaid debit card specifically for food on campus. … you
> don't pay sales tax on purchases made with Dining Dollars … if you buy them in bulk … you
> can get a 10% bonus … BuzzCard Funds: … works at over 200 places on & off campus …

**[13-0] — source: doc 13, "Campus Life — Real Student Opinions" (Niche)**
> Food / Campus Food / C+ … Average Meal Plan Cost / $4,840/ year … What are the best food
> options on campus? … Chik-fil-a 20% / Student center food court 14% / Subway 10% / Food
> trucks 10% / Panda express 9% / Tin Drum 8% / Wing Zone 7% …

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

## Retrieval Test Results

Three queries with their top retrieved chunks (cosine distance, source doc, snippet), from
the retrieval-only smoke test in `src/index.py` (`smoke_test()`).

**Query: "What do students call the West Village dining hall?"**
```
0.286  doc 8  Food Around Campus        | NAV and West Village … West Village "Willage"'s dining hall hours …
0.327  doc 3  Tech Dining rebrands      | Woodruff Dining Hall was also open until 2 a.m. … at West Village …
0.358  doc 6  Institute extends hours   | The front desk at the West Village dining hall on the west side …
```
*Why relevant:* the #1 chunk (distance 0.286) is the only place in the corpus that pairs the
official name with the nickname — "West Village 'Willage'" — so it's exactly what's needed to
answer a nickname question. The others are genuinely about West Village too, just without the
nickname.

**Query: "Where can I get coffee on campus near the CULC?"**
```
0.286  doc 1  A full layout of on-campus dining | … the CULC … has a coffee shop and cafe, Kaldi's Coffee, on the 2nd floor …
0.399  doc 7  Power Rankings            | Whatever the [Foghat] Ferst Place is … (off-topic)
0.454  doc 10 Top Restaurants Near GT   | 3. Taco Mac … 10 minute walk (off-topic)
```
*Why relevant:* the #1 chunk (0.286) names Kaldi's Coffee and locates it on the 2nd floor of the
CULC — a direct answer, matched on meaning even though the query never says "Kaldi's." This query
also shows the corpus's weakness: ranks 2–4 drift into "restaurant-shaped" noise (a fan-blog riff,
Taco Mac) at distances 0.4+, which is why the top result matters and why I keep a distance cutoff.

**Query: "What are some late-night food options on or near campus?"**
```
0.246  doc 5  Late night dining         | Students ultimately need food options late at night …
0.324  doc 8  Food Around Campus        | … late-night options like The Missing T for burgers and wings …
0.357  doc 4  Meal swipes in Tech Dining| … only places that take meal swipes are Brittain, North Avenue, West Village …
```
(On-topic, but note the top two are a 2012 column and the wiki — see the Evaluation Report for how
the 2012 content skews the generated answer.)

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

---

## Example Responses

Real system outputs (answer text plus the "Retrieved from" attribution the system appends).

**Example 1 — in-scope, with source attribution**
> **Q:** What do students call the West Village dining hall?
> **Answer:** Students refer to the West Village dining hall as "Willage" [S1].
> **Retrieved from:** • Food Around Campus (GTAE Aero Maker Space Wiki) — https://gtae.gitbook.io/ams/miscellaneous/food-around-campus

**Example 2 — in-scope, with source attribution**
> **Q:** Where can I get coffee on campus near the CULC?
> **Answer:** You can get coffee on campus near the CULC at Kaldi's Coffee, located on the
> second floor of the CULC [S1], or at the Starbucks in the CULC [S2].
> **Retrieved from:** • A full layout of on-campus dining at Tech (The Technique) —
> nique.net/life/2023/08/25/… • Bye Week Power Rankings: Tech Dining Experiences (From The Rumble Seat)

**Out-of-scope — refusal**
> **Q:** What are the opening hours of the campus gym (CRC)?
> **Answer:** I don't have enough information on that.
> **Retrieved from:** *(none)*

---

## Query Interface

Two front-ends over the same `ask()` function.

**Input field:** one text box, "Your question."
**Output fields:** "Answer" — the grounded response with inline `[S#]` citations — and
"Retrieved from" — the cited source documents with their URLs.

- **Web UI:** `python app.py` → open `http://localhost:7860` (Gradio: question box + Ask
  button, an Answer panel, a "Retrieved from" panel, and clickable example questions).
- **CLI:** `python ask.py "is the meal plan worth it?"` (one-shot) or `python ask.py`
  (interactive REPL — the embedding model loads once and stays warm for follow-ups).

**Sample interaction transcript (CLI):**
```
$ python ask.py
> What do students call the West Village dining hall?

Answer:
Students refer to the West Village dining hall as "Willage" [S1].

Retrieved from:
  • Food Around Campus (GTAE Aero Maker Space Wiki (student-run))
    https://gtae.gitbook.io/ams/miscellaneous/food-around-campus
------------------------------------------------------------------------
```

---

## Evaluation Report

Run all five with `python src/evaluate.py`. Results below are verbatim summaries
of that run (retrieved docs and cosine distances included).

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | The 3 dining halls + which campus side? | Brittain & North Ave on **East**; West Village ("Willage") on **West**; all-you-can-eat | Named Brittain/North Ave/West Village (from doc 14 + doc 12) but said it "does not specify the side of campus" — **missed the East/West split** | Partially relevant (got halls, not the campus-side chunk) | **Partially accurate** |
| 2 | What do students call West Village? | "Willage" | "Students refer to the West Village dining hall as 'Willage' [S1]." | Relevant (doc 8 @ 0.286) | **Accurate** |
| 3 | Coffee on campus near the CULC? | Kaldi's Coffee, 2nd floor of CULC | "Kaldi's Coffee, on the second floor of the CULC [S1]" (+ an added "Starbucks in the CULC [S2]" — slightly off; it's in the Barnes & Noble) | Relevant (doc 1 @ 0.286) | **Accurate** (minor stray detail) |
| 4 | Roughly how much does a meal plan cost? | ~$2,977/sem (guides); ~$4,840/yr (Niche) | Gave only Dining-Dollars ranges ($50–$660) and concluded the total cost "is not clearly stated" — **never surfaced $2,977 or $4,840** | Off-target for the price (price chunks not retrieved) | **Inaccurate** (failure case below) |
| 5 | Late-night food options? | The Missing T; WingZone & Starbucks at West Village; Waffle House (24h), Insomnia; Sublime (24/7) | Grounded in the **2012** "Late night dining" piece (NADH late-night being cut, Quizno's/Wingnuts gone, Waffle House "not close enough") — missed the current options | Partially relevant (pulled doc 5 ×3 + doc 8, but leaned on the stale doc) | **Partially accurate** |

**Scorecard:** 2 accurate (Q2, Q3), 2 partially accurate (Q1, Q5), 1 inaccurate (Q4).

Two patterns explain the misses, both predicted in `planning.md`:
- **Specific sub-facts can be missed even when an "expected" document is retrieved.** Q1 retrieved doc 14/8 (which list the halls) but *not* doc 1, the only chunk that says "two on East — Brittain and North Avenue — and one on West." Hitting the right document ≠ hitting the right sentence.
- **Staleness.** Q5's top matches are from a 2012 column, so the model answered about 2012 late-night policy. The corpus spans 2012–2026 and the embedder has no notion of "most recent."

---

## Failure Case Analysis

**Question that failed:** "Roughly how much does a Georgia Tech meal plan cost?"

**What the system returned:** Only the Dining-Dollars *add-on* ranges ("$50 to $660 … $50,
$100, $200, $400, or $600") and the conclusion that the total cost "is not clearly stated."
It never surfaced the actual figures — ~$2,977/semester (the guides) or ~$4,840/year (Niche).

**Root cause (tied to a specific pipeline stage): retrieval / embedding, abetted by chunking.**
The price figures *are* in the corpus — `src/evaluate.py`'s diagnostic shows them in chunks
`11-11`, `11-18`, `11-19`, `12-5…12-8`, and `13-0`. But for this query **not one of them appears
even in the top-12** retrieved chunks (all top results are `price=no`). The reason is an
embedding mismatch: a natural-language question ("how much does a meal plan cost?") embeds
closest to *prose* — the meal-plan **explanation** chunks ("which meal plan is right for me",
the Dining-Dollars description) — while the chunks that actually hold the dollar amounts are
number-dense **tables** (plan-comparison rows, "Average Meal Plan Cost / $4,840/ year" sitting
in a list of poll percentages in the Niche chunk). Those table chunks are dominated by digits
and short tokens, so their embeddings land far from a conversational price question. Increasing
`k` wouldn't rescue it — the price chunks aren't even in the top 12. The generation step then
did the *right* thing given bad retrieval: it refused to invent a number and said the cost
wasn't stated. So this is a retrieval failure surfacing as an incomplete answer, not a
hallucination.

**What you would change to fix it:** (1) **Hybrid retrieval** — add a keyword/BM25 pass for
queries containing "cost/price/$" and union it with the semantic results, so a literal `$2,977`
chunk is retrievable; (2) **chunk tabular content with a natural-language header** — prepend a
sentence like "Georgia Tech meal plan prices:" to the price tables so their embedding carries
the concept "price," not just digits; (3) **query expansion** — embed the question alongside a
paraphrase ("meal plan price per semester in dollars") to pull the question vector toward the
numeric chunks.

---

## Spec Reflection

**One way the spec helped you during implementation:** Writing the Chunking Strategy in
`planning.md` *around the embedding model's 256-token limit* (rather than picking a round
number) is what made me verify token counts after building — and that verification caught two
bugs I'd otherwise have shipped: a chunk inflated to 1,205 chars by overlap (over the cap), and
a token check that was silently passing because the `tokenizers` library truncates at 128 by
default. The spec turned "chunk size" from a guess into a constraint I had to test against, so
the failure was visible at the chunking stage instead of as mysterious bad retrieval later.
The same "test retrieval before generation" plan surfaced the Q1 and Q4 gaps at the retrieval
layer, where they were cheap to diagnose.

**One way your implementation diverged from the spec, and why:** The plan said retrieval would
use a cosine-distance **threshold to drop weak chunks** as the main way to abstain on
out-of-scope questions. In practice I set that cutoff loose (0.7) and let the **grounding
prompt** do the abstaining ("reply exactly 'I don't have enough information on that.'"). On a
corpus this small, a strict distance threshold either dropped valid borderline matches or let
junk through depending on the query, whereas the prompt-level rule abstains reliably (verified
on the out-of-corpus gym-hours question). I also ended with **157 chunks vs. the ~110–140 I
estimated**, because the list-style guides produce more, smaller entries than I expected, and I
added a bidirectional small-chunk merge and per-source cleaning (Wayback recovery, slicing the
Niche page) that the original spec didn't anticipate — the real documents forced those.

---

## AI Usage

**Instance 1 — implementing the chunker from the spec**

- *What I gave the AI:* my `planning.md` Chunking Strategy section (≈700-char target, ~100
  overlap, 900-char/256-token cap, line-then-sentence packing) and a sample of the cleaned docs.
- *What it produced:* a `chunk_text()` doing greedy line/sentence packing, plus a token-count
  check using the `tokenizers` library.
- *What I changed or overrode:* inspection showed a 1,205-char chunk — the overlap prepend was
  pushing chunks past the cap — and the token check was a false pass because `tokenizers`
  truncates at 128 by default (so nothing could ever "exceed 256"). I directed three fixes:
  bound the overlap so a chunk can't exceed `hard_max`, merge sub-150-char fragments into a
  neighbour (so a restaurant's name stays with its blurb), and call `no_truncation()` so the
  assertion measures the real token length (true max came out to 224).

**Instance 2 — collecting real sources**

- *What I gave the AI:* the domain (GT campus dining) and the instruction to fetch *real* public
  documents and extract clean text into `documents/`.
- *What it produced:* a collector that first tried `trafilatura`, then (when that wouldn't
  install in this environment) a stdlib-only HTML extractor.
- *What I changed or overrode:* when `nique.net` turned out to be a JavaScript single-page app
  serving empty shells (and Reddit blocked automated fetching with HTTP 403), I had it add an
  **Internet Archive Wayback Machine fallback** to recover the six Technique articles, keep
  per-source cleaning rules (e.g., slicing the Niche page down to just its Food block, stripping
  the repeated "sapphire card" ad in the Infatuation guide), and **gitignore the bulky raw HTML**
  while committing only the cleaned `.txt` + a `sources.json` manifest for citation.
