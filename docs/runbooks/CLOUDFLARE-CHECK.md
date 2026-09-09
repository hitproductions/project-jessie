# Cloudflare tunnel check — request for Sir Pao

**What we need:** four views from the Cloudflare dashboard, filtered to two past time
windows, plus one config upgrade. Screenshots of each are enough. This is a diagnostic
request — it narrows the Jessie/Posty outage question; it does not by itself prove a cause.

> Revised 9 Sept after a technical review (Genzo + ChatGPT). Corrections folded in: the
> status-code table, the tunnel-health caveat, the security-rule scope, the Free-plan log
> retention limit, the connector-upgrade resilience, and — importantly — the framing that
> **the outages may not have one universal cause.**

## Why (short context)

Jessie and Posty (Slack bots) went silent to Slack several times, then recovered on their
own. The cloudflared connector log shows the connector was a **stable pod with no restarts
and no origin errors _during the Sept 3 and Sept 5 windows specifically_** — just a daily
version warning.

**Important scope correction:** cloudflared *did* record origin/LAN failures on other days
— `connection refused`, `no route to host`, `connection reset by peer`, `EOF` to
`192.168.0.230:5678` — but every one of them falls on **Sept 2, 7, and 8**, the
troubleshooting and container-recreate days, **not** the Sept 3/5 outage windows. So those
are real failures tied to n8n restarts, not evidence about the outages. This is why the
outages should **not** be assumed to share a single cause with those events.

What the connector log *cannot* tell us: whether Cloudflare's edge was routing traffic to
the connector during the outages. Only the dashboard shows that side.

**The question we're narrowing:** during the outage windows, did Slack's requests reach
Cloudflare's edge — and if so, what did Cloudflare do with them? (This narrows; it does not
conclude — see the caveats in each step.)

## The two windows to filter to

Cloudflare usually shows **UTC** — both are given:

| Outage | Manila (PHT) | UTC |
|---|---|---|
| **Sept 5** (reported ~13 h — check first) | Sept 5, 00:05 → 13:03 | Sept 4 16:05 → Sept 5 05:03 |
| **Sept 3** (morning) | Sept 3, 09:00 → 10:20 | Sept 3 01:00 → 02:20 |

> Note on Sept 5: the "13-hour outage" is so far inferred from Jessie/Posty having **no
> executions**, which by itself does not prove an outage — it could be no Slack events were
> generated. It needs corroboration from actual Slack event timestamps (or the external
> backup's failure, whose network path is still unconfirmed). Treat the window as
> *suspected*, not established.

Hostname to filter on: **`signal.hitpromanila.net`**

## What to check — 4 views

### 1. Traffic during the windows  *(the most important one)*
**Where:** Analytics & Logs → Traffic (filter to `signal.hitpromanila.net`, zoom to each
window).
**Capture:** request count and status-code breakdown during each window.
**How to read it — carefully:**
- Requests present (even if erroring) → Slack's events reached Cloudflare; the break is
  Cloudflare → connector → n8n.
- **Zero requests is ambiguous**, not proof of a Slack/DNS failure. It can also mean no
  qualifying Slack event occurred, the dashboard data expired, the filter was wrong, or
  low-volume traffic was sampled out. **Correlate the request counts against specific
  Slack messages and their exact timestamps** before concluding anything.

### 2. Error status codes during the windows
**Where:** same Traffic view. Better still, capture the `cf-error-type` / `cf-error-origin`
response headers if visible — they identify the failing hop more reliably than the status
code alone.

| Code | Meaning |
|---|---|
| **530 / 1033** | No healthy tunnel connector connected to Cloudflare (edge ↔ connector) |
| **502 (tunnel-generated)** | Tunnel is connected, but cloudflared **could not reach the origin** — this includes `connection refused`. It does **not** mean n8n received the request. |
| **522 / 523** | Connection timed out / unreachable to origin |
| **504** | Timeout — needs diagnostic headers + origin logs to locate |
| **200** | HTTP exchange succeeded — but the workflow could still fail *after* acknowledging |

Ref: Cloudflare Tunnel troubleshooting, and Cloudflare error headers (`cf-error-type`).

### 3. Tunnel connector health/uptime history
**Where:** Zero Trust → Networks → Tunnels → the tunnel for `signal.hitpromanila.net` →
connector status / connection history.
**Capture:** whether it shows **DOWN or DEGRADED** at the outage timestamps.
**Caveat (important):** Cloudflare's tunnel-health view covers only the **Cloudflare ↔
cloudflared** leg. A tunnel can read **Healthy** while cloudflared still cannot reach n8n.
So "Healthy" here does not clear the origin path — it only tells us about the edge side.

### 4. Security Events for the webhook path
**Where:** Security → Events (filter to the webhook path / `signal.hitpromanila.net`, the
window times).
**Why:** Cloudflare was already caught **blocking bot crawlers** (Slackbot, Facebot) in our
n8n logs, so a WAF / bot-fight / rate-limit rule *could* have blocked Slack's event POSTs.
If you see blocked/challenged POSTs there, that's a lead.
**On the fix — do not broadly allowlist "Slack IPs."** A narrowly scoped rule is safer:
exact hostname + exact webhook path + `POST` method + proper request validation, rather
than a broad IP range or bot bypass.

## ⚠️ Retention — expect gaps, check today

On the **Free plan**, Cloudflare's detailed historical HTTP request logs (Logpush) are
**not available** — that's an Enterprise feature — and Traffic analytics retain only a
short window. So the Sept 3/5 dashboard data **may already be incomplete or gone.** Check
view #1 first; if it's expired, views #3 and #4 usually retain longer. Live tunnel logs
help *future* incidents but cannot reconstruct expired historical requests — which is the
argument for the external monitor + log capture going forward.

## Separate ask — upgrade cloudflared (and add a second replica)

The connector runs **cloudflared `2025.2.1`**, flagged as outdated (recommends `2026.7.3` /
`2026.8.3`) — ~18 months old. Worth upgrading regardless of the outage.

**But there is currently only one connector pod**, so an upgrade (or any restart) briefly
interrupts traffic. For a clean upgrade *and* better resilience:
1. Deploy a second fixed `cloudflared` replica for the same tunnel.
2. Confirm both are Ready and connected.
3. Upgrade one replica at a time.
4. Retain the Kubernetes pod logs externally so they survive pod churn.

A second always-on replica also means a single connector hiccup no longer takes inbound
delivery down — useful independent of the version.

## What to send back

Per window: screenshots of Traffic + status codes (views 1–2, with `cf-error-*` headers if
shown), the tunnel connector history (view 3), and anything in Security Events (view 4).
Plus confirmation once cloudflared is upgraded and a second replica is running.

## Honest framing of the conclusion

For the Sept 3 and 5 windows, the available connector logs show **no connector restart and
no origin error**. That leaves several possibilities open — Slack delivery, Cloudflare
security/routing, missing/expired analytics data, and unobserved application behavior.
Cloudflare dashboard data may narrow these, but **aggregate traffic analytics alone cannot
conclusively identify Slack requests** — they must be matched to real message timestamps.
And the earlier/later incidents (Sept 2, 7, 8) *did* include confirmed origin/LAN failures,
so **the outages should not be treated as having one universal cause.** This checklist is
worth working through; its dashboard requests are sound; its role is to *narrow*, not to
declare a verdict.

---

### Reference — the setup
- Connector: Kubernetes pod `cloudflared-859f98bbfb-vzm9q`, one continuous pod
  Aug 11 → Sept 8, no restarts. QUIC connections to Cloudflare edge in Manila + Hong Kong.
- Origin: n8n at `192.168.0.230:5678` (also seen via NodePort `192.168.0.252:30069`).
- Confirmed origin/LAN errors (`connection refused`, `no route to host`, `connection reset`,
  `EOF`) occurred on **Aug 25/30/31, Sept 2, 7, 8** — not during the Sept 3/5 windows.
- cloudflared version `2025.2.1` (outdated). Single replica.
- Public hostname: `signal.hitpromanila.net`. Cloudflare **Free** plan (no Logpush).
