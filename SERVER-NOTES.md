# Server notes — for whoever has shell access to the box

Jessie and Posty run in Docker on the Mac Mini. These are the two things worth
fixing on the *server* — not in the n8n workflows. Both make Jessie slow (and one
also causes the outages) because something the server does at the **start** of
handling each message is slow.

Don't change the n8n workflows for either of these. The detailed measurements and
history are in `PENDING.md` items 13, 15 and 18; this is the plain version.

---

## 1. The server is slow to look up addresses (DNS) — and sometimes fails outright

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

- **The outages (item 15).** The one thing that would pin down the cause is the
  Cloudflare tunnel / `cloudflared` container's own log from a failure window
  (~5am Manila is common). n8n's own logs show nothing at the moment it drops.
- **Execution storage.** The daily pruner keeps the row count down but does not
  shrink the database file — that needs a `VACUUM`. The real long-term fix is moving
  n8n off the single-file SQLite database to Postgres.
