from github import Github, GithubException
from typing import List, Dict, Optional
import sys
from src.app_config import config

class GitHubService:
    """
    Service layer for interacting with GitHub API.
    Handles authentication and data fetching logic.
    """

    def __init__(self):
        self.client = Github(config.github_token)
        self.repo_name = config.github_repo_name
        self._repo = None

    @property
    def repo(self):
        """Lazy loading of the repository object."""
        if not self._repo:
            try:
                self._repo = self.client.get_repo(self.repo_name)
            except GithubException as e:
                print(f"ERROR: Could not fetch repository '{self.repo_name}'. Details: {e}")
                sys.exit(1)
        return self._repo

    def get_all_commits(self) -> List[Dict]:
        """
        Fetches all commits from the repository.
        Returns ordered from OLDEST to NEWEST.
        """
        try:
            commits_paginated = self.repo.get_commits()
            commit_data = []
            
            for commit in commits_paginated:
                commit_data.append({
                    "sha": commit.sha,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date,
                    "message": commit.commit.message,
                    "url": commit.html_url
                })

            return commit_data[::-1]

        except GithubException as e:
            print(f"ERROR: Failed to fetch commits. Details: {e}")
            return []

    def get_commit_by_sha(self, sha: str) -> Optional[Dict]:
        try:
            commit = self.repo.get_commit(sha)
            return {
                "sha": commit.sha,
                "author": commit.commit.author.name,
                "date": commit.commit.author.date,
                "message": commit.commit.message,
                "url": commit.html_url
            }
        except GithubException as e:
            print(f"ERROR: Could not find commit {sha}. Details: {e}")
            return None