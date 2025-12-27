#!/usr/bin/env python3
"""Generate neofetch-style SVG for GitHub profile."""

import os
import json
import datetime
from urllib.request import Request, urlopen

# GitHub API token from environment
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = "cbabil"

# Neofetch-style colors
COLORS = {
    "dark": {
        "bg": "#161b22",
        "fg": "#c9d1d9",
        "key": "#ffa657",      # Orange for keys
        "value": "#a5d6ff",    # Light blue for values
        "comment": "#6e7681",  # Gray for comments/dots
        "title": "#58a6ff",    # Blue for title
        "green": "#3fb950",
        "yellow": "#d29922",
        "red": "#f85149",
        "cyan": "#39c5cf",
        "purple": "#bc8cff",
        "white": "#ffffff",
    },
    "light": {
        "bg": "#ffffff",
        "fg": "#24292f",
        "key": "#953800",
        "value": "#0550ae",
        "comment": "#6e7681",
        "title": "#0969da",
        "green": "#1a7f37",
        "yellow": "#9a6700",
        "red": "#cf222e",
        "cyan": "#1b7c83",
        "purple": "#8250df",
        "white": "#24292f",
    },
}

# GitHub Octocat ASCII art
ASCII_ART = [
    "                                     ",
    "              ████████               ",
    "          ████▒▒▒▒▒▒▒▒████           ",
    "        ██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒██         ",
    "      ██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒██       ",
    "    ██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒██     ",
    "    ██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒██     ",
    "  ██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒██   ",
    "  ██▒▒▒▒▒▒▒▒████▒▒▒▒████▒▒▒▒▒▒▒▒██   ",
    "  ██▒▒▒▒▒▒▒▒████▒▒▒▒████▒▒▒▒▒▒▒▒██   ",
    "  ██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒██   ",
    "  ██▒▒▒▒▒▒▒▒▒▒▒▒████▒▒▒▒▒▒▒▒▒▒▒▒██   ",
    "    ██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒██     ",
    "    ██▒▒▒▒██▒▒▒▒▒▒▒▒▒▒▒▒██▒▒▒▒██     ",
    "      ██▒▒▒▒████████████▒▒▒▒██       ",
    "        ██▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒██         ",
    "          ████▒▒▒▒▒▒▒▒████           ",
    "              ████████               ",
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
    days = age.days

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
        "uptime": f"{days} days ({years}y {months}m)",
        "repos": user.get("repositories", {}).get("totalCount", 0),
        "followers": user.get("followers", {}).get("totalCount", 0),
        "stars": total_stars,
        "commits": total_commits,
        "languages": languages,
    }


def generate_svg(stats: dict, mode: str = "dark") -> str:
    """Generate neofetch-style SVG content."""
    c = COLORS[mode]

    # Build ASCII art lines
    ascii_lines = ""
    for i, line in enumerate(ASCII_ART):
        y = 45 + (i * 16)
        # Escape special characters for SVG
        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        ascii_lines += f'    <tspan x="20" y="{y}">{escaped}</tspan>\n'

    # Format languages as comma-separated list
    lang_list = ", ".join([f"{l['name']} ({l['percent']}%)" for l in stats["languages"][:4]])

    # Create info lines with dots for alignment (neofetch style)
    def info_line(key: str, value: str, dots: int = 20) -> str:
        dot_count = dots - len(key)
        dots_str = "." * max(dot_count, 2)
        return f'<tspan fill="{c["key"]}">{key}</tspan><tspan fill="{c["comment"]}">{dots_str}</tspan><tspan fill="{c["value"]}">{value}</tspan>'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="850" height="380" viewBox="0 0 850 380">
  <style>
    text {{
      font-family: 'Consolas', 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      font-size: 14px;
      white-space: pre;
    }}
  </style>

  <!-- Background -->
  <rect width="850" height="380" fill="{c['bg']}"/>

  <!-- ASCII Art (Octocat) -->
  <text fill="{c['title']}">
{ascii_lines}  </text>

  <!-- User title -->
  <text x="340" y="45" fill="{c['title']}" font-weight="bold">{stats['login']}@github</text>
  <text x="340" y="61" fill="{c['comment']}">─────────────────────────────────</text>

  <!-- System info -->
  <text x="340" y="85">{info_line("OS", "GitHub")}</text>
  <text x="340" y="105">{info_line("Host", "github.com/" + stats['login'])}</text>
  <text x="340" y="125">{info_line("Uptime", stats['uptime'])}</text>
  <text x="340" y="145">{info_line("Repos", str(stats['repos']))}</text>
  <text x="340" y="165">{info_line("Commits", str(stats['commits']))}</text>
  <text x="340" y="185">{info_line("Stars", str(stats['stars']))}</text>
  <text x="340" y="205">{info_line("Followers", str(stats['followers']))}</text>

  <!-- Languages -->
  <text x="340" y="235" fill="{c['comment']}">─────────────────────────────────</text>
  <text x="340" y="255">{info_line("Languages", lang_list)}</text>

  <!-- Color blocks (terminal palette) -->
  <text x="340" y="285" fill="{c['comment']}">─────────────────────────────────</text>
  <rect x="340" y="295" width="30" height="20" fill="#24292f"/>
  <rect x="375" y="295" width="30" height="20" fill="{c['red']}"/>
  <rect x="410" y="295" width="30" height="20" fill="{c['green']}"/>
  <rect x="445" y="295" width="30" height="20" fill="{c['yellow']}"/>
  <rect x="480" y="295" width="30" height="20" fill="{c['title']}"/>
  <rect x="515" y="295" width="30" height="20" fill="{c['purple']}"/>
  <rect x="550" y="295" width="30" height="20" fill="{c['cyan']}"/>
  <rect x="585" y="295" width="30" height="20" fill="{c['white']}"/>

  <rect x="340" y="320" width="30" height="20" fill="#6e7681"/>
  <rect x="375" y="320" width="30" height="20" fill="#ff7b72"/>
  <rect x="410" y="320" width="30" height="20" fill="#7ee787"/>
  <rect x="445" y="320" width="30" height="20" fill="#ffa657"/>
  <rect x="480" y="320" width="30" height="20" fill="#79c0ff"/>
  <rect x="515" y="320" width="30" height="20" fill="#d2a8ff"/>
  <rect x="550" y="320" width="30" height="20" fill="#a5d6ff"/>
  <rect x="585" y="320" width="30" height="20" fill="#f0f6fc"/>

  <!-- Footer -->
  <text x="700" y="365" fill="{c['comment']}" font-size="11">Updated: {datetime.datetime.now().strftime('%Y-%m-%d')}</text>
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
