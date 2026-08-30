# Project Jessie — start here

Jessie is a Slack bot that books studio time. She runs in n8n, talks to Airtable
and Google Calendar, and is driven by a Gemini agent. Launch is **25 September
2026**. This folder is the source of truth for how she works.

You are picking this up from Tara. Everything below has been verified against the
live build; where something is unproven or uncertain it says so.

## First, get your own API access

**Do not reuse Tara's key.** n8n API keys are per user — your own key means the
audit trail shows who did what, and either key can be revoked without breaking the
other.

1. In n8n → **Settings → n8n API → Create an API key**
2. `cp .env.example .env` and paste it in

```bash
./scripts/n8n list        # should print the six Jessie workflows
```

`.env` is gitignored and must stay that way. The key has never been committed —
please keep it that way. It should never appear in a chat message either.

## Read in this order

1. **`CLAUDE.md`** — how the build works, the ground rules, and the gotchas that
   have already cost days. Read this one properly.
2. **`DETERMINISM.md`** — which rules the workflow enforces and which are still
   left to the model. This is the design argument of the whole project.
3. **`PENDING.md`** — thirteen items needing a change in Airtable, the Slack app,
   Google Calendar or the n8n server. Several are yours.
4. `BIGCHANGES.md` — the four things a person using Jessie in Slack will notice.
5. `HANDOFF.md` — the original August handoff. **Treat as unreliable**: it has been
   wrong on several facts. Check anything in it against the live workflow.

`git log` is the real record of why things are the way they are. The messages are
long on purpose — most explain a bug that took hours to find.

## Check the build is what you think it is

```bash
./scripts/test-nodes --live      # 101 checks against what is actually deployed
```

If that passes, the deployed workflows behave as documented. If it fails, trust
the test and not the docs.

It reads what n8n has *stored*, though, which is not always what n8n is *running*.
After any import, also look at one real execution and check the per-node
`executionStatus` and `executionTime` — see gotchas 11 and 12 in `CLAUDE.md`. On
2026-08-30 `Guard Probe` failed on every message for five turns while every
stored-definition check passed.

## The one thing to understand before changing anything

> Anything that must be true is enforced in a sub-workflow.
> Anything the prompt merely asks for is unreliable.

Every rule that was only stated in the prompt has failed at least once —
the conflict check, waiting for confirmation, the room ranking, even the rule
against `**`. Every rule moved into n8n has held.

There is a third place: `Guard Probe` rewrites the reply on the way out, and is
where anything that must be true of the *text* belongs — the weekday beside a
date, the confirmation marker, the internal vocabulary.

If you find yourself adding a sentence to the prompt to fix a behaviour, that is
the moment to ask whether it can be enforced in code instead.

## Working rules

- **Pull before you change anything.** `./scripts/n8n pull <id> <file>`. The n8n UI
  and this folder overwrite each other silently, and Tara edits the canvas.
- **Build every file from a fresh pull**, and keep the full export shape — do not
  strip it down.
- **`./scripts/check-fromai` and `./scripts/test-nodes` before every import.** An
  unescaped apostrophe in a `$fromAI` description takes the whole agent down, and
  it fails at runtime, not on save.
- **After changing a tool's inputs, or adding/removing a tool, toggle the workflow
  Active off and on.** Saving does not reload tool definitions.
- **Import by hand and verify with a pull.** `./scripts/n8n push` has reported
  success and changed nothing (PENDING 12).
- Bookings on the calendar are real. QA runs on 2027 dates on purpose.

## Where things stand

Live: main workflow **v109**, Book Session v25, Cancel Booking v5, Move Booking v3,
Find Booking v3, Room Availability v5.

QA groups A, B, C, D, E, F, M, N and X have all been run against the live build
(2026-08-30). Eleven findings came out of it and ten are fixed.

`NOT_YOURS` is now **proven live**. It was tested with a seeded calendar event
carrying a foreign `ref:`, rather than by aiming the bot at a real third-party
booking, and it refused through two escalations — a claim of authority, then a
claim of ownership. That removes the "needs two people" blocker.

Known and unfixed, all in `CLAUDE.md` under *Not done*:

- **She can claim a booking she never made.** Once in 120 runs she answered an
  approved booking with "Booked." without calling `Book Session` at all, and
  nothing reached the calendar. This is the one serious open item. The obvious
  guard is unavailable — asking `Guard Probe` whether a tool ran hangs the task
  runner (gotcha 11) — so it needs the execution id passed into the sub-workflows
  and echoed back as a token. Written up in `DETERMINISM.md`.
- She sometimes presents a summary without checking availability that turn; a
  guard catches it.
- She sometimes asks for a date already given.
- The model occasionally corrupts a string it is copying — "Tara Lim" became
  "Tara Inf", "REASON1" became "REazon1". The summary line and title resolution
  are defended now, but nothing stops it appearing somewhere new.

## Before launch

`YEAR_SHIFT` at the top of `Gate Context`, and `plus({ years: 1 })` in the system
prompt, are the QA year shift. **They must go to zero together.** Change one and
the model and the guards will disagree about what day it is.

## The two things most worth your attention

1. **PENDING 13 — the task runner.** The first Code node in every execution costs
   ~3.5s; later ones cost ~0.07s. That is about 28% of a 12.5-second turn, paid on
   every message. The runner shuts down after 12–13 seconds idle. It is a server
   configuration question, and it is the largest single win available.
2. **PENDING 5, 6 and 7 — Airtable.** A client field returns record ids Jessie
   cannot read, a Technical Requirements note points at that field and she fills
   the gap by inventing, and four session types list the same rooms twice.
