import json
import os
from typing import Optional, List

class PersistenceManager:
    """
    Manages the persistent state of the bot.
    Now supports a 'message queue' to split large updates across multiple days.
    """

    def __init__(self, file_path: str = "data/bot_state.json"):
        self.file_path = file_path
        self._ensure_directory_exists()

    def _ensure_directory_exists(self):
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def load_state(self) -> dict:
        if not os.path.exists(self.file_path):
            return {"last_processed_sha": None, "pending_updates": []}
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"last_processed_sha": None, "pending_updates": []}

    def save_state(self, state: dict):
        try:
            with open(self.file_path, 'w') as f:
                json.dump(state, f, indent=4)
        except IOError as e:
            print(f"CRITICAL ERROR: Could not save state. {e}")

    def get_last_processed_sha(self) -> Optional[str]:
        return self.load_state().get("last_processed_sha")

    def update_last_processed_sha(self, sha: str):
        state = self.load_state()
        state["last_processed_sha"] = sha
        self.save_state(state)

    def get_pending_updates(self) -> List[str]:
        """Returns the list of queued messages waiting to be sent."""
        return self.load_state().get("pending_updates", [])

    def set_pending_updates(self, updates: List[str]):
        """Overwrites the pending updates queue."""
        state = self.load_state()
        state["pending_updates"] = updates
        self.save_state(state)
        
    def pop_next_update(self) -> Optional[str]:
        """Retrieves and removes the next update from the queue."""
        state = self.load_state()
        updates = state.get("pending_updates", [])
        if not updates:
            return None
        
        next_msg = updates.pop(0)
        state["pending_updates"] = updates
        self.save_state(state)
        return next_msg