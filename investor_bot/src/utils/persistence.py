import json
import os
from typing import Optional

class PersistenceManager:
    """
    Manages the persistent state of the bot using a local JSON file.
    Ensures the bot knows which commit was last processed to avoid duplicates.
    """

    def __init__(self, file_path: str = "data/bot_state.json"):
        self.file_path = file_path
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        """Creates the data directory if it does not exist."""
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def load_state(self) -> dict:
        """Loads the state from the JSON file. Returns empty dict if file not found."""
        if not os.path.exists(self.file_path):
            return {}
        
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"WARNING: Corrupted state file. Starting fresh. Error: {e}")
            return {}

    def save_state(self, state: dict):
        """Writes the current state to the JSON file safely."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(state, f, indent=4)
        except IOError as e:
            print(f"CRITICAL ERROR: Could not save state to {self.file_path}. Error: {e}")

    def get_last_processed_sha(self) -> Optional[str]:
        """Retrieves the SHA of the last commit that was successfully sent."""
        state = self.load_state()
        return state.get("last_processed_sha")

    def update_last_processed_sha(self, sha: str):
        """Updates the state with the new commit SHA."""
        state = self.load_state()
        state["last_processed_sha"] = sha
        self.save_state(state)