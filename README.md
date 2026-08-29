# Project Jessie — n8n workspace

Working repo for the Slack booking bot. The full background is in [HANDOFF.md](HANDOFF.md);
this file is just how to drive it.

## Setup (once)

1. n8n → Settings → n8n API → create an API key.
2. `cp .env.example .env`, open `.env` in an editor, paste the key after `N8N_API_KEY=`.
   `.env` is gitignored. Don't paste the key into a chat window, here or anywhere else.
3. Check it works:

```bash
cd /Users/tara/Documents/Claude/jessie && ./scripts/n8n list
```

## The script

| Command | What it does |
|---|---|
| `./scripts/n8n list` | every workflow with its id and active state |
| `./scripts/n8n pull <id> workflows/name.json` | download a workflow to a file |
| `./scripts/n8n push <id> workflows/name.json` | upload a file over a workflow — asks for a typed `yes` first |
| `./scripts/n8n execs` | last 20 runs of the main workflow |
| `./scripts/n8n execs <id> 50` | last 50 runs of any workflow |
| `./scripts/n8n exec <execId> --errors` | per-node item counts and errors for one run |
| `./scripts/n8n exec <execId>` | that run in full, including data |
| `./scripts/n8n ids` | the two workflow ids |

`push` sends only `name`, `nodes`, `connections`, `settings` — the API rejects a
payload carrying `id`, `active`, `tags` or `versionId`, which is what an n8n UI
export gives you.

## Workflow ids

| Workflow | id | State |
|---|---|---|
| Project Jessie (main) | `uVVYVB2M7kxpLleI` | live, active |
| Jessie — Book Session (sub) | `EUG3sGXkfsJSYIMz` | built, tested, not wired |

## What's in here

```
workflows/project-jessie-v36.json   the live main workflow — source of truth
workflows/book-session-v2.json      the tested sub-workflow
prompts/system-prompt-v36.md        the agent's systemMessage, lifted out of v36 so it diffs
code/check-conflicts.js             Book Session → Check Conflicts
code/return-rejection.js            Book Session → Return Rejection
code/guard-probe.js                 Project Jessie → Guard Probe (empty-output fallback)
scripts/n8n                         the API wrapper above
HANDOFF.md                          Aug 30 handoff, verbatim
CLAUDE.md                           context for a fresh Claude Code session
```

The files under `prompts/` and `code/` are extracted copies for diffing and review.
The JSON under `workflows/` is what actually gets pushed — edit there, or re-embed
after editing an extract.

## Working rule

Pull before you change anything, so the file matches what n8n is really running.
Someone editing in the browser and someone pushing a file will overwrite each other
without warning.
