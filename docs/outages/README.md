# Outages

Jessie has gone silent to Slack repeatedly (2, 3, 5, 7–8 September 2026). This is the largest open
risk, and it is not in the workflows. Everything about it lives here.

| File | What it is |
|---|---|
| [`OUTAGES.md`](OUTAGES.md) | **Start here.** The authoritative account: ranked causes, the onset window, what is ruled out, and the theories that were wrong (host DNS, SQLite) or wrongly retracted (Cloudflare). |
| [`OUTAGE-2026-09-02.md`](OUTAGE-2026-09-02.md) | The 2 September outage in detail: signing-secret mismatch plus webhook deregistration. Solved. |
| [`OUTAGE-INSPECTION-2026-09-09.md`](OUTAGE-INSPECTION-2026-09-09.md) | The 9 September inspection. |
| [`SERVER-NOTES.md`](SERVER-NOTES.md) | The server-side fixes (DNS, task runner) in plain language, for whoever has shell access. |
| [`CLOUDFLARE-CHECK.md`](CLOUDFLARE-CHECK.md) | Runbook: did Slack's requests reach the Cloudflare edge, and what did it answer? (15 Sep: Slack saw 403s from Cloudflare.) |
| [`MONITOR-SETUP.md`](MONITOR-SETUP.md) | Runbook: the external uptime monitor. Still not in place (PENDING 15). |
| [`CANARY-SETUP.md`](CANARY-SETUP.md) | Runbook: `scripts/webhook-canary`, the signed probe that catches a silent signature rejection. |
| [`evidence/`](evidence/) | The only surviving execution capture from 2–4 September. |
| `logs/` | Raw logs. Kept out of git (see `.gitignore`); ask before committing any. |

Moved here from the repo root and `docs/runbooks/` on 2026-09-25.
