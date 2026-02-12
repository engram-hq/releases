#!/usr/bin/env python3
"""Fetch skills and memories from public GitHub repos into demo-data.json.

Reads demo-sources.json for the list of repos to scan.
All fetches use raw.githubusercontent.com (no auth, no rate limit).
To add new data: edit demo-sources.json and re-run this script or the workflow.
"""
import json, os, sys, urllib.request, datetime


def fetch_raw(org, repo, path):
    """Fetch raw file from public repo (no auth needed)."""
    url = f"https://raw.githubusercontent.com/{org}/{repo}/main/{path}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  WARN: {org}/{repo}/{path} -> {e}", file=sys.stderr)
        return None


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sources_path = os.path.join(script_dir, "..", "..", "demo-sources.json")
    with open(sources_path) as f:
        sources = json.load(f)

    data = {
        "skills": [],
        "memories": [],
        "generated_at": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
            print(f"  SKIP: {org}/{repo}/{path}")

    # Fetch memories
    for m in sources.get("memories", []):
        org, path = m["org"], m["path"]
        content = fetch_raw(org, ".memory", path)
        if content:
            data["memories"].append({
                "org": org, "repo": ".memory",
                "path": path, "name": os.path.basename(path),
                "content": content,
            })
            print(f"  Memory: {org}/.memory/{path} ({len(content)} bytes)")
        else:
            print(f"  SKIP: {org}/.memory/{path}")

    print(f"\nTotal: {len(data['skills'])} skills, {len(data['memories'])} memories")
    if not data["skills"] and not data["memories"]:
        print("ERROR: No data fetched", file=sys.stderr)
        sys.exit(1)

    with open("demo-data.json", "w") as out:
        json.dump(data, out, indent=2)
    print("Wrote demo-data.json")


if __name__ == "__main__":
    main()
