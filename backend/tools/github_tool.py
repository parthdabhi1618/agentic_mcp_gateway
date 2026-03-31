from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")


def create_branch(name: str, from_branch: str = "main", **kwargs) -> None:
    """Create a branch in the configured GitHub repository."""
    if not name:
        raise ValueError("Branch name is required")
    if not GITHUB_TOKEN or not GITHUB_REPO:
        raise ValueError("GITHUB_TOKEN or GITHUB_REPO not set in .env")

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    ref_url = f"https://api.github.com/repos/{GITHUB_REPO}/git/ref/heads/{from_branch}"
    ref_response = requests.get(ref_url, headers=headers, timeout=15)
    ref_response.raise_for_status()
    sha = ref_response.json()["object"]["sha"]

    create_url = f"https://api.github.com/repos/{GITHUB_REPO}/git/refs"
    payload = {"ref": f"refs/heads/{name}", "sha": sha}
    create_response = requests.post(
        create_url, headers=headers, json=payload, timeout=15
    )

    if create_response.status_code == 422:
        raise ValueError(f"Branch '{name}' already exists")

    create_response.raise_for_status()
