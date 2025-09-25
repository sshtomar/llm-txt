"""GitHub PR creation and management."""

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import aiohttp

from .auth import GitHubAuth


class GitHubPR:
    """Manage GitHub pull requests for llm.txt updates."""

    def __init__(self, owner: str, repo: str):
        self.owner = owner
        self.repo = repo
        self.auth = GitHubAuth()
        self.api_base = 'https://api.github.com'

    async def create_or_update_pr(
        self,
        llm_path: Path,
        full_path: Optional[Path] = None,
        reports_dir: Optional[Path] = None
    ) -> Optional[str]:
        """
        Create or update a PR with llm.txt files.

        Returns:
            PR URL if successful, None otherwise
        """
        token = self.auth.get_token()
        if not token:
            print("Not authenticated. Run 'llmxt github login' first.")
            return None

        headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {token}'
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                # Get default branch
                default_branch = await self._get_default_branch(session)
                if not default_branch:
                    print("Failed to get default branch")
                    return None

                # Create or update branch
                branch_name = 'llm-txt/update'
                branch_created = await self._create_or_update_branch(
                    session,
                    branch_name,
                    default_branch
                )

                if not branch_created:
                    print("Failed to create/update branch")
                    return None

                # Get current user
                user = await self._get_current_user(session)
                if not user:
                    print("Failed to get user information")
                    return None

                # Prepare files to commit
                files_to_commit = []

                # Add llm.txt
                if llm_path.exists():
                    content = llm_path.read_text(encoding='utf-8')
                    files_to_commit.append({
                        'path': 'public/llm.txt',
                        'content': content
                    })

                # Add llms-full.txt if exists
                if full_path and full_path.exists():
                    content = full_path.read_text(encoding='utf-8')
                    files_to_commit.append({
                        'path': 'public/llms-full.txt',
                        'content': content
                    })

                # Add reports if directory exists
                if reports_dir and reports_dir.exists():
                    for report_file in reports_dir.glob('*.json'):
                        content = report_file.read_text(encoding='utf-8')
                        files_to_commit.append({
                            'path': f'reports/{report_file.name}',
                            'content': content
                        })

                # Commit files
                commit_sha = await self._commit_files(
                    session,
                    branch_name,
                    files_to_commit,
                    f"Update llm.txt - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )

                if not commit_sha:
                    print("Failed to commit files")
                    return None

                # Check for existing PR
                existing_pr = await self._find_existing_pr(session, branch_name)

                if existing_pr:
                    pr_number = existing_pr['number']
                    pr_url = existing_pr['html_url']

                    # Update PR description
                    await self._update_pr(session, pr_number, files_to_commit)
                    return pr_url
                else:
                    # Create new PR
                    pr_url = await self._create_pr(
                        session,
                        branch_name,
                        default_branch,
                        files_to_commit
                    )
                    return pr_url

            except Exception as e:
                print(f"Error creating/updating PR: {e}")
                return None

    async def _get_default_branch(self, session: aiohttp.ClientSession) -> Optional[str]:
        """Get the default branch of the repository."""
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}'

        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('default_branch', 'main')
            return None

    async def _get_current_user(self, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Get current authenticated user."""
        url = f'{self.api_base}/user'

        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None

    async def _create_or_update_branch(
        self,
        session: aiohttp.ClientSession,
        branch_name: str,
        base_branch: str
    ) -> bool:
        """Create or update a branch."""
        # Get base branch SHA
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}/git/refs/heads/{base_branch}'

        async with session.get(url) as response:
            if response.status != 200:
                return False
            data = await response.json()
            base_sha = data['object']['sha']

        # Try to create branch
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}/git/refs'
        data = {
            'ref': f'refs/heads/{branch_name}',
            'sha': base_sha
        }

        async with session.post(url, json=data) as response:
            if response.status == 201:
                return True
            elif response.status == 422:
                # Branch exists, update it
                url = f'{self.api_base}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch_name}'
                data = {'sha': base_sha, 'force': True}

                async with session.patch(url, json=data) as update_response:
                    return update_response.status == 200

            return False

    async def _commit_files(
        self,
        session: aiohttp.ClientSession,
        branch_name: str,
        files: List[Dict],
        commit_message: str
    ) -> Optional[str]:
        """Commit files to a branch."""
        # Get current tree
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch_name}'

        async with session.get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()
            current_sha = data['object']['sha']

        # Get current commit
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}/git/commits/{current_sha}'

        async with session.get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()
            tree_sha = data['tree']['sha']

        # Create blobs for each file
        tree_items = []
        for file_info in files:
            # Create blob
            url = f'{self.api_base}/repos/{self.owner}/{self.repo}/git/blobs'
            blob_data = {
                'content': base64.b64encode(file_info['content'].encode()).decode(),
                'encoding': 'base64'
            }

            async with session.post(url, json=blob_data) as response:
                if response.status != 201:
                    continue
                blob_response = await response.json()
                blob_sha = blob_response['sha']

                tree_items.append({
                    'path': file_info['path'],
                    'mode': '100644',
                    'type': 'blob',
                    'sha': blob_sha
                })

        if not tree_items:
            return None

        # Create tree
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}/git/trees'
        tree_data = {
            'base_tree': tree_sha,
            'tree': tree_items
        }

        async with session.post(url, json=tree_data) as response:
            if response.status != 201:
                return None
            tree_response = await response.json()
            new_tree_sha = tree_response['sha']

        # Create commit
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}/git/commits'
        commit_data = {
            'message': commit_message,
            'tree': new_tree_sha,
            'parents': [current_sha]
        }

        async with session.post(url, json=commit_data) as response:
            if response.status != 201:
                return None
            commit_response = await response.json()
            new_commit_sha = commit_response['sha']

        # Update branch reference
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}/git/refs/heads/{branch_name}'
        ref_data = {'sha': new_commit_sha}

        async with session.patch(url, json=ref_data) as response:
            if response.status == 200:
                return new_commit_sha

        return None

    async def _find_existing_pr(
        self,
        session: aiohttp.ClientSession,
        branch_name: str
    ) -> Optional[Dict]:
        """Find existing PR from the branch."""
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}/pulls'
        params = {
            'head': f'{self.owner}:{branch_name}',
            'state': 'open'
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                prs = await response.json()
                if prs:
                    return prs[0]
        return None

    async def _create_pr(
        self,
        session: aiohttp.ClientSession,
        branch_name: str,
        base_branch: str,
        files: List[Dict]
    ) -> Optional[str]:
        """Create a new pull request."""
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}/pulls'

        # Generate PR body
        body = self._generate_pr_body(files)

        data = {
            'title': 'Add/Update llm.txt for AI-friendly documentation',
            'head': branch_name,
            'base': base_branch,
            'body': body
        }

        async with session.post(url, json=data) as response:
            if response.status == 201:
                pr_data = await response.json()
                return pr_data['html_url']
        return None

    async def _update_pr(
        self,
        session: aiohttp.ClientSession,
        pr_number: int,
        files: List[Dict]
    ) -> bool:
        """Update existing PR description."""
        url = f'{self.api_base}/repos/{self.owner}/{self.repo}/pulls/{pr_number}'

        body = self._generate_pr_body(files)
        data = {'body': body}

        async with session.patch(url, json=data) as response:
            return response.status == 200

    def _generate_pr_body(self, files: List[Dict]) -> str:
        """Generate PR description body."""
        file_list = '\n'.join([f"- `{f['path']}`" for f in files])

        body = f"""## Summary

This PR adds/updates the `llm.txt` file to provide AI-friendly documentation summaries.

## Files Modified

{file_list}

## What is llm.txt?

`llm.txt` is a standardized format for making documentation more accessible to AI language models. It provides a concise, structured summary of your project's documentation that:

- Improves AI understanding of your project
- Enhances code generation accuracy
- Provides better context for AI-assisted development

## Test Plan

- [ ] Verify `llm.txt` is properly formatted
- [ ] Check file size is within limits (<100KB)
- [ ] Confirm no sensitive information is exposed
- [ ] Validate links are working

---
Generated with [llmxt CLI](https://github.com/yourusername/llm-txt)
"""
        return body