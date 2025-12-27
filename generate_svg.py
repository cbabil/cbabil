#!/usr/bin/env python3
"""Generate neofetch-style SVG for GitHub profile."""

import os
import json
import datetime
from urllib.request import Request, urlopen

# GitHub API token from environment
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = "cbabil"

# Floppy disk ASCII art (old school MS-DOS style) - wider version
ASCII_ART = [
    " _____________________________________.    ",
    "|;;|                             |;;||     ",
    "|[]|-----------------------------|[]||     ",
    "|;;|                             |;;||     ",
    "|;;|                             |;;||     ",
    "|;;|                             |;;||     ",
    "|;;|                             |;;||     ",
    "|;;|                             |;;||     ",
    "|;;|                             |;;||     ",
    "|;;|_____________________________|;;||     ",
    "|;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;||     ",
    "|;;;;;;;;___________________;;;;;;;;||     ",
    "|;;;;;;;|  _____            |;;;;;;;||     ",
    "|;;;;;;;| |;;;;;|           |;;;;;;;||     ",
    "|;;;;;;;| |;;;;;|           |;;;;;;;||     ",
    "|;;;;;;;| |;;;;;|           |;;;;;;;||     ",
    "|;;;;;;;| |;;;;;|           |;;;;;;;||     ",
    "|;;;;;;;| |_____|           |;;;;;;;||     ",
    "\\________|___________________|______||     ",
    " ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^~~~~~~~~     ",
]


def graphql_query(query: str) -> dict:
    """Execute a GraphQL query against GitHub API."""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }
    data = json.dumps({"query": query}).encode("utf-8")
    req = Request("https://api.github.com/graphql", data=data, headers=headers)
    with urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def get_user_stats() -> dict:
    """Fetch user statistics from GitHub API."""
    query = """
    {
      user(login: "%s") {
        name
        login
        createdAt
        repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
          totalCount
          nodes {
            stargazerCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                  color
                }
              }
            }
          }
        }
        followers {
          totalCount
        }
        following {
          totalCount
        }
        pullRequests {
          totalCount
        }
        issues {
          totalCount
        }
        gists {
          totalCount
        }
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
        }
      }
    }
    """ % USERNAME

    result = graphql_query(query)
    user = result.get("data", {}).get("user", {})

    # Calculate account age
    created_at = datetime.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    age = now - created_at
    years = age.days // 365
    months = (age.days % 365) // 30
    days = (age.days % 365) % 30

    # Calculate total stars
    repos = user.get("repositories", {}).get("nodes", [])
    total_stars = sum(repo.get("stargazerCount", 0) for repo in repos)

    # Calculate language breakdown
    language_sizes: dict[str, int] = {}
    language_colors: dict[str, str] = {}
    for repo in repos:
        for edge in repo.get("languages", {}).get("edges", []):
            lang_name = edge["node"]["name"]
            lang_size = edge["size"]
            lang_color = edge["node"].get("color", "#8b949e")
            language_sizes[lang_name] = language_sizes.get(lang_name, 0) + lang_size
            if lang_name not in language_colors:
                language_colors[lang_name] = lang_color

    # Sort languages by size and get top 5
    sorted_langs = sorted(language_sizes.items(), key=lambda x: x[1], reverse=True)[:5]
    total_size = sum(size for _, size in sorted_langs)
    languages = [
        {
            "name": name,
            "percent": round((size / total_size) * 100, 1) if total_size > 0 else 0,
            "color": language_colors.get(name, "#8b949e"),
        }
        for name, size in sorted_langs
    ]

    contributions = user.get("contributionsCollection", {})
    total_commits = (
        contributions.get("totalCommitContributions", 0)
        + contributions.get("restrictedContributionsCount", 0)
    )

    # Get top language
    top_lang = languages[0]["name"] if languages else "Unknown"

    return {
        "name": user.get("name") or user.get("login", USERNAME),
        "login": user.get("login", USERNAME),
        "uptime": f"{years} years, {months} months, {days} days",
        "repos": user.get("repositories", {}).get("totalCount", 0),
        "followers": user.get("followers", {}).get("totalCount", 0),
        "following": user.get("following", {}).get("totalCount", 0),
        "stars": total_stars,
        "commits": total_commits,
        "prs": user.get("pullRequests", {}).get("totalCount", 0),
        "issues": user.get("issues", {}).get("totalCount", 0),
        "gists": user.get("gists", {}).get("totalCount", 0),
        "top_lang": top_lang,
        "languages": languages,
    }


def generate_svg(stats: dict, mode: str = "dark") -> str:
    """Generate neofetch-style SVG content."""

    if mode == "dark":
        bg = "#161b22"
        title_color = "#58a6ff"
        key_color = "#ffa657"
        value_color = "#a5d6ff"
        comment_color = "#6e7681"
        ascii_color = "#58a6ff"
    else:
        bg = "#ffffff"
        title_color = "#0969da"
        key_color = "#953800"
        value_color = "#0550ae"
        comment_color = "#6e7681"
        ascii_color = "#0969da"

    # Build ASCII art
    ascii_lines = ""
    for i, line in enumerate(ASCII_ART):
        y = 30 + (i * 18)
        ascii_lines += f'    <tspan x="20" y="{y}">{line}</tspan>\n'

    # Create dotted lines (neofetch style)
    def make_line(key: str, value: str, total_width: int = 55) -> str:
        dots = "." * (total_width - len(key) - len(str(value)) - 2)
        return f'<tspan class="key">{key}</tspan><tspan class="dot">:</tspan><tspan class="dot">{dots}</tspan><tspan class="val">{value}</tspan>'

    divider = "─" * 55

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="390" viewBox="0 0 800 390">
  <style>
    text {{
      font-family: 'Consolas', 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 14px;
      white-space: pre;
    }}
    .title {{ fill: {title_color}; font-weight: bold; }}
    .key {{ fill: {key_color}; }}
    .val {{ fill: {value_color}; }}
    .dot {{ fill: {comment_color}; }}
    .ascii {{ fill: {ascii_color}; font-size: 12px; }}
  </style>

  <!-- Background -->
  <rect width="800" height="390" fill="{bg}"/>

  <!-- ASCII Art -->
  <text class="ascii">
{ascii_lines}  </text>

  <!-- Title -->
  <text x="340" y="30" class="title">{stats['login']}@github</text>
  <text x="340" y="48" class="dot">{divider}</text>

  <!-- System Info -->
  <text x="340" y="75">{make_line("OS", "GitHub")}</text>
  <text x="340" y="95">{make_line("Host", "github.com/" + stats['login'])}</text>
  <text x="340" y="115">{make_line("Uptime", stats['uptime'])}</text>

  <text x="340" y="145" class="dot">{divider}</text>

  <!-- GitHub Stats -->
  <text x="340" y="170">{make_line("Repos", str(stats['repos']))}</text>
  <text x="340" y="190">{make_line("Commits", str(stats['commits']))}</text>
  <text x="340" y="210">{make_line("Stars", str(stats['stars']))}</text>
  <text x="340" y="230">{make_line("Followers", str(stats['followers']))}</text>

  <text x="340" y="260" class="dot">{divider}</text>

  <!-- More GitHub Stats -->
  <text x="340" y="285">{make_line("PRs", str(stats['prs']))}</text>
  <text x="340" y="305">{make_line("Issues", str(stats['issues']))}</text>
  <text x="340" y="325">{make_line("Gists", str(stats['gists']))}</text>
  <text x="340" y="345">{make_line("Following", str(stats['following']))}</text>
  <text x="340" y="365">{make_line("Top Lang", stats['top_lang'])}</text>

</svg>'''

    return svg


def main():
    """Generate both dark and light mode SVGs."""
    print("Fetching GitHub stats...")
    stats = get_user_stats()
    print(f"Stats: {stats}")

    print("Generating dark mode SVG...")
    dark_svg = generate_svg(stats, "dark")
    with open("dark_mode.svg", "w") as f:
        f.write(dark_svg)

    print("Generating light mode SVG...")
    light_svg = generate_svg(stats, "light")
    with open("light_mode.svg", "w") as f:
        f.write(light_svg)

    print("Done!")


if __name__ == "__main__":
    main()
