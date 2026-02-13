from dataclasses import dataclass, asdict
from typing import Dict, Optional
import os
import json

@dataclass
class TweetContext:
    text: str
    author: str
    topic: Optional[str] = None
    sentiment: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)

class PromptBuilder:
    """
    Constructs prompts for the LLM based on persona, algorithm insights, and tweet context.
    Enforces Chain of Thought (CoT) and strict JSON output.
    """
    
    INSIGHTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'TWITTER_ALGORITHM_INSIGHTS.md')

    def __init__(self):
        self.insights = self._load_insights()

    def _load_insights(self) -> str:
        """Loads Twitter Algorithm Insights from the markdown file."""
        if not os.path.exists(self.INSIGHTS_PATH):
            return "No insights available."
        
        try:
            with open(self.INSIGHTS_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error loading insights: {e}"

    def build_system_prompt(self, persona: Dict[str, str]) -> str:
        """
        Builds the system prompt including:
        1. Persona definition
        2. Twitter Algorithm Insights
        3. Chain of Thought instructions
        4. Strict JSON Output Schema
        """
        
        return f"""
You are {persona['role']}.
Style: {persona['style']}
Mission: {persona['directive']}

### TWITTER ALGORITHM INSIGHTS
Use these rules to optimize your response:
{self.insights}

### INSTRUCTIONS
1. **Analyze First (Chain of Thought):**
   - Identify the user's sentiment (Positive/Negative/Neutral).
   - Identify the core topic (Crypto, Tech, Meme, Politics, etc.).
   - Determine the viral potential of the input.
   - Plan a reply that maximizes 'Conversation Weight' and 'SimClusters' relevance.

2. **Draft the Reply:**
   - Adhere strictly to your Persona (CEO or ENGINEER).
   - If CEO: Focus on macro/strategy/alpha. Confident & terse.
   - If ENGINEER: Focus on tech/code/security. Skeptical & detailed.
   - **Viral Score Target:** Aim for 90+ (Viral) or at least 75-90 (Growth).
   - **NO** generic comments like "Great project!".
   - **NO** hashtags unless absolutely necessary for the topic context.

3. **Output Format (STRICT JSON):**
   You must output a single JSON object. Do not include any text outside the JSON.
   
   Schema:
   {{
      "analysis": {{
          "sentiment": "User sentiment analysis",
          "topic": "Core topic identified",
          "context_thought": "Brief CoT reasoning about how to reply"
      }},
      "viral_score": 85,  // Integer 0-100 based on Algorithm Insights
      "reply_text": "Your drafted tweet content here..."
   }}
"""

    def build_user_prompt(self, context: TweetContext) -> str:
        """
         Wraps the user input/context for the LLM.
        """
        context_str = f"""
INPUT TWEET:
Author: {context.author}
Text: "{context.text}"
Topic Hint: {context.topic if context.topic else "Auto-detect"}
Sentiment Hint: {context.sentiment if context.sentiment else "Auto-detect"}

TASK: Generate the optimal reply in JSON format.
"""
        return context_str
