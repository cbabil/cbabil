#!/usr/bin/env python3
"""Generate neofetch-style SVG for GitHub profile."""

import os
import json
import datetime
from urllib.request import Request, urlopen

# GitHub API token from environment
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = "cbabil"

# Colors
COLORS = {
    "dark": {
        "bg": "#0d1117",
        "fg": "#c9d1d9",
        "accent": "#70a5fd",
        "secondary": "#8b949e",
        "purple": "#bf91f3",
        "green": "#3fb950",
        "yellow": "#d29922",
        "red": "#f85149",
    },
    "light": {
        "bg": "#ffffff",
        "fg": "#24292f",
        "accent": "#0969da",
        "secondary": "#57606a",
        "purple": "#8250df",
        "green": "#1a7f37",
        "yellow": "#9a6700",
        "red": "#cf222e",
    },
}

# ASCII art
ASCII_ART = r"""
   _____ ____  ____ _____ _____ _
  / ____/ __ \|  _ \_   _|  __ \ |
 | |   | |  | | |_) || | | |__) | |
 | |   | |  | |  _ < | | |  ___/| |
 | |___| |__| | |_) || |_| |    | |____
  \_____\____/|____/_____|_|    |______|
"""


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

    return {
        "name": user.get("name") or user.get("login", USERNAME),
        "login": user.get("login", USERNAME),
        "uptime": f"{years}y {months}m" if years > 0 else f"{months}m",
        "repos": user.get("repositories", {}).get("totalCount", 0),
        "followers": user.get("followers", {}).get("totalCount", 0),
        "stars": total_stars,
        "commits": total_commits,
        "languages": languages,
    }


def generate_svg(stats: dict, mode: str = "dark") -> str:
    """Generate SVG content."""
    colors = COLORS[mode]

    # Build language bars
    lang_bars = ""
    for i, lang in enumerate(stats["languages"]):
        bar_width = int(lang["percent"] * 1.5)  # Scale to fit
        y_pos = 195 + (i * 22)
        lang_bars += f"""
    <text x="230" y="{y_pos}" fill="{colors['secondary']}" font-size="12">{lang['name']}</text>
    <rect x="320" y="{y_pos - 10}" width="{bar_width}" height="12" fill="{lang['color']}" rx="2"/>
    <text x="{325 + bar_width}" y="{y_pos}" fill="{colors['secondary']}" font-size="11">{lang['percent']}%</text>
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="340" viewBox="0 0 600 340">
  <style>
    .mono {{ font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace; }}
    .ascii {{ font-family: monospace; font-size: 10px; white-space: pre; }}
  </style>

  <!-- Background -->
  <rect width="600" height="340" fill="{colors['bg']}" rx="10"/>

  <!-- Terminal header -->
  <rect width="600" height="30" fill="{colors['bg']}" rx="10"/>
  <circle cx="20" cy="15" r="6" fill="{colors['red']}"/>
  <circle cx="40" cy="15" r="6" fill="{colors['yellow']}"/>
  <circle cx="60" cy="15" r="6" fill="{colors['green']}"/>
  <text x="300" y="20" text-anchor="middle" fill="{colors['secondary']}" class="mono" font-size="12">cbabil@github</text>

  <!-- ASCII Art -->
  <text x="20" y="55" fill="{colors['accent']}" class="ascii">
    <tspan x="20" dy="0">   _____ ____  ____ _____ _____ _</tspan>
    <tspan x="20" dy="12">  / ____| __ )|  _ \\_   _|  __ \\ |</tspan>
    <tspan x="20" dy="12"> | |   |  _ \\| |_) || | | |__) | |</tspan>
    <tspan x="20" dy="12"> | |   | |_) |  _ &lt; | | |  ___/| |</tspan>
    <tspan x="20" dy="12"> | |___| |__/| |_) || |_| |    | |____</tspan>
    <tspan x="20" dy="12">  \\_____\\____/|____/_____|_|    |______|</tspan>
  </text>

  <!-- User info -->
  <text x="230" y="55" fill="{colors['accent']}" class="mono" font-size="14" font-weight="bold">{stats['login']}@github</text>
  <line x1="230" y1="62" x2="400" y2="62" stroke="{colors['secondary']}" stroke-width="1"/>

  <text x="230" y="82" fill="{colors['purple']}" class="mono" font-size="12">name</text>
  <text x="290" y="82" fill="{colors['fg']}" class="mono" font-size="12">{stats['name']}</text>

  <text x="230" y="102" fill="{colors['purple']}" class="mono" font-size="12">uptime</text>
  <text x="290" y="102" fill="{colors['fg']}" class="mono" font-size="12">{stats['uptime']}</text>

  <text x="230" y="122" fill="{colors['purple']}" class="mono" font-size="12">repos</text>
  <text x="290" y="122" fill="{colors['fg']}" class="mono" font-size="12">{stats['repos']}</text>

  <text x="230" y="142" fill="{colors['purple']}" class="mono" font-size="12">commits</text>
  <text x="290" y="142" fill="{colors['fg']}" class="mono" font-size="12">{stats['commits']}</text>

  <text x="370" y="82" fill="{colors['purple']}" class="mono" font-size="12">stars</text>
  <text x="430" y="82" fill="{colors['fg']}" class="mono" font-size="12">{stats['stars']}</text>

  <text x="370" y="102" fill="{colors['purple']}" class="mono" font-size="12">followers</text>
  <text x="430" y="102" fill="{colors['fg']}" class="mono" font-size="12">{stats['followers']}</text>

  <!-- Languages section -->
  <text x="230" y="172" fill="{colors['accent']}" class="mono" font-size="12" font-weight="bold">languages</text>
  <line x1="230" y1="179" x2="400" y2="179" stroke="{colors['secondary']}" stroke-width="1"/>

{lang_bars}

  <!-- Footer -->
  <text x="20" y="320" fill="{colors['secondary']}" class="mono" font-size="10">Building developer tools | Open source enthusiast</text>
  <text x="580" y="320" text-anchor="end" fill="{colors['secondary']}" class="mono" font-size="10">Updated: {datetime.datetime.now().strftime('%Y-%m-%d')}</text>
</svg>"""

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
