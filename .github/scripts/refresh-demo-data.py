#!/usr/bin/env python3
"""Fetch skills and memories from GitHub repos into demo-data.json + demo-data.js.

Merge strategy: fetched data is merged with existing demo-data.json.
- Successfully fetched items replace their existing counterparts (content refresh).
- Items that fail to fetch (404, timeout, auth) are kept from existing data.
- New items in demo-sources.json that fetch successfully are added.
- Items removed from demo-sources.json are dropped.
This ensures data is always the latest available and never lost due to partial failures.

Uses GH_TOKEN env var for private repos, falls back to unauthenticated for public.
To add new data: edit demo-sources.json and re-run this script or the workflow.
"""
import json, os, sys, urllib.request, datetime


GH_TOKEN = os.environ.get("GH_TOKEN", "")


def fetch_raw(org, repo, path):
    """Fetch raw file content. Uses GitHub API with auth for private repos."""
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


def load_existing():
    """Load existing demo-data.json as lookup dicts keyed by org/repo/path."""
    if not os.path.exists("demo-data.json"):
        return {}, {}
    with open("demo-data.json") as f:
        data = json.load(f)
    skills = {}
    for s in data.get("skills", []):
        key = f"{s['org']}/{s['repo']}/{s['path']}"
        skills[key] = s
    memories = {}
    for m in data.get("memories", []):
        key = f"{m['org']}/{m['repo']}/{m['path']}"
        memories[key] = m
    return skills, memories


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sources_path = os.path.join(script_dir, "..", "..", "demo-sources.json")
    with open(sources_path) as f:
        sources = json.load(f)

    existing_skills, existing_memories = load_existing()

    auth_status = "authenticated" if GH_TOKEN else "unauthenticated (public repos only)"
    print(f"Mode: {auth_status}")
    if existing_skills or existing_memories:
        print(f"Existing data: {len(existing_skills)} skills, {len(existing_memories)} memories")

    skills = []
    fetched, cached, failed = 0, 0, 0

    for s in sources.get("skills", []):
        org, repo, tier, path = s["org"], s["repo"], s["tier"], s["path"]
        key = f"{org}/{repo}/{path}"
        content = fetch_raw(org, repo, path)
        if content:
            skills.append({
                "org": org, "repo": repo, "tier": tier,
                "path": path, "name": os.path.basename(path),
                "content": content,
            })
            fetched += 1
            print(f"  OK    {key} ({len(content)} bytes)")
        elif key in existing_skills:
            # Keep existing content on fetch failure
            skills.append(existing_skills[key])
            cached += 1
            print(f"  CACHE {key} (kept from existing data)")
        else:
            failed += 1
            print(f"  MISS  {key} (no existing data to fall back on)")

    memories = []
    mem_fetched, mem_cached, mem_failed = 0, 0, 0

    for m in sources.get("memories", []):
        org, path = m["org"], m["path"]
        mem_repo = ".memory"
        key = f"{org}/{mem_repo}/{path}"
        content = fetch_raw(org, mem_repo, path)
        if content:
            memories.append({
                "org": org, "repo": mem_repo,
                "path": path, "name": os.path.basename(path),
                "content": content,
            })
            mem_fetched += 1
            print(f"  OK    {key} ({len(content)} bytes)")
        elif key in existing_memories:
            memories.append(existing_memories[key])
            mem_cached += 1
            print(f"  CACHE {key} (kept from existing data)")
        else:
            mem_failed += 1
            print(f"  MISS  {key} (no existing data to fall back on)")

    total_skills = len(skills)
    total_memories = len(memories)
    print(f"\nSkills:   {fetched} fetched, {cached} cached, {failed} failed -> {total_skills} total")
    print(f"Memories: {mem_fetched} fetched, {mem_cached} cached, {mem_failed} failed -> {total_memories} total")

    if not skills and not memories:
        print("ERROR: No data at all (fetched or cached)", file=sys.stderr)
        sys.exit(1)

    data = {
        "skills": skills,
        "memories": memories,
        "generated_at": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stats": {
            "skills_fetched": fetched, "skills_cached": cached, "skills_failed": failed,
            "memories_fetched": mem_fetched, "memories_cached": mem_cached, "memories_failed": mem_failed,
        },
    }

    with open("demo-data.json", "w") as out:
        json.dump(data, out, indent=2)
    print("Wrote demo-data.json")

    compact = json.dumps(data, separators=(",", ":"))
    with open("demo-data.js", "w") as out:
        out.write(f"window.ENGRAM_DEMO_DATA={compact};")
    print(f"Wrote demo-data.js ({len(compact)} bytes)")


if __name__ == "__main__":
    main()
