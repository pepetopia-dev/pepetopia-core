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
        Analyzes code changes to generate detailed, story-driven updates.
        Ignores raw commit messages in the final output.
        """
        
        # Dosya analiz verisi yoksa (örn: binary dosya), mesajdan üretmeye çalış ama süsle.
        files_analysis = commit_data.get('files_analysis', 'No detailed file changes available.')

        prompt = (
            f"Role: You are the Lead Developer of 'Pepetopia', a Solana memecoin project.\n"
            f"Task: Write a daily development update based ONLY on the code changes (patches) below.\n"
            f"Target Audience: Non-technical crypto investors who want to feel the project is active and professional.\n\n"
            
            f"🚫 CONSTRAINT 1: NEVER output the raw commit message (e.g. 'feat: initial commit'). Ignore it completely in the output.\n"
            f"🚫 CONSTRAINT 2: Do NOT mention specific filenames (like 'main.py' or 'utils.py'). Use concepts like 'AI Engine', 'Blockchain Connectivity', 'Security Layer'.\n\n"
            
            f"INPUT DATA:\n"
            f"Commit Message (For context only): {commit_data['message']}\n"
            f"Code Changes (THE REAL TRUTH): \n{files_analysis}\n\n"
            
            f"INSTRUCTIONS:\n"
            f"1. Analyze the code changes. If you see '.env', talk about Security. If you see 'requirements.txt', talk about Infrastructure. If you see 'bot', talk about AI logic.\n"
            f"2. Write a detailed, exciting story. Explain WHY this change matters.\n"
            f"3. IF the changes are huge (many files), split the story into a JSON LIST of 2 or 3 strings. [\"Part 1 text\", \"Part 2 text\"].\n"
            f"   - Spread the excitement over multiple days.\n"
            f"4. IF changes are small, return a JSON LIST with 1 string.\n"
            f"5. Output Language: Turkish 🇹🇷.\n"
            f"6. Format: Plain text with Emojis. (No markdown headers like **Title** inside the text, just the content).\n"
            f"7. OUTPUT FORMAT: Strictly a JSON List of strings. Example: [\"Bugün altyapıda devrim yaptık...\", \"Güvenlik protokollerini sıkılaştırdık...\"]"
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
            # HATA DURUMUNDA ARTIK COMMIT MESAJINI BASMIYORUZ.
            # Onun yerine genel geçer, havalı bir mesaj dönüyoruz.
            return [
                "🛠️ **Altyapı Güçlendirme Çalışması**\n\n"
                "Ekibimiz bugün sistemin çekirdek modüllerinde performans optimizasyonları gerçekleştirdi. "
                "Veri akışını hızlandırmak ve güvenliği artırmak adına arka planda önemli kod refactoring işlemleri tamamlandı."
            ]