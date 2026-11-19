#!/usr/bin/env python3
"""Refresh the 35ni profile artwork and individually clickable project cards."""

from __future__ import annotations

import html
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "35ni")
PROFILE_REPO = f"{OWNER}/{OWNER}"
README_PATH = "README.md"
START = "<!-- REPOSITORIES:START -->"
END = "<!-- REPOSITORIES:END -->"


def github_get(url: str, token: str) -> object:
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "35ni-profile-readme-updater",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def esc(value: object) -> str:
    return html.escape(str(value or "—"), quote=True)


def build_header() -> str:
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="220" viewBox="0 0 1000 220">
  <rect width="1000" height="220" rx="24" fill="#111827"/>
  <rect x="16" y="16" width="968" height="188" rx="20" fill="none" stroke="#263449"/>
  <rect x="32" y="32" width="76" height="76" rx="18" fill="#090b12"/>
  <path d="M70 48 L91 60 L70 73 L49 60 Z" fill="#a78bfa"/>
  <path d="M49 64 L70 77 L70 96 L49 83 Z" fill="#6366f1"/>
  <path d="M91 64 L70 77 L70 96 L91 83 Z" fill="#4338ca"/>
  <text x="124" y="58" class="name">35ni</text>
  <text x="124" y="84" class="role">Independent Developer</text>
  <text x="124" y="110" class="tagline">Building software, tools &amp; experiments.</text>
  <line x1="32" y1="140" x2="968" y2="140" stroke="#3a4960"/>
  <text x="32" y="181" class="heading">Public Projects</text>
  <style>
    .name { font: 700 30px Arial, sans-serif; fill: #f8fafc; }
    .role { font: 14px Arial, sans-serif; fill: #cbd5e1; }
    .tagline { font: 14px Arial, sans-serif; fill: #e2e8f0; }
    .heading { font: 700 21px Arial, sans-serif; fill: #f8fafc; }
  </style>
</svg>
'''


def build_project_card(repo: dict) -> str:
    name = esc(repo.get("name"))
    description = esc(repo.get("description") or "Public repository")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="450" height="76" viewBox="0 0 450 76">
  <rect width="450" height="76" rx="12" fill="#202c40"/>
  <text x="18" y="31" class="repo">{name}</text>
  <text x="18" y="55" class="desc">{description[:62]}</text>
  <style>
    .repo {{ font: 700 17px Arial, sans-serif; fill: #f8fafc; }}
    .desc {{ font: 13px Arial, sans-serif; fill: #cbd5e1; }}
  </style>
</svg>
'''


def main() -> None:
    token = os.environ["GITHUB_TOKEN"]
    repos = []
    page = 1
    while True:
        data = github_get(
            f"https://api.github.com/users/{OWNER}/repos?type=public"
            f"&sort=updated&direction=desc&per_page=100&page={page}", token
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

    with open("profile-card.svg", "w", encoding="utf-8", newline="\n") as file:
        file.write(build_header())

    cards = []
    for index, repo in enumerate(public_repos):
        filename = f"project-card-{index}.svg"
        with open(filename, "w", encoding="utf-8", newline="\n") as file:
            file.write(build_project_card(repo))
        url = repo.get("html_url") or f"https://github.com/{OWNER}"
        cards.append(f"[![{esc(repo.get('name'))}](./{filename})]({url})")

    if cards:
        project_rows = []
        for i in range(0, len(cards), 2):
            left = cards[i]
            right = cards[i + 1] if i + 1 < len(cards) else ""
            project_rows.append(f"| {left} | {right} |")
        showcase = "\n".join(["| | |", "|:--:|:--:|", *project_rows])
    else:
        showcase = "_More public projects coming soon._"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    replacement = (
        f"{START}\n\n![35ni profile header](./profile-card.svg)\n\n"
        f"{showcase}\n\n<sub>Automatically refreshed from public GitHub repositories · {timestamp}</sub>\n\n{END}"
    )
    with open(README_PATH, "r", encoding="utf-8") as file:
        readme = file.read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    updated_readme, count = pattern.subn(lambda _: replacement, readme, count=1)
    if count != 1:
        raise RuntimeError("Could not find repository showcase markers in README.md")
    with open(README_PATH, "w", encoding="utf-8", newline="\n") as file:
        file.write(updated_readme)


if __name__ == "__main__":
    main()
