# Pending — owned by someone else

Things found while working on Jessie that can't be fixed in the workflow.
Raised 2026-08-30, all checked against the build that is live now. Each one says
how it was found and what it breaks.

---

## Tel — Airtable

**1. `Room Type` marks nine rooms as `5.1 Mixing`. Two of them record in stereo only.**

Read out of Rooms & Studios directly:

```
                 Room Type has 5.1   Recording Format      Equipment says
Studio 3,4,5,6   yes                 5.1, Stereo
Studio C         yes                 Stereo, 5.1, Atmos
Studio 7         yes                 Stereo                "stereo only"
Studio 8         yes                 Stereo with Sub       "stereo only"
Studio 1         yes                 Stereo                "5.1 capable"
```

Jessie answers format questions from `Recording Format` now, so she says Studios
3, 4, 5, 6 and C. `Room Type` is still misleading for anyone reading the table.
Either correct it for 7 and 8, or rename it so it reads as a category rather
than a capability.

**2. Studio 1 contradicts itself.** `Equipment` says "5.1 capable",
`Recording Format` says `Stereo`. Jessie reports it as stereo. If that is wrong,
it is an Airtable edit — nothing in the workflow needs to change.

**3. Studio E — booth or not?** `Room Type` includes `Recording Booth`, but the
`Vocal Booth` flag is not set. The flag covers Studio A, B and D only, and that
is what Jessie answers from, so E is excluded.

**4. `Studio 2 ` has a trailing space in `Room Name`.** Any exact-match query for
"Studio 2" fails. It is only reachable by partial match.

**5. `Clients.Preferred Rooms` needs a companion field. Nothing gets deleted.**

The field is a link to Rooms & Studios, so the API returns record ids —
`reced8Jk7wG24KpdE` — not names. Jessie cannot read those. When she tried, she
reported Sasa Abella's preferred rooms as "Studio 1, Studio 2, Studio 3"; they
are Studio 8, Studio F and one other. She is no longer sent the field at all,
which is why she asks which room instead of proposing one.

*What to add:* a new **Lookup** field on the Clients table, `Preferred Room Names`:

    Field type:        Lookup
    Linked record:     Preferred Rooms
    Field to look up:  Room Name

Read-only and computed, so it cannot drift from the link.

*What not to do:* do not delete or convert `Preferred Rooms`. The link is where
the data lives and the lookup reads through it — remove the link and both fields
go.

*What it unlocks:* Jessie can propose a room again instead of always asking.
Until then, always-ask is correct and is what she does.

---

## Howard — Slack app

**6. Does the bot have `reactions:write`?**

Jessie puts 👀 on an incoming message and removes it when she replies, so people
can see it landed during the 7–12 seconds a turn takes. Without the scope the
reaction silently never appears — replies still work, so it fails invisibly.
Needs the scope added in the Slack app config and a reinstall.

**7. The Claude Slack connector appends a suffix to messages.**

Messages sent through it arrive as `reset *Sent using* <@U0AVDBNH1K4>`. That
breaks the exact match on `reset`, and can turn a short approval into something
the confirmation gate reads as a new request. It only affects QA driven through
the connector, not people typing in Slack — but it means approval steps can't be
tested that way.

---

## Howard — n8n

**8. Worth exploring an n8n update — we don't know what the current version can do.**

Two things we wanted turned out not to be reachable from the installed version:

- the OpenAI Chat Model node always sends `frequency_penalty`, which Gemini's
  OpenAI-compatible endpoint rejects outright, so that node can't talk to Gemini
  at all here
- neither that node nor the Gemini node exposes a thinking or reasoning setting,
  and prompt caching isn't exposed either

Gemini itself accepts those parameters — tested directly against the API — so
the limits are on the n8n side. Whether a newer version lifts any of them is an
open question, not a promise: worth checking the changelogs for those two nodes
against what's installed before deciding whether an update is worth the restart.

**9. The first Code node in every run costs about 3.5 seconds.**

n8n runs Code nodes in a separate task-runner process. The first one in an
execution waits for that process to be ready; later ones in the same execution
take about 0.05s. Measured across runs, that first-node wait is consistently
3.4–3.6 seconds.

It is paid on every message, including ones that do nothing — a bare "hi" costs
it. With the conflict query now fixed, it is the single largest remaining piece
of latency, worth more than everything else left combined.

The question for Howard: can the task runner be kept warm or started ahead of
time, so the first Code node doesn't pay for it? If it can, every turn gets
about 3.5 seconds shorter.
