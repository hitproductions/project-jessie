# The outages — what we know

Jessie (and Posty) go silent to Slack for minutes to hours, then recover on their
own. Caught live on 2026-09-08, the cause is **Cloudflare challenging Slack's
servers**. Nothing here is fixed in the n8n workflows — the fault is at the front
door, and the fix is in the Cloudflare dashboard.

## The cause (confirmed live 2026-09-08)

Slack reaches n8n through Cloudflare. When Cloudflare decides to **challenge**
traffic, it answers with a "Just a moment..." page that only a real browser can
pass (it runs JavaScript). **Slack's servers can't pass it**, so the webhook event
never reaches n8n and Jessie goes silent. Both bots share the same Cloudflare front,
so both drop and recover together.

**The proof — same URL, same moment, two source IPs:**

| Request from | Got back |
|---|---|
| The office machine's IP | the real n8n API (JSON) — reachable |
| A datacenter IP (our GitHub backup, standing in for Slack) | Cloudflare `Just a moment...` — blocked |

Slack's webhook-delivery servers are datacenter IPs, exactly like the one blocked.

**How sure are we?** Today is confirmed — we captured the challenge page and tested
office-IP reachability during the outage. The earlier outages (below) match the same
signature and their external failures are consistent with it, but the challenge body
was not logged then, so they are *near-certain*, not proven. The backup now logs the
body, so the next occurrence confirms it with no caveat.

## Why it explains every symptom

| Symptom | Cloudflare challenge explains it |
|---|---|
| Both bots go down at the same second | they share one Cloudflare front |
| n8n stays alive, scheduled jobs keep running | internal jobs don't go through Cloudflare |
| Reachable from inside, unreachable from outside | the challenge is applied by source IP |
| n8n's own logs show nothing | the requests never reach n8n — Cloudflare stops them first |
| Recovers on its own | Cloudflare's challenge condition clears (e.g. an "Under Attack" burst expiring) |
| Toggling the workflow "fixed" it | coincidence — recovery lined up with the challenge lifting, not the toggle |

## The fix (Cloudflare dashboard, needs account access)

In order — the first two are the usual cause, the third is the permanent guard.

1. **Turn off "I'm Under Attack" mode.** Security → Settings (zone Security Level).
   If it is "I'm Under Attack", it challenges everyone, Slack included. Set it to
   **Managed Challenge** or **Essentially Off** for normal use.
2. **Turn off Bot Fight Mode / Super Bot Fight Mode.** Security → Bots. It challenges
   automated traffic, which is what Slack's webhook delivery is. Off, or exclude the
   webhook path.
3. **Add a WAF rule that skips security for the webhook path (permanent).**
   Security → WAF → Custom rules. Match the Slack webhook path (contains `/webhook/`)
   and set the action to **Skip → All remaining custom rules**, disabling Bot Fight /
   Managed Challenge for that match. Then Slack can always deliver, whatever the zone
   security is set to later.

**Confirm it worked:** from a datacenter IP (not the office network) the n8n URL
should return the app, not "Just a moment..." — the nightly backup does exactly this
from GitHub, so its runs should stop logging "n8n was unreachable". Then send Jessie
a Slack message and confirm it produces an execution.

## When it has happened

| Date        | Down (Manila)        | Recovered | Notes                                  |
|-------------|----------------------|-----------|----------------------------------------|
| 2026-09-02  | ~morning             | same day  | first noticed                          |
| 2026-09-03  | ~09:00–10:20         | ~10:20    | mid-morning                            |
| 2026-09-05  | 00:05–13:03 (~13 h)  | 13:03     | both bots recovered the same second    |
| 2026-09-07  | from 22:51           | (caught)  | the one caught live — Cloudflare proven |

Recurring, self-recovering. Note 2026-09-07 started at night, not the ~5am of the
earlier ones — so it is not a pure time-of-day trigger.

## The trail — suspects we ruled out

Before catching it live, the evidence pointed at "the network path between the box
and the internet," which was right, but the specific suspects were not:

| Suspect | Why it looked plausible | Why it is not the cause |
|---|---|---|
| Cloudflare tunnel dropping | both bots, self-recovery | the tunnel was up — the box answered, it just served a challenge |
| Site internet flapping | alive inside, dead outside | reachable from the office IP throughout |
| Host DNS flapping (`EAI_AGAIN`) | errors appeared near outages | a separate, minor *outbound* issue on the box; unrelated to inbound |
| n8n losing its webhook registration | Sep 3 log showed "webhook not registered" | the challenge stops Slack before n8n is ever asked |
| Execution table filling SQLite | pruning once coincided with recovery | Sep 5 recovered with no pruning |

## What would catch the next one live

An **external uptime monitor** (UptimeRobot, Better Stack, Cloudflare Health Checks)
pinging the public URL every minute from outside. It sees the challenge the moment it
starts and alerts you, instead of finding out hours later. Highest-value thing not
yet in place; needs the owner's accounts, not a code change.
