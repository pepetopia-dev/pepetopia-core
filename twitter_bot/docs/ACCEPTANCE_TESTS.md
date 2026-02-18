# Acceptance Tests — Pepetopia Reply Draft Bot

## Setup
- Telegram bot token configured.
- Gemini API key configured.
- Run `python main.py` and send test messages.

---

## A. Language
### A1 — English output
Input: any tweet pasted.
Expected: All bot output is English.

---

## B. Persona Switching
### B1 — Engineer persona
Input: message contains `@pepetopia_dev` and a technical tweet.
Expected:
- More technical tone, mentions tradeoffs, implementation thinking.
- No fluff marketing.

### B2 — CEO persona default
Input: message does NOT contain `@pepetopia_dev`.
Expected:
- Visionary, grounded framing, invites discussion.

---

## C. Diversity & Non-Repetition
### C1 — Candidate diversity
Expected:
- 5–8 candidates.
- No near-duplicates.
- At least 4 distinct angles visible.

### C2 — Re-run variability
Expected:
- Not identical results on repeat runs (while staying relevant).

---

## D. Anti-Promo & Safety
### D1 — No autopromo
Input: a random tech/crypto tweet not about Pepetopia.
Expected: no Pepetopia mention, no “bio”, no call-to-buy.

### D2 — Pepetopia allowed only when relevant
Input: tweet asks “What is PepeTopia / TOPI / forum?”
Expected:
- Factual explanation, no hype.
- No price predictions.

### D3 — No financial advice
Input: “Price target? When moon?”
Expected: refuses predictions, redirects to fundamentals.

---

## E. Scoring Output
### E1 — Scores present
Expected per candidate:
- score_total (0–100)
- 1-line rationale
- risk flags (optional)

### E2 — Ranking makes sense
Expected:
- Top candidates are most relevant, most conversation-inviting, most credible.

---

## F. Telegram Rendering Stability
Expected:
- No Markdown entity errors.
- Clean formatting (prefer HTML).

---

## G. Model Selection
Expected:
- Uses newest available Gemini model via discovery.
- If discovery fails, uses a safe fallback and logs it (without secrets).

---

## H. Scope Constraints
Expected:
- No operations outside `twitter_bot/`.
- `main.py` stays in place.
- Existing file names are not changed.
