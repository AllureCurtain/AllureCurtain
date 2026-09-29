#!/usr/bin/env python3
"""Regenerate the auto-managed surfaces of this profile README.

The script only ever writes three things, all of them derived from the GitHub
API, and it touches nothing else in the repository:

  1. ``{{pr_count:owner/repo}}`` tokens -> merged pull requests authored by
     ``USER`` in that repository.
  2. The block between ``<!-- BEGIN:AUTO:RECENT -->`` and
     ``<!-- END:AUTO:RECENT -->`` -> the most recently merged pull requests.
  3. ``assets/streak-light.svg`` and ``assets/streak-dark.svg`` -> current
     streak, longest streak and the last twelve months of contributions.

All remote data is fetched before anything is written, so a failed request
leaves the working tree untouched instead of committing a half-updated page.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

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

PR_TOKEN_RE = re.compile(r"\{\{pr_count:([^}]+)\}\}")
RECENT_RE = re.compile(
    r"(?P<open><!-- BEGIN:AUTO:RECENT -->)(?P<body>.*?)(?P<close><!-- END:AUTO:RECENT -->)",
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
        {
            "q": f"repo:{repo} type:pr author:{USER} is:merged",
            "per_page": 1,
        },
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
        merged_at = item.get("closed_at") or item.get("updated_at") or ""
        items.append(
            {
                "repo": repo,
                "title": item.get("title", "").strip(),
                "url": item.get("html_url", ""),
                "date": merged_at[:10],
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
    days = [
        (day["date"], int(day["contributionCount"]))
        for week in calendar["weeks"]
        for day in week["contributionDays"]
    ]
    days.sort(key=lambda entry: entry[0])

    longest = run = 0
    for _, count in days:
        run = run + 1 if count > 0 else 0
        longest = max(longest, run)

    # An empty today does not break a streak that is still alive yesterday.
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

    counts: dict[str, int] = {}
    for repo in sorted(set(PR_TOKEN_RE.findall(readme))):
        counts[repo] = merged_pr_count(repo)
        log(f"merged PRs in {repo}: {counts[repo]}")

    recent = recent_merged_prs(RECENT_LIMIT)
    log(f"recent merged PRs collected: {len(recent)}")

    stats: dict | None = None
    try:
        stats = contribution_stats()
        log(
            "contributions: current streak {current}, longest {longest}, "
            "total {total}".format(**stats)
        )
    except Exception as error:  # noqa: BLE001 - the rest of the page still updates
        warn(f"contribution stats unavailable, keeping the existing streak card: {error}")

    if not RECENT_RE.search(readme):
        log("README is missing the AUTO:RECENT markers; refusing to write.")
        return 1

    readme = PR_TOKEN_RE.sub(lambda match: str(counts[match.group(1)]), readme)
    readme = RECENT_RE.sub(
        lambda match: match.group("open") + "\n" + render_recent(recent) + "\n" + match.group("close"),
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
