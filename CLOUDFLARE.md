# Cloudflare is what takes Jessie down

Caught live on 2026-09-08, ~02:35 Manila, while Jessie was down. This is the
confirmed cause of the outages — not DNS, not the tunnel, not n8n. The fix is in
the Cloudflare dashboard.

## What is happening

Slack reaches n8n through Cloudflare. When Cloudflare decides to **challenge**
traffic, it answers requests with a "Just a moment..." page that only a real
browser can pass (it runs JavaScript). **Slack's servers can't pass it**, so the
webhook event never reaches n8n and Jessie goes silent. Both bots share the same
Cloudflare front, so both drop together and recover together when the challenge
lifts.

## The proof (same URL, same moment, two source IPs)

| Request from | Got back |
|---|---|
| The office machine's IP | the real n8n API (JSON) — reachable |
| A datacenter IP (our GitHub backup, standing in for Slack) | Cloudflare `Just a moment...` challenge — blocked |

Slack's webhook-delivery servers are datacenter IPs, exactly like the one that got
blocked. So Slack was being challenged and could not deliver.

## Why this explains everything we saw

| Symptom | Cloudflare challenge explains it |
|---|---|
| Both bots go down at the same second | they share one Cloudflare front |
| n8n stays alive, scheduled jobs keep running | internal jobs don't go through Cloudflare |
| Reachable from inside, unreachable from outside | the challenge is applied by source IP |
| n8n's own logs show nothing | the requests never reach n8n — Cloudflare stops them first |
| Recovers on its own | Cloudflare's challenge condition clears (e.g. "Under Attack" mode expires) |
| Toggling the workflow "fixed" it | coincidence — recovery lined up with the challenge lifting, not the toggle |

## The fix (Cloudflare dashboard, needs account access)

Do these in order; the first two are the usual cause, the third is the permanent guard.

1. **Turn off "I'm Under Attack" mode.** Security → Settings (or the zone's Security
   Level). If the level is "I'm Under Attack", that challenges *everyone*, Slack
   included. Set it to **Managed Challenge** or **Essentially Off** for normal use.
2. **Turn off Bot Fight Mode / Super Bot Fight Mode.** Security → Bots. When on, it
   challenges automated traffic — which is what Slack's webhook delivery is. Turn it
   off, or exclude the webhook path.
3. **Add a WAF rule that skips security for the webhook path (permanent fix).**
   Security → WAF → Custom rules. Match the Slack webhook path (it contains
   `/webhook/`) and set the action to **Skip → All remaining custom rules** and
   disable Bot Fight / Managed Challenge for that match. Then Slack can always
   deliver, whatever the zone's security posture is later set to.

## How to confirm it is fixed

- From a **datacenter IP** (not the office network), request the n8n URL and confirm
  you get the app, not a "Just a moment..." page. The nightly backup does exactly
  this from GitHub — after the change, its runs should stop logging
  "n8n was unreachable" and start succeeding from that source.
- Send Jessie a Slack message and confirm it produces an execution.

## What this rules out

Earlier suspects — host DNS flapping, the Cloudflare tunnel dropping, n8n losing
its webhook registration — are not the cause. The `EAI_AGAIN` DNS errors are a
separate, minor outbound issue on the box, unrelated to the outages. The box and
n8n were healthy every time; Cloudflare was turning Slack away at the door.
