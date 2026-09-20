import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

README = "README.md"
GITHUB_USER = "aman-singh-negi"
LEETCODE_USER = "amansinghnegi"
CODEFORCES_USER = "amansinghnegi"
CODECHEF_USER = "amansinghnegi0"

session = requests.Session()
session.headers.update({
    "User-Agent": "aman-singh-negi-github-profile-updater/1.0"
})


def get_codeforces():
    url = "https://codeforces.com/api/user.info"
    response = session.get(url, params={"handles": CODEFORCES_USER}, timeout=20)
    response.raise_for_status()
    payload = response.json()

    if payload.get("status") != "OK" or not payload.get("result"):
        raise RuntimeError("Codeforces profile unavailable")

    user = payload["result"][0]
    rating = user.get("rating", "Unrated")
    max_rating = user.get("maxRating", "—")
    rank = user.get("rank", "unrated")
    max_rank = user.get("maxRank", "unrated")

    return (
        f"**[{CODEFORCES_USER}](https://codeforces.com/profile/{CODEFORCES_USER})**  \n"
        f"Rating: **{rating}** • Max: **{max_rating}** • "
        f"Rank: **{rank}** • Max rank: **{max_rank}**"
    )


def get_leetcode():
    # LeetCode's public GraphQL endpoint is used for the public profile counters.
    query = """
    query userProfilePublicProfile($username: String!) {
      matchedUser(username: $username) {
        username
        profile {
          ranking
          reputation
        }
        submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    """

    response = session.post(
        "https://leetcode.com/graphql",
        json={"query": query, "variables": {"username": LEETCODE_USER}},
        headers={"Referer": f"https://leetcode.com/u/{LEETCODE_USER}/"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    user = data.get("data", {}).get("matchedUser")
    if not user:
        raise RuntimeError("LeetCode profile unavailable")

    counts = {
        item["difficulty"]: item["count"]
        for item in user.get("submitStatsGlobal", {}).get("acSubmissionNum", [])
    }

    total = counts.get("All", 0)
    easy = counts.get("Easy", 0)
    medium = counts.get("Medium", 0)
    hard = counts.get("Hard", 0)
    ranking = user.get("profile", {}).get("ranking")

    rank_text = f"{ranking:,}" if isinstance(ranking, int) else "—"

    return (
        f"**[{LEETCODE_USER}](https://leetcode.com/u/{LEETCODE_USER}/)**  \n"
        f"Solved: **{total}** • Easy: **{easy}** • Medium: **{medium}** • "
        f"Hard: **{hard}** • Rank: **{rank_text}**"
    )


def get_codechef():
    url = f"https://www.codechef.com/users/{CODECHEF_USER}"
    response = session.get(url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = " ".join(soup.stripped_strings)

    # CodeChef pages change their HTML frequently. We intentionally keep
    # extraction conservative and fall back gracefully when fields move.
    rating = None
    stars = None

    rating_match = re.search(r"\b(\d{3,5})\b", text)
    if rating_match:
        candidate = int(rating_match.group(1))
        if 100 <= candidate <= 5000:
            rating = candidate

    star_match = re.search(r"\b([1-7])\s*Star\b", text, re.I)
    if star_match:
        stars = star_match.group(1)

    parts = [f"**[{CODECHEF_USER}](https://www.codechef.com/users/{CODECHEF_USER})**"]

    if stars:
        parts.append(f"**{stars}★**")
    if rating:
        parts.append(f"Rating: **{rating}**")

    if len(parts) == 1:
        parts.append("Rating unavailable")

    return " • ".join(parts)





def replace_section(text, start_marker, end_marker, replacement):
    pattern = (
        re.escape(start_marker)
        + r".*?"
        + re.escape(end_marker)
    )
    block = f"{start_marker}\n{replacement}\n{end_marker}"
    updated, count = re.subn(pattern, block, text, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Could not update section: {start_marker}")
    return updated


def main():
    with open(README, "r", encoding="utf-8") as f:
        readme = f.read()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    try:
        leetcode = get_leetcode()
    except Exception as exc:
        leetcode = f"**[{LEETCODE_USER}](https://leetcode.com/u/{LEETCODE_USER}/)**  \nStats unavailable"
        print("LeetCode:", exc)

    try:
        codeforces = get_codeforces()
    except Exception as exc:
        codeforces = f"**[{CODEFORCES_USER}](https://codeforces.com/profile/{CODEFORCES_USER})**  \nStats unavailable"
        print("Codeforces:", exc)

    try:
        codechef = get_codechef()
    except Exception as exc:
        codechef = f"**[{CODECHEF_USER}](https://www.codechef.com/users/{CODECHEF_USER})**  \nStats unavailable"
        print("CodeChef:", exc)

    stats = f"""### 📈 Live Coding Progress

| Platform | Progress |
|---|---|
| 🟧 **LeetCode** | {leetcode} |
| 🔵 **Codeforces** | {codeforces} |
| 🟫 **CodeChef** | {codechef} |

> Last automated refresh: **{now}**"""

    readme = replace_section(readme, "<!-- STATS:START -->", "<!-- STATS:END -->", stats)

    with open(README, "w", encoding="utf-8") as f:
        f.write(readme)

    print("README updated successfully.")


if __name__ == "__main__":
    main()
