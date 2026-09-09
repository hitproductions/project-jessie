# Overnight inspection — night of 8→9 September 2026

**Bottom line (corrected 9 Sept):** the VM, n8n, and the tunnel endpoint stayed healthy all
night — but a **real Slack message still dropped**: Tara messaged Jessie at 2:12 AM and it
never arrived (no reply, no execution). So there was **no whole-system outage, but there
*was* a real delivery failure** — and the health checks could not see it. That gap is the
most important finding here.

> This doc originally concluded "no outage overnight" and claimed we had "captured the
> outage mechanism (DHCP lease loss)." Both were wrong and are corrected below, after
> Tara's screenshot and Genzo's technical review.

## Background (for anyone new to this)

Jessie and Posty are Slack bots on a self-hosted n8n instance, exposed via a Kubernetes
`cloudflared` tunnel at `signal.hitpromanila.net`. Between 2 and 5 September they went
silent to Slack several times and recovered on their own. 8 September was the first night
with full VM-side logging (canary, VM health, DNS journal, debug log).

## What was inspected

Genzo's observability export (8 Sept 12:00 → 9 Sept ~15:00 PHT), cross-checked against the
n8n execution audit, the webhook debug log, and Tara's Slack DM with Jessie.

## Findings

### 1. The VM and endpoint were healthy all night — but that is not the same as "working"

The canary probed the public path every ~65 s (4,521 probes, largest gap 1.1 min) and was
green throughout, except four probes during Genzo's afternoon maintenance. n8n ran, gateway
reachable, DNS resolvers healthy. **This proves the endpoint was reachable. It does not
prove Slack's events were being delivered** — see #2.

### 2. Confirmed: a real Slack message dropped at 2:12 AM

Tara messaged Jessie "Test" at **2:12 AM**; Jessie did not reply. The debug log records
*every* webhook n8n receives — around 18:12 UTC it shows only the 65-second canary probes,
**no receipt for Tara's actual message, and no execution.** Real Slack events reaching
Jessie were absent for **8.5 hours (00:32 → 09:04 AM PHT)**; her 12:06 PM re-test got
through normally. At 2:12 AM the VM was healthy (canary green, no network event), so **the
message was lost upstream of the box — between Slack and the tunnel, not on the VM.**

**This is the actual outage signature, and the key lesson:** the endpoint stays reachable
(so every health check passes) while real Slack events silently fail to arrive. It is
exactly why earlier investigations kept finding "n8n healthy, webhook registered" during
the outages — the green checks were masking the real failure.

### 3. The DHCP lease losses were admin-triggered — NOT the mechanism

The two lease-loss events (≈2:46 and 2:50 PM on 8 Sept) were **caused by an administrator
running `sudo netplan apply`** — the log shows the command at 06:46:19 UTC, with the lease
loss 2 seconds later. So they demonstrate what a brief interruption looks like; they do
**not** show DHCP caused the Sept 3/5 outages, and a 4-second reacquire cannot be
extrapolated to a multi-hour outage. A DHCP reservation for `192.168.0.230` is still worth
doing as **preventive hardening**, but it is not a confirmed root-cause fix.

### 4. The tunnel connector is largely cleared (edge side still unchecked)

The `cloudflared` connector is a stable Kubernetes pod, ran Aug 11 → Sept 8 with zero
restarts, and logged no reconnects or origin errors during the Sept 3/5 windows. But its
own log cannot show whether Cloudflare's *edge* routed traffic to it — only the dashboard
can. Given #2 (a message lost upstream of the VM), that edge-side check is now central.

### 5. Two supporting points

- DNS `EAI_AGAIN` errors: none after the hardening (good, but that layer was never the
  inbound-delivery cause).
- No runner-starvation errors in the package — but we lack a clean before/after rate, so
  treat "improved" as plausible, not measured.

## What it means

- **The failure is upstream of the VM** — Slack → Cloudflare edge. The box, n8n, the tunnel
  connector, and DHCP are not implicated in the 2:12 AM drop.
- **Reachability checks (canary, `/healthz`, an external uptime monitor) cannot detect this
  class of failure.** They test whether the endpoint answers, not whether Slack's events
  arrive. Detecting real drops requires correlating actual Slack messages against
  executions (which is how this one was caught).
- **The outages are not proven to share one universal cause.** Sept 2/7/8 had confirmed
  origin/LAN failures tied to n8n restarts; the 2:12 AM drop is an upstream delivery failure
  with the box healthy. Different signatures.

## Next actions

1. **Slack app → Event Subscriptions delivery/failure log** — did Slack even send the 2:12
   event, or did it fail / back off? This is now the most direct lead, and it's free.
2. **Cloudflare dashboard** for the Sept 3/5 windows and, ideally, the 2:12 AM window —
   did the request reach the edge? Checklist:
   [docs/runbooks/CLOUDFLARE-CHECK.md](docs/runbooks/CLOUDFLARE-CHECK.md).
3. **DHCP reservation** for `192.168.0.230` — preventive hardening (not a confirmed fix).
4. **Upgrade `cloudflared`** off `2025.2.1`, and add a second replica **on a different host
   / k8s node** (a same-host replica protects against nothing).
5. **Add a real end-to-end delivery check** — a periodic signed Slack-style event, or a
   Slack-message-vs-execution reconciliation — since reachability probes miss real drops.

## Credits / corrections

Tara's 2:12 AM screenshot established the real delivery failure. Genzo's technical review
(with ChatGPT) corrected the DHCP framing and the 502 interpretation, and refined the
replica and runner points. Full history: [OUTAGE-2026-09-02.md](OUTAGE-2026-09-02.md),
[OUTAGES.md](OUTAGES.md).
