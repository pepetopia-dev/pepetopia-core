import google.generativeai as genai
import sys
import json
import re
from src.app_config import config

class CommitSummarizer:
    def __init__(self):
        if not config.gemini_api_key:
            sys.exit(1)
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def analyze_and_split(self, commit_data: dict) -> list[str]:
        """
        Returns a LIST of status updates (strings). 
        If the commit is small, list has 1 item.
        If huge, list has 2-3 items (Storytelling mode).
        """
        
        prompt = (
            f"Role: You are the Lead Developer of 'Pepetopia', a Solana memecoin project.\n"
            f"Target Audience: Non-technical crypto investors.\n"
            f"Goal: Explain the technical progress based on the code changes provided below.\n\n"
            
            f"INPUT DATA:\n"
            f"Commit Message: {commit_data['message']}\n"
            f"Files Changed & Code Snippets:\n{commit_data['files_analysis']}\n\n"
            
            f"INSTRUCTIONS:\n"
            f"1. Analyze the code changes deeply. Don't just say 'files added'. Say 'Security protocols initialized' if you see .env or gitignore.\n"
            f"2. IMPORTANT: If the changes are massive (like 'Initial commit' or >5 files), split the update into a 'Series' of 2 or 3 distinct messages to be sent on consecutive days.\n"
            f"   - Day 1 focus: Infrastructure & Core Setup\n"
            f"   - Day 2 focus: Security & Configuration\n"
            f"   - Day 3 focus: Features & Logic\n"
            f"3. If small change, just return 1 message.\n"
            f"4. Tone: Hype, professional, transparent. Use emojis.\n"
            f"5. OUTPUT FORMAT: strictly a JSON list of strings. Example: [\"Update 1 text...\", \"Update 2 text...\"]\n"
            f"6. Do NOT use Markdown bold/italic inside the JSON strings yet, plain text with emojis is fine. I will format it later.\n"
            f"7. Language: Turkish 🇹🇷."
        )

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up markdown code blocks if AI adds them
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            
            updates = json.loads(text)
            
            if isinstance(updates, list):
                return updates
            return [text] # Fallback if not list

        except Exception as e:
            print(f"ERROR: AI Analysis failed. {e}")
            return [f"🛠️ **Sistem Güncellemesi**\n\nEkibimiz kod tabanında önemli iyileştirmeler yaptı. ({commit_data['message']})"]