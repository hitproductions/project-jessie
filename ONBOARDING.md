# Project Jessie — start here

Jessie is a Slack bot that books studio time. She runs in n8n, talks to Airtable
and Google Calendar, and is driven by a Gemini agent. Launch is **25 September
2026**. This folder is the source of truth for how she works.

Everything below has been verified against the live build; where something is
unproven or uncertain it says so.

## Setting up

**1. Unzip this folder** anywhere on your machine.

**2. Open a Claude Code session inside it.** In a terminal, type:

```bash
cd path/to/jessie
claude
```

Claude reads `CLAUDE.md` on its own when it starts. That file is the working
brief — how the system is built, and which mistakes have already cost days. You
do not need to explain the project to it.

**3. Get your own n8n API key.** In n8n, go to **Settings → n8n API → Create an
API key**. Then, in the terminal:

```bash
cp .env.example .env
```

Open the new `.env` file and paste your key in where it says `N8N_API_KEY=`.

Do not reuse someone else's key. Keys are per user, so your own means the audit
trail shows who did what, and either key can be revoked without breaking the
other. `.env` is gitignored and must stay that way — the key has never been
committed, and should never appear in a chat message either.

**4. Check it worked.** In the terminal:

```bash
./scripts/n8n list
```

That should print the six Jessie workflows. If it does, you are set up.

## Check the build is what you think it is

Two commands, and they answer different questions. Both are typed in the
terminal.

```bash
./scripts/test-nodes --live
```

108 checks against the deployed workflows, plus 27 gate scenarios. If a doc and a test disagree, the test
is right.

```bash
./scripts/health
```

What the live workflow actually *did* on its last few turns — per-node status and
timing. **Run this after every import.**

The difference matters. `test-nodes --live` reads what n8n has *stored*;
`health` reads what it *ran*. On 2026-08-30 those two disagreed: `Guard Probe`
failed on every message for five turns while every stored-definition check
passed. A failing node still lets replies reach Slack, just unprocessed, so
nothing looks wrong from the outside.

## The one thing to understand before changing anything

> Anything that must be true is enforced in a sub-workflow.
> Anything the prompt merely asks for is unreliable.

Every rule that was only stated in the prompt has failed at least once — the
conflict check, waiting for confirmation, the room ranking, even the rule against
`**`. Every rule moved into n8n has held.

There is a third place: `Guard Probe` rewrites the reply on the way out, and is
where anything that must be true of the *text* belongs — the weekday beside a
date, the confirmation marker, the internal vocabulary.

If you find yourself adding a sentence to the prompt to fix a behaviour, that is
the moment to ask whether it can be enforced in code instead.

## How changes get made

Nothing here pushes itself, on purpose.

- **Pull before you change anything**, and build every file from that fresh pull.
  The n8n UI and this folder overwrite each other silently.

  ```bash
  ./scripts/n8n pull <workflow-id> <file>
  ```

- **Run the checks before every import.** An unescaped apostrophe in a `$fromAI`
  description takes the whole agent down, and it fails at runtime rather than on
  save.

  ```bash
  ./scripts/check-fromai <file>
  ./scripts/test-nodes
  ```

- **Import by hand** through the n8n browser UI, then pull it back and check what you
  imported is what n8n kept. There is no API write path in use — the one that exists
  reported success and changed nothing (PENDING 12).
- **After changing a tool's inputs, or adding or removing a tool, toggle the
  workflow Active off and on.** Saving does not reload tool definitions.
- **Bookings on the calendar are real.** QA runs on 2027 dates for that reason.

Each file in `workflows/` is a numbered build kept as history. The comments inside
the Code nodes are long on purpose — most of them explain a bug that took hours to
find, and why the fix looks the way it does. Read them before rewriting one.

## Where things stand

Live: main workflow **v119**, Book Session v26, Cancel Booking v5, Move Booking
v3, Find Booking v3, Room Availability v5. A scheduled `Jessie - Prune
Executions` runs at 04:00; without it the execution table grows until the
instance stops answering, which it did twice on 2026-09-02 and 2026-09-03.

QA groups A, B, C, D, E, F, M, N and X have all been run against the live build
(2026-08-30). Eleven findings came out of that run and all eleven are fixed.

The last of them is worth knowing about, because it is the one failure no other
guard covered: she once answered an approved booking with "Booked." without
calling `Book Session` at all, and nothing reached the calendar. `Guard Probe`
now requires the tool to appear in the agent's own report of what it called, with
a success status, before a reply is allowed to claim anything happened.

`NOT_YOURS` — refusing to cancel someone else's booking — is proven live. It was
tested with a seeded calendar event carrying a foreign booker reference, rather
than by aiming the bot at a real third-party booking, and it held through two
escalations: a claim of authority, then a claim of ownership.

Known and unfixed, all in `CLAUDE.md` under *Not done*:

- She sometimes presents a summary without checking availability that turn. A
  guard catches it at confirmation, so it costs a wasted turn rather than a wrong
  booking.
- She sometimes asks for a date already given.
- The model occasionally corrupts a string it is copying — a booking title came
  back as "REazon1" instead of "REASON1". The summary line and title resolution
  are defended now, but nothing stops it appearing somewhere new.

## The two things most worth your attention

1. **PENDING 13 — the task runner.** The first Code node in every execution costs
   ~3.5s; later ones cost ~0.07s. That is about 28% of a 12.5-second turn, paid on
   every message. The runner shuts down after 12–13 seconds idle. It is a server
   configuration question, and it is the largest single win available.
2. **PENDING 5, 6 and 7 — Airtable.** A client field returns record ids Jessie
   cannot read, a Technical Requirements note points at that field and she fills
   the gap by inventing, and four session types list the same rooms twice.
