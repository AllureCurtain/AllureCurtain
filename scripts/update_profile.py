#!/usr/bin/env python3
"""Regenerate the auto-managed surfaces of this profile README.

GitHub READMEs cannot include other files, so everything this script produces is
rewritten in place. Four surfaces are managed, and nothing else in the
repository is touched:

  1. ``<!-- BEGIN:AUTO:BADGES -->`` .. ``<!-- END:AUTO:BADGES -->``
     The badge row, including the live merged-pull-request counts.
  2. ``<!--pr:owner/repo-->N<!--/pr-->`` inline markers
     The merged pull request count for that repository, anywhere in the prose.
     The markers are HTML comments, so GitHub renders only the number.
  3. ``<!-- BEGIN:AUTO:RECENT -->`` .. ``<!-- END:AUTO:RECENT -->``
     The most recently merged pull requests.
  4. ``assets/streak-light.svg`` and ``assets/streak-dark.svg``
     Current streak, longest streak and the last twelve months of contributions.

Every remote value is fetched before anything is written, so a failed request
leaves the working tree untouched instead of committing a half-updated page.
Running the script twice in a row is a no-op.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

USER = "AllureCurtain"
API_ROOT = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"
RECENT_LIMIT = 8
TITLE_LIMIT = 110

TOKEN = (
    os.environ.get("PROFILE_TOKEN")
    or os.environ.get("GITHUB_TOKEN")
    or os.environ.get("GH_TOKEN")
    or ""
).strip()

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(REPO_ROOT, "README.md")
ASSETS_DIR = os.path.join(REPO_ROOT, "assets")

# The count badges carry live numbers, so the row is generated rather than
# hand-edited. Order here is the order on the page.
BADGES = [
    {
        "repo": "sandbaseai/sandbase-harness",
        "label": "sandbase--harness",
        "alt": "Merged PRs in sandbase-harness",
    },
    {
        "repo": "gitmono-dev/mega",
        "label": "mega",
        "alt": "Merged PRs in mega",
    },
]

STATIC_BADGES = [
    ("Rust", "https://img.shields.io/badge/Rust-b7410e?logo=rust&logoColor=white"),
    ("TypeScript", "https://img.shields.io/badge/TypeScript-3178c6?logo=typescript&logoColor=white"),
    ("Tauri", "https://img.shields.io/badge/Tauri-24c8db?logo=tauri&logoColor=white"),
]

INLINE_RE = re.compile(r"<!--\s*pr:(?P<repo>[^\s>]+?)\s*-->.*?<!--\s*/pr\s*-->", re.S)


def block_re(name: str) -> re.Pattern:
    return re.compile(
        rf"(?P<open><!-- BEGIN:AUTO:{name} -->)(?P<body>.*?)(?P<close><!-- END:AUTO:{name} -->)",
        re.S,
    )


def log(message: str) -> None:
    print(message, flush=True)


def warn(message: str) -> None:
    # ::warning:: turns the message into an annotation in the Actions UI.
    print(f"::warning::{message}", flush=True)
    print(f"WARNING: {message}", flush=True)


def request(url: str, *, data: bytes | None = None, accept: str = "application/vnd.github+json"):
    req = urllib.request.Request(url, data=data)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", accept)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "AllureCurtain-profile-readme")
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def rest(path: str, params: dict | None = None):
    url = API_ROOT + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return request(url)


def graphql(query: str, variables: dict):
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    return request(GRAPHQL_URL, data=payload, accept="application/json")


def merged_pr_count(repo: str) -> int:
    result = rest(
        "/search/issues",
        {"q": f"repo:{repo} type:pr author:{USER} is:merged", "per_page": 1},
    )
    return int(result["total_count"])


def recent_merged_prs(limit: int):
    result = rest(
        "/search/issues",
        {
            "q": f"type:pr author:{USER} is:merged",
            "sort": "updated",
            "order": "desc",
            "per_page": limit,
        },
    )
    items = []
    for item in result.get("items", []):
        repo = item["repository_url"].split("/repos/", 1)[-1]
        items.append(
            {
                "repo": repo,
                "title": item.get("title", "").strip(),
                "url": item.get("html_url", ""),
                "date": (item.get("closed_at") or item.get("updated_at") or "")[:10],
            }
        )
    return items


CONTRIBUTIONS_QUERY = """
query ($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def contribution_stats():
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=364)
    payload = graphql(
        CONTRIBUTIONS_QUERY,
        {
            "login": USER,
            "from": f"{start.isoformat()}T00:00:00Z",
            "to": f"{today.isoformat()}T23:59:59Z",
        },
    )
    if "errors" in payload:
        raise RuntimeError("; ".join(err.get("message", "?") for err in payload["errors"]))

    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = sorted(
        (
            (day["date"], int(day["contributionCount"]))
            for week in calendar["weeks"]
            for day in week["contributionDays"]
        ),
        key=lambda entry: entry[0],
    )

    longest = run = 0
    for _, count in days:
        run = run + 1 if count > 0 else 0
        longest = max(longest, run)

    # An empty today does not break a streak that was still alive yesterday.
    index = len(days) - 1
    if index >= 0 and days[index][1] == 0:
        index -= 1
    current = 0
    while index >= 0 and days[index][1] > 0:
        current += 1
        index -= 1

    return {
        "current": current,
        "longest": longest,
        "total": int(calendar["totalContributions"]),
        "active_days": sum(1 for _, count in days if count > 0),
        "window_end": days[-1][0] if days else today.isoformat(),
    }


def markdown_escape(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    for char in ("\\", "`", "*", "_", "[", "]", "<", ">", "&", "|"):
        text = text.replace(char, "\\" + char)
    return text


def truncate(text: str, limit: int = TITLE_LIMIT) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rstrip()
    if " " in cut:
        cut = cut[: cut.rfind(" ")].rstrip()
    return cut + "…"


def render_badges(counts: dict) -> str:
    lines = ['<p align="center">']
    for badge in BADGES:
        count = counts[badge["repo"]]
        href = (
            f'https://github.com/{badge["repo"]}'
            f"/pulls?q=is%3Apr+author%3A{USER}+is%3Amerged"
        )
        lines.append(f'  <a href="{href}">')
        lines.append(
            f'    <img alt="{badge["alt"]}" '
            f'src="https://img.shields.io/badge/{badge["label"]}-{count}%20merged%20PRs-2563eb">'
        )
        lines.append("  </a>")
    for alt, src in STATIC_BADGES:
        lines.append(f'  <img alt="{alt}" src="{src}">')
    lines.append("</p>")
    return "\n".join(lines)


def render_recent(items) -> str:
    lines = ["_Most recently merged pull requests across the projects I work in._", ""]
    for item in items:
        title = markdown_escape(truncate(item["title"]))
        lines.append(f"- `{item['date']}` · [{item['repo']}]({item['url']}) — {title}")
    return "\n".join(lines)


THEMES = {
    "light": {
        "background": "#ffffff",
        "border": "#d0d7de",
        "title": "#0969da",
        "value": "#1f2328",
        "label": "#57606a",
        "note": "#8c959f",
    },
    "dark": {
        "background": "#0d1117",
        "border": "#30363d",
        "title": "#58a6ff",
        "value": "#e6edf3",
        "label": "#8b949e",
        "note": "#6e7681",
    },
}

FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def streak_svg(theme: str, stats: dict) -> str:
    palette = THEMES[theme]
    stats_row = [
        (f"{stats['current']}", "current streak (days)"),
        (f"{stats['longest']}", "longest streak (days)"),
        (f"{stats['total']:,}", "contributions · 12 mo"),
    ]
    columns = ""
    for index, (value, label) in enumerate(stats_row):
        center = 24 + 150 * index + 75
        columns += (
            f'  <text x="{center}" y="118" text-anchor="middle" font-family="{FONT}" '
            f'font-size="30" font-weight="700" fill="{palette["value"]}">{value}</text>\n'
            f'  <text x="{center}" y="142" text-anchor="middle" font-family="{FONT}" '
            f'font-size="12" fill="{palette["label"]}">{label}</text>\n'
        )

    aria = (
        f"Contribution streak: {stats['current']} days current, "
        f"{stats['longest']} days longest, {stats['total']} contributions in the last year"
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="495" height="200" viewBox="0 0 495 200" '
        f'role="img" aria-label="{aria}">\n'
        f'  <rect x="0.5" y="0.5" width="494" height="199" rx="8" fill="{palette["background"]}" '
        f'stroke="{palette["border"]}"/>\n'
        f'  <text x="24" y="38" font-family="{FONT}" font-size="15" font-weight="600" '
        f'fill="{palette["title"]}">Contribution streak</text>\n'
        f'  <line x1="24" y1="56" x2="471" y2="56" stroke="{palette["border"]}"/>\n'
        f"{columns}"
        f'  <text x="24" y="178" font-family="{FONT}" font-size="11" '
        f'fill="{palette["note"]}">active on {stats["active_days"]} days in the last year</text>\n'
        f'  <text x="471" y="178" text-anchor="end" font-family="{FONT}" font-size="11" '
        f'fill="{palette["note"]}">updated {stats["window_end"]}</text>\n'
        "</svg>\n"
    )


def main() -> int:
    if not TOKEN:
        log("No token found in PROFILE_TOKEN, GITHUB_TOKEN or GH_TOKEN.")
        return 1

    with open(README_PATH, encoding="utf-8") as handle:
        readme = handle.read()

    badges_re = block_re("BADGES")
    recent_re = block_re("RECENT")
    for name, pattern in (("BADGES", badges_re), ("RECENT", recent_re)):
        if not pattern.search(readme):
            log(f"README is missing the AUTO:{name} markers; refusing to write.")
            return 1

    repos = {badge["repo"] for badge in BADGES}
    repos.update(INLINE_RE.findall(readme))

    counts = {}
    for repo in sorted(repos):
        counts[repo] = merged_pr_count(repo)
        log(f"merged PRs in {repo}: {counts[repo]}")

    recent = recent_merged_prs(RECENT_LIMIT)
    log(f"recent merged PRs collected: {len(recent)}")

    stats = None
    try:
        stats = contribution_stats()
        log(
            "contributions: current streak {current}, longest {longest}, total {total}".format(
                **stats
            )
        )
    except Exception as error:  # noqa: BLE001 - the rest of the page still updates
        warn(f"contribution stats unavailable, keeping the existing streak card: {error}")

    readme = badges_re.sub(
        lambda match: f'{match.group("open")}\n{render_badges(counts)}\n{match.group("close")}',
        readme,
    )
    readme = recent_re.sub(
        lambda match: f'{match.group("open")}\n{render_recent(recent)}\n{match.group("close")}',
        readme,
    )
    readme = INLINE_RE.sub(
        lambda match: (
            f"<!--pr:{match.group('repo')}-->{counts[match.group('repo')]}<!--/pr-->"
        ),
        readme,
    )

    with open(README_PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(readme)
    log("README.md updated")

    if stats is not None:
        os.makedirs(ASSETS_DIR, exist_ok=True)
        for theme in THEMES:
            path = os.path.join(ASSETS_DIR, f"streak-{theme}.svg")
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(streak_svg(theme, stats))
            log(f"wrote {os.path.relpath(path, REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
