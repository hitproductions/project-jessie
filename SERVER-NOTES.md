# Server notes

These are the two things worth fixing on the server. Both make Jessie **slow**.
Neither is fixed in the n8n workflows — the workflows are fine, the slowness is
underneath them.

**Neither of these causes the outages.** An earlier version of this file said the DNS
problem did; that was wrong. The `EAI_AGAIN` errors are on *outbound* calls and the
outages are inbound — outbound was working mid-outage. The outages are a separate,
still-unsolved problem: see `OUTAGES.md`.

---

## 1. The server's DNS lookups are slow, and sometimes fail (outbound only)

*(the numbers behind this are in Measurements, at the bottom)*

Every time Jessie talks to Airtable or Google, the server looks up "where is that
server?" On this box that lookup is slow, and the `EAI_AGAIN` errors in the container
log show it failing outright at times.

This is **outbound only** — it slows Jessie down and it is worth fixing, but it does
not cause the outages. Don't conflate the two.

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

- **The outages.** Not a DNS problem — see `OUTAGES.md`. The 8 Sep instrumented
  window shows the tunnel up and the webhook registered while a Slack message never
  arrived, so what is left needs Cloudflare Security Events and Slack's delivery log,
  neither of which is on the box.
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
  later) takes ~1.1s. The Bookers table is ~14 rows, so it is not the query or the
  table size — something about being *first* costs ~3s.
- **The spikes are concurrency, not DNS.** Genzo's flood test on 7 Sep measured
  `Get Booker` going 1.2s → 3.36s under ten overlapping messages, which accounts for
  its previously unexplained 8-12s outliers. An earlier version of this file blamed
  cold DNS for those; the controlled test is better evidence than that inference.
- `*` in turn 5137 `Gate Context` was 0.12s — that is the Code helper being *warm*
  for once (problem 2), which is what it should always look like.
- `**` in the same turn `All Rooms` spiked to 8.9s — concurrency, same as the
  `Get Booker` spikes above.

`Get Booker` across many turns: mostly ~4s, with a tail of 5.7s, 8.9s and 16.5s.
That tail is concurrency (Genzo's flood test), not DNS.

### Turn time, measured on clean turns only

Concurrent turns inflate everything, so these exclude any turn with another execution
overlapping it: **median 14.1s** across 8 clean turns (range 8.2–15.1s), 7–8 Sep.
Sampled earlier in the week at 12.8s, but that figure cannot be re-filtered the same
way because those executions are pruned — treat the difference as noise, not a
regression.

Genzo measures ~10.5s serial / 9.2s under load. That is wall-clock Slack-to-reply;
the numbers above are the sum of node execution times. Different measures — do not put
them in one table. His is closer to what a user feels.
