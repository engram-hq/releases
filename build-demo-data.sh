#!/usr/bin/env bash
set -euo pipefail
# Regenerates demo-data.json from local .skills and .memory repos.
# Run after adding/editing skills or session memories.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ORGS_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

python3 -c "
import json, os, glob, datetime

data = {
    'skills': [],
    'memories': [],
    'generated_at': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
}

orgs_dir = '$ORGS_DIR'

# Skill sources: (org, repo, tier, local_path, display_path)
skill_sources = [
    ('engram-hq', '.skills', 2, os.path.join(orgs_dir, 'engram-hq/.skills'), ''),
    ('sreniatnoc', '.skills', 2, os.path.join(orgs_dir, 'sreniatnoc/.skills'), ''),
    ('sreniatnoc', 'rusd', 3, os.path.join(orgs_dir, 'sreniatnoc/rusd/.skills'), '.skills/'),
]

for org, repo, tier, base_dir, prefix in skill_sources:
    if not os.path.isdir(base_dir):
        continue
    for root, dirs, files in os.walk(base_dir):
        for f in sorted(files):
            if not f.endswith('.md') or f == 'README.md':
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, base_dir)
            with open(fp) as fh:
                content = fh.read()
            data['skills'].append({
                'org': org, 'repo': repo, 'tier': tier,
                'path': prefix + rel, 'name': f,
                'content': content
            })

# Memory sources
mem_sources = [
    ('engram-hq', os.path.join(orgs_dir, 'engram-hq/.memory/sessions')),
    ('sreniatnoc', os.path.join(orgs_dir, 'sreniatnoc/.memory/sessions')),
]

for org, dirpath in mem_sources:
    if not os.path.isdir(dirpath):
        continue
    for fp in sorted(glob.glob(os.path.join(dirpath, '*.md'))):
        name = os.path.basename(fp)
        if name == 'README.md':
            continue
        with open(fp) as fh:
            content = fh.read()
        data['memories'].append({
            'org': org, 'repo': '.memory',
            'path': 'sessions/' + name, 'name': name,
            'content': content
        })

with open('$SCRIPT_DIR/demo-data.json', 'w') as out:
    json.dump(data, out, indent=2)

print(f'Generated demo-data.json: {len(data[\"skills\"])} skills, {len(data[\"memories\"])} memories')
"
