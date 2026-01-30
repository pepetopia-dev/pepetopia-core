import os
import re
from datetime import datetime

class DiaryReader:
    """
    Handles reading and parsing of the markdown diary file.
    Optimized for Python 3.12+ syntax.
    """

    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Diary file not found at: {file_path}")
        self.file_path: str = file_path

    # Python 3.12 Update: Used 'str | None' instead of 'Optional[str]'
    def get_entry_by_date(self, target_date: str | None = None) -> str | None:
        """
        Retrieves the diary entry for a specific date.
        
        Args:
            target_date (str | None): Date string in 'DD.MM.YYYY' format. 
                                      If None, uses today's date (System Local Time).
            
        Returns:
            str | None: The content of the entry if found, otherwise None.
        """
        if target_date is None:
            target_date = datetime.now().strftime("%d.%m.%Y")
            
        # Regex uses raw strings (r'') which is critical in Python 3.12
        # to avoid SyntaxWarnings about invalid escape sequences.
        header_pattern = re.compile(rf'^#\s+{re.escape(target_date)}\s*$', re.MULTILINE)
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content: str = file.read()

            match = header_pattern.search(content)
            if not match:
                return None

            start_index: int = match.end()
            remaining_content: str = content[start_index:]

            next_header_pattern = re.compile(r'^#\s+\d{2}\.\d{2}\.\d{4}', re.MULTILINE)
            next_match = next_header_pattern.search(remaining_content)

            entry_text: str = ""
            if next_match:
                entry_text = remaining_content[:next_match.start()]
            else:
                entry_text = remaining_content

            return entry_text.strip()

        except Exception as e:
            print(f"Error reading diary file: {e}")
            return None