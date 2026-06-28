import os
import re
import json
import urllib.request
import urllib.error

TOKEN = os.environ.get('METRICS_TOKEN')
README_PATH = 'README.md'

def make_request(url):
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'token {TOKEN}')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    req.add_header('User-Agent', 'Antigravity-Agent')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error for {url}: {e.code} {e.reason}")
        return None
    except Exception as e:
        print(f"Request Error for {url}: {e}")
        return None

def format_number(num):
    if num >= 1000:
        return f"{num/1000:.1f}K+"
    return str(num)

def main():
    if not TOKEN:
        print("Error: METRICS_TOKEN env variable not set.")
        return

    print("Fetching authenticated user info...")
    user_info = make_request("https://api.github.com/user")
    if not user_info:
        print("Auth failed.")
        return

    username = user_info.get('login')
    print(f"User: {username}")

    print("Fetching public repos...")
    repos = make_request("https://api.github.com/user/repos?visibility=public&affiliation=owner")
    if not repos:
        print("No repos found.")
        return

    total_stars = 0
    total_views = 0
    total_clones = 0

    for repo in repos:
        repo_full_name = repo.get('full_name')
        total_stars += repo.get('stargazers_count', 0)
        
        print(f"Fetching traffic for {repo_full_name}...")
        
        # Views
        views_data = make_request(f"https://api.github.com/repos/{repo_full_name}/traffic/views")
        if views_data:
            total_views += views_data.get('count', 0)
            
        # Clones
        clones_data = make_request(f"https://api.github.com/repos/{repo_full_name}/traffic/clones")
        if clones_data:
            total_clones += clones_data.get('count', 0)

    print(f"Totals -> Stars: {total_stars}, Views: {total_views}, Clones: {total_clones}")

    clones_str = format_number(total_clones)
    views_str = format_number(total_views)

    # Read README
    with open(README_PATH, 'r') as f:
        content = f.read()

    # Generate new badges section
    badges_section = (
        f'<img src="https://img.shields.io/badge/Stars-⭐_{total_stars}-yellow?style=flat-square" alt="Stars" />\n'
        f'&nbsp;\n'
        f'<img src="https://img.shields.io/badge/Clones-📥_{clones_str}-10B981?style=flat-square" alt="Clones" />\n'
        f'&nbsp;\n'
        f'<img src="https://img.shields.io/badge/Views-📈_{views_str}-6366f1?style=flat-square" alt="Views" />'
    )

    pattern = r'(<!-- STATS_BADGES_START -->\n)(.*?)(\n<!-- STATS_BADGES_END -->)'
    new_content = re.sub(pattern, f'\\1{badges_section}\\3', content, flags=re.DOTALL)

    # Write updated README
    with open(README_PATH, 'w') as f:
        f.write(new_content)

    print("README.md updated successfully.")

if __name__ == "__main__":
    main()
