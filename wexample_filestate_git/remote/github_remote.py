import os
import re
from typing import Dict, List
from pydantic import Field

from wexample_helpers_api.enums.http import HttpMethod
from .abstract_remote import AbstractRemote

GITHUB_API_TOKEN: str = "GITHUB_API_TOKEN"
GITHUB_DEFAULT_URL: str = "GITHUB_DEFAULT_URL"


class GithubRemote(AbstractRemote):
    base_url: str = Field(
        default="https://api.github.com",
        description="GitHub API base URL"
    )

    def model_post_init(self, *args, **kwargs):
        super().model_post_init(*args, **kwargs)

        self.default_headers.update({
            "Authorization": f"token {os.getenv(GITHUB_API_TOKEN)}",
            "Accept": "application/vnd.github.v3+json"
        })

        if os.getenv(GITHUB_DEFAULT_URL) is not None:
            self.base_url = os.getenv(GITHUB_DEFAULT_URL)

    def get_expected_env_keys(self) -> List[str]:
        return [
            GITHUB_API_TOKEN,
        ]

    def create_repository(self, name: str, description: str = "", private: bool = False, namespace: str = "") -> Dict:
        response = self.make_request(
            method=HttpMethod.POST,
            endpoint="user/repos",
            data={
                "name": name,
                "description": description,
                "private": private,
                "auto_init": True
            },
            call_origin=__file__,
            expected_status_codes=[201],  # Only 201 Created is acceptable
            fatal_if_unexpected=True  # Any other status code should raise an error
        )
        return response.json()

    def check_repository_exists(self, name: str, namespace: str = "") -> bool:
        try:
            # If namespace is provided, use it, otherwise search in user's repositories
            if namespace:
                endpoint = f"repos/{namespace}/{name}"
                response = self.make_request(
                    endpoint=endpoint,
                    call_origin=__file__,
                    expected_status_codes=[200, 404]
                )
                return response.status_code == 200
            else:
                endpoint = f"user/repos"
                response = self.make_request(
                    endpoint=endpoint,
                    call_origin=__file__
                )
                repos = response.json()
                return any(repo["name"] == name for repo in repos)

        except Exception:
            return False

    @classmethod
    def detect_remote_type(cls, remote_url: str) -> bool:
        return bool(re.search(r'github\.com[:/]', remote_url))

    def parse_repository_url(self, remote_url: str) -> Dict[str, str]:
        """
        Parse a GitHub repository URL to extract repository information.
        Supports both HTTPS and SSH URLs:
        - https://github.com/owner/repo.git
        - git@github.com:owner/repo.git
        """
        # Remove protocol and domain
        path = re.sub(r'^(https://github\.com/|git@github\.com:)', '', remote_url)
        # Remove .git suffix if present
        path = path.replace('.git', '')
        
        parts = path.split('/')
        if len(parts) >= 2:
            return {
                'name': parts[-1],
                'namespace': parts[-2]
            }
        return {
            'name': parts[0],
            'namespace': ''
        }
