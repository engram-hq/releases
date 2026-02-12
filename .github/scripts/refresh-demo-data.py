#!/usr/bin/env python3
"""Fetch skills and memories from GitHub and write demo-data.json."""
import json, os, sys, urllib.request, datetime

TOKEN = os.environ.get("GH_TOKEN", "")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if TOKEN:
    HEADERS["Authorization"] = f"token {TOKEN}"

SKILL_SOURCES = [
    ("engram-hq", ".skills", 2, "org-knowledge/SKILL.md"),
    ("sreniatnoc", ".skills", 2, "org-knowledge/SKILL.md"),
    ("sreniatnoc", "rusd", 3, ".skills/kind-validation.md"),
]

MEMORY_ORGS = ["engram-hq", "sreniatnoc"]


def fetch(url):
    """Fetch URL with auth token, return text or None."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  WARN: {url} -> {e}", file=sys.stderr)
        return None


def fetch_json(url):
    """Fetch URL and parse as JSON."""
    text = fetch(url)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def main():
    data = {
        "skills": [],
        "memories": [],
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    # Fetch skills
    for org, repo, tier, path in SKILL_SOURCES:
        raw_url = f"https://raw.githubusercontent.com/{org}/{repo}/main/{path}"
        content = fetch(raw_url)
        if content and "404" not in content[:20]:
            data["skills"].append({
                "org": org, "repo": repo, "tier": tier,
                "path": path, "name": os.path.basename(path),
                "content": content,
            })
            print(f"  Skill: {org}/{repo}/{path} ({len(content)} bytes)")
        else:
            print(f"  SKIP skill: {org}/{repo}/{path}")

    # Fetch memories
    for org in MEMORY_ORGS:
        api_url = f"https://api.github.com/repos/{org}/.memory/contents/sessions"
        files = fetch_json(api_url)
        if not files or not isinstance(files, list):
            print(f"  SKIP memory org: {org} (no sessions dir)")
            continue

        for f in files:
            name = f.get("name", "")
            if not name.endswith(".md") or name == "README.md":
                continue
            path = f"sessions/{name}"
            raw_url = f"https://raw.githubusercontent.com/{org}/.memory/main/{path}"
            content = fetch(raw_url)
            if content and "404" not in content[:20]:
                data["memories"].append({
                    "org": org, "repo": ".memory",
                    "path": path, "name": name,
                    "content": content,
                })
                print(f"  Memory: {org}/.memory/{path} ({len(content)} bytes)")

    # Validate
    print(f"\nTotal: {len(data['skills'])} skills, {len(data['memories'])} memories")
    if not data["skills"]:
        print("ERROR: No skills fetched", file=sys.stderr)
        sys.exit(1)
    if not data["memories"]:
        print("ERROR: No memories fetched", file=sys.stderr)
        sys.exit(1)

    # Write output
    with open("demo-data.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Wrote demo-data.json")


if __name__ == "__main__":
    main()
