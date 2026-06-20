#!/usr/bin/env python3
"""Update the "Latest Repositories" section of the profile README.

Fetches the most recently pushed public repositories owned by the user from
the GitHub API and rewrites the content between the LATEST_REPOS markers.
Uses only the Python standard library so it needs no extra dependencies.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

USERNAME = os.environ.get("GH_USERNAME", "anycodef")
README_PATH = os.environ.get("README_PATH", "README.md")
MAX_REPOS = int(os.environ.get("MAX_REPOS", "5"))

START_MARKER = "<!-- LATEST_REPOS:START -->"
END_MARKER = "<!-- LATEST_REPOS:END -->"


def fetch_repos() -> list[dict]:
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?per_page=100&sort=pushed&type=owner"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USERNAME}-profile-readme",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def select_repos(repos: list[dict]) -> list[dict]:
    """Skip forks, archived repos and the profile repo itself."""
    selected = [
        repo
        for repo in repos
        if not repo.get("fork")
        and not repo.get("archived")
        and repo.get("name") != USERNAME
    ]
    return selected[:MAX_REPOS]


def render(repos: list[dict]) -> str:
    if not repos:
        return "_No public repositories yet._"

    lines = []
    for repo in repos:
        name = repo["name"]
        url = repo["html_url"]
        description = (repo.get("description") or "").strip()
        language = repo.get("language")

        line = f"- **[{name}]({url})**"
        if description:
            line += f" — {description}"
        if language:
            line += f" `({language})`"
        lines.append(line)

    return "\n".join(lines)


def update_readme(content: str) -> bool:
    with open(README_PATH, "r", encoding="utf-8") as handle:
        readme = handle.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    if not pattern.search(readme):
        print("Markers not found in README; nothing to update.", file=sys.stderr)
        return False

    replacement = f"{START_MARKER}\n{content}\n{END_MARKER}"
    updated = pattern.sub(replacement, readme)

    if updated == readme:
        return False

    with open(README_PATH, "w", encoding="utf-8") as handle:
        handle.write(updated)
    return True


def main() -> int:
    try:
        repos = fetch_repos()
    except (urllib.error.URLError, urllib.error.HTTPError) as error:
        print(f"Failed to fetch repositories: {error}", file=sys.stderr)
        return 1

    content = render(select_repos(repos))
    changed = update_readme(content)
    print("README updated." if changed else "README already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
