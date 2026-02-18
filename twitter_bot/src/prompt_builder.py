import os
from dataclasses import dataclass, asdict
from typing import Optional, Dict

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
    Constructs prompts for the LLM based on persona and algorithm insights.
    Enforces Chain of Thought (CoT) and strict JSON output with 3 distinct options.
    """
    
    # Path handling to ensure it works regardless of where main.py is run
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    INSIGHTS_PATH = os.path.join(BASE_DIR, 'docs', 'TWITTER_ALGORITHM_INSIGHTS.md')

    def __init__(self):
        self.insights = self._load_insights()

    def _load_insights(self) -> str:
        """Loads Twitter Algorithm Insights from the markdown file."""
        if not os.path.exists(self.INSIGHTS_PATH):
            return "Prioritize high engagement, conversation starters, and relevant niche keywords."
        
        try:
            with open(self.INSIGHTS_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error loading insights: {e}"

    def build_system_prompt(self, persona: Dict[str, str]) -> str:
        """
        Builds the system prompt.
        Crucial Update: Demands 3 distinct reply options in the JSON output.
        """
        
        return f"""
You are {persona['role']}.
Style: {persona['style']}
Mission: {persona['directive']}

### TWITTER ALGORITHM INSIGHTS
Use these rules to optimize your response:
{self.insights}

### INSTRUCTIONS
1. **Analyze First:**
   - Identify the user's sentiment and core topic.
   - Determine the viral potential.

2. **Draft 3 Distinct Replies (English Only):**
   - You must generate THREE (3) different options based on your persona.
   - **Option 1 (Viral/Hook):** Short, punchy, designed to grab attention.
   - **Option 2 (Value/Insight):** Adds specific knowledge or a unique perspective.
   - **Option 3 (Question/Engagement):** Ends with a strong open-ended question to spark debate.
   - **Constraint:** All replies must be in **ENGLISH**.

3. **Output Format (STRICT JSON):**
   You must output a single JSON object. Do not include any text outside the JSON.
   
   Schema:
   {{
      "analysis": {{
          "sentiment": "User sentiment analysis",
          "topic": "Core topic identified",
          "context_thought": "Brief reasoning in TURKISH explaining why these replies were chosen."
      }},
      "viral_score": 85,  // Integer 0-100
      "replies": [
          {{
              "type": "Viral Hook",
              "text": "Draft text for option 1..."
          }},
          {{
              "type": "Value Add",
              "text": "Draft text for option 2..."
          }},
          {{
              "type": "Engagement",
              "text": "Draft text for option 3..."
          }}
      ]
   }}
"""

    def build_user_prompt(self, context: TweetContext) -> str:
        """Wraps the user input/context for the LLM."""
        context_str = f"""
INPUT TWEET:
Author: {context.author}
Text: "{context.text}"

TASK: Generate 3 optimal replies in JSON format.
"""
        return context_str