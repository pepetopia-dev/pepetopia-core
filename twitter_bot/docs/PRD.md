# Pepetopia Reply Draft Bot (Telegram) — PRD

## Goal
A Telegram bot that helps an operator craft high-engagement replies for Twitter/X by:
- Accepting a pasted tweet (plain text) via Telegram.
- Selecting the newest available Gemini model dynamically.
- Generating multiple diverse reply candidates in English.
- Scoring candidates using an X-like "multi-action" engagement proxy.
- Returning a ranked list so the operator can pick one and manually post on X.

## Non-Goals
- No automatic posting to X (manual copy/paste only).
- No scraping / no fetching tweet content from x.com/twitter.com.
- No Nitter / RSS / monitoring accounts.
- No spam, no repetition loops, no deceptive engagement bait.

## Operator Workflow
1. Operator pastes a tweet text into Telegram.
2. Optional persona trigger:
   - If message contains `@pepetopia_dev`, use Engineer persona.
   - Otherwise default to CEO persona.
3. Bot produces:
   - A short analysis (topic, intent, tone).
   - 5–8 reply candidates (distinct angles).
   - A score + 1-line rationale for each.
   - Risk flags (if any).

## Personas
### CEO Persona (default)
- Visionary, grounded, high-signal.
- Build-in-public energy: clarity, long-term thinking, curiosity.
- Avoid empty hype ("moon", "lambo", guarantees).
- Prefer crisp framing and questions that invite discussion.

### Engineer Persona (`@pepetopia_dev`)
- Engineering-first: AI, programming, systems thinking.
- Concrete tradeoffs, practical suggestions.
- Avoid jargon dumps; keep it readable and tweet-length.

## Output Language Requirements
- Telegram output MUST be English.
- Source code, identifiers, docstrings, and comments MUST be English.

## Anti-Spam & Anti-Promo Rules
- Do not repeat the same phrasing/cadence across candidates.
- Do not mention Pepetopia unless:
  - The tweet explicitly asks about Pepetopia/TOPI/the forum, OR
  - The operator explicitly requests a Pepetopia-related angle (future feature).
- Never include: "check our bio", "we built this", "buy now", "join now".
- Never give price predictions or financial advice.

## Candidate Diversity Requirements
Each candidate must differ in at least one of:
- angle (question-first / contrarian / mini-tutorial / witty / supportive / critical)
- structure (1-liner / 2-liner / micro-bullets / question-first)
- rhetorical device (hook / analogy / definition / challenge assumption)

## Scoring Approach (X-like Multi-Action Proxy)
X’s open description ranks content by predicting probabilities for multiple actions
(e.g., reply, repost, quote, click, dwell) and combining them with weights.
We cannot reproduce the real model/weights, so we approximate with heuristics:

Positive signals (boost):
- Relevance and specificity to the tweet
- Reply-likelihood (invites conversation)
- Repost/quote-likelihood (shareable, crisp, insightful)
- Dwell (interesting framing, non-generic)
- Credibility (no fabricated claims)
- Persona fit

Negative signals (penalty):
- Promo / forced Pepetopia mention
- Repetition / template spam
- Hallucination risk (numbers/claims without basis)
- Rage-bait / hostility / report-worthy tone
- Finance advice / price talk

## Acceptance Criteria
- Same input tweet returns 5–8 meaningful, diverse candidates.
- `@pepetopia_dev` produces more technical replies; default is visionary CEO tone.
- No autopromo unless the tweet is about Pepetopia.
- Each candidate includes: score (0–100), 1-line rationale, optional risk flags.
- Telegram output is stable (no Markdown parse failures).
- Bot selects newest Gemini model via discovery (with safe fallback).

## Repo & Scope Constraints
- Work ONLY inside `twitter_bot/`.
- Do NOT move `main.py`.
- Do NOT rename existing files. New files may be added.
