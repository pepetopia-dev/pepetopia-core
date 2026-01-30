"""
GitHub Service Module

Provides integration with GitHub's API for fetching repository commits
and detailed change information. Handles authentication, pagination,
and error handling for reliable data retrieval.

Author: Pepetopia Development Team
"""

from typing import Any, Dict, List, Optional

from github import Github, GithubException

from src.app_config import config
from src.utils.logger import get_logger


# Initialize module logger
logger = get_logger(__name__)


class GitHubService:
    """
    Service for interacting with GitHub repositories.
    
    Provides methods for fetching commit history and detailed commit
    information including file changes and patches.
    
    Attributes:
        client: Authenticated GitHub API client
        repo_name: Target repository in 'owner/repo' format
    """
    
    # Maximum characters for patch preview to avoid token limits
    MAX_PATCH_PREVIEW_LENGTH = 500
    
    # Maximum total characters for file analysis
    MAX_TOTAL_ANALYSIS_LENGTH = 15000
    
    def __init__(self):
        """
        Initializes the GitHub service with authentication.
        
        Uses the GitHub access token from application configuration
        to create an authenticated API client.
        """
        self.client = Github(config.github_token)
        self.repo_name = config.github_repo_name
        self._repo = None
        
        logger.info(f"GitHubService initialized for repository: {self.repo_name}")
    
    @property
    def repo(self):
        """
        Lazily loads and caches the repository object.
        
        Returns:
            Repository object for the configured repository
        """
        if self._repo is None:
            self._repo = self.client.get_repo(self.repo_name)
            logger.debug(f"Repository loaded: {self._repo.full_name}")
        return self._repo
    
    def get_all_commits(self) -> List[Dict[str, Any]]:
        """
        Fetches all commits from the repository.
        
        Retrieves the complete commit history and returns them in
        chronological order (oldest first) for sequential processing.
        
        Returns:
            List of commit dictionaries containing:
                - sha: Commit hash
                - author: Author name
                - date: Commit timestamp
                - message: Commit message
                - url: GitHub URL for the commit
        """
        try:
            logger.info("Fetching commit history...")
            
            commits_paginated = self.repo.get_commits()
            commit_data: List[Dict[str, Any]] = []
            
            for commit in commits_paginated:
                commit_data.append({
                    "sha": commit.sha,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date,
                    "message": commit.commit.message,
                    "url": commit.html_url
                })
            
            # Reverse to get oldest first for sequential processing
            commit_data = commit_data[::-1]
            
            logger.info(f"Retrieved {len(commit_data)} commits")
            return commit_data
            
        except GithubException as e:
            logger.error(f"Failed to fetch commits: {e}")
            return []
    
    def get_commit_details(self, sha: str) -> Optional[Dict[str, Any]]:
        """
        Fetches detailed information for a specific commit.
        
        Retrieves comprehensive commit data including file changes,
        patches, and status information for AI analysis.
        
        Args:
            sha: The commit SHA hash to retrieve details for
            
        Returns:
            Dictionary containing detailed commit information:
                - sha: Commit hash
                - author: Author name
                - date: Commit timestamp
                - message: Commit message
                - url: GitHub URL
                - files_analysis: Formatted string of file changes
            Returns None if the commit cannot be retrieved.
        """
        try:
            logger.info(f"Fetching details for commit: {sha[:8]}...")
            
            commit = self.repo.get_commit(sha)
            
            # Analyze changed files
            files_changed: List[str] = []
            
            for file in commit.files:
                # Truncate patch to avoid token limits
                if file.patch:
                    patch_preview = file.patch[:self.MAX_PATCH_PREVIEW_LENGTH]
                    if len(file.patch) > self.MAX_PATCH_PREVIEW_LENGTH:
                        patch_preview += "\n... [truncated]"
                else:
                    patch_preview = "Binary or large file (no diff available)"
                
                file_info = (
                    f"File: {file.filename}\n"
                    f"Status: {file.status}\n"
                    f"Changes: +{file.additions} -{file.deletions}\n"
                    f"Patch Preview:\n{patch_preview}\n"
                    f"---"
                )
                files_changed.append(file_info)
            
            # Combine file analyses with total length limit
            files_analysis = "\n".join(files_changed)
            if len(files_analysis) > self.MAX_TOTAL_ANALYSIS_LENGTH:
                files_analysis = files_analysis[:self.MAX_TOTAL_ANALYSIS_LENGTH]
                files_analysis += "\n\n... [additional files truncated for brevity]"
            
            logger.info(f"Analyzed {len(commit.files)} changed files")
            
            return {
                "sha": commit.sha,
                "author": commit.commit.author.name,
                "date": commit.commit.author.date,
                "message": commit.commit.message,
                "url": commit.html_url,
                "files_analysis": files_analysis
            }
            
        except GithubException as e:
            logger.error(f"Failed to get commit details: {e}")
            return None
    
    def get_commits_since(self, since_sha: str) -> List[Dict[str, Any]]:
        """
        Fetches all commits after a specific commit SHA.
        
        Useful for incremental processing of new commits since
        the last processed commit.
        
        Args:
            since_sha: The SHA of the last processed commit
            
        Returns:
            List of commit dictionaries for commits after since_sha
        """
        all_commits = self.get_all_commits()
        
        if not since_sha:
            return all_commits
        
        # Find the index of the since_sha commit
        for i, commit in enumerate(all_commits):
            if commit["sha"] == since_sha:
                # Return all commits after this one
                return all_commits[i + 1:]
        
        # If since_sha not found, return all commits
        logger.warning(f"Commit {since_sha[:8]} not found in history")
        return all_commits
