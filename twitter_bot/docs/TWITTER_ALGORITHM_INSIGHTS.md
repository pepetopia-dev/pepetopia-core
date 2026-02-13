# X (Twitter) Algorithm Optimization Rules

## 1. Ranking Signals (from Source Code)

### Conversation Weight
**The algorithm prioritizes replies that spark a conversation.** (Source: threaded_conversation_scorer).
*   **Action:** End replies with an open-ended question or a controversial take to provoke a response.

### SimClusters (Topic Relevance)
**Users and Tweets are clustered.** (Source: sim_clusters).
*   **Action:** Stay strictly within the niche (Crypto/Tech). Using keywords outside the cluster reduces visibility.

### Reputation Penalty
**Low-quality interactions lower the user's reputation score.** (Source: reputation_scorer).
*   **Action:** Avoid generic comments like 'Great project!'. They look like spam bot behavior.

## 2. Viral Score Logic (0-100)

*   **< 50 (Reject):** Generic, short, agrees without adding value.
*   **50-75 (Safe):** Good format, relevant, but lacks a hook.
*   **75-90 (Growth):** Provocative, uses data/chart reference, strictly targeted to the niche.
*   **90+ (Viral):** Strong emotional trigger (Humor/Shock/Insight), perfect formatting, highly likely to get a Reply from the OP.

## 3. Persona Guidelines

### CEO
*   **Focus:** Macro-economics, strategy, partnership, and 'Alpha'.
*   **Tone:** Confident, terse.

### ENGINEER
*   **Focus:** Technical implementation, solidity/rust code, security, and optimization.
*   **Tone:** Skeptical, detailed.