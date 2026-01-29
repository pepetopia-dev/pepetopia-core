import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import sys
from src.app_config import config

class CommitSummarizer:
    """
    Uses Google's Gemini API to transform technical commit messages 
    into investor-friendly summaries.
    """

    def __init__(self):
        if not config.gemini_api_key:
            print("ERROR: Gemini API Key is missing.")
            sys.exit(1)
            
        genai.configure(api_key=config.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    def summarize(self, commit_message: str, author: str) -> str:
        """
        Generates a non-technical summary of a git commit.
        """
        prompt = (
            f"Role: You are a Lead Developer updating non-technical investors.\n"
            f"Task: Rewrite the following technical git commit message into a clear, "
            f"positive, and professional status update in Turkish.\n"
            f"Constraints:\n"
            f"1. Do not use technical jargon (like refactoring, API, JSON, bugfix).\n"
            f"2. Focus on the business value, user experience, or system stability.\n"
            f"3. Keep it to 1 or 2 sentences max.\n"
            f"4. Speak as if this work was done today.\n"
            f"5. Mention that '{author}' completed this task if relevant.\n\n"
            f"Technical Commit Message: '{commit_message}'\n\n"
            f"Turkish Summary:"
        )

        try:
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = self.model.generate_content(prompt, safety_settings=safety_settings)
            
            if response.text:
                return response.text.strip()
            else:
                return "Bugün sistem altyapısında önemli iyileştirmeler yapıldı."

        except Exception as e:
            print(f"ERROR: AI Summarization failed. Details: {e}")
            return f"Bugün geliştirme ekibi sistem üzerinde güncellemeler yaptı. (Detay: {commit_message})"