---
name: deep-research
description: Use when the user wants a deep, multi-source, fact-checked research report on any topic (triggers like "딥 리서치", "deep research", "웹조사해서 정리", "리서치 보고서"). Runs a structured pipeline — decompose into search angles, search, extract falsifiable claims from sources, adversarially verify, synthesize a cited report. For a quick single-fact lookup, just search directly instead.
---

# Deep Research

## Overview

Produce a fact-checked, citation-backed research report through a fixed pipeline:
Scope → Search → Fetch/Extract → Verify → Synthesize. Every finding in the final
report must trace back to a fetched source and survive a skeptical verification pass.

Respond in the user's language (Korean by default). Keep source titles/quotes in
their original language.

## Step 0 — Scope check (before any search)

If the question is underspecified (e.g. "what car to buy" without budget/use-case/region),
ask 2-3 clarifying questions first. Otherwise restate the research question in one
sentence and proceed.

## Step 1 — Decompose into search angles

Break the question into 5 complementary search angles. Pick angles that suit the domain,
for example:

- broad/primary · academic/technical · recent news · contrarian/skeptical · practitioner/implementation
- tech: state-of-art · benchmarks · limitations · industry adoption · cost/tradeoffs
- medical: anatomy · common causes · serious differentials · authoritative refs · red flags

Write one specific search query per angle. Avoid redundant angles.

## Step 2 — Search

Run a web search for each angle (refine the query if the first attempt is low-signal).
Keep the top 4-6 results per angle. Skip obvious SEO spam and content farms.
Rank by relevance to the ORIGINAL question, not just the query.

Dedup URLs across angles (normalize: drop scheme/www/trailing slash). Cap the fetch
list at ~15 sources, preferring high-relevance and primary sources.

## Step 3 — Fetch and extract claims

For each selected source, fetch the page content. For each source record:

- **sourceQuality**: primary (official docs / research / institution) · secondary (reporting) · blog · forum · unreliable
- **publishDate** if available
- **2-5 falsifiable claims** that bear on the question. Each claim must:
  - be a concrete, checkable statement (not a vague generality)
  - include a short direct quote from the source as support
  - be rated central / supporting / tangential

If a fetch fails or the page is irrelevant/paywalled, mark the source unreliable and move on.

## Step 4 — Adversarial verification

Rank claims by importance (central first) then source quality. Verify the top ~15
claims. For each, actively try to REFUTE it:

1. Does the quote actually support the claim, or is it an overreach/misread?
2. Search for contradicting evidence — does any credible source dispute or heavily qualify it?
3. Is the source quality sufficient for the claim's strength? (extraordinary claims need primary sources)
4. Is it outdated? (check dates — old claims in fast-moving fields are suspect)
5. Is it marketing copy / press release / cherry-picked benchmark / forum speculation?

Verdict per claim: **confirmed** / **refuted** / **unverified** (could not check).
Default to refuted when uncertain. For load-bearing claims, prefer verifying against
the primary source directly (official docs over blog posts citing them).

## Step 5 — Synthesize the report

1. Merge claims that say the same thing; combine their sources.
2. Group related claims into findings that directly answer the question.
3. Assign confidence per finding:
   - **high** — multiple primary sources, no credible dispute
   - **medium** — secondary sources, or minor disputes/qualifications
   - **low** — single source or blog-quality only
4. Report structure:
   - 3-5 sentence executive summary answering the question
   - Findings grouped by theme, each with confidence + inline source links
   - Refuted claims (for transparency, brief)
   - Caveats: what is uncertain, weak sources, time-sensitivity
   - 2-4 open questions that emerged but were not answered

## Hard rules

- Never present an unverified or refuted claim as a finding.
- Every finding cites at least one fetched URL — no citations from memory.
- Distinguish "no evidence found" from "evidence against" — say which one it is.
- Do not write files unless the user explicitly asks to save the report.
