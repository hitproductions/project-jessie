# Project Jessie — n8n build

Slack bot that books studio time for Hit Productions. Moved out of a chat session into
this folder on 2026-08-30 so the workflows have version history and n8n's API is reachable
without export/import cycles.

## First time (once per machine)

```bash
git clone https://github.com/hitproductions/project-jessie.git
cd project-jessie
```

Then get an n8n API key (n8n → Settings → n8n API → Create), and:

```bash
cp .env.example .env      # then paste the key after N8N_API_KEY= in .env
./scripts/n8n list        # should print the Jessie and Posty workflows
```

`.env` is gitignored and must stay that way — the key never goes in a commit or a
chat message. Then start Claude Code in the folder (`claude`); it reads this file
on its own, so you do not have to explain the project to it.

## Start here — brief the person who just opened this

This file is the whole handover. The people working on Jessie use Claude Code far
more than they read docs, so assume they will not open anything else: they cloned
this, started you, and expect you to tell them where things stand. Before anything
else, unprompted:

1. `git pull` — three or four people work on this; someone may have changed it
   since last time. Nobody types git commands here, you run them.
2. Read the **triage board at the top of `PENDING.md`**: 🔴 urgent before launch, 🟠 before the SOP,
   🟢 additive. Item numbers are permanent; the details sit below the board.
3. Check what is live and what it actually did:

   ```
   ./scripts/test-nodes --live     # 300+ checks + 28 gate scenarios, what is stored
   ./scripts/health                # per-node status and timing, what actually ran
   ./scripts/verify-ids            # workflow + bot ids still point where they should
   ```

   The first reads what n8n has *stored*, the second what it *ran*. They have
   disagreed, and the gap was five turns of silently broken replies.

Then orient them, in plain language, drawing on *Where things stand* below:

- what Jessie is, and that launch is **12 October 2026** (dev freeze 23 Sep)
- the live versions, and whether anything is failing (`./scripts/health`)
- what changed since the last commit (`git log`)
- the biggest open risk (the outages - a Cloudflare exemption rule for the webhooks went in on 1 Oct; being watched, see
  `docs/outages/OUTAGES.md`) and the
  one or two most pressing items from `PENDING.md`

And whenever you are about to change a workflow, **pull it first and build from
that pull** — the n8n UI and this folder overwrite each other silently, and people
do edit in the browser. The `(Thunesday)` fix in `Guard Probe` existed in no file
at all; building from a stale copy would have deleted it and nobody would have
known.

```
./scripts/n8n pull <workflow-id> <file>
```

## No direct n8n access (from 29 Sep 2026) - how changes reach n8n now

**IT's decision: Claude does not connect to the n8n server** (`signal.hitpromanila.net`: API, webhooks, healthz). So
none of the scripts that talk to n8n are run any more - `n8n`, `n8n-write`, `health`, `verify-ids`, `backup-live`,
`test-nodes --live`, `eval-run`, `eval-twin`, `reapply-main-fixes` - not even to "just check". Everything offline still
works: the build scripts, `test-nodes` with five file paths, `test-gate <file>`, the sims.

**Deploying is by hand, in the n8n UI (route 1, chosen 29 Sep).** Claude builds and tests offline and pushes; the
person deploying imports. Every import, every workflow, in this order:
1. **Say it in Slack** before importing (two people importing the same workflow overwrite each other).
2. **Download the live workflow first** (open it → ⋯ → Download) into `workflows/imported/<name>-live-before-vN.json`,
   and run `./scripts/check-import before <that file> <the build it should match>`. MATCHES = safe. DIFFERS = someone
   changed it since that build: do not import; rebuild on top of the download (this replaces "pull first").
3. **Import** into that same workflow: ⋯ → Import from File → the exact file from the instructions → **Save** →
   **Publish** with the version name (e.g. `v192 - move range fix`) and its one-line description. Publishing is also
   the Active toggle that reloads tool inputs.
4. **Download it again** into `workflows/imported/<name>-vN-imported.json` and run
   `./scripts/check-import after <that file> <the build>` (stored == built). Then update `VERSIONS.md` and commit.

`check-import` reads files only. **Route 2 is parked:** `Jessie — Deploy from GitHub` (`scripts/build-deployer.py`,
`deploy/next.json`, `scripts/sim-deployer.js`) - n8n pulls the builds from this repo and does steps 2-4 itself. IT is
fine with it; it needs a fine-grained GitHub token for the org and an n8n API key credential. Not imported.

**What is lost:** reading executions (`health`, tool calls, timings) - ask the person testing to paste or download an
execution, or add an n8n workflow that writes run summaries to the repo; and `eval-run`, until it runs inside n8n.

## Where things stand

**Launch is 12 October 2026** (amended sprint, 2026-09-21 — was 25 Sep). Jessie is
live and in daily use. A second bot, Posty (release announcements — Google Sheets
and Slack, no Airtable), runs on the same n8n instance.

**The amended sprint milestones:**
- **23 Sep** — major dev freeze (end of the dev sprint).
- **24 Sep** — QA round 2 (Trish, Camy, Jess).
- **25 Sep** — address QA round-2 concerns (Howard, Tel).
- **28 Sep** — finalize the Living Doc.
- **29 Sep–2 Oct** — produce the End User SOP (Kristine, Camy).
- **5 Oct** — pre-launch: confirm all QA issues resolved or documented as known
  limitations. This is the end of the back-end polish headroom.
- **7 Oct** — HAIST monthly meeting 3. **8 Oct** — SOP finalized; async
  deliverables confirmed landed (Drew). **9 Oct** — cross-department orientation.
- **12 Oct** — launch: ready-to-use for selected departments / key persons.

**Working, and proven live:** the main workflow and every sub-workflow are active and
green. The confirmation gate, the ownership refusals (`NOT_YOURS`), Guard Probe's text
rewrites and **Prepare Booking** (code writes the summary the requester approves) all
hold in real conversations. Last verified end to end 2026-10-01 (14:14–14:37 PHT, series rerun 14:53–14:56 on main v207 / Book Session v75; the four booking types 15:12–15:24 on main v208 / Book Session v77 - Advertising, Entertainment from Netflix's record, Internal for a Likha meeting, Personal from "my own project", each booked, read back from the event and cancelled) through Slack on main v206 / Book Session v74 / Cancel v21 / Move v25 / Room Availability v12: book (short card, engineer defaulted), "make it 3pm instead" (Move Direct), the short cancel card and cancel, an internal-room card and "no", "is studio 7 free this week?" day by day, and a series (short card with the Expand Series dates, "none" carried on, "no") - one event at a time, calendar clean after. Before that, 2026-09-29 on main v191: book, move, move again, cancel, and a dateless cancel by name. **Live since 6 Oct ~15:39 PHT: main v226 / Book Series v5 / Book Session v92 / Room Availability v17 / Cancel v22 / Find v8** / Move v25
(hand imports, before + after MATCH; not yet tried in Slack - client asked first and until "none" (PENDING 84), past bookings
(85), name search over the last 60 days (86)). The full end-to-end checklist
has not been rerun since 1 Oct. **QA round 3** sheets (jess / trish / camy v3) are in `docs/qa/round3/`. Next build:
PENDING 78 + 79 (priority-request messages with blank names; "cleared with ..." loop).
The latest builds and what each fixed: [`docs/eod/EOD-2026-10-04.md`](docs/eod/EOD-2026-10-04.md).

**Testing through Slack.** An end-to-end test can be run by sending the test messages in the
tester's DM with Jessie through the Slack connector (with the tester's go-ahead for the exact
list), waiting for the execution whose trigger `ts` is that message, and checking the reply,
the tool calls and the calendar before the next message. Stop at the first wrong reply.
Where each build stands and what it fixed: [`VERSIONS.md`](VERSIONS.md). The latest
eval: [`docs/eval/eval-report-2026-09-28.md`](docs/eval/eval-report-2026-09-28.md).

**The biggest thing to understand — reliability, and it is not the workflows.**
Jessie has gone silent to Slack repeatedly (2, 3, 5, 7-8 September), from minutes to
~13 hours, each time recovering on its own. n8n does not crash: it keeps running
scheduled jobs and serving HTTP throughout.

**2 September is solved** — a Slack signing-secret mismatch plus a webhook
deregistration from test-listening on the live trigger.

**A second mechanism was confirmed on 15 September.** Slack support stated that every
request they sent to Jessie's event URL had been answered with **403** for at least 24
hours, and that Slack had therefore turned off event dispatch for the app. A 403 comes
from **Cloudflare**, at the edge — n8n never sees the request, which is why n8n logged
nothing, cloudflared logged nothing, and every check run from the VM or from a laptop
came back green. The same URL probed from a home connection returns 401 (reached n8n,
no valid signature); from a datacenter IP it returned 403. **Cloudflare is treating
Slack's servers differently from ours.** Whether this also explains 3, 5 and 7–8
September is unproven, but it fits all of them.

Read `docs/outages/OUTAGES.md` before touching this — it has the ranked causes, the onset window,
and the one lookup that would settle it. Two theories in it were confidently wrong
(host DNS, SQLite). A third, Cloudflare, was wrongly *retracted* and cost a week;
that is written up there too. `docs/outages/MONITOR-SETUP.md` is the external monitor that would
timestamp these properly and probe from outside our network. **This is the largest
open risk, and it is not in the workflows.**
**1 Oct 2026: the fix went in** - a Cloudflare exemption (skip) rule for Jessie's and Posty's webhooks, set after the
zone moved to Pro; both bots answered again immediately. It went silent at ~09:30 PHT on 30 Sep and 1 Oct, so watch
that window for a few days before calling it solved (PENDING 21).

**Safety nets already in place:**
- a daily pruner (04:00) keeps the execution table from filling the SQLite database
- `./scripts/backup-live` snapshots every live workflow into `workflows/live/`, run by hand after imports (the GitHub
  Action that ran it twice a day was deleted 29 Sep 2026: Cloudflare challenged GitHub's servers)
- `./scripts/verify-ids` catches a swapped Slack app or a changed workflow id

**Not yet in place:** an external uptime monitor — the one thing that would catch an
outage the moment it happens and alert someone. It needs the owner's accounts, not
a code change. See `PENDING.md` item 15.

**Whose account, and which key.** There is more than one n8n account now, and the
**Jessie workflows live in Howard's Personal project**. An n8n API key carries the
permissions of the account that created it, so a key made on any other account gets
`Forbidden` on all seven of them and the scripts go blind — see gotcha 15, which cost
an hour on 2026-09-17. **The key in `.env` must be created on the account that owns
Jessie.** It is still one shared login in practice, so n8n cannot tell you who changed
what, and has no restorable history. That is why this git repo is both the record and the rollback: pull before
you change anything, commit after every import. Changes go into n8n through
`./scripts/n8n-write` (the API write path, working since 2026-09-18 — see
`PENDING.md` item 12), or by hand through the browser UI as a fallback.

**Taking this over, do this first:** run the session-start checks above, read
`PENDING.md`, skim `docs/outages/SERVER-NOTES.md`. And before launch, the QA year shift has to go
to zero — see *Before launch*.

## Before you finish

Anything learned goes into a file, or the next session rediscovers it the hard way:

- a new failure mode, or anything that cost real time → a numbered gotcha below
- blocked on Airtable, Slack, Google or the server → `PENDING.md`
- a build that was imported and confirmed → say so in the commit message
- every new build → a row in [`VERSIONS.md`](VERSIONS.md): what it fixes and **which version had the problem**.
  Numbers only go up; a fix to v166 is v167 labelled "fixes v166: …", never a renamed file (scripts sort by the
  number, and `verify-ids` / `backup-live` key on the n8n workflow names, which do not change)
- label styles: `vN (vN-1 fixed)` only when the build repairs a problem the previous build introduced; otherwise
  2–4 words saying what it fixes or adds, e.g. `v182 (date + room fixes)` (see `VERSIONS.md`)
- every import → **label it in two places**: set the workflow title in the file to `<stable title> — v169 (v168
  fixed)` before `n8n-write put`, then publish with the version name: `./scripts/n8n-write activate <id> "v169 -
  v168 fixed" "<one line>"` (this is also the Active toggle that reloads tool inputs). `verify-ids` and `backup-live`
  only look at the stable part before ` — v<n>`, so a new build never breaks them (since 2026-09-28)

Then commit and push. One shared n8n instance means the folder is the only place
knowledge accumulates.

## Ground rules

- **Pull before you change anything.** The n8n UI and this folder overwrite each other
  silently. Someone editing in the browser and someone importing a file will overwrite
  each other without warning, and a file built from a stale pull throws away the canvas
  layout along with anything else changed since.
- **Build every file from a fresh pull and keep the full export shape.** Do not strip the
  file down to `name/nodes/connections/settings`. `./scripts/n8n-write` prunes to that shape
  itself at PUT time, and the browser-UI fallback expects the full n8n export — so the repo
  files stay full-shape either way.
- **Run `./scripts/check-fromai` on every build.** An unescaped apostrophe in a `$fromAI`
  description takes the whole agent down, and it fails at runtime, not on save.
- **Run `./scripts/test-nodes` before shipping anything.** It runs every Code node that
  decides something — `Guard Probe`, `Check Conflicts`, `Check Ownership`, `Shape Results`,
  `Resolve Booking` — against a table of scenarios offline, then delegates to
  `./scripts/test-gate` for `Gate Context`. 300+ checks on live (450+ on a new candidate), plus 28 gate scenarios. `--live` tests what is actually
  deployed; five explicit paths (main, book, cancel, find, move) test a candidate before
  importing it. Every one of those nodes shipped a bug this weekend that was caught by
  reading output by hand.
- **Run `./scripts/health` after every import.** `test-nodes --live` reads what n8n has
  *stored*; this reads what it *ran* — per-node `executionStatus` and `executionTime` from
  real executions, flagging any failure and anything over a second. It exits non-zero if a
  node failed. `Guard Probe` is the canary: if it is not green and fast, none of what it
  does is happening, and nothing looks wrong from the outside. See gotchas 11 and 12.
- `Gate Context` is the one node every message passes through, so a scope or syntax error
  there takes Jessie down completely rather than degrading one feature. That has happened
  twice.
- **After changing any tool's inputs, or adding/removing a tool, toggle Active off and on.**
  Saving does not reload tool definitions — the agent keeps calling the old schema.
- **The API key lives in `.env` only.** Never in a message, a commit, or a shared file.
- **The repo is the only record and the only rollback.** One shared n8n login and
  no restorable history on the free plan. Run `./scripts/backup-live` after every
  import to snapshot the live workflows into `workflows/live/`, and commit your own
  changes so the folder never falls behind what n8n runs.
- Bookings in the live calendar are real. QA runs on year-shifted dates (2027) on purpose.

## The stack

```
Slack DM → n8n → agent (Gemini 3.5 Flash Lite, temp 0.2) → Airtable + Google Calendar → Slack
```

Titles below are the stable part; in n8n each also carries its current build, e.g. `Jessie — Book Session — v55 (v54 fixed)`. Main was `Project Jessie v2` until 2026-09-28; the "v2" was dropped
because it read like a build number.

| Workflow | id | What it is |
|---|---|---|
| `Project Jessie` | `uVVYVB2M7kxpLleI` | main, 54 nodes including the lane notes |
| `Jessie — Book Session` | `EUG3sGXkfsJSYIMz` | the only way a booking is created |
| `Jessie — Cancel Booking` | `bAyDw7udhmY0NL38` | the only way one is deleted |
| `Jessie — Move Booking` | `t7lwR2km4tfN8DbM` | the only way one is rescheduled |
| `Jessie — Find Booking` | `yzirq12O227VTFp8` | shapes a day's events before the model sees them |
| `Jessie — Room Availability` | `e7tBQB458nstrqei` | what is free, computed not reasoned |
| `Jessie — Expand Series` | `hkx9PXcgW9nrzY2a` | computes the dates of a recurring booking (deterministic; the model does not do the date math), for the pre-confirmation summary |
| `Jessie — Book Series` | `UAwFoifgkfL1xNP2` | creates a whole recurring series server-side — expands the dates and loops Book Session per date, all-or-skip; the model calls it once |
| `Jessie — Prune Executions` | `K2tPBykMwKcQGMub` | daily 04:00 cleanup so the DB does not fill |
| `Jessie — Open Consent Request` | `nEHnCMMXS0am59Zy` | consent engine — writes a PENDING row to the Consent Requests Sheet + DMs the holder/incumbent (both cross-dept **priority preemption** and **M-booth** shared-booth requests) |
| `Jessie — Finalize Consent` | `TO1UnZTZ2LhtE9J3` | consent engine — on approval, places the requester: **M-booth** = cancel the holder's hold instance then book (resource transfer); **preempt** = place-only after the incumbent has moved |
| `Jessie — Consent Sweep` | `QHHDevaWhMk8gSBX` | consent engine — **scheduled ~10 min**; on a PENDING row past its `Deadline`: M-booth → book (timeout=book), preempt → mark EXPIRED. Fires even during a Cloudflare edge outage |

The **consent engine** (the three workflows above) handles two callers that both need someone's OK before
acting: **cross-department priority preemption** (a higher-ranked session bumps a lower one, incumbent
consents + moves) and **M-booth shared use** (a booth with a standing recurring hold; the holder consents,
their hold instance is cancelled and the requester is booked). State lives in the `Consent Requests` tab of
the Jessie Log Google Sheet (gid `431550013`), one row per request. Detection + the request are wired into
`Book Session`/`Move Booking`; the reply-router + `Call Finalize` live in `Project Jessie v2`. Design:
`docs/design/consent-engine.md` + `docs/design/mbooth-approval.md`. During QA, consent DMs reach the dev +
QA roster (Howard, Trish, Camy, Jess, Tel, Tara, Genzo) and everyone else is redirected to Howard. The
launch flip is `DEV_REDIRECT=''` in the three spots (see *Before launch* #2 and `docs/launch-checklist.md`).

Airtable base `app8GQxEInqJi1NRP` · calendar `c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com`
· launch 2026-10-12 (dev freeze 2026-09-23).

Versions in `workflows/` are a local convention, not n8n's. The live build is whatever was
last imported and confirmed — check with `./scripts/n8n pull` rather than assuming.

## The scripts

Run from the repo root. Everything here reads except `n8n-write`, which is the
only script that writes to n8n.

| script | what it does |
|---|---|
| `./scripts/n8n list` · `pull <id> <file>` · `execs` · `exec <id>` | read workflows and executions from n8n |
| `./scripts/n8n-write put <id> <file>` · `activate <id>` · `deactivate <id>` | **writes to n8n** — schema-clean import, and the Active toggle for a tool-schema reload |
| `./scripts/test-all` · `--local` | **every offline check against what is live, in one command** — run before every import; then the live smoke test in [`docs/qa/CHECKLIST.md`](docs/qa/CHECKLIST.md) |
| `./scripts/test-nodes` · `--live` | 300+ offline checks + 28 gate scenarios, on a candidate file or on what is deployed |
| `./scripts/test-gate` | the confirmation gate and date resolver on their own |
| `./scripts/test-consent` · `<file>` · `--live` | the consent engine's `Build Request`: M-booth deadline tiers, the PREEMPT window, and recipient routing (test-nodes does not load the consent workflows) |
| `./scripts/test-mirror` · `<file>` | the Envoy Mirror's `Plan Changes` offline: create/update/delete, and that a failed room or KDC read never deletes or duplicates (not yet imported, PENDING 42) |
| `./scripts/fix-studio-e <file>...` · `--check` | swaps Studio E's dead resource id for the live one in freshly pulled files, nodes only (PENDING 43) |
| `./scripts/eval-run` · `--only A,B` · `--repeat n` · `--main <file>` | the hallucination eval: plays `docs/eval/scenarios.json` through the **eval twin** (a guarded test copy of main, real Gemini + live sub-workflows, no Slack, never a yes) and scores every reply against tool output and Airtable. `--main` tests a candidate prompt before import. Raw results in git-ignored `eval/`. Report: `docs/eval/eval-report-2026-09-27.md` |
| `./scripts/eval-twin build [file]` · `guard <twin> <src>` | builds / re-checks the eval twin (`KRZmVfKIwCiLREjz`, inactive except during a run) |
| `./scripts/test-dates` | the padded-timestamp protections (gotcha 18), offline, on the newest file of each workflow: clean query, fail closed on a failed read, studios scope |
| `./scripts/check-fromai <file>` | catches an unescaped apostrophe in a `$fromAI` description before it takes the agent down |
| `./scripts/health [n]` | per-node status and timing from the last *n* real turns — what n8n actually ran |
| `./scripts/verify-ids` | all twelve Jessie workflow ids (incl. the three consent workflows) resolve to **active** workflows with the right names, and the Jessie bot id still points at the live app |
| `./scripts/backup-live` | snapshot every live workflow into `workflows/live/`; run by hand after imports |
| `./scripts/reapply-main-fixes` · `--check` | after someone else imports main: report which of our main fixes survived, and re-apply the missing ones **on top of** their version (never imports; flags structural gaps for a hand merge) |

## The one principle

Everything that must be true is enforced in a sub-workflow. Everything the prompt merely
asks for is unreliable.

That is not a design preference, it is what testing showed: every rule stated in the prompt
failed at least once — the conflict check, waiting for confirmation, the room ranking,
checking availability before summarising, even the rule against `**`. Every rule moved into
n8n has held on every run since.

A third place now does real work: **`Guard Probe`**, which rewrites the reply on the way out.
Use it for anything that must be true of the *text* rather than the action. It already
collapses `**` to `*`, corrects the weekday printed beside a date, removes the words
"priority room", "last resort", "deviation" and the `BLOCKED - ` prefix, normalises the
confirmation marker, relabels "Booking Owner" to "Booked by", and repairs a mistyped
booker name against Airtable.

That last one is narrower than it sounds, and the wide version was a bug. "Booked
by:" is not always the requester - a cancel or a lookup shows someone else's
booking - and until v120 the rewrite relabelled it as theirs. It now only
overwrites a name that is both absent from what the tools returned this turn and
a near-miss of the real one by edit distance: a corruption is neither reported
nor plausible, a third party's name is reported and is nobody's typo. Each of those was a prompt rule first, and
each failed as a prompt rule.

It also now refuses to let a claim through that nothing backs. If the reply says "Booked",
"Cancelled" or "Moved", the matching tool must appear in the agent's own `intermediateSteps`
on this turn **with a success status** — otherwise the text is replaced with an honest
failure. A `REJECTED` Book Session does not count as a booking.

That reads the agent's output, which arrives on Guard Probe's input, because the direct
question — asking whether the tool node ran — hangs the task runner (gotcha 11). It depends
on `returnIntermediateSteps` being set on the agent node: clear that and the check goes quiet
rather than failing loudly. `claimProbe`, returned alongside `output` and never sent to Slack,
says on every turn which happened. On 2026-08-30 she answered an approved booking with
"Booked. That is a bit shorter than VO Recording sessions usually run" without calling
`Book Session` at all — copied from an almost identical exchange two turns earlier. Nothing
was created and the requester was told it had been. Every other guard stops a wrong booking
being *made*; only this one stops one being *claimed*.

## Prepare Booking — code writes the summary the requester approves (main v166, LIVE 2026-09-28)

The model gathers details and calls **Prepare Booking** (Book Session in `mode: prepare`). It runs every guard,
then its `Render Summary` node writes the summary in one fixed format — calendar title first, the details, a
`_check xxxxxxxx_` code (a hash of the booking fields) and the confirmation marker — and Guard Probe sends
exactly that text. At the yes, main's `Prepared Booking` node reads Jessie's newest message back, verifies the
code, and Book Session books **those** details whatever the model passes (`use` → the tool inputs come from `p`).
A yes to a summary Prepare Booking did not write is refused (`NOT_PREPARED`). Guard Probe skips every rewrite of a
prepared summary's booking lines, because any change would break the code. Before it: five date formats, the
title in 16% of summaries, one live booking titled differently from the summary approved. Still model-written: moves.
**Series too, since main v226 / Book Series v5** (PENDING 90): `Prepare Series` writes the series card in code and stores it,
and at the yes `Prepared Series` → `Series Direct` books exactly the card's dates through Book Series, without the model. Prepare mode also asks what the model used to guess: no date named
(`MISSING_DATE`), department (`NEED_DEPARTMENT`), External/Personal (`NEED_BOOKING_TYPE`), the arranger
(`NEED_ARRANGER`), a near-miss client ("Did you mean …?", `CLIENT_CHECK` / `CLIENT_AMBIGUOUS`).

## Details come from the requester's words, not the model's (main v167 / Book Session v55)

Every detail the model passes into a booking is a place it can invent or misspell something. `Booked For` reads
the requester's own messages for the current booking (newest first) for the **engineer, arranger, project,
client and time range**, resolving people against Bookers (name, first name, "Goes by" alias, initials in
capitals). The Prepare Booking / Book Session / Book Series inputs use those whenever the model's value holds a
word nobody typed — Jessie's own offers count once answered, except a name she quoted to refuse. A name that is
unknown or shared is passed exactly as typed, so Book Session asks about what the requester wrote. A shift ("an
hour later") or a start time alone leaves the model's times alone. Book Session v55 fills in the full name, role
(from Info, for the department) and initials. **This makes Bookers `Info` load-bearing: a nickname people use
that is not listed there is refused** (PENDING 53). The prompt and tool inputs ask for names exactly as typed.

## What is enforced, and where

`Book Session` refuses before anything reaches the calendar:

```
MISSING_DETAILS · MISSING_CLIENT · CLIENT_UNVERIFIED · ENGINEER_UNKNOWN · ENGINEER_UNVERIFIED · TITLE_INITIALS · NO_REFERENCE_DATA · NOT_CONFIRMED · DURATION_INVALID
ROOM_UNSUITABLE · ROOM_NOT_PRIORITY · NO_ROOM · UNKNOWN_ROOM · ROOM_OCCUPIED · UNVERIFIABLE
```

`TITLE_INITIALS` enforces the title convention: a studio title (`PROJECT / Client / initials`, or
`PROJECT / initials` when there is no client — clients are optional since main v161 / Book v49,
2026-09-28) must end in initials (`DR` or `DR x PL`), never a name or nickname — the model put "Drey"
(Daryl Reyes = DR) there and nothing corrected it. It checks any three-segment title, and a two-segment
one when a session type was given (no-client studio titles and Localization's `Project Code / initials`);
internal rooms use " - " and carry no session type. It is now mostly a backstop: the staff resolver below
rewrites the initials first, on both title shapes.

`ENGINEER_UNKNOWN` / `ENGINEER_UNVERIFIED`: every engineer and arranger the model supplies is
resolved against the **Bookers** table (read by the `All Bookers` node at the top of Book Session,
before `Get Client`). An exact `Name`, a "Goes by" alias from `Info`, `Initials`, or a unique first
name becomes the canonical name, and the title's initials segment is rewritten from Bookers
`Initials` (`Drey` → `DR`, `Brian Cua` → `BC`). Anything else is refused with suggestions, so an
engineer not on the staff list is never written. QA 2026-09-25: asked for "Daryl", the model wrote
"Daryl Javier" (an invented surname) and titled it DJ. If the staff list cannot be read and an
engineer was given, it refuses (`ENGINEER_UNVERIFIED`) rather than guessing.

`MISSING_CLIENT` guards on-behalf bookings: when a booking is *booked for* a colleague
(`Booked by: X (for Y)`) and is External, Y is never the client and never the title's Client segment.
Prompt-only rules did not hold (the model laundered the booked-for name into the client/title), so this is
enforced in `Check Conflicts`. Since Book v49 a booking with **no client at all** passes (title
`PROJECT / initials`); only Y standing in as the client is refused. See the `booked_for` tool input and
`(for …)` in `Guard Probe`/summary.

**Clients are optional, and new clients are welcome** (main v161 / Book v49, decided 2026-09-28). Jessie
still always asks for a client, but a booking can go ahead without one, and a client who is not in the
Clients table is booked as typed — for every department, Advertising and Localization included. Book Session
then writes the client to the **`New Clients` tab of the Jessie Log spreadsheet** (`New Client?` → `New
Client Row` → `Log New Client`, one row per client, `appendOrUpdate` on `Client`, Status `For Review`) for Tel
to add to Airtable: only Tel can write Airtable, and the service account behind `Log to Sheet` already
writes that spreadsheet. A lookup that errored, and a Localization Project Code in the client slot, are not
logged. The sheet write can never fail a booking (`continueRegularOutput`).

**The four eval decisions** (2026-09-28; main v162 / Book v50 / Room Availability v9 / Book Series v3,
**LIVE 2026-09-28 11:33 PHT** with Move v20, Cancel v16, Find v4, Expand Series v2):
- *(a) "for <name>" that is not staff is the client.* `Booked For` now also returns `forClient`: a capitalised
  name after "for" that is not in Bookers (any name or alias, the requester included), not a room, session type,
  department, date word or the project, when the requester did not name a client outright. The prompt is told
  "THE CLIENT IS X", Room Table's "ask who the client is" notice is suppressed, and the Book Session / Book Series
  `client` inputs fall back to it. Before: "Who is the client?" 20 of 20 for "for Spotify" / "for Jem Lim".
- *(b) A new client must be one the requester typed* — `CLIENT_UNVERIFIED`. `Booked For` hands on
  `requesterText` (the requester's messages for this booking) as the tools' `requester_text`; Check Conflicts
  refuses a client that is neither found in Clients nor present in that text, so a name Gemini invented is never
  booked or written to New Clients. Skipped when a caller sends no text (consent placements). A note glued onto the
  client ("Acme (new client)") is stripped in Book Session and on the summary's Client line (Guard Probe), and a
  given client is put back into a `PROJECT / initials` title.
- *(c) Unusual length: no question, always the heads-up.* Guard Probe's line is now a statement ("Heads up: 9
  hours is longer than VO Recording sessions usually run (1–3 hours).") and the prompt says never ask first.
- *(d) Studios vs rooms.* `Booked For` sets `roomScope` from what the requester typed ("studios" without
  "rooms" → studios); Room Availability then leaves conference rooms and the lobby (Airtable Room Type
  `Conference Room` / `Lobby`, passed as `common` by Room Table) out of the free list, keeping the M booths.
- Also: "Client: None" only stands after the requester said there is none (Guard Probe otherwise drops the
  confirmation line and asks), and Room Availability's own instruction no longer leaks into replies.

**Who a booking is *for* is decided deterministically** (main v154). The `Booked For` node (between
`All Bookers` and `Room Table`) scans the requester's messages for the current booking, newest first,
stopping at the booking request, a finished booking, or a reset, for "for / on behalf of <someone in
Bookers>" (full name, first name, or a "Goes by" alias). A client is never in Bookers, so "for Jem Lim"
stays the client; "for John Smith" isn't John Cutangco (a capitalised surname after a lone first name
blocks the match). The Book Session / Book Series tools prefer its answer over the model's `booked_for`,
the prompt gets a notice so Jessie doesn't ask "who is Japs?", and Guard Probe adds "(for X)" to the
summary's booker line. It never throws (on error it answers "no one"). QA B2, 2026-09-25: "Book Studio F
for Japs" had been booked as plain `Booked by: Camy Caridad`.

**Unusual lengths are flagged before the yes** (main v155). Min/Max Duration in Session Types is what a
session *usually* runs, not a limit (raised in QA, 2026-08-30: "it could go on for 8 hours"), so nothing blocks
on it. Book Session adds a note to the "Booked." reply (`durationNote`), and Guard Probe now also puts one
plain line above the confirmation, computed from the summary's *Time:* and *Session Type:* against Room
Table's reference data: *"Heads up: 9 hours is longer than VO Recording sessions usually run (1–3 hours).
Still book it as is?"* It first drops the model's own duration remarks, so there's one line and never
"minimum" or "maximum allowed". QA M5, 2026-09-25: the prompt-only version flagged 15 minutes and missed 9 hours.

Past sessions can be booked (decided 2026-10-06, Book Session v91 / main v220 / Room Availability v17): there is no
`PAST_DATE` refusal any more; the card says "Heads up: this date has already passed.", and a date with a year is taken as
written, so during the QA year shift "oct 1 2026" books 2026.

`Cancel Booking` refuses with:

```
NOT_CONFIRMED · MISSING_DATE · MISSING_DETAILS · LOOKUP_FAILED
NOT_ON_CALENDAR · AMBIGUOUS_TITLE · NO_REFERENCE · NOT_YOURS
```

`Move Booking` refuses with the same ownership and confirmation checks plus
`MISSING_TIMES`, `DURATION_INVALID`, `ROOM_OCCUPIED`, and returns `PARTIAL` if the
replacement was created but the original could not be removed.

**Every guard above has now refused something in a live conversation.** `NOT_YOURS` was the
last one outstanding and was proven on 2026-08-30, using a seeded calendar event carrying a
foreign `ref:` rather than by aiming the bot at a real third-party booking. It held through
two escalations — a claim of authority over the other person's bookings, then a claim that
the session was really the requester's.

**The confirmation gate.** `Gate Context` reads Slack history and computes `confirmed`,
`confirmedCancel`, `confirmedMove` and the memory `epoch`. The model supplies no part of
them. Because `Send Reply` runs after the agent, a summary written this turn is not in
Slack yet, so a same-turn booking cannot pass. Approval must be an explicit yes — a literal
match against a fixed set. Before v81 any reply at all counted, including "no".

**Markers.** Summaries end `Confirm to book. (yes/no)`, `Confirm to cancel. (yes/no)` or
`Confirm to move. (yes/no)`. The gate matches the marker at the end of the message, so
`Guard Probe` normalises whatever the model writes — "Confirm to cancel both." broke the
gate before it did. The gate accepts the older `(y/n)` suffix too, because old messages sit
in the history window it reads.

**Rescheduling.** `Move Booking` does the whole move in one call and one confirmation, and
creates the replacement **before** deleting the original, so a failure leaves the booking
where it was. The old flow deleted first and needed a second yes to recreate — walk away in
between and the session was gone.

**Cancellation.** `Cancel Booking` fetches the event from Google and reads the booker
reference off the real record. The booking is resolved by the title shown to the requester,
so the model never has to hold or invent an event id.

**Memory.** The session key is `user-date-epoch`. Only a typed `reset` advances the epoch;
it also rolls over at midnight Manila. A completed booking used to advance it, which meant
"actually cancel that" had nothing to refer to.

## Reference data — read it, don't restate it

Do not trust any list of rooms, session types or capabilities written down in a document,
including this one. Several have been wrong. Read Airtable.

Injected into the prompt on every message by `Room Table`: the room ranking per session
type, the full session-type list, the room list, and a department-flavoured suggestion list.

Known contradictions in Rooms & Studios, and which field Jessie trusts:

- **Format questions read `Recording Format`.** `Room Type` marks nine rooms as `5.1 Mixing`
  including two whose own Equipment says "stereo only".
- **`Vocal Booth` is the flag, not the `Recording Booth` room type.**
- **`Room Requirements` is a capability string**, not a room list. The ranking is the list.
- **Jessie reads only Name, Client Type, Booker Type, Importance and Notes from Clients** (2026-09-28). Tel is
  deleting every other field — the three preferred-room fields, Typical Session Length, Technical Requirements,
  Min Simultaneous Rooms, Tends to Overrun and the Advertising / Localization Projects links. **Hiding a field in an
  Airtable view does not hide it from Jessie**: the API returns every field, which is how a hidden preference and
  Jem Lim's hidden Technical Requirements kept reaching replies. Book Session v50 no longer writes "Tech
  requirements" into event descriptions; main v162's prompt no longer mentions any of these fields.
- **Client room preferences are not used** (dropped 2026-09-28). Rooms come from the session-type
  ranking only. The Clients table's `Preferred Rooms` / `Preferred Room Name` / `Preferred Room Names` fields
  (the last is a *link*, so it returned record ids) are being removed by Tel; nothing in the workflows reads
  them, and the Clients tool returns whatever fields exist, so removing them cannot break a lookup.

## Before launch

Three switches flip for launch — do them together:

1. **`YEAR_SHIFT`** at the top of `Gate Context` and the **`plus({ years: 1 })`** in the system
   prompt are the QA year shift. **They must go to zero together.** Change one and the model and the
   guards will disagree about what day it is — which decides what "next Thursday" means and whether a
   date is in the past.
2. **`DEV_REDIRECT`** in the `Build Recipients` node of **both** `Cancel Booking` and `Move Booking`.
   It reroutes every authorized-change notification to a dev/QA inbox so real staff aren't pinged
   while building; `ALLOW` beside it lists the ids that still get their own DMs (dev + the Sept-24 QA
   testers). **Set `DEV_REDIRECT = ''` at launch** and the booker + assigned engineer are DM'd for
   real (the `ALLOW` list then no longer matters). Booker id is the event `ref:`; the engineer is
   resolved from the title initials via `Lookup Engineer`.
   - **Consent engine has its OWN `DEV_REDIRECT`** in `Open Consent Request` → `Build Request` (added
     2026-09-22). It routes the row's `Approver` and `Requester` — which every consent DM downstream
     (Open, Finalize, main router) reads — to Howard unless the recipient is on `ALLOW` (since
     2026-09-24 the same dev + QA roster as Cancel/Move). So no real non-QA person is DM'd during
     testing. **Set its `DEV_REDIRECT = ''` at launch too** — it was missing from
     `docs/launch-checklist.md` until 2026-09-25. The tail hook matches on
     `Incumbent Event Id`, not `Approver`, so the real booking is still the one moved/placed.
3. **`TEST_COORD`** (the hard-coded Howard id) in `Check Ownership` / `Resolve Booking` — drop it once
   the `HAIST Dev` Airtable tag is live on Howard (it's strictly broader). Weekend hard-code only.
4. **`HAIST Dev`** authority (Bookers `Authority` tag) — **god-mode**: bypasses the owner check and
   the department scope, so a holder can move/cancel *any* booking in *any* department. Dev team
   only: **Howard, Tel, Genzo**. Before/after launch, **decide: keep for devs or pull.** Enforced in
   `Check Ownership` / `Resolve Booking` via `isHaistDev`. (Tara, the strategic lead rather than a
   dev, is set up QA-style: on the notification ALLOW list with her real Standard authority.)

Notification routing during dev (not a launch flip, but related): `Build Recipients` in Cancel/Move
has `DEV_REDIRECT` (reroute to Howard) and `ALLOW` (ids that get their own real DM). Since QA round 2
(2026-09-24) `ALLOW` applies to both the booker **and** the engineer notice (it used to be booker-only),
so Tara, the one listed tester who is also an engineer, gets engineer notices. `DEV_REDIRECT=''` at
launch restores real DMs to booker + engineer for everyone.

## Waiting on other systems

[PENDING.md](PENDING.md): everything still open, triaged at the top (🔴 urgent before launch, 🟠 before
the SOP, 🟢 additive), including what waits on Airtable, the Slack app, Google Calendar or the server.
Each item says how it was found and what it breaks. Numbers are permanent; resolved items move to the bottom.

`docs/outages/SERVER-NOTES.md` is the plain-language version of the server-side fixes (DNS and
the task runner), for whoever has shell access to the box.

## Gotchas that already cost time

0. **A sub-workflow must be `active` to be callable as a tool.** A workflow created through the
   API (`./scripts/n8n-write create`) defaults to `active:false`, and the agent's tool call
   then fails with the model reporting the tool "unavailable" — with **no execution record** on
   the sub-workflow to point at. Activate it: `./scripts/n8n-write activate <id>`. This cost a
   QA round on 2026-09-18 with `Expand Series`.
1. A `throw` inside an **optional** collection like `additionalFields` does not fail the
   node — n8n drops the field. Guards only work in required top-level fields.
2. Never put a fan-out node in the agent's main chain without collapsing back to one item.
3. `$('Node').first()`, never `$('Node').item`.
4. A node chained after a multi-item node runs once per item. That is what made the conflict
   query fire 25 times and take 11 seconds. Use `executeOnce`.
5. Duplicate `$fromAI` keys in one node with different descriptions kill the agent on every
   message.
6. The prompt must not demonstrate what it forbids. Models copy context over instructions.
7. **An empty value in an Airtable formula matches every row.** `SEARCH(LOWER(''), ...)` is
   true for everything: a booking was once assembled from a stranger's client record. Every
   lookup now refuses rather than returning a table.
8. **A pulled file carries an `activeVersion` block** — n8n's snapshot of the *previous*
   version. Grep will find stale names and values in it. Check the nodes, not the whole file.
9. **Renaming a tool leaves dangling references** in the prompt, other tool descriptions and
   the sticky notes. Search for the old name everywhere before shipping.
10. **Import with `./scripts/n8n-write put <id> <file>`, then verify with a pull.** The API
    write path works when the body is schema-clean (name/nodes/connections/settings, settings
    pruned to the API-allowed keys) — the old "PUT changed nothing" was a payload-shape
    problem, now handled by the helper (PENDING 12). The browser UI import still works as a
    fallback. Either way, pull afterward to confirm what is stored, and `./scripts/health` to
    confirm what ran.
11. **Never reference a tool node from a Code node.** `$('Book Session')` inside `Guard Probe`
    hangs the task runner until it times out — 60,007 ms, then `Unknown error`. `$('Gate
    Context')` and `$('Room Table')` are fine at ~70 ms; it is specifically nodes wired to the
    agent's `ai_tool` port, which produce no `main` output. This cost an evening on 2026-08-30:
    v102 shipped it and Guard Probe failed on *every* message for five turns.
12. **A failing Code node fails open.** When `Guard Probe` errored, replies still reached Slack
    — just unprocessed, with none of its corrections applied. Nothing looked broken from the
    outside. Read `executionStatus` and `executionTime` per node after any change; a pull only
    proves what is *stored*, never what is *running*.

14. **A Slack signing-secret mismatch is completely silent.** n8n receives the POST,
    checks the signature, rejects it, and at the default log level writes *nothing*. No
    execution, no log line, and the webhook still reports as registered — so "the
    webhook is registered" proves nothing about whether events are being processed.
    This was the 2 September root cause and it cost days. `N8N_LOG_LEVEL=debug` is now
    set, which makes it visible; `./scripts/webhook-canary` (on the VM) sends a *signed*
    verification, which is the only probe that catches it.

13. **Detect Jessie's own messages by `bot_id`, never by a hardcoded user id.** The Slack app
    has been swapped once, changing Jessie's bot user id. The live code survived because
    `Loop filter` and `Gate Context` both test `bot_id` first — a hardcoded id (`Gate Context`
    still carries an old one as dead redundant code) would have silently stopped matching. A
    diagnostic script that *did* hardcode the id filtered the wrong bot for weeks unnoticed.
    `./scripts/verify-ids` now compares the hardcoded ids to the live app and fails if they
    drift; run it on start.

15. **`Forbidden` from the n8n API means "this key cannot see it", not "it is gone".**
    An API key carries its creating account's permissions. Point one at a workflow in
    another account's project and you get `{"message":"Forbidden"}` — where a genuinely
    deleted workflow gives a not-found. On 2026-09-17 the key in `.env` belonged to a
    different account than the one holding Jessie: `n8n list` showed 5 workflows instead
    of 18, `execs` returned nothing, and `verify-ids` reported all seven as *no longer
    exists*. Nothing was deleted and Jessie never stopped running. Both scripts now
    distinguish the two. **A short list from n8n means check the key first.** And note
    what nearly followed: `backup-live` used to delete snapshots for workflows n8n did
    not list, so one nightly run with that key would have erased the entire rollback
    artifact and exited 0. It no longer deletes anything — it warns and leaves them.

16. **The model glues visible junk onto strings it copies, not just invisible characters.**
    QA on 2026-09-24 caught `2027-09-27T17:00:00+08:00ភាsa` and `…+08:00容器id` sent to Room
    Availability. The `clean()` scrubber only strips invisible characters (the 30 Aug U+FE0F case),
    so these came back `BAD_WINDOW`. The model retried cleanly in the same turn, but Guard Probe
    refused on *any* failed call and replaced a correct, checked summary with "Hold on — the
    availability check did not run". Both refusals that day were false positives. Timestamps now
    go through `isoOnly()` (Room Availability + Book Session), and Guard Probe judges the latest
    answer that turn rather than any answer. Treat every model-supplied string as possibly padded.

17. **`test-nodes` with one to four paths used to test the wrong files, silently.** Only the
    five-path form (`MAIN BOOK CANCEL FIND MOVE`) takes a candidate; `test-nodes main <file>` fell
    through to "the newest file of each workflow in `workflows/`" and reported on those. It went
    unnoticed on 2026-09-25 only because every candidate happened to be the newest file. It now refuses
    anything but zero or five paths. In zsh, pass the paths literally: an unquoted `$VAR` holding
    several paths is ONE argument (zsh does not word-split).

18. **A calendar query that errors reads as "every room free".** Found by the eval on 2026-09-27: the
    model pads a timestamp (`…+08:00hq`), Room Availability sends it raw to Google, Google answers 400, the
    HTTP node carries on (`continueRegularOutput`), and the code reads "no events" as "all free". 79 of 199
    checks in the eval, 4 of 27 live. `isoOnly()` (gotcha 16) cleaned the value *after* the query. Book
    Session's conflict query has the same shape (a padded start falls back to now + 24 h). Any node that
    queries with a model-supplied value must clean it *before* the query and fail closed on an error —
    PENDING 51. Fixed everywhere a model-supplied date or time reaches the calendar (2026-09-28): Room
    Availability v9 (clean query, `CALENDAR_ERROR` instead of "all free"), Book Session v50 (clean query; Create
    Event and Verify read the cleaned `final_start` / `final_end`), Move Booking v20 (clean inputs and day query;
    a failed read of the new window is `LOOKUP_FAILED`, not free), Cancel v16 / Find v4 (clean day query — both
    already failed closed), Expand Series v2 / Book Series v3 (clean dates and HH:MM), and main's `List Events`
    tool. `./scripts/test-dates` checks all of it offline.

19. **Asking the model for something it does not have makes it invent it.** The tool inputs and the prompt asked
    for an engineer's "full name and role, e.g. Tara Lim (Post Engineer)" and for initials; given "Drey", a made-up
    surname was the only way to comply ("Daryl Javier", "Andrian \"Drey\" Sison", "Andre Cabuay"). Changing the
    wording to "exactly as the requester gave it" took the eval twin from 0/2 to 27/27. Before blaming the model,
    read every `$fromAI` description and prompt format line for a demand the requester's message cannot satisfy,
    and let code fill it from Airtable. (Also: hiding a field in an Airtable view does not hide it from the API —
    see *Reference data*.)

20. **The eval twin only swaps main.** `eval-run --main <file>` tests a candidate main against the *live*
    sub-workflows, so a Book Session change cannot be eval-tested until it is imported; a main change that needs
    it will look half-fixed. Import the two together, then run a short live eval. And a `test-nodes` group whose
    marker is not in the build is skipped silently — register new groups in `GROUPS`, and check the new cases
    actually ran (the count goes up), not just that nothing failed.

21. **A new tool input has to go in up to three tool nodes** (Prepare Booking, Book Session, Book Series), and check
    whether Book Series must pass it on to its per-date Book Session call. Missing one fails quietly: that path
    simply behaves the old way.

22. **`test-nodes --live` tested the gate on the newest repo file, not on live** (until 2026-09-29). It pulled the live
    workflows for the node checks but left `MAIN` unset, so `test-gate` ran on the newest `workflows/project-jessie-v*.json`.
    With a candidate in the folder, "--live" reported the candidate's gate result. Found when a new gate case passed on
    "live" while failing on the live build itself. Fixed; if a live result ever looks too good, run
    `./scripts/test-gate <pulled file>` directly.

23. **A fix in a tool the model does not call does nothing.** Cancel Booking v20 could find a booking by title, but
    "cancel QANODATE" never reached it: the model looked the booking up with Find Booking first (with today's date) and
    asked for the date. The offline sims passed because they called Cancel Booking directly. Before building, check
    which tool the model actually calls on that turn (the live execution's `intermediateSteps`), and put the fix there
    or in every tool on the path. Then test it through Slack, not only offline.
24. **A build number can collide with an unimported candidate.** Today's Move Booking v25 was written to
    `workflows/move-booking-v25.json`, which already held the consent rebuild's unimported Move candidate (same
    number, different change); git kept the old one (`060afd9`). Before writing `workflows/<name>-vN.json`, run
    `git log -- workflows/<name>-vN.json`: if it exists, take the next free number.
25. **A Code node must name the nodes it reads literally, and must not read the AI Agent.** v193's Turn Log Row failed on
    every turn with "Unknown error" (the gotcha 11 signature) - it looked nodes up through a variable (`const has = n =>
    $(n).first()`) and read `$('Jessie AI Agent')` directly; nothing else in main does either. n8n works out which nodes'
    data to give the code runner from the literal `$('Name')` strings. With "continue on error" set, it then passed its
    input (Slack's receipt) to the sheet, so nothing looked broken. Take the agent's tool steps from Guard Probe (its
    input), and write `$('Book Direct')` etc. out, one try each.

26. **Workflow static data is saved only when an execution finishes.** Gate Context's carried date lives there, and since
    v193 a turn runs on after its reply (the Turn Log sheet write). A requester answering within ~3 s starts a new
    execution that loads the store before the last one saved it: on 30 Sep "no client" lost "tomorrow" and Jessie asked
    for the date. Anything static data carries must also be recoverable from the Slack history (main v195 does that for
    the date). And two overlapping turns each save their whole snapshot, so the later one wins.

27. **Airtable long text can end in a line break, and `(.*)$` then matches nothing.** `Info` for Angelo Villegas, Rico
    Gonzales, Alec Elijah Gan and Cristel Cube ends in `\n`; `/goes by\s+(.*)$/i` failed on all four, and the code
    fell back to splitting the whole Info - which kept most nicknames but lost the first one ("Enrico"). Read up to
    the line break (`/goes by\s+([^\n]*)/i`), never to `$`. Found 30 Sep building PENDING 65 (v70 / v196).

28. **Ctrl+Z after clearing the canvas restores the nodes, but not always the connection order.** On 30 Sep someone
    deleted everything before importing (the usual routine), remembered the live download was still needed, and undid
    it. The download then differed from the last build only in the order of two connection lists - harmless, but
    `check-import before` rightly said DIFFERS. Download the live workflow *before* clearing the canvas. When only
    connection order differs, rebuild on the download (the sims accept either order).

29. **Simulate a tool's result in the shape the agent receives, not the shape the code returns.** Book Session's Check Conflicts
    says `verdict`; its `Return Rejection` node renames it `status` before the agent sees it. Guard Probe's word-for-word relay
    of Book Session's questions (v203) tested `verdict`, and every sim fed it Check Conflicts' raw output - so it passed offline
    and never fired live for two days; the model relayed the questions itself and, on 2 Oct, widened one. Build sim observations
    from a real execution's `intermediateSteps` (fixed in main v216).

30. **A refusal that needs the requester's answer must carry the question, in quotes, after "Ask exactly this".** Guard Probe
    relays that quoted question word for word (v203/v216). A refusal written only as an instruction ("Ask the requester who
    the client is ... If there is no client, leave it empty.") gets pasted by the model, and the leak filter can only drop the
    sentences it recognises - on 6 Oct the requester got "Nothing was booked. If there is no client, leave it empty." and
    guessed what to type. Better still, in prepare mode fix the input and ask (v89 drops a client nobody typed).

31. **Moving a job to a new tool means rewording every tool that still claims it - or removing the old one.** main v225 added
    Prepare Series and changed the prompt, but Expand Series' own description still said "Use this for any repeating booking
    ... its answer says how to present the series - follow it", its answer said "Present these dates in ONE summary", and the
    prompt and Prepare Booking's description each named the old path once more. A tool's own instruction tends to win over
    the prompt, so the deterministic path would have been skipped. Caught in review (v226 takes Expand Series off the agent).
    After such a change, search every node the model reads (prompt, tool descriptions, `$fromAI` descriptions) for the old
    tool name. And a direct action that takes longer than a reply (a series books ~25 s a date) needs an in-progress lock:
    the repeat-yes guard only works once the result is posted.

## Not done

- Titles are still composed by the model, but since v167 the project and client segments are put back to what the
  requester typed when the model's hold a word nobody typed, and the initials come from Bookers.
- She sometimes presents a summary without checking availability that turn. `Guard Probe`
  now refuses the summary when *this turn's* check contradicts it — the check errored, or
  named that room busy — but when no check ran at all the offer still stands until
  `ROOM_OCCUPIED` refuses at confirmation. That costs a wasted turn, not a wrong booking.
  Closing it properly means remembering availability across turns in static data.
- She sometimes asks for a date already given, and has invented a justification for a room
  choice. Both are free-text failures with nothing binding them to a source.
- **The model corrupts strings it is copying.** Three times in ~60 turns on 2026-08-30:
  "Tara Lim" → "Tara Inf", and "REASON1" → "REazon1" twice. The summary line and the title
  resolution are now defended, but nothing stops it happening somewhere new.
- QA groups: A, B, C, D, E, F, M, N, X all run 2026-08-30, and all eleven findings from that
  run are fixed — six in v100/v101 and the sub-workflows, five across v102–v112. `M2` is left
  as a judgement call rather than a defect: "vocal recording" was read as Music Vocal
  Recording without asking, where "a mix" got a clarifying question. Both are defensible.

## The record

This file, `PENDING.md`, `VERSIONS.md` (which build fixed what) and the current workflow files are the whole working
tree. Every superseded build, every old handoff, and the reasoning behind each fix
live in git history — `git log` is the record of why things are the way they are,
and the commit messages are long on purpose. `workflows/live/` is the backup of what n8n is actually running, written by
`./scripts/backup-live`.
