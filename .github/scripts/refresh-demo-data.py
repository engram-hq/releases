#!/usr/bin/env python3
"""Fetch skills and memories from GitHub repos into demo-data.json + demo-data.js.

Reads demo-sources.json for the list of repos to scan.
Uses GH_TOKEN env var for private repos, falls back to unauthenticated for public.
To add new data: edit demo-sources.json and re-run this script or the workflow.
"""
import json, os, sys, urllib.request, datetime


GH_TOKEN = os.environ.get("GH_TOKEN", "")


def fetch_raw(org, repo, path):
    """Fetch raw file content. Uses GitHub API with auth for private repos."""
    # Try authenticated API first (works for private repos)
    if GH_TOKEN:
        api_url = f"https://api.github.com/repos/{org}/{repo}/contents/{path}"
        req = urllib.request.Request(api_url, headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept": "application/vnd.github.raw+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8")
        except Exception:
            pass

    # Fallback: raw.githubusercontent.com (public repos only)
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

    auth_status = "authenticated" if GH_TOKEN else "unauthenticated (public repos only)"
    print(f"Mode: {auth_status}")

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

    # Also generate demo-data.js for instant script-tag loading (no fetch/CORS)
    compact = json.dumps(data, separators=(",", ":"))
    with open("demo-data.js", "w") as out:
        out.write(f"window.ENGRAM_DEMO_DATA={compact};")
    print(f"Wrote demo-data.js ({len(compact)} bytes)")


if __name__ == "__main__":
    main()
