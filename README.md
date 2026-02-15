# Engram - Releases & Demo Site

Live demo site for the Engram project, hosted via GitHub Pages.

**Live**: https://engram-hq.github.io/releases/

## What's Here

| File | Purpose |
|------|---------|
| `index.html` | Main site (single-page, all inline) |
| `demo-data.json` | Skills + memories data (14 skills, 10 memories) |
| `demo-data.js` | Same data as sync-loadable script |
| `showcase-data.json` | 8 AI-analyzed open-source repos |
| `demo-sources.json` | Source registry for nightly refresh |
| `engram-demo.mp4` | Demo video (embedded on site) |
| `privacy-policy.html` | Privacy policy for App Store |

## Demo Features

- **Skills Browser** - Skill tree + viewer with rendered markdown
- **3D Timeline** - Force-directed knowledge graph (three.js)
- **Search** - Full-text search across all content
- **Analytics** - Cost analytics from session data
- **Sync** - Sync status simulation
- **AI Showcase** - 8 repos analyzed by engram-cli

## Nightly Refresh

The `refresh-demo.yml` workflow runs at 02:00 UTC daily:
1. Reads `demo-sources.json` for the canonical list of skills/memories
2. Fetches latest content from GitHub
3. Merges into `demo-data.json` (failed fetches fall back to cached data)
4. Commits and pushes if data changed

To add new content, update `demo-sources.json` with the raw GitHub URL.

## Local Build

```bash
./build-demo-data.sh    # Reads from local .skills/.memory dirs
```

## Related Repos

- [engram-cli](https://github.com/engram-hq/engram-cli) - Local AI code analyzer
- [engram-web](https://github.com/engram-hq/engram-web) - Web dashboard
- [engram-sdk](https://github.com/engram-hq/engram-sdk) - TypeScript metrics SDK
