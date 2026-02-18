# X-like Multi-Action Scoring Proxy (Based on xai-org/x-algorithm README)

## What the open-source README tells us
X’s "For You" feed ranking is described as:
- Predict probabilities for multiple engagement actions (reply, repost, quote, click, dwell, etc.)
- Combine them as a weighted sum
- Apply filtering before and after scoring

We don’t have the production weights or model, so we implement a proxy.

## Proxy Goals
- Optimize for conversation and shareability (replies, reposts, quotes)
- Maintain credibility and avoid negative outcomes (not interested / report vibe)
- Avoid spam and templated replies

## Engagement Actions We Approximate
We model these as heuristic components:

Positive intent:
- Reply-likelihood: Does it invite a response naturally?
- Repost/quote-likelihood: Would someone share it because it’s crisp or insightful?
- Click/profile-likelihood: Does it create curiosity without bait?
- Dwell: Is it interesting enough to pause and read?

Negative risk:
- Not-interested vibe: generic/irrelevant/low-value
- Report vibe: hostility, harassment, misinformation tone
- Block/mute vibe: overly aggressive, spammy, repetitive

## Scoring Components (0–10 each)
- relevance: directly addresses the tweet’s point
- hook: strong first sentence
- clarity: readable, tweet-length, clean structure
- novelty: not generic, not template
- conversation_invite: good question or prompt
- credibility: no invented claims
- persona_fit: CEO vs Engineer voice match
- shareability: quotable / concise / insightful
- safety: avoids risky language and advice

## Penalties (0–30 each)
- promo: forced Pepetopia mention / “bio” / selling
- repetition: same cadence across candidates
- hallucination_risk: numbers/claims without support
- finance_advice: price talk, buy/sell instructions
- hostility: rage-bait / insulting tone

## Total Score (0–100)
score_total = base_score - penalties
Where base_score is a weighted sum of the 0–10 components.

## Candidate Diversity Enforcement
Generate 5–8 candidates with:
- distinct angles (question-first, contrarian, mini-tutorial, witty, supportive)
- distinct structure (one-liner vs two-liner vs micro-bullets)
- distinct hooks

## Output JSON Contract (internal)
The LLM must return STRICT JSON (no extra text):
- analysis: {topic, intent, tone, audience_hint}
- candidates: [{id, angle, reply_text_en, score_total, score_breakdown, penalties, rationale_en, risk_flags}]
- recommended_id
