# Cloudflare tunnel check — request for Sir Pao

**What we need:** four views from the Cloudflare dashboard, filtered to two past time
windows, plus one config upgrade. Screenshots of each are enough. This closes the last
open question in the Jessie/Posty outage investigation.

## Why (short context)

Jessie and Posty (Slack bots) went silent to Slack several times, then recovered on their
own. We've now cleared almost everything: n8n itself stayed up, the box was healthy
inside, and the **cloudflared connector log you sent shows the tunnel connector was
running fine** during the outages (stable pod, no reconnects, no origin errors — just a
daily version warning).

But the connector's own log can't tell us one thing: whether **Cloudflare's edge was
actually routing traffic to it** during the outages. Only the Cloudflare dashboard shows
that side. That's the missing piece.

**The single question we're answering:** during the outage windows, did Slack's requests
reach Cloudflare's edge — and if so, what did Cloudflare do with them?

## The two windows to filter to

Cloudflare usually shows **UTC** — both are given:

| Outage | Manila (PHT) | UTC |
|---|---|---|
| **Sept 5** (the big 13-hour one — check this first) | Sept 5, 00:05 → 13:03 | Sept 4 16:05 → Sept 5 05:03 |
| **Sept 3** (morning) | Sept 3, 09:00 → 10:20 | Sept 3 01:00 → 02:20 |

(Sept 2 also had an outage but is muddied by n8n restarts that day, so Sept 5 and 3 are
the clean ones.)

Hostname to filter on: **`signal.hitpromanila.net`**

## What to check — 4 views

### 1. Traffic during the windows  *(the most important one)*
**Where:** Analytics & Logs → Traffic (filter to `signal.hitpromanila.net`, zoom to each
window above).
**Capture:** the request count and status-code breakdown during each window.
**What it tells us:**
- Requests present (even if erroring) → Slack's events reached Cloudflare; the break is
  Cloudflare → connector → n8n.
- **Zero requests** during the window → the problem is *upstream* of Cloudflare (Slack
  didn't send, or DNS) — which would mean the tunnel is not the cause at all.

### 2. Error status codes during the windows
**Where:** same Traffic view, the status-code breakdown.
**What the code means:**

| Code | Meaning |
|---|---|
| 530 (error 1033) | Argo Tunnel error — no healthy connector (**tunnel down, edge side**) |
| 522 / 523 | Connection timed out / unreachable to origin |
| 502 / 504 | n8n got the request but didn't respond |
| 200 | Delivered fine — outage was not at Cloudflare |

### 3. Tunnel connector health/uptime history
**Where:** Zero Trust → Networks → Tunnels → the tunnel for `signal.hitpromanila.net` →
its connector status / connection history.
**Capture:** whether the tunnel shows **DOWN or DEGRADED** at the outage timestamps.
**Why:** the connector's own log showed *no* disconnects during Sept 3–6. If Cloudflare's
side shows a drop the connector didn't log, that's an edge-side registration problem —
exactly what we can't see from the box.

### 4. Security Events for the webhook path
**Where:** Security → Events (filter to the webhook path / `signal.hitpromanila.net`, the
window times).
**Why this matters specifically:** Cloudflare was already caught **blocking bot crawlers**
(Slackbot, Facebot) in our n8n logs. So it's possible a WAF / bot-fight / rate-limit rule
**blocked Slack's event POSTs** during a window. If you see blocked or challenged requests
from Slack's IPs here, that's the cause — and the fix is a WAF allow rule for Slack, not
anything on the box.

## ⚠️ Do this today — retention

Cloudflare's Traffic analytics often only retain ~24–72 hours on lower plans, so the
Sept 3/5 windows **may already be rolling off**. Please check view #1 first. If the
traffic data is already gone, views #3 (connector history) and #4 (Security Events)
usually retain longer and are the fallback.

## Separate ask — upgrade cloudflared

The connector is running **cloudflared `2025.2.1`**, which it flags as outdated
(recommends `2026.7.3` / `2026.8.3`). That's ~18 months old. Independent of the outage,
please upgrade it — it clears a class of known connection-stability bugs. It's a rolling
restart of the `cloudflared` deployment in Kubernetes, so no lasting downtime.

## What to send back

For each of the two windows: a screenshot of the Traffic + status codes (view 1–2),
the tunnel connector history (view 3), and anything in Security Events (view 4). Plus
confirmation once cloudflared is upgraded.

---

### Reference — what we already know about the setup
- Connector: Kubernetes pod `cloudflared-859f98bbfb-vzm9q`, one continuous pod
  Aug 11 → Sept 8, no restarts. QUIC connections to Cloudflare edge in Manila + Hong Kong.
- Origin: n8n at `192.168.0.230:5678` (also seen via NodePort `192.168.0.252:30069`).
- cloudflared version `2025.2.1` (outdated).
- Public hostname: `signal.hitpromanila.net`.
