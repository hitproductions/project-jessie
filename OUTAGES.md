# The outages — what we know

Jessie and Posty go silent to Slack, then recover on their own with nobody touching
them. **2 September is solved. Everything after it is not.** This file is the state of
the investigation as of 8 September, including the theories that turned out to be
wrong, so nobody spends a day re-chasing them.

Nothing here is fixed in the n8n workflows.

## Solved: 2 September

Two independent faults overlapped, both found by Genzo:

1. **A Slack signing-secret mismatch.** Jessie's Slack Trigger was moved onto a new
   credential whose signing secret did not match the Slack app. Fixed by a credential
   update at 17:43:23.
2. **A webhook deregistration, 17:25–17:43**, caused by someone test-listening on the
   *live* Slack Trigger. n8n cannot listen for a test event and production events at
   the same time, so starting a test takes the production webhook down.

**The signing-secret failure is the important one to understand, because it is
invisible.** n8n receives Slack's POST, checks the signature, rejects it — and at the
default log level writes *nothing at all*. So you get:

- the request reaching n8n
- **no execution created**
- **no log line anywhere**
- the webhook still showing as **registered**

That last point matters: a registered webhook proves nothing. It can be registered,
receiving requests, and silently discarding every one. `N8N_LOG_LEVEL=debug` is now
set, which makes this case legible next time.

## Not solved: 3 September onward

Recorded: 3 Sep (~09:00–10:20), 5 Sep (00:05–13:03, ~13 h), 7–8 Sep (overnight).
Not credential, not restart, not test-listen, not load.

### What is established

- Both bots stop receiving; n8n itself stays up — scheduled jobs run straight through
- **Outbound works mid-outage** — Posty Index reached Google Sheets and Slack's API at
  02:00 on 8 Sep, inside the outage
- **Cloudflare→origin worked mid-outage** — at 02:35 a request returned real n8n JSON
  (`cf-cache-status: DYNAMIC`, so from the origin) while Jessie was dead
- It needs **no traffic** — it has broken across a weekend with nobody using it
- It needs **no human** — it heals itself
- **Not the signing secret** — the secret is unchanged and it still heals itself
- n8n has **79 days uptime**; no restarts, no OOM, disk 34% used
- **SQLite ruled out** — no lock or disk errors, contiguous execution ids, no latency
  creep before either stall, and the heaviest hour of 2–3 Sep ran clean

### Ruled out

| Suspect | Killed by |
|---|---|
| Anything traffic-triggered — Slack throttle, rate limits, fail2ban, bot challenges | it breaks across an idle weekend; no traffic to trigger anything |
| Signing secret expiring or rotating | secret unchanged, still self-heals |
| n8n crashing or restarting | 79 days uptime, scheduled jobs run through it |
| The box offline, or its DNS broken | outbound worked mid-outage |
| SQLite / execution table | see above |
| Per-workflow webhook registration | independent per bot; cannot explain both |

### The 8 September window — the one properly instrumented

Genzo's canary and `N8N_LOG_LEVEL=debug` were both running for 00:00–05:00 PHT on
8 Sep, inside a window where Jessie was not answering. This is the only outage window
with real instrumentation, and it localises the fault precisely.

| Check | Result across the window |
|---|---|
| public n8n health, through the tunnel | **200 × 278**, no gap over 90s |
| jessie webhook registration | **401 `route_present_signature_rejected` × 278** — registered throughout |
| n8n errors / DNS / `db_locked` / OOM | **all zero** |
| webhooks n8n actually received | **278 — every one the canary's own probe** |

A test Slack message was sent at **18:35:53 UTC (02:35:53 PHT)**. The canary probes
land on a strict 65s beat (…18:34:58, 18:36:03, 18:37:08), so the nearby receive is
the canary. **There is no extra receive anywhere in the window.**

**So the message never reached n8n**, while the tunnel was up, the webhook was
registered, and n8n was healthy.

This rules out, for this window:

- **the tunnel dropping, and the connector machine sleeping** — 278 consecutive 200s
  straight through it (so the connector-sleep hypothesis in `MONITOR-SETUP.md` does not
  explain *this* window, whatever it explains elsewhere)
- **webhook deregistration** — route present on all 278 probes
- **n8n being unhealthy** — zero errors of any kind
- **a signature mismatch** — a rejection still logs `Received webhook` first. Nothing
  arrived to be rejected.

**One blind spot to be honest about:** the canary runs *on the VM*, so its "public"
check leaves and returns from the VM's own IP. It cannot detect Cloudflare treating
**Slack's** IPs differently from the VM's. A green canary does not clear Cloudflare —
that is exactly the gap the external monitor in `MONITOR-SETUP.md` exists to close.

### Still standing, ranked

After the 8 Sep window, two candidates remain — and both are about what happens
*before* the request reaches our front door:

1. **Slack did not deliver the event.** Nothing arrived, so either Slack never sent it
   or it was dropped upstream. Split it with the Slack app's Event Subscriptions
   delivery/failure counts.
2. **Something between Slack and the origin dropped it, discriminating by source.**
   The canary's request from the VM sails through Cloudflare; Slack's did not arrive.
   Anything that treats those two sources differently fits. Split it with
   Cloudflare → Security → Events, filtered to the hostname: if Slack's IPs appear
   being challenged or blocked, that is the answer; if they never appear, Slack never
   sent.

Those two checks are the whole remaining question, and neither can be done from the VM.

**This is what survived one enumeration, not a closed set.** The signature-rejection
mechanism above was in nobody's list until Genzo found it, and there is no reason to
think it was the only gap.

## Theories that were wrong — do not re-chase

| Theory | Why it is wrong |
|---|---|
| **Host DNS causes the outages** | The `EAI_AGAIN` errors are on *outbound* calls. The outages are inbound. Outbound worked mid-outage. Written into SERVER-NOTES as the cause; it was not. |
| **Cloudflare challenges Slack's servers** | Built on the GitHub backup being challenged and treated as a stand-in for Slack. Slack is not challenged — a re-verify from Slack got through. And the GitHub challenge is intermittent and independent: the backup failed at 05:00 on 6 Sep while Jessie worked fine at 05:02. |
| **SQLite / execution table filling** | Ruled out with specific evidence. Pruning once coincided with recovery; 5 Sep recovered with no pruning. |

**And a method note, because it produced most of the above.** Several "eliminations"
came from a single probe taken hours into a multi-hour outage, then written up as
covering the whole window. A reading at 02:35 says nothing about 22:51. Anything
measured mid-outage needs its timestamp recorded and its scope stated.

## What to do when it next drops

Do these **while it is confirmed down**, and note the time.

**1. Are the webhooks registered?** Two GETs:

```
curl https://signal.hitpromanila.net/webhook/jessie-slack-webhook/webhook
curl https://signal.hitpromanila.net/webhook/posty-slack-webhook/webhook
```

| Response | Means |
|---|---|
| `This webhook is not registered for GET requests. Did you mean to make a POST request?` | webhook is **live** — this is the healthy baseline, confirmed 8 Sep 09:48 with both bots working |
| `The requested webhook "…" is not registered` | webhook is **gone** from the registry |

**2. Can Slack reach it?** In the Slack app → Event Subscriptions, paste the Request
URL and save. That forces a fresh challenge from Slack's own servers. "Verified" means
Slack got through; an error means it did not. The persistent green badge proves
nothing — it survives every outage.

**3. Read the container log.** With `N8N_LOG_LEVEL=debug` now on, this shows whether
Slack's request **arrived** at all. That single fact splits the list: nothing arriving
points at 1, 3 or 4 above; arriving and being rejected points at 2 or a signature
problem.

**4. `./scripts/webhook-canary`** (Genzo's) — an unsigned probe for registration plus a
*signed* verification, which is the only thing that catches a silent signature
rejection. Better than the two GETs above; use it if you can.

## Still not in place

An **external uptime monitor** on the public URL. It would catch the drop the moment
it happens and record the exact start and end, instead of everyone inferring backwards
from "the last message that worked." Every argument in this file has been weakened by
not knowing when the outages actually begin — the timestamps we quote are the last
successful message, which is not the same thing.
