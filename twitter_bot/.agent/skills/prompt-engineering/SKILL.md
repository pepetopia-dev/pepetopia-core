---
name: prompt-engineering
description: Builds robust prompts for multi-candidate generation, diversity constraints, anti-promo rules, and strict JSON outputs.
---

# Prompt Engineering Skill

When generating replies:
- Always produce 5–8 candidates with distinct angles.
- Enforce anti-promo: do not mention Pepetopia unless tweet is about it.
- Enforce no finance advice and no price predictions.
- Require strict JSON output (no extra text outside JSON).
- Add a 1-line Turkish rationale per candidate.
- Penalize repetition: discourage same cadence and phrases.
