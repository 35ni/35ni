#!/usr/bin/env python3
"""Refresh the public repository showcase in the 35ni profile README."""

from __future__ import annotations

import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "35ni")
PROFILE_REPO = f"{OWNER}/{OWNER}"
README_PATH = "README.md"
START = "<!-- REPOSITORIES:START -->"
END = "<!-- REPOSITORIES:END -->"


def github_get(url: str, token: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "35ni-profile-readme-updater",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        import json
        return json.loads(response.read().decode("utf-8"))


def safe_cell(value: object) -> str:
    return str(value or "—").replace("|", r"\|").replace("\n", " ").strip()


def main() -> None:
    token = os.environ["GITHUB_TOKEN"]
    repos = []
    page = 1

    while True:
        data = github_get(
            f"https://api.github.com/users/{OWNER}/repos?type=public"
            f"&sort=updated&direction=desc&per_page=100&page={page}",
            token,
        )
        if not isinstance(data, list) or not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1

    public_repos = [
        repo for repo in repos
        if repo.get("private") is False
        and repo.get("visibility", "public") == "public"
        and repo.get("full_name", "").lower() != PROFILE_REPO.lower()
        and not repo.get("archived", False)
    ]

    lines = [
        f"_Automatically refreshed {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
    ]
    if not public_repos:
        lines.append("_More public projects coming soon._")
    else:
        lines.extend([
            "| Project | Description | Language | ★ | Updated |",
            "|:--|:--|:--|--:|:--|",
        ])
        for repo in public_repos:
            name = safe_cell(repo.get("name"))
            url = repo.get("html_url", "")
            description = safe_cell(repo.get("description"))
            language = safe_cell(repo.get("language"))
            stars = repo.get("stargazers_count", 0)
            updated = (repo.get("updated_at") or "")[:10] or "—"
            lines.append(
                f"| [{name}]({url}) | {description} | {language} | {stars} | {updated} |"
            )

    showcase = "\n".join(lines)
    with open(README_PATH, "r", encoding="utf-8") as file:
        readme = file.read()

    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        flags=re.DOTALL,
    )
    replacement = f"{START}\n{showcase}\n{END}"
    updated_readme, count = pattern.subn(lambda _: replacement, readme, count=1)
    if count != 1:
        raise RuntimeError("Could not find the repository showcase markers in README.md")

    with open(README_PATH, "w", encoding="utf-8", newline="\n") as file:
        file.write(updated_readme)


if __name__ == "__main__":
    main()
