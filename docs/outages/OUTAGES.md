# The outages — what we know

Jessie and Posty go silent to Slack, then recover on their own with nobody touching
them.

**State as of 16 September. The mechanism is found: Cloudflare is issuing Managed
Challenges to automated callers, and a challenge no machine can solve is a 403.** Slack
support confirmed the 403s and said they had turned off event dispatch because of them;
a captured `cf-mitigated: challenge` header proves the response is Cloudflare's. What
remains unknown is only *which rule or setting* issues the challenge — one lookup in
Cloudflare's Security Events answers that.

Whether this also explains the earlier outages (3, 5, 7–8 September) is not proven. It
fits all of them, and nothing else found so far fits any of them.

Nothing here is fixed in the n8n workflows. The fault has never been in the workflows.

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

## Confirmed: 14–15 September — Cloudflare 403 to Slack, dispatch disabled

Slack support, in writing, in response to a request for their delivery records:

> It seems that Event dispatches to this App were turned off because for at least the
> past 24 hours, every HTTP Request we've sent to the Event Request URL for your App
> has received HTTP 403 Response.

This is the first evidence from the sending side, and it is decisive about the
mechanism. Two things follow from it.

**The 403 is Cloudflare's, not n8n's.** n8n has no code path that returns 403 for this
URL. Its two responses are:

| Response | Source | Means |
|---|---|---|
| `404` + `not registered for GET requests. Did you mean POST?` | n8n | webhook is live |
| `401 Unauthorized` (12 bytes) | n8n | reached n8n, signature rejected |
| `403` | **Cloudflare edge** | never reached the tunnel, never reached n8n |

A 403 is returned before the request enters the tunnel. That is why n8n logged
nothing, cloudflared logged nothing, and the canary stayed green: **there was nothing
on our side to log.**

**It discriminates by source IP.** Probed from Tara's Mac on a residential connection
at 15 Sep 08:22 UTC, the same URL returned **401** — through Cloudflare, through the
tunnel, into n8n, rejected there only because the probe carried no valid Slack
signature. The whole path was up. Slack, from AWS, got 403 at the edge.

This is exactly the blind spot the 8 September write-up flagged: a check that leaves
from our own IP cannot see Cloudflare treating someone else's IP differently.

### When it started

The nightly backup runs from a GitHub Actions runner — a datacenter IP, like Slack's —
twice a day. It is an unintentional but continuous probe of exactly the condition that
matters.

| Run (UTC) | Result |
|---|---|
| 6 Sep through 13 Sep 15:50 | **20 consecutive successes** |
| **14 Sep 11:45** | **failure** |
| **14 Sep 17:54** | **failure** |
| **15 Sep 11:02** | **failure** |
| **15 Sep 16:34** | **failure** |

So datacenter-IP access broke between **13 Sep 15:50 UTC and 14 Sep 11:45 UTC** and has
not recovered since. That window is independent of Slack's account and agrees with it.

**The failure is a Cloudflare Managed Challenge, captured verbatim** from the 15 Sep
16:34 run:

```
HTTP/2 403 | cf-mitigated: challenge | server: cloudflare | cf-ray: a3b90afebfcd9b19-PDX
<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>
```

`cf-mitigated: challenge` and the "Just a moment…" interstitial identify a **Managed
Challenge**. This matters more than it looks: **no automated client can ever solve one.**
There is no browser to run the JavaScript. For Slack, GitHub, an uptime monitor or any
other machine caller, a challenge is simply a permanent 403 on that request.

That `cf-ray`, `a3b90afebfcd9b19`, is the key to Cloudflare → Security → Events, which
will name the exact rule or service that issued it.

### Two things that do not line up — do not smooth them over

1. **Jessie received events at 14 Sep 23:00 and 15 Sep 00:00 UTC** (execs 8819 and
   8821), which sits inside Slack's "at least the past 24 hours." Either Slack's agent
   was approximating, or dispatch was disabled shortly after those two got through.
   Worth asking Slack to give the exact time the 403s began.
2. **The earlier claim that the GitHub backup was being challenged intermittently
   through early September does not survive the run history above** — 6 to 13 September
   is 20 clean runs. Whatever produced the earlier 403s, the clean datacenter signal
   starts on 14 September. Treat pre-14-September GitHub evidence as unreliable.

3. **GitHub is challenged on every run since 14 September, yet Slack delivered seven of
   nine test messages on the night of 15–16 September.** So this is not a blanket block
   on datacenter traffic. Cloudflare scores each source address, and Slack's dispatch
   IPs mostly pass where GitHub's runners never do.

**That third point is the explanation, not an inconsistency.** Slack dispatches from a
pool of addresses. Most of them clear Cloudflare; occasionally one does not, and every
event sent from it is challenged and lost. The bot goes silent until Slack happens to
dispatch from an address that passes. Nobody has to do anything for it to break, and
nobody has to do anything for it to recover.

That single mechanism accounts for every property of these outages that made them so
hard to chase: no execution and no log line on our side, because nothing arrived; a
green canary, because the canary leaves from the VM's own IP; breakage across an idle
weekend, because the trigger is Cloudflare's opinion of Slack's IPs rather than our
traffic; and self-healing, because the IP pool rotates.

### What could produce an intermittent 403 at Cloudflare

Ranked by how well each explains *all* the observed behaviour — invisible to the
origin, source-discriminating, needs no traffic from us, and turns itself off again.

1. **Bot Fight Mode / Super Bot Fight Mode.** Blocks traffic scored "definitely
   automated," which is what a webhook dispatcher from AWS looks like. Returns 403,
   logs nothing at the origin, and varies as bot scores and IP pools shift. Fits every
   property including the self-healing. **Most likely.**
2. **HTTP DDoS managed ruleset auto-mitigation.** Cloudflare turns mitigations on and
   off by itself when it detects a pattern. Explains onset and recovery with nobody
   touching any setting.
3. **Security Level set to High, or IP-reputation challenges.** Datacenter IPs fail
   challenges they cannot solve. Intermittent as Slack rotates dispatch IPs.
4. **Browser Integrity Check**, or a **custom WAF rule whose action is Managed
   Challenge**. Both produce exactly this response.

**Narrowed by the captured header.** `cf-mitigated: challenge` means the action was a
*challenge*, not a block. That removes everything that blocks outright: an IP or ASN
access rule set to Block, a WAF managed rule firing on payload content, and rate
limiting (which returns 429). Whatever is configured, it is something that issues
challenges — and a challenge to a machine is a block, because no non-browser client can
solve one.

**One lookup ends the guessing.** `cf-ray: a3b90afebfcd9b19` is from the 15 Sep 16:34
run. In Cloudflare → Security → Events, search that ray id: the entry names the exact
service or rule that issued the challenge. That is the GitHub request rather than
Slack's, but it is almost certainly the same rule, and it is available right now without
waiting on Slack.

### The fix, when the cause is named

A WAF **skip** rule on the webhook paths for `signal.hitpromanila.net`, so no bot,
reputation or challenge logic is applied to them. Slack's dispatcher can never solve a
challenge, so any rule that can challenge that path will eventually take the bots down
again. This needs doing before launch (12 October) regardless of whether it is down today.

## The measured outages — 15 and 16 September

Hourly test messages were scheduled through Slack and checked against n8n executions.
These are the only outages whose start and end are measured rather than inferred
backwards from "the last message that worked." The method is cheap and should be the
default whenever this is being investigated.

### Night of 14–15 September

| Sent (PHT) | UTC | Reached n8n? |
|---|---|---|
| 02:12:56 | 14 Sep 18:12:56 | no |
| 02:14:54 | 14 Sep 18:14:54 | no |
| 02:23:34 | 14 Sep 18:23:34 | no |
| 03:00:00 | 14 Sep 19:00:00 | no |
| 04:00:03 | 14 Sep 20:00:03 | no |
| 05:00:02 | 14 Sep 21:00:02 | no |
| 06:00:00 | 14 Sep 22:00:00 | no |
| 07:00:00 | 14 Sep 23:00:00 | **yes** — exec 8819, replied 07:00:20 |
| 08:00:12 | 15 Sep 00:00:12 | **yes** — exec 8821, replied 08:00:28 |

Recovery happened between **22:00 and 23:00 UTC on 14 September**, with nobody touching
anything. The pruner ran at 04:00 PHT, mid-outage, and changed nothing.

Every one of those messages posted to Slack successfully and is in the conversation
history. Slack accepted them; the dispatch is what failed.

### Night of 15–16 September

Nine messages, 23:00 through 07:00 PHT. Jessie only.

| Sent (PHT) | UTC | Reached n8n? |
|---|---|---|
| 23:00 | 15 Sep 15:00 | yes — exec 8939 |
| 00:00 | 15 Sep 16:00 | yes — exec 8941 |
| 01:00 | 15 Sep 17:00 | yes — exec 8943 |
| 02:00 | 15 Sep 18:00 | yes — exec 8945 |
| 03:00 | 15 Sep 19:00 | yes — exec 8948 |
| 04:00 | 15 Sep 20:00 | yes — exec 8950 |
| **05:00** | **15 Sep 21:00** | **no** |
| **06:00** | **15 Sep 22:00** | **no** |
| 07:00 | 15 Sep 23:00 | yes — exec 8953 |

**Outage window: 21:00–22:00 UTC (05:00–06:00 PHT), recovered by 23:00 UTC.** Both
missing messages are in the Slack conversation history, posted normally; Jessie did not
reply to either, and n8n has no execution for either. The messages on both sides got
replies within 20 seconds.

### Night of 16–17 September

Nine messages again, same schedule. Confirmed twice over: Slack shows which messages
Jessie replied to, and the execution list agrees exactly.

| Sent (PHT) | UTC | Reached n8n? |
|---|---|---|
| 23:00 | 16 Sep 15:00 | yes — exec 9079, replied 23:00:45 |
| 00:00 | 16 Sep 16:00 | yes — exec 9081, replied 00:00:38 |
| 01:00 | 16 Sep 17:00 | yes — exec 9083, replied 01:00:18 |
| **02:00** | **16 Sep 18:00** | **no** |
| **03:00** | **16 Sep 19:00** | **no** |
| **04:00** | **16 Sep 20:00** | **no** |
| **05:00** | **16 Sep 21:00** | **no** |
| **06:00** | **16 Sep 22:00** | **no** |
| 07:00 | 16 Sep 23:00 | yes — exec 9087, replied 07:00:29 |

**Outage window: 18:00–22:00 UTC (02:00–06:00 PHT), recovered by 23:00 UTC.**

### Three nights, one recovery hour

| Night | Down (PHT) | Back by |
|---|---|---|
| 14–15 Sep | 02:12 – 06:00 | 07:00 |
| 15–16 Sep | 05:00 – 06:00 | 07:00 |
| 16–17 Sep | 02:00 – 06:00 | 07:00 |

The start times vary. **The recovery hour does not.** Three nights running, service
returns between 06:00 and 07:00 Manila (22:00–23:00 UTC).

**This is the most useful fact in this file, and it argues against the explanation
above.** Per-request IP scoring should not respect a daily boundary. Something that
recovers at the same hour every night looks scheduled: a rule with a time condition, a
reputation or bot-score feed that refreshes daily, a rate-limit counter resetting, or a
cache expiring. Whoever looks at the Cloudflare side should be told this, because it
narrows the search from "which rule" to "which rule has a daily cycle."

Worth keeping honest: three points is a pattern, not a proof, and every test message was
sent on the hour, so the resolution is one hour and no better. Recovery could fall
anywhere in 06:00–07:00. Messages every fifteen minutes across that hour would pin it
down and cost nothing.

**This gives an exact hour to look up.** Cloudflare → Security → Events, filtered to
`signal.hitpromanila.net`, 21:00–22:00 UTC on 15 September. Slack's blocked requests
should appear there with the rule that caught them. If nothing appears in that hour at
all, Slack never dispatched and the fault is upstream of Cloudflare.

## Not solved: 3, 5, 7–8 September

Recorded: 3 Sep (~09:00–10:20), 5 Sep (00:05–13:03, ~13 h), 7–8 Sep (overnight).
Not credential, not restart, not test-listen, not load.

The Cloudflare 403 mechanism fits all of them — same invisibility, same
self-healing, same green checks from the VM — but there is no direct evidence for those
dates. Do not record them as explained.

### What is established

- Both bots stop receiving; n8n itself stays up — scheduled jobs run straight through
- **Outbound works mid-outage** — Posty Index reached Google Sheets and Slack's API at
  02:00 on 8 Sep, inside the outage
- **Cloudflare→origin worked mid-outage from the VM's own IP** — at 02:35 a request
  returned real n8n JSON while Jessie was dead. This says nothing about Slack's IPs
- It needs **no traffic from us** — it has broken across a weekend with nobody using it
- It needs **no human** — it heals itself
- **Not the signing secret** — the secret is unchanged and it still heals itself
- n8n has **79 days uptime**; no restarts, no OOM, disk 34% used
- **SQLite ruled out** — no lock or disk errors, contiguous execution ids, no latency
  creep before either stall, and the heaviest hour of 2–3 Sep ran clean

### Ruled out

| Suspect | Killed by |
|---|---|
| Signing secret expiring or rotating | secret unchanged, still self-heals |
| n8n crashing or restarting | 79 days uptime, scheduled jobs run through it |
| The box offline, or its DNS broken | outbound worked mid-outage |
| SQLite / execution table | see above |
| Per-workflow webhook registration | independent per bot; cannot explain both |
| Anything triggered by *our* traffic volume — throttling, fail2ban | it breaks across an idle weekend |

**Removed from this table on 15 September:** "bot challenges." They were ruled out on
the grounds that nothing we did could trigger one. That reasoning was wrong — the
trigger is the reputation and classification of *Slack's* source IPs, which has nothing
to do with our traffic. Slack has now confirmed 403s.

### The 8 September window — the one with instrumentation

Genzo's canary and `N8N_LOG_LEVEL=debug` were both running for 00:00–05:00 PHT on
8 Sep, inside a window where Jessie was not answering.

| Check | Result across the window |
|---|---|
| public n8n health, through the tunnel | **200 × 278**, no gap over 90s |
| jessie webhook registration | **401 `route_present_signature_rejected` × 278** — registered throughout |
| n8n errors / DNS / `db_locked` / OOM | **all zero** |
| webhooks n8n actually received | **278 — every one the canary's own probe** |

A test Slack message was sent at **18:35:53 UTC (02:35:53 PHT)**. The canary probes
land on a strict 65s beat, so the nearby receive is the canary. **There is no extra
receive anywhere in the window.**

**So the message never reached n8n**, while the tunnel was up, the webhook was
registered, and n8n was healthy. That is precisely the signature of an edge 403.

**The blind spot, now the main event:** the canary runs *on the VM*, so its "public"
check leaves and returns from the VM's own IP. It cannot detect Cloudflare treating
**Slack's** IPs differently. A green canary does not clear Cloudflare. The external
monitor in `MONITOR-SETUP.md` exists to close this gap and is still not in place.

## Theories that were wrong — do not re-chase

| Theory | Why it is wrong |
|---|---|
| **Host DNS causes the outages** | The `EAI_AGAIN` errors are on *outbound* calls. The outages are inbound. Outbound worked mid-outage. Written into SERVER-NOTES as the cause; it was not. |
| **SQLite / execution table filling** | Ruled out with specific evidence. Pruning once coincided with recovery; 5 Sep recovered with no pruning. |

**A retraction that was itself wrong.** "Cloudflare challenges Slack's servers" was in
this table until 15 September, dismissed because the evidence for it — a GitHub Actions
runner getting 403 — had been treated as a stand-in for Slack without justification.
The evidence was bad; the conclusion was right. Slack has now confirmed the 403s
directly. **Bad evidence for a claim is not evidence against it**, and writing the
theory into a do-not-chase list on that basis cost roughly a week.

**And a method note, because it produced most of this section.** Several
"eliminations" came from a single probe taken hours into a multi-hour outage, then
written up as covering the whole window. A reading at 02:35 says nothing about 22:51.
Anything measured mid-outage needs its timestamp recorded and its scope stated. The
same applies to *where a probe is sent from*: a request from the VM and a request from
AWS are different experiments.

## Data point: 28 September — one message 60 s late, recovered by Slack's retry

Howard DM'd "hello" at **04:06:44 UTC** (Slack event ts 1790568404.56). No execution was created for Slack's first
attempt; the execution started at **04:07:44.84, 60.3 s later** — the one-minute step of Slack's retry schedule. Every
other message that hour, both directions, arrived in ~1 s (execs 13616-13619), and the conversation then ran normally.
Checked at the time: n8n up, trigger registered (unsigned POST 401), the public URL answered 404 (n8n) — not 403 — from
both a home connection and a datacenter IP, and Posty had received Slack events at 01:00 UTC. Nothing was changed; it
recovered on its own. Earlier that morning the Jessie workflows had been imported (03:33 UTC) and the eval twin, which has
no Slack trigger, was deactivated at ~04:05:08 — no known mechanism links either to a dropped delivery 1.5 minutes later.
Same shape as 2 September's "61 s late: a Slack retry". Without an external monitor (PENDING 15) or Cloudflare's Security
Events for that minute, whether the first attempt met a 403 at the edge cannot be told.

## Data point: 29 September — silent for about 2 hours (~09:48 to ~11:55 PHT)

**Onset window: between 09:47:33 and 10:14 PHT** (01:47:33–02:14 UTC).
- **Last Slack event that reached n8n:** 09:47:33 PHT, exec 16291 (Jessie's own reply to a QA booking request, echoed
  back by Slack). The request before it came in at 09:46:22 PHT (exec 16289), so events were flowing normally in both
  directions until then.
- **First known miss:** Howard DM'd "hello" at **10:14 PHT**. No execution, no reaction, no reply. Nothing reached n8n
  after 09:47:33.
- **Just before the onset:** main v181 was imported at ~09:42 PHT (updatedAt 01:41:55 UTC). The two turns above ran on
  it normally afterwards, so the import did not stop delivery by itself; recorded because it is the nearest change.

**Checked 10:20–10:24 PHT, from a home connection (Cloudflare MNL):**
- n8n up: `/healthz` 200 `{"status":"ok"}` in 0.08 s (cf-ray `a427822e5c2e7d23-MNL`); API 200; editor 200.
- Jessie's trigger listening: unsigned POST to `/webhook/jessie-slack-webhook/webhook` → **401** (reached n8n, rejected
  for no signature). GETs to both `jessie-slack-webhook` and `posty-slack-webhook` → "not registered for GET" (live).
- n8n's scheduled jobs kept running: Consent Sweep 10:10 and 10:20, Refresh Reference Cache 10:20.
- Posty's last Slack event was at 09:00 PHT; it gets too little traffic to say whether it is affected too.

So n8n, the tunnel and the webhook registration all look healthy from our side, and **Slack's deliveries are not
arriving** — the same shape as 3, 5, 7–8 and 15 September. **Not yet done:** the datacenter probe (step 1), Cloudflare
Security Events for 09:47–10:24 PHT (step 3), the Slack app's Event Subscriptions status (step 4) and the container log
(step 5).

**Recovery: by 11:55 PHT (03:55 UTC).** The first Slack event to arrive again was Howard's "what can i book for a
meeting?", sent 11:55:23 and processed 11:55:24 (exec 16361); nothing arrived between 09:47:33 and then. Delivery was
still uneven at the very start: a "hello" sent at 11:54:48 was processed at 11:55:49 (exec 16364), 61 s late — Slack's
one-minute retry — so it was answered after the question sent 35 s after it. Nothing was changed on our side before
recovery; the Slack app's Event Subscriptions stayed enabled and "Verified" throughout (checked ~10:30 PHT). As on 15
September, no cause is visible from our side; Cloudflare's Security Events for 09:47–11:55 PHT is the lookup that
would settle it.

## Data point: 29 September, second drop — silent ~14:05–14:08 PHT (about 4 minutes, recovered on its own)

**Last Slack event that reached n8n:** 14:04:46 PHT (exec 16675, Jessie's own "Moved …" reply echoed back), right after a
normal run of live QA turns that had been arriving within about a second (13:59–14:04). Howard then got no reaction or
reply; nothing reached n8n after 14:04:46.
- **Nearest change:** main v186 + Book Session v62 imported at 14:02:46–14:02:48 PHT. Four turns ran normally on them
  afterwards (14:02:59–14:04:46), so, as in the morning, the import did not stop delivery by itself.
- **Checked 14:08 PHT, home connection:** `/healthz` 200 (0.26 s); unsigned POST to `jessie-slack-webhook` → 401 (n8n
  reached, listening); GET → "not registered for GET" (live); Refresh Reference Cache ran at 14:05, Consent Sweep at 14:00.

Same shape as the morning drop (09:47–11:55): n8n healthy and reachable from here, Slack's deliveries not arriving. Two
drops in one day, each a few minutes after an import, is worth noting but not yet a pattern: the morning one began two
minutes after the v181 import, this one about two minutes after v186, and in both cases turns ran normally in between.
**Recovered 14:08:56 PHT:** exec 16680 at 14:08:57, a new message (its Slack `ts` is 14:08:56, so a fresh send and not a
late retry of anything sent during the gap). Turns then ran normally from 14:09:57 on. Whatever the requester sent between
14:05 and 14:08 never reached n8n, not even as a Slack retry. Nothing was changed to fix it. Short enough that Slack
did not disable event dispatch; as with every drop, only Cloudflare Security Events for 14:04–14:09 PHT would say whether
the edge refused those deliveries.

## Data point: 29 September, one message delivered 61 s late (15:41 PHT)

Not a drop: one delivery missed, and Slack's own retry brought it in. The requester's message sent at **15:41:01 PHT**
(Slack `ts` 1790667661.31) first reached n8n at **15:42:02** (exec 16877) - 61 s later, which is Slack's first retry
after an event is not acknowledged. The first attempt left no execution at all: n8n was idle (the turn before finished
at 15:41:00 in 0.1 s) and every other event in 15:40-15:42 arrived within about a second. The requester saw no
reaction, re-sent the same text at 15:41:33 (exec 16875, processed at once), and the retry then ran as well, so two
identical summaries went out. Same shape as the morning's "hello" (sent 11:54:48, delivered 61 s late): a single
delivery that never reached n8n. Something between Slack and n8n (the Cloudflare edge or the tunnel) is dropping
individual requests, not only whole windows. Cloudflare's logs for 15:41:01 PHT would show whether the first attempt
was answered at the edge.

## Data point: 29 September, 16:16 PHT - three of four deliveries in 30 s arrived 61 s late

The clearest case yet of single deliveries failing while n8n is idle and healthy. Between 16:16:24 and 16:16:51 PHT
Slack sent four events; three first reached n8n exactly 61 s later (Slack's first retry), one arrived on time:

| Sent (Slack ts) | Event | First reached n8n |
|---|---|---|
| 16:16:24 | Jessie's summary (echo) | 16:17:25 (exec 16953), 61 s late |
| 16:16:31 | requester "yes" | 16:17:32 (exec 16954), 61 s late |
| 16:16:40 | requester "yes" (re-sent) | 16:16:41 (exec 16951), on time - booked |
| 16:16:51 | Jessie's "Booked." (echo) | 16:17:52 (exec 16956), 61 s late |

n8n had finished the previous turn at 16:16:24 and was idle. The late "yes" was answered "That's already booked -
nothing else was changed" (the repeat-yes guard, bug 17), so nothing was double-booked. Probed from a home connection
at 16:19-16:21: 150 of 150 unsigned POSTs to the trigger answered 401 (reached n8n), average 0.44 s, slowest 2.1 s.

So some deliveries fail on the way in and succeed on Slack's retry a minute later, interleaved with ones that get
through - more like a fraction of requests failing (one bad tunnel connection among cloudflared's several, or an edge
rule such as rate limiting or bot protection applied to Slack's datacenter IPs) than a window where everything is
down. Our own probes do not see it, which also fits: they come from a different network. **To settle it:** Cloudflare
Security Events and the tunnel's connection log (cloudflared on the VM) for 15:41:01 and 16:16:24-16:16:51 PHT.
Same session: the 15:41:01 PHT message (above) is the same pattern.

## Data point: 29 September, 20:43 PHT - Cloudflare challenging every request, including ours

At 20:43:36 PHT every request to `signal.hitpromanila.net` - the Slack webhook (`/webhook/jessie-slack-webhook/webhook`),
the n8n API (`/api/v1/...`) and `/healthz` - was answered by Cloudflare itself: HTTP 403, `server: cloudflare`,
`cf-mitigated: challenge`, a "Just a moment..." page (cf-ray a42b131e2b60ddd8-MNL). From a home connection too, which
had always reached n8n before (401 on the webhook, 200 on healthz). Jessie had answered normally at 20:36 PHT. This is
the edge serving a managed challenge to everything - a zone setting switched on (Bot Fight Mode, a challenge rule, or
security level), most likely during the Cloudflare Pro / Super Bot Fight Mode set-up (PENDING 21), before the
exception for the webhook was in. Slack cannot pass a challenge, so every delivery fails; after enough failures Slack
turns event delivery off (as on 15 Sep). **Fix:** a WAF skip rule (or security level off) for `/webhook/*` and
`/api/*` on that hostname, before any bot-protection setting is on. **Recovered by 22:29 PHT at the latest:** the n8n UI
was usable for the hand imports from ~22:05, and Slack messages were answered normally from 22:29 (seen in the DM; the
exact time is unknown because, from 29 Sep ~20:50, Claude no longer reads n8n's executions). Afterwards IT decided Claude
does not connect to the n8n server at all (CLAUDE.md, "No direct n8n access").

## Data point: 30 September - silent from ~09:30 PHT (ongoing at 11:21)

Seen without any access to the server (IT's rule from 29 Sep), from Slack and the Turn Log only:
- **Last turn processed: 09:30:22 PHT** - the Jessie Log sheet (Turn Log tab) was last modified then, right after
  Jessie's 09:30:19 reply; nothing since.
- **11:19:39 "hello" got no reaction and no reply** - it never reached n8n (or n8n was not running).
- **Already patchy at 09:28:** "is anj a producer" sent three times (09:28:30, 09:28:44, 09:29:06), one answer
  (09:29:18). The eyes reaction on the 09:28:02 "no" was never cleared.
- Cannot tell from outside whether n8n is down or Slack's deliveries are blocked at the edge: both look the same from
  Slack and the sheet. A heartbeat (a scheduled n8n workflow writing a timestamp to the sheet every few minutes) would
  tell them apart without anyone connecting to the server. **Who can check:** IT - is n8n up; Cloudflare Security
  Events from ~09:28 PHT. **Recovered between 11:19 and 11:56 PHT** (the 11:56:22 "hello" was answered at 11:56:29; the
  11:19 one never was) - roughly 2 to 2.5 hours. The zone showed the Pro plan by then, with a spike of challenged requests
  at 10:35 in Cloudflare's security analytics (screenshot, 30 Sep); whether Slack's deliveries were among them is not
  yet confirmed (Security -> Events, path /webhook/, from 09:20).

## What to do when it next drops

Do these **while it is confirmed down**, and note the time.

**1. Probe from a datacenter IP, not from your laptop.** This is the check that would
have found it in a day. Your home connection is treated differently from Slack's
servers, so a green result from your Mac means nothing.

```bash
gh workflow run nightly-backup.yml
```

That runs the backup from a GitHub runner. If it fails with 403 while your own curl
returns 401 or 404, Cloudflare is blocking datacenter traffic and that is the outage.

**2. Are the webhooks registered?** Two GETs, from anywhere:

```
curl https://signal.hitpromanila.net/webhook/jessie-slack-webhook/webhook
curl https://signal.hitpromanila.net/webhook/posty-slack-webhook/webhook
```

| Response | Means |
|---|---|
| `not registered for GET requests. Did you mean to make a POST request?` | webhook is **live** |
| `The requested webhook "…" is not registered` | webhook is **gone** from the registry |
| `403` | **Cloudflare is blocking you** — this is the outage, not an n8n problem |

**3. Cloudflare → Security → Events**, filtered to `signal.hitpromanila.net`. Blocked
requests appear here with the rule that caught them. Nothing about this is visible from
the VM.

**4. Check the Slack app's Event Subscriptions is still enabled.** Slack disables
dispatch automatically after sustained delivery failures, and it stays disabled. A
recovered tunnel does not bring the bot back if Slack has stopped sending.

**5. Read the container log.** With `N8N_LOG_LEVEL=debug`, this shows whether Slack's
request **arrived** at all. Nothing arriving points at the edge; arriving and being
rejected points at a signature problem.

**6. `./scripts/webhook-canary`** (Genzo's) — an unsigned probe for registration plus a
*signed* verification, the only thing that catches a silent signature rejection. Note
it runs on the VM, so it cannot see an edge block.

## Still not in place

An **external uptime monitor** on the public URL, **running from outside our network**.
It would catch the drop when it happens, record the exact start and end, and — the part
that matters most — probe from a source IP that Cloudflare classifies the way it
classifies Slack's. Every argument in this file has been weakened by not knowing when
the outages actually begin.
