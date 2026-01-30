from github import Github, GithubException
from typing import List, Dict, Optional
import sys
from src.app_config import config

class GitHubService:
    def __init__(self):
        self.client = Github(config.github_token)
        self.repo_name = config.github_repo_name
        self._repo = None

    @property
    def repo(self):
        if not self._repo:
            self._repo = self.client.get_repo(self.repo_name)
        return self._repo

    def get_all_commits(self) -> List[Dict]:
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
            return commit_data[::-1] # Oldest first
        except GithubException as e:
            print(f"ERROR: Failed to fetch commits. {e}")
            return []

    def get_commit_details(self, sha: str) -> Optional[Dict]:
        """
        Fetches DETAILED info including file changes.
        """
        try:
            commit = self.repo.get_commit(sha)
            
            # Analyze changed files
            files_changed = []
            for file in commit.files:
                # We limit patch size to avoid token limits
                patch_preview = file.patch[:500] if file.patch else "Binary or large file"
                files_changed.append(f"File: {file.filename}\nStatus: {file.status}\nChange: {patch_preview}\n---")

            return {
                "sha": commit.sha,
                "author": commit.commit.author.name,
                "date": commit.commit.author.date,
                "message": commit.commit.message,
                "url": commit.html_url,
                "files_analysis": "\n".join(files_changed)[:15000] # Limit total char count for AI
            }
        except GithubException as e:
            print(f"ERROR: Could not get commit details. {e}")
            return None