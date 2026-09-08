# External uptime monitor — setup

**Purpose:** catch the Cloudflare tunnel dropping, from *outside* the VM. This is the one
failure mode the on-VM tooling can never see — when the tunnel or the box's network goes
down, anything running on the box goes dark with it. A hosted monitor sits outside all of
it and alerts the moment Jessie's public route fails.

Flagged in [OUTAGES.md](OUTAGES.md) as "the single highest-value thing not yet in place."
It **detects and timestamps** the outage; it does not fix the tunnel. Those timestamps are
what let us confirm the connector-machine-sleeps hypothesis (see EOD-2026-09-08) by lining
them up against the connector's sleep/wake log.

## What to use

**UptimeRobot free** (recommended) — 50 monitors, 5-minute checks, Slack/email/push
alerts. Our outages last hours, so 5-minute checks are more than enough; the free tier is
sufficient and there is no need to pay. BetterStack free (10 monitors, 3-minute) is an
equivalent alternative if preferred.

Nothing installs on the VM. It is a hosted service that pings the public URL from its own
servers. The only setup is creating the account and adding the two monitors below.

## It needs no n8n access

The monitor sends an anonymous public GET — no n8n login, no API key, no credentials. It
sees only the HTTP status code (and, optionally, a keyword in the body). It cannot see
bookings, executions, or anything behind auth. The only account involved is the
UptimeRobot account itself, which is unrelated to n8n.

## The monitor

One monitor. It targets the actual recurring outage — the tunnel drop — and nothing else.

| Field | Value |
|---|---|
| Type | HTTP(S) |
| URL | `https://signal.hitpromanila.net/healthz` |
| Method | GET |
| Expected status | **200** |
| Interval | 5 min |
| Alert | Slack channel + phone (push/SMS) |

When healthy, `/healthz` returns `200 {"status":"ok"}` fetched through the tunnel from
n8n (confirmed: `cf-cache-status: DYNAMIC`, so it reaches origin, not an edge cache). If
the tunnel drops, Cloudflare returns **530 / 502** or the request times out → the check
fails → you are alerted, with a timestamp. This is the failure mode the on-VM tooling
cannot see, and the whole reason to add an external monitor.

> Endpoint state verified on setup day: `/healthz` → 200.

**Webhook registration is deliberately not monitored here.** A 404 on the webhook path
means the route was deregistered (an operator fault from test-listening) — not Slack, and
not the recurring tunnel/DNS outage this monitor is for. The on-VM `webhook-canary` already
watches registration, so an external monitor for it would only duplicate the canary and add
noise. This doc stays focused on the tunnel/DNS problem.

## Alerts

Route to a Slack channel **and** a phone (push or SMS). The monitor is a third party
outside our network, so its alerts arrive even when the tunnel is completely down — unlike
anything that depends on the box.

## Caveat — Cloudflare may block the monitor

Cloudflare can block automated requests, and it was **observed doing exactly that** in the
3 Sept docker log (it blocked Slackbot and Facebot crawlers). If a bot-fight rule or WAF
blocks UptimeRobot, you will get **false "down" alerts** while n8n is actually fine.

Plain requests get through today (a manual GET to `/healthz` returns 200 cleanly). But if
the monitor starts flapping after setup, the cause is likely Cloudflare, not n8n. Fix:
allowlist UptimeRobot in Cloudflare — its published IP ranges, or a WAF skip rule for its
user-agent. Tell Genzo up front so a false alarm is not mistaken for a real outage.

## Setup steps

1. Create a free UptimeRobot account (Howard or Genzo). This is the only manual step and
   the only account required.
2. Add the `/healthz` → 200 monitor with the values above.
3. Connect a Slack alert contact + a phone contact.
4. Confirm the monitor reads "up" while Jessie is working — that is the baseline; a later
   "down" then means something genuinely changed.
5. If the monitor flaps, check Cloudflare bot protection before assuming an outage.

## How this fits the other layers

| Layer | Runs where | Catches |
|---|---|---|
| `scripts/webhook-canary` | on the VM (Genzo) | signature mismatch, webhook deregistration — but blind to its own host being down |
| VM health / debug / journald logs | on the VM (Genzo) | DNS, resource, container, kernel issues |
| **External monitor (this doc)** | **hosted, outside** | **tunnel drop / box unreachable — the gap the others can't see** |
