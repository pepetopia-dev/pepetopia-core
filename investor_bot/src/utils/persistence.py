"""
Persistence Manager Module

Provides persistent state management for the Investor Bot application.
Handles saving and loading of bot state including processed commits
and queued update messages.

Author: Pepetopia Development Team
"""

import json
import os
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger


# Initialize module logger
logger = get_logger(__name__)


# Type alias for state dictionary
StateDict = Dict[str, Any]


class PersistenceManager:
    """
    Manages persistent state storage for the bot.
    
    Provides methods for tracking processed commits and managing
    a queue of pending update messages for multi-day distribution.
    
    Attributes:
        file_path: Path to the JSON state file
    """
    
    # Default state structure
    DEFAULT_STATE: StateDict = {
        "last_processed_sha": None,
        "pending_updates": []
    }
    
    def __init__(self, file_path: str = "data/bot_state.json"):
        """
        Initializes the persistence manager.
        
        Args:
            file_path: Path to the state file (relative to project root)
        """
        self.file_path = file_path
        self._ensure_directory_exists()
        
        logger.debug(f"PersistenceManager initialized with file: {file_path}")
    
    def _ensure_directory_exists(self) -> None:
        """
        Creates the directory for the state file if it doesn't exist.
        """
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
    
    def load_state(self) -> StateDict:
        """
        Loads the current state from the persistence file.
        
        Returns:
            Dictionary containing the current bot state.
            Returns default state if file doesn't exist or is corrupted.
        """
        if not os.path.exists(self.file_path):
            logger.debug("State file not found, using default state")
            return self.DEFAULT_STATE.copy()
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                logger.debug("State loaded successfully")
                return state
                
        except json.JSONDecodeError as e:
            logger.warning(f"State file corrupted, using default: {e}")
            return self.DEFAULT_STATE.copy()
            
        except IOError as e:
            logger.error(f"Failed to read state file: {e}")
            return self.DEFAULT_STATE.copy()
    
    def save_state(self, state: StateDict) -> bool:
        """
        Saves the current state to the persistence file.
        
        Args:
            state: Dictionary containing the state to save
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=4, ensure_ascii=False)
            logger.debug("State saved successfully")
            return True
            
        except IOError as e:
            logger.critical(f"Failed to save state: {e}")
            return False
    
    def get_last_processed_sha(self) -> Optional[str]:
        """
        Retrieves the SHA of the last processed commit.
        
        Returns:
            The SHA string if available, None otherwise
        """
        sha = self.load_state().get("last_processed_sha")
        if sha:
            logger.debug(f"Last processed SHA: {sha[:8]}...")
        return sha
    
    def update_last_processed_sha(self, sha: str) -> bool:
        """
        Updates the last processed commit SHA.
        
        Args:
            sha: The commit SHA to mark as processed
            
        Returns:
            True if update was successful, False otherwise
        """
        state = self.load_state()
        state["last_processed_sha"] = sha
        success = self.save_state(state)
        
        if success:
            logger.info(f"Updated last processed SHA to: {sha[:8]}...")
        
        return success
    
    def get_pending_updates(self) -> List[str]:
        """
        Retrieves the list of queued update messages.
        
        Returns:
            List of pending update message strings
        """
        updates = self.load_state().get("pending_updates", [])
        logger.debug(f"Retrieved {len(updates)} pending updates")
        return updates
    
    def set_pending_updates(self, updates: List[str]) -> bool:
        """
        Overwrites the pending updates queue.
        
        Args:
            updates: List of update messages to queue
            
        Returns:
            True if update was successful, False otherwise
        """
        state = self.load_state()
        state["pending_updates"] = updates
        success = self.save_state(state)
        
        if success:
            logger.info(f"Queued {len(updates)} updates for future delivery")
        
        return success
    
    def pop_next_update(self) -> Optional[str]:
        """
        Retrieves and removes the next update from the queue.
        
        Implements FIFO (First-In-First-Out) queue behavior.
        
        Returns:
            The next update message, or None if queue is empty
        """
        state = self.load_state()
        updates = state.get("pending_updates", [])
        
        if not updates:
            logger.debug("No pending updates in queue")
            return None
        
        # Pop the first item (FIFO)
        next_msg = updates.pop(0)
        state["pending_updates"] = updates
        self.save_state(state)
        
        logger.info(f"Popped update from queue ({len(updates)} remaining)")
        return next_msg
    
    def clear_pending_updates(self) -> bool:
        """
        Clears all pending updates from the queue.
        
        Returns:
            True if clear was successful, False otherwise
        """
        state = self.load_state()
        state["pending_updates"] = []
        success = self.save_state(state)
        
        if success:
            logger.info("Cleared all pending updates")
        
        return success
    
    def get_queue_length(self) -> int:
        """
        Returns the number of pending updates in the queue.
        
        Returns:
            Number of queued update messages
        """
        return len(self.get_pending_updates())
