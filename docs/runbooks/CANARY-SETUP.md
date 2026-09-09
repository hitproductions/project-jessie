# Canary setup — for Genzo

Deploys `scripts/webhook-canary` on the n8n host so Slack→n8n delivery is checked
continuously instead of being discovered by a person noticing Jessie is quiet.

Background: [OUTAGE-2026-09-02.md](../../OUTAGE-2026-09-02.md). Short version — on
2 September Jessie silently rejected every Slack event for hours because the signing
secret in her n8n credential did not match the Slack app. Nothing looked wrong:
`/healthz` was 200, the webhook was registered, and an unsigned probe returned the
same 401 a healthy endpoint returns. It went unfound for two days.

## What it checks

| Check | Detects | Needs |
|---|---|---|
| Unsigned POST to the production path | **Webhook deregistered.** Registered = 401, deregistered = 404. Happens when someone test-listens or unpublishes a live Slack Trigger. | nothing |
| Correctly signed `url_verification` | **Signing-secret mismatch.** A 401 to a *signed* request means every real Slack event is being rejected too. | the app's signing secret |
| `GET /healthz` | Instance unreachable | nothing |

The second check is the one that matters most, and it is the one an unsigned probe
cannot do — a healthy endpoint and a broken one both answer 401 to unsigned traffic.

n8n validates the signature *before* handling `url_verification`, so the signed probe
tests the secret end to end while creating **no execution and no Slack traffic**.
Verified against this instance on 2026-09-04.

## Prerequisites

`bash`, `curl`, `python3` (standard library only). No n8n changes, no restart, no
workflow import. Read-only against n8n.

## 1. Place the files

The script reads `../.env` relative to itself, so either keep that layout or supply
the variables from the environment (step 2 covers both).

```
/opt/jessie-canary/
├── .env                     chmod 600
└── scripts/
    └── webhook-canary       chmod 755
```

Copy `scripts/webhook-canary` from this repo. It is self-contained.

## 2. Configure

Create `/opt/jessie-canary/.env`:

```
N8N_BASE_URL=https://signal.hitpromanila.net
JESSIE_SLACK_SIGNING_SECRET=<from the Slack app that owns the Jessie bot>
POSTY_SLACK_SIGNING_SECRET=<from the Slack app that owns Posty>

# optional
N8N_API_KEY=<read-only use: adds a "newest execution" info line>
CANARY_ALERT_WEBHOOK=https://hooks.slack.com/services/...
CANARY_STATE_FILE=/var/lib/jessie-canary/state
```

```
chmod 600 /opt/jessie-canary/.env
```

**Signing secrets:** api.slack.com/apps → the app → *Basic Information* →
*App Credentials* → *Signing Secret*. Two different apps — Jessie's and Posty's.
Mixing them up produces a `FAIL` on a perfectly healthy instance, so verify in step 3
while Jessie is known to be working.

These are the same secrets already stored in the n8n credentials `Jessie Slack
(signed)` (`EcX8szEJrOLYLUfl`) and `Posty Slack (Bot)` (`nmFoMiSOz2wjLG1I`). The
canary needs its own copy because it deliberately does not read n8n's credential
store — the whole point is to detect the two drifting apart.

**Alerting:** `CANARY_ALERT_WEBHOOK` takes a Slack Incoming Webhook URL. It posts only
when the status *changes* (ok→fail and fail→ok), so a 10-minute schedule does not
spam. Outbound Slack posting is independent of inbound event delivery, so the alert
still arrives when Slack→n8n is completely dead.

If systemd is preferred over the `.env` file, drop it and point `EnvironmentFile` at
the same content — the script accepts the variables from the environment when no
`.env` is present.

## 3. Verify, while Jessie is working

```
/opt/jessie-canary/scripts/webhook-canary
```

Expected:

```
ok    /healthz 200
ok    jessie registered (401 to unsigned probe)
ok    jessie signature accepted (200)
ok    posty  registered (401 to unsigned probe)
ok    posty  signature accepted (200)
info  newest execution N min ago (...) — quiet gaps are normal, not a fault
```

**Do not skip this.** Those two `signature accepted` lines are the baseline that
proves the secrets are correct today. Without them, a later `FAIL` is ambiguous —
nobody will know whether the secret just broke or was never right.

### One DNS caveat, specific to running on the n8n host

The canary must reach n8n **the way Slack does** — out to Cloudflare and back through
the tunnel. If `signal.hitpromanila.net` resolves to `127.0.0.1` or the container on
this host (a `/etc/hosts` entry or split-horizon DNS), the probe bypasses Cloudflare
and tests much less than it appears to. Confirm:

```
getent hosts signal.hitpromanila.net
```

That should return a Cloudflare address, not a loopback or private one. If it returns
a local address, run the canary from a different machine instead.

## 4. Schedule it

systemd timer, every 10 minutes:

`/etc/systemd/system/jessie-canary.service`
```
[Unit]
Description=Jessie/Posty Slack webhook canary
After=network-online.target

[Service]
Type=oneshot
ExecStart=/opt/jessie-canary/scripts/webhook-canary --quiet
```

`/etc/systemd/system/jessie-canary.timer`
```
[Unit]
Description=Run the Slack webhook canary every 10 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=10min
AccuracySec=30s

[Install]
WantedBy=timers.target
```

```
systemctl daemon-reload && systemctl enable --now jessie-canary.timer
```

`--quiet` prints nothing and exits 0 when healthy, so the journal only carries
failures. Check it with `systemctl list-timers jessie-canary.timer` and
`journalctl -u jessie-canary.service`.

Cron equivalent, if preferred:

```
*/10 * * * * /opt/jessie-canary/scripts/webhook-canary --quiet
```

## 5. Test the alert path deliberately

An alert nobody has ever seen arrive is not an alert. Force one:

```
CANARY_ALERT_WEBHOOK=<hook> N8N_BASE_URL=https://signal.hitpromanila.net JESSIE_SLACK_SIGNING_SECRET=deliberately-wrong /opt/jessie-canary/scripts/webhook-canary jessie
```

That should exit 3, print the signing-secret failure, and post to Slack. Then delete
`$CANARY_STATE_FILE` so the next real run re-baselines to `ok`.

## Known blind spot

A canary running on the n8n host cannot report that the host or tunnel is down — it
would simply stop running, and silence looks identical to health.

Cover that with an **external** HTTP monitor on
`https://signal.hitpromanila.net/webhook/jessie-slack-webhook/webhook`, POST, expected
status **401**. No secret required, and any uptime service can do it. That catches
both "host unreachable" and "webhook deregistered" from outside. The signed check
stays on the host, because it needs the secret.

## When it fires — triage

| Canary says | Meaning | Action |
|---|---|---|
| `WEBHOOK DEREGISTERED (404)` | Someone test-listened or unpublished a live Slack Trigger. Events are being dropped right now. | Republish the workflow. Never test-listen a live one — n8n cannot serve test and production at once. |
| `SIGNING SECRET MISMATCH` | Endpoint 401s a correctly signed request, so it rejects every real event too. Silent: no execution, no log line. | Re-copy the Signing Secret from the Slack app into the n8n credential on that trigger. This was the 2 September fault. |
| `/healthz` not 200 | Instance or tunnel down | Normal infrastructure check |
| Everything `ok`, but messages still dropping | Not n8n. Either Slack is not sending, or Cloudflare is dropping Slack's POSTs. | Slack app → Event Subscriptions (failure counts, disable events), and Cloudflare → Security Events filtered to the webhook path. **Do this the same day** — Security Events retention is short on lower plans. |

## Two related asks, same visit

Both need a container recreate, so worth doing in the same window:

1. **`N8N_LOG_LEVEL=debug`**, plus `N8N_LOG_OUTPUT=console,file` and a log file inside
   the persisted volume (`/home/node/.n8n/logs/`) with size and count caps. At `info`,
   n8n records **nothing** when it rejects a request for a bad signature — that single
   omission is why the 3 September outage still has no established cause. Check
   whether 2.25.7 supports `N8N_LOG_SCOPES`; full debug on an instance already logging
   100+ runner registrations a day will be noisy. Temporary — revert once the next
   occurrence is captured.

2. **After any restart or recreate, run the canary.** Recreating re-registers every
   webhook, and re-registration is exactly when this breaks.
