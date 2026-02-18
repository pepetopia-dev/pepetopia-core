---
trigger: always_on
---

# Style Rule

Language:
- Telegram user-facing output MUST be English.
- Source code, identifiers, docstrings, and comments MUST be English.

Engineering:
- Prefer small, testable functions.
- Handle errors explicitly (network, API errors, JSON parsing errors).
- Logs must be useful but never include secrets.

Output format:
- The model must return strict JSON internally (no extra text).
- Telegram rendering must be stable (avoid Markdown entity issues; prefer HTML + escaping).

Product rules:
- No autopromo, no “bio”, no forced Pepetopia mentions unless tweet is about Pepetopia.
- No financial advice, no price predictions.
- Must generate diverse candidates (no near-duplicates).
