#!/usr/bin/env python3
"""Refresh the visual public-repository card in the 35ni profile README."""

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
SVG_PATH = "profile-card.svg"
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
        return json.loads(response.read().decode("utf-8"))


def esc(value: object) -> str:
    return html.escape(str(value or "—"), quote=True)


def build_svg(repos: list[dict]) -> str:
    width = 1000
    columns = 2
    card_h = 76
    rows = max(1, (len(repos) + columns - 1) // columns)
    height = 330 + rows * (card_h + 14) + 60
    cards = []

    for index, repo in enumerate(repos):
        col, row = index % columns, index // columns
        x, y = 30 + col * 470, 250 + row * (card_h + 14)
        name = esc(repo.get("name"))
        description = esc(repo.get("description") or "Public repository")
        url = esc(repo.get("html_url") or f"https://github.com/{OWNER}")
        cards.append(f"""
  <a href="{url}">
    <rect x="{x}" y="{y}" width="450" height="{card_h}" rx="12" fill="#202c40"/>
    <text x="{x + 18}" y="{y + 31}" class="repo">{name}</text>
    <text x="{x + 18}" y="{y + 55}" class="desc">{description[:62]}</text>
  </a>""")

    if not repos:
        cards.append('<text x="42" y="292" class="desc">More public projects coming soon.</text>')

    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    card_markup = "\n".join(cards)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="{height}" viewBox="0 0 1000 {height}">
  <rect width="1000" height="{height}" rx="24" fill="#111827"/>
  <rect x="16" y="16" width="968" height="{height - 32}" rx="20" fill="none" stroke="#263449"/>
  <rect x="32" y="32" width="76" height="76" rx="18" fill="#090b12"/>
  <path d="M70 48 L91 60 L70 73 L49 60 Z" fill="#a78bfa"/>
  <path d="M49 64 L70 77 L70 96 L49 83 Z" fill="#6366f1"/>
  <path d="M91 64 L70 77 L70 96 L91 83 Z" fill="#4338ca"/>
  <text x="124" y="58" class="name">35ni</text>
  <text x="124" y="84" class="role">Independent Developer</text>
  <text x="124" y="110" class="tagline">Building software, tools &amp; experiments.</text>
  <line x1="32" y1="140" x2="968" y2="140" stroke="#3a4960"/>
  <text x="32" y="194" class="heading">Public Projects</text>
  {card_markup}
  <text x="32" y="{height - 38}" class="foot">Automatically generated from public GitHub repositories · Updated {updated}</text>
  <style>
    .name {{ font: 700 30px Arial, sans-serif; fill: #f8fafc; }}
    .role {{ font: 14px Arial, sans-serif; fill: #cbd5e1; }}
    .tagline {{ font: 14px Arial, sans-serif; fill: #e2e8f0; }}
    .heading {{ font: 700 21px Arial, sans-serif; fill: #f8fafc; }}
    .repo {{ font: 700 17px Arial, sans-serif; fill: #f8fafc; }}
    .desc {{ font: 13px Arial, sans-serif; fill: #cbd5e1; }}
    .foot {{ font: 12px Arial, sans-serif; fill: #94a3b8; }}
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

    with open(SVG_PATH, "w", encoding="utf-8", newline="\n") as file:
        file.write(build_svg(public_repos))

    with open(README_PATH, "r", encoding="utf-8") as file:
        readme = file.read()

    replacement = f"{START}\n\n![35ni profile card](./{SVG_PATH})\n\n{END}"
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    updated_readme, count = pattern.subn(lambda _: replacement, readme, count=1)
    if count != 1:
        raise RuntimeError("Could not find repository showcase markers in README.md")

    with open(README_PATH, "w", encoding="utf-8", newline="\n") as file:
        file.write(updated_readme)


if __name__ == "__main__":
    main()
