#!/usr/bin/env python3
"""Fetch skills and memories from public GitHub repos into demo-data.json.

Reads demo-sources.json for the list of repos to scan.
No auth needed for public repos - raw.githubusercontent.com has no rate limit.
Optional GH_TOKEN env var adds auth to API calls only (5000 req/hr vs 60).
"""
import json, os, sys, urllib.request, datetime

TOKEN = os.environ.get("GH_TOKEN", "")


def fetch_raw(org, repo, path):
    """Fetch raw file from public repo (no auth needed)."""
    url = f"https://raw.githubusercontent.com/{org}/{repo}/main/{path}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  WARN raw: {org}/{repo}/{path} -> {e}", file=sys.stderr)
        return None


def fetch_api(path):
    """Fetch from GitHub API (optional auth for rate limits)."""
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  WARN api: {path} -> {e}", file=sys.stderr)
        return None


def main():
    # Load configurable sources
    sources_path = os.path.join(os.path.dirname(__file__), "..", "..", "demo-sources.json")
    with open(sources_path) as f:
        sources = json.load(f)

    data = {
        "skills": [],
        "memories": [],
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    # Fetch skills
    for s in sources.get("skills", []):
        org, repo, tier, path = s["org"], s["repo"], s["tier"], s["path"]
        content = fetch_raw(org, repo, path)
        if content:
            data["skills"].append({
                "org": org, "repo": repo, "tier": tier,
                "path": path, "name": os.path.basename(path),
                "content": content,
            })
            print(f"  Skill: {org}/{repo}/{path} ({len(content)} bytes)")
        else:
            print(f"  SKIP skill: {org}/{repo}/{path}")

    # Fetch memories
    for m in sources.get("memory_orgs", []):
        org = m["org"]
        files = fetch_api(f"/repos/{org}/.memory/contents/sessions")
        if not files or not isinstance(files, list):
            print(f"  SKIP memory: {org} (no sessions dir)")
            continue

        for f in sorted(files, key=lambda x: x.get("name", "")):
            name = f.get("name", "")
            if not name.endswith(".md") or name == "README.md":
                continue
            path = f"sessions/{name}"
            content = fetch_raw(org, ".memory", path)
            if content:
                data["memories"].append({
                    "org": org, "repo": ".memory",
                    "path": path, "name": name,
                    "content": content,
                })
                print(f"  Memory: {org}/.memory/{path} ({len(content)} bytes)")

    # Summary
    print(f"\nTotal: {len(data['skills'])} skills, {len(data['memories'])} memories")
    if not data["skills"]:
        print("ERROR: No skills fetched", file=sys.stderr)
        sys.exit(1)
    if not data["memories"]:
        print("ERROR: No memories fetched", file=sys.stderr)
        sys.exit(1)

    with open("demo-data.json", "w") as out:
        json.dump(data, out, indent=2)
    print("Wrote demo-data.json")


if __name__ == "__main__":
    main()
