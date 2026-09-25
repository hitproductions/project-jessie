# Project Jessie

Slack bot that books studio time for Hit Productions, built in n8n. A second bot,
Posty, runs on the same instance. Launch: **12 October 2026** (dev freeze 23 Sep).

## Start here

Open this folder in **Claude Code** and it reads `CLAUDE.md` on its own, then tells
you what is live, what is failing and what is open. That is the intended way in — you
should not have to read your way up to speed.

```bash
git clone https://github.com/hitproductions/project-jessie.git
cd project-jessie
claude
```

## What is in here

| | |
|---|---|
| `CLAUDE.md` | the working brief — how it is built, and the mistakes that already cost days |
| `PENDING.md` | open items, each waiting on Airtable, Slack, Google or the server |
| `docs/outages/OUTAGES.md` | the recurring outages: what is ruled out, what is not, and three theories that were wrong |
| `docs/outages/SERVER-NOTES.md` | the server-side slowness, in plain language |
| `docs/outages/MONITOR-SETUP.md` | the external uptime monitor, still not in place |
| `workflows/` | the current build of each workflow, plus `live/` — a nightly backup of what n8n is actually running |
| `scripts/` | read-only tools: check what is deployed, what it ran, whether ids still match |

## Two rules

1. **Never commit `.env`.** It holds the n8n API key. It is gitignored — keep it that
   way, and don't paste the key into a message either.
2. **Pull the workflow from n8n before you change it.** The n8n UI and this folder
   overwrite each other silently, and people do edit in the browser.

Changes go into n8n **by hand** through its browser UI, then get pulled back and
checked. There is no API write path in use.

## Why the commit messages are long

They are the record of *why*, not just *what* — most of them explain a bug that took
hours to find. `git log` is worth reading before changing something that looks odd.
