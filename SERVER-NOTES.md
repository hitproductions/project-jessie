# Server notes

These are the two things worth fixing on the server. Both make Jessie slow (and one
also causes the outages) because something the server does at the **start** of
handling each message is slow. Neither is fixed in the n8n workflows — the workflows
are fine, the slowness is underneath them. The plain fixes are up top; the numbers
and the outage history are in Measurements at the bottom.

---

## 1. The server is slow to look up addresses (DNS) — and sometimes fails outright

*(the numbers behind this are in Measurements, at the bottom)*

Every time Jessie talks to Airtable or Google, the server first looks up "where is
that server?" On this box that lookup is slow: it adds about **3 seconds to the
first outside call of every message** (later calls in the same message reuse it and
are fast). When the lookup *fails* completely, that's the **outages** — Jessie goes
silent because the machine briefly can't reach the internet.

This is the biggest win: it fixes the slowness **and** the outages, because they are
the same root cause.

**What to try, simplest first:**

1. Point the server and the Docker container at reliable DNS — Cloudflare `1.1.1.1`
   or Google `8.8.8.8` — instead of whatever flaky resolver it uses now.
2. Run a small local DNS cache on the machine so lookups are instant and stop
   flapping.
3. Keep network connections alive so n8n reuses them instead of re-looking-up on
   every call.

**How to confirm it worked:** watch a few messages — the first Airtable step
(`Get Booker`) should drop from ~4s toward ~1s, and the `EAI_AGAIN` / "DNS server
returned an error" lines should disappear from the container logs.

---

## 2. n8n shuts its "Code" helper down when idle; restarting it costs ~3.5s

*(the numbers behind this are in Measurements, at the bottom)*

n8n runs the small code steps in a separate helper process (the "task runner"). It
turns itself off after ~12 seconds of no activity. Since messages usually arrive
after a quiet gap, nearly every message waits ~**3.5s** for the helper to start
back up. It shows up as the `Gate Context` step being slow on most turns.

**What to try:**

- Stop the helper from shutting down, or raise its idle timeout, so it stays warm
  between messages (a setting / environment variable).
- Or run the code steps in n8n's main process instead of the separate helper
  (another environment variable) — simpler, slightly less isolation, fine for an
  internal instance.
- The exact variable names depend on your n8n version — check its task-runner docs.

**How to confirm it worked:** the `Gate Context` step should drop from ~3.5s to well
under 1s on most messages.

---

## While you're on the box — two more things that need shell access

- **The outages.** The one thing that would pin down the cause is the
  Cloudflare tunnel / `cloudflared` container's own log from a failure window
  (~5am Manila is common). n8n's own logs show nothing at the moment it drops.
- **Execution storage.** The daily pruner keeps the row count down but does not
  shrink the database file — that needs a `VACUUM`. The real long-term fix is moving
  n8n off the single-file SQLite database to Postgres.

---

## Measurements

All measured from the live n8n execution data, 2026-09-05 and 2026-09-06.

### Where a message's time goes

A typical message takes about **16.5s end to end** (median; p90 ~23s, worst seen
~33s). Nearly all of it is a few slow steps at the start, in this order every turn:

```
step                 time      what it is
------------------   -------   ------------------------------------------
Get Booker           ~4.2s     first Airtable call of the turn   (problem 1)
Gate Context         ~3.5s     first Code step, cold helper      (problem 2)
All Rooms            ~1.1s     Airtable, same base, warm now
All Session Types    ~1.1s     Airtable, same base, warm now
Jessie AI Agent      ~1.7s     the model
```

Problems 1 and 2 together are ~7.5s of that ~16.5s — about half of every message.

### Proof that problem 1 is DNS/connection, not Airtable or the query

Four consecutive real turns, showing when each step started (offset from the first
step) and how long it took:

```
             Get Booker      Gate Context     All Rooms       All Session Types
turn 5171    +0.9s  4.27s    +5.6s  3.75s     +9.3s  1.13s    +10.4s 1.16s
turn 5141    +0.9s  4.34s    +5.7s  3.46s     +9.2s  1.10s    +10.3s 1.09s
turn 5139    +0.9s  4.18s    +5.5s  3.73s     +9.2s  1.12s    +10.4s 1.14s
turn 5137    +0.8s  4.11s    +5.4s  0.12s*    +5.5s  8.93s**  +14.4s 1.16s
```

- `Get Booker` and `All Rooms` hit the **same Airtable base with the same
  credentials**. `Get Booker` (first) takes ~4.2s every time; `All Rooms` (seconds
  later) takes ~1.1s. The only difference is that one is first — so the ~3s gap is
  cold DNS + TLS the first call pays and later calls reuse. The Bookers table is
  ~14 rows, so it is not the query or table size.
- `*` in turn 5137 `Gate Context` was 0.12s — that is the Code helper being *warm*
  for once (problem 2), which is what it should always look like.
- `**` in the same turn `All Rooms` spiked to 8.9s. That turn was ~05:00 Manila,
  in the outage window, and the spike is the same DNS flapping getting worse.

`Get Booker` across many turns: mostly ~4s, tail of 5.7s, 8.9s, 16.5s — the long
tail lines up with the host's `EAI_AGAIN` DNS errors.

### Proof that problems 1 and the outages share a root cause

The outage on 2026-09-05: the last message got through at **00:05**, the next not
until **13:03** — ~13 hours. Both bots came back at the **same second** (Posty
13:03:13, Jessie 13:03:31), which means the shared front door recovered, not either
bot. The scheduled pruner ran at 04:00 straight through it, so n8n itself was alive
— only the path in and out was down. Independently, the nightly backup, which runs
from GitHub's servers *outside* this network, failed to reach the site at ~05:00 on
both 2026-09-04 and -05 — an outside client getting nothing, i.e. the box was
unreachable from the internet, not merely wedged. All of it points at the network
layer (Cloudflare tunnel / host DNS), the same thing making the first call slow.
