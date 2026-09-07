# The outages — what we know

> **Cause confirmed 2026-09-08 — it is Cloudflare challenging Slack's servers. See
> `CLOUDFLARE.md` for the finding and the fix. The suspects below are kept as the
> trail that led there; the network-path reasoning held, the specific suspects did not.**

Jessie (and Posty) have gone silent to Slack several times, then come back on their
own. This is the running record of what the evidence says, so whoever gets server
access knows what to check and in what order. Nothing here is fixed in the n8n
workflows — the fault is in the network path between the box and the internet.

## When it has happened

| Date        | Down (Manila)        | Recovered | Notes                                  |
|-------------|----------------------|-----------|----------------------------------------|
| 2026-09-02  | ~morning             | same day  | first noticed                          |
| 2026-09-03  | ~09:00–10:20         | ~10:20    | recovered around mid-morning           |
| 2026-09-05  | 00:05–13:03 (~13 h)  | 13:03     | best-documented; both bots same second |

Recurring, roughly overnight-to-midday, self-recovering.

## What the evidence rules in and out

| What we observed | What it means |
|---|---|
| Scheduled jobs (pruner 04:00, index 02:00) ran *during* outages | n8n itself was alive — not crashed |
| The backup, run from GitHub *outside* the network, could not reach the box at ~05:00 on Sep 4 and 5 | The box was unreachable from the internet — not merely stuck inside |
| Both bots dropped and recovered at the **same second** (Sep 5: Posty 13:03:13, Jessie 13:03:31) | One shared front door failed, not either bot |
| n8n's own logs show nothing at the moment it fails | The failure is below n8n — it never sees the lost messages |
| `EAI_AGAIN` / "DNS server returned an error" appear minutes before | DNS is unhealthy around the failures |
| The backup hits n8n's API directly, not Slack, and still failed | **Not** a Slack-side problem |

**Conclusion:** alive inside, unreachable from outside → the fault is the network
path between the box and the internet. Not n8n, not the workflows, not Slack.

## The suspects, most likely first

| # | Cause | Why it fits | How to confirm |
|---|---|---|---|
| 1 | **Cloudflare tunnel (`cloudflared`) drops and reconnects** | Tunnel is the one shared door for both bots; a drop stops all inbound and self-heals on reconnect | Read the `cloudflared` container log from a failure window for disconnect/reconnect lines |
| 2 | **Site internet flaps** (ISP blip, router reboot, public IP change) | Cuts the box off in and out, both bots; recovers when the link/lease restores | Continuous ping from the box to the internet; check router/ISP logs and whether the public IP changed |
| 3 | **DNS flapping** | The `EAI_AGAIN` errors; likely a *trigger* for 1/2 rather than the root | Check the box's DNS resolver; try a fixed resolver (1.1.1.1 / 8.8.8.8) |
| 4 | **Mac power management** (sleep / nap / network throttle overnight) | Fits the overnight timing; jobs still fire but the network suspends | `pmset -g`; Console sleep/wake log at the outage times |
| 5 | **Dynamic IP / DHCP lease change** breaks the tunnel routing | Overnight lease renewals match the timing | Watch the public and LAN IP across a failure |

Less likely, given the evidence: Docker networking (would not self-recover), n8n
resource exhaustion (the box stayed alive and Sep 5 recovered with no pruning),
Slack-side delivery (ruled out above).

## The one check that decides it

Get the **`cloudflared` log from a failure window** (outages cluster around 5am
Manila). If it shows the tunnel disconnecting and reconnecting at those times, it is
#1. If the tunnel log is clean but the box was still unreachable, it is the link
itself (#2).

## What would catch the next one live

An **external uptime monitor** (UptimeRobot, Better Stack, or Cloudflare Health
Checks) pinging the public URL every minute. It watches from outside, so it works
even when the box's own network is down, and it alerts the moment Jessie drops —
instead of finding out hours later. This is the single highest-value thing not yet
in place. It needs the owner's accounts, not a code change.
