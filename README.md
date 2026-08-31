# Project Jessie — n8n workspace

Working repo for the Slack booking bot. `CLAUDE.md` is the working brief and
`ONBOARDING.md` is the setup walkthrough — this file is just how to drive the
scripts.

## Setup (once)

1. n8n → Settings → n8n API → create an API key.
2. `cp .env.example .env`, open `.env` in an editor, paste the key after `N8N_API_KEY=`.
   `.env` is gitignored. Don't paste the key into a chat window, here or anywhere else.
3. Check it works:

```bash
./scripts/n8n list
```

## The script

| Command | What it does |
|---|---|
| `./scripts/n8n list` | every workflow with its id and active state |
| `./scripts/n8n pull <id> workflows/name.json` | download a workflow to a file |
| `./scripts/n8n execs` | last 20 runs of the main workflow |
| `./scripts/n8n execs <id> 50` | last 50 runs of any workflow |
| `./scripts/n8n exec <execId> --errors` | per-node item counts and errors for one run |
| `./scripts/n8n exec <execId>` | that run in full, including data |
| `./scripts/n8n ids` | the six workflow ids |

Reading is what this script is for. **Changes go into n8n by hand**, through the
browser UI: import the JSON file, then pull it back and check what you imported is
what n8n kept.

## The other scripts

| Command | What it does |
|---|---|
| `./scripts/test-nodes` | 117 offline checks over every Code node that decides something |
| `./scripts/test-nodes --live` | the same checks against what is deployed |
| `./scripts/test-gate` | the confirmation gate and date resolver on their own |
| `./scripts/check-fromai` | catches an unescaped apostrophe in a `$fromAI` description |
| `./scripts/health` | what the live workflow actually did on its last few turns |

Run `check-fromai` and `test-nodes` before importing anything, and `health` after.

## Working rule

Pull before you change anything, so the file matches what n8n is really running.
Someone editing in the browser and someone importing a file will overwrite each
other without warning.
