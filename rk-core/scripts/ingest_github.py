"""
ingest_github.py — Fetches a GitHub user's profile and repositories and writes them
as structured markdown files into knowledge_base/github/ for the RAG pipeline.

Usage:
    python scripts/ingest_github.py

Reads GITHUB_TOKEN and GITHUB_USERNAME from .env (loaded automatically).
"""
from __future__ import annotations

import base64
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

GH_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GH_USER = os.getenv("GITHUB_USERNAME", "").strip()
OUT_DIR = ROOT / "knowledge_base" / "github"
OUT_DIR.mkdir(parents=True, exist_ok=True)

API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "rk-genai-chatbot-ingest",
}
if GH_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GH_TOKEN}"


def _log(msg: str) -> None:
    print(f"[github] {msg}", flush=True)


def fetch_user(client: httpx.Client) -> dict:
    r = client.get(f"{API}/users/{GH_USER}", headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def fetch_repos(client: httpx.Client) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        r = client.get(
            f"{API}/users/{GH_USER}/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "sort": "updated", "type": "owner"},
            timeout=30,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def fetch_readme(client: httpx.Client, full_name: str) -> str:
    try:
        r = client.get(
            f"{API}/repos/{full_name}/readme",
            headers={**HEADERS, "Accept": "application/vnd.github.raw"},
            timeout=20,
        )
        if r.status_code == 200:
            return r.text[:8000]
        if r.status_code != 404:
            _log(f"  readme {full_name}: HTTP {r.status_code}")
    except httpx.HTTPError as e:
        _log(f"  readme {full_name} error: {e}")
    return ""


def write_profile(profile: dict) -> None:
    name = profile.get("name") or profile.get("login", GH_USER)
    bio = profile.get("bio") or ""
    company = profile.get("company") or ""
    location = profile.get("location") or ""
    blog = profile.get("blog") or ""
    twitter = profile.get("twitter_username") or ""
    followers = profile.get("followers", 0)
    following = profile.get("following", 0)
    public_repos = profile.get("public_repos", 0)
    created = profile.get("created_at", "")[:10]
    html_url = profile.get("html_url", "")

    md = f"""# GitHub Profile — {name}

## Identity
- **Username:** @{profile.get('login', GH_USER)}
- **Name:** {name}
- **Bio:** {bio}
- **Company:** {company}
- **Location:** {location}
- **Blog:** {blog}
- **Twitter:** {twitter}
- **Profile:** {html_url}
- **Member since:** {created}

## Stats
- **Public repositories:** {public_repos}
- **Followers:** {followers}
- **Following:** {following}
"""
    (OUT_DIR / "_profile.md").write_text(md, encoding="utf-8")
    _log(f"wrote _profile.md for {name}")


def write_repos(repos: list[dict], client: httpx.Client) -> None:
    # Summary file
    lines = ["# GitHub Repositories — Summary\n"]
    lines.append(f"_Total public repos: {len(repos)}_\n")
    lines.append("| Repository | Language | Stars | Forks | Description |")
    lines.append("|---|---|---|---|---|")
    for repo in sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True):
        name = repo.get("name", "")
        lang = repo.get("language") or "-"
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        desc = (repo.get("description") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| [{name}]({repo.get('html_url', '')}) | {lang} | {stars} | {forks} | {desc} |")
    (OUT_DIR / "_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _log(f"wrote _summary.md with {len(repos)} repos")

    # Per-repo files
    for repo in repos:
        name = repo.get("name", "")
        full = repo.get("full_name", "")
        desc = repo.get("description") or ""
        lang = repo.get("language") or "Not specified"
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        topics = repo.get("topics") or []
        homepage = repo.get("homepage") or ""
        created = (repo.get("created_at") or "")[:10]
        updated = (repo.get("updated_at") or "")[:10]
        html = repo.get("html_url", "")
        archived = repo.get("archived", False)

        readme = fetch_readme(client, full) if not archived else ""

        md = f"""# {name}

- **Repository:** {html}
- **Description:** {desc}
- **Primary language:** {lang}
- **Stars:** {stars}
- **Forks:** {forks}
- **Topics:** {", ".join(topics) if topics else "None"}
- **Homepage:** {homepage or "N/A"}
- **Created:** {created}
- **Last updated:** {updated}
- **Archived:** {"Yes" if archived else "No"}

"""
        if readme:
            md += f"## README\n\n{readme}\n"
        else:
            md += "## README\n\n_No README available._\n"

        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
        (OUT_DIR / f"{safe}.md").write_text(md, encoding="utf-8")
        _log(f"  wrote {safe}.md ({lang}, {stars} stars)")


def main() -> int:
    if not GH_USER:
        print("ERROR: GITHUB_USERNAME is not set in .env", file=sys.stderr)
        return 1

    _log(f"ingesting GitHub data for user: {GH_USER}")
    with httpx.Client() as client:
        try:
            profile = fetch_user(client)
        except httpx.HTTPError as e:
            print(f"ERROR: failed to fetch user profile: {e}", file=sys.stderr)
            return 1
        write_profile(profile)

        try:
            repos = fetch_repos(client)
        except httpx.HTTPError as e:
            print(f"ERROR: failed to fetch repos: {e}", file=sys.stderr)
            return 1
        _log(f"fetched {len(repos)} repos")
        write_repos(repos, client)

    _log(f"done. files written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
