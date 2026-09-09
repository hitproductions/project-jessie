# Overnight outage inspection — night of 8→9 September 2026

**Bottom line: no outage overnight.** The first fully-instrumented night shows the public
path stayed up continuously. This also captured the outage *mechanism* at small scale
(DHCP lease loss) and resolves the "2am down" report.

## Background (for anyone new to this)

Jessie and Posty are Slack bots running on a self-hosted n8n instance (a Kubernetes
`cloudflared` tunnel exposes it at `signal.hitpromanila.net`). Between 2 and 5 September
they went silent to Slack several times and recovered on their own. The investigation
concluded the fault is in the **network path**, not Slack and not n8n. On 8 September
Genzo stood up VM-side logging, so this is the **first night with full instrumentation**.

## What was inspected

Genzo's observability export covering **8 Sept 12:00 → 9 Sept ~15:00 PHT**:
`canary.jsonl` (path probes every ~65 s), `vm-health.jsonl`, the DNS/network journal,
docker + system journals, an external soak CSV, and the n8n event audit — cross-checked
against n8n execution history and Slack.

## Findings

### 1. No outage — and now that's measured, not assumed

The canary probed the public path **every ~65 seconds** from 8 Sept 12:00 to 9 Sept 15:08
PHT — **4,521 probes, largest gap 1.1 min** — and was **green the entire time**, except
four probes during Genzo's 8 Sept afternoon maintenance window. n8n was running, gateway
reachable at 0.6 ms, DNS resolvers healthy.

The ~5-hour overnight gap in bot activity (22:45 → ~09:33) was **no inbound traffic**
(nobody messaged the bots overnight), **not downtime** — the path was up throughout.

### 2. The "2am down" report — no outage at 2am

The concern that it was "down around 2am" is not borne out: the canary was green every
65 s through the whole night. The reporter did not message the bot at 2am (their Slack is
silent from 8 Sept 16:54 to 9 Sept 10:21), so it was an inference, not a failed check —
phrased as "around 2am, I think."

What *was* real overnight: a 155-minute quiet stretch (22:45 → 01:20) followed by a burst
of ~30 Posty events at 01:21. A quiet-then-burst pattern can look like "down then
recovered" in activity history, but it reflects low overnight traffic plus likely Slack
pacing its delivery after brief afternoon blips — not a crash.

The linked worry — that the tunnel connector "asks to update" (an old version) and might
be crashing — is not supported: that update prompt is a daily cosmetic warning, and the
connector ran 28 days without a single restart. (The upgrade is still worth doing; see
Next actions.)

### 3. The outage mechanism, captured at small scale: DHCP lease loss

The most valuable find. On **8 Sept afternoon** the logs caught the mechanism directly
(times UTC):

```
06:46:21  ens3: DHCP lease lost               ← the VM's network interface drops its lease
06:46:23  probe: couldn't resolve host         ← 2 s later, no network → DNS fails
06:46:25  ens3: DHCPv4 192.168.0.230 acquired  ← lease reacquired 4 s after loss
```

A second lease-loss followed at 06:50. **DHCP lease loss → brief total network loss →
DNS failure → delivery would fail.** This unifies two long-standing suspects (DNS
flapping and DHCP lease change) — they are the same event.

This reconciles the entire outage profile. A 4-second lease-loss is invisible; but a
lease that **doesn't reacquire quickly, returns with a different IP, or whose DHCP server
stalls** leaves the VM with no network for hours — which is exactly what the outages
looked like: both bots down the same second (whole VM offline), n8n healthy inside
(process fine, no network), unreachable from outside, self-recovering when the lease
returns.

*Caveat:* these specific lease-losses fell inside Genzo's maintenance window, so they may
be maintenance-induced rather than spontaneous. But the mechanism is now demonstrated,
and the fix applies either way.

### 4. The Cloudflare tunnel connector is largely cleared

From Pao's `cloudflared` log (separately analysed): the connector is a stable Kubernetes
pod, ran Aug 11 → Sept 8 with **zero restarts**, and logged nothing but a daily version
warning during the real outages — no reconnects, no origin errors. So the tunnel connector
is not the cause. (One edge-side check remains — see Next actions.)

### 5. Two pieces of good news

- **DNS `EAI_AGAIN` errors: zero.** The container outbound-DNS problems from 2 September
  have not recurred — the DNS hardening worked on that layer.
- **Task-runner starvation down** — 4 occurrences in 27 hours, versus ~12/day before.

## What it means

- **The sustained outage did not recur** on the first fully-instrumented night.
- **The strongest lead has shifted** from "the Cloudflare tunnel" to **the VM's own
  network — DHCP lease loss / DNS instability.** That's a more fixable place.
- The instrumentation is working: it caught seconds-long blips that execution history
  alone would miss.

## Next actions (server), in priority order

1. **Assign the n8n VM a static IP / DHCP reservation** for `192.168.0.230` (lease comes
   from the router at `192.168.0.100`). Removes the lease-loss failure mode entirely —
   the demonstrated mechanism. **Highest priority.**
2. **Cloudflare dashboard check** for the 3 Sept / 5 Sept windows — the one edge-side view
   that confirms whether requests reached the connector. Checklist:
   [docs/runbooks/CLOUDFLARE-CHECK.md](docs/runbooks/CLOUDFLARE-CHECK.md).
3. **Upgrade `cloudflared`** off the ~18-month-old `2025.2.1` (rolling restart, low risk).
4. **Stand up an external uptime monitor** to timestamp the next drop from outside:
   [docs/runbooks/MONITOR-SETUP.md](docs/runbooks/MONITOR-SETUP.md).

Full investigation history: [OUTAGE-2026-09-02.md](OUTAGE-2026-09-02.md) and
[OUTAGES.md](OUTAGES.md).
