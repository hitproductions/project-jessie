# Pending — owned by someone else

Things found while working on Jessie that can't be fixed in the workflow.
Raised 2026-08-30. Each one names what's wrong, how it was found, and what it breaks.

---

## Tel — Airtable, Rooms & Studios

**1. `Room Type` says nine rooms do 5.1. Two of them are stereo only.**

`Room Type` marks Studios 1–8 and C as `5.1 Mixing`. Studio 7 and Studio 8 say
"stereo only" in their own `Equipment` notes, and their `Recording Format` is
`Stereo` and `Stereo with Sub`.

```
                 Room Type has 5.1   Recording Format      Equipment
Studio 3,4,5,6   yes                 5.1, Stereo
Studio C         yes                 Stereo, 5.1, Atmos
Studio 7         yes                 Stereo                "stereo only"
Studio 8         yes                 Stereo with Sub       "stereo only"
Studio 1         yes                 Stereo                "5.1 capable"
```

Tara's call was to follow `Recording Format`, and Jessie does that as of v61 —
she answers format questions with Studios 3, 4, 5, 6 and C. `Room Type` is
still wrong for anyone reading the table directly. Either correct it for 7 and
8, or rename it so it's clearly a category rather than a capability.

**2. Studio 1 contradicts itself.** `Equipment` says "5.1 capable",
`Recording Format` says `Stereo`. Jessie currently reports it as stereo. If
that's wrong, it's an Airtable edit — no workflow change needed.

**3. Studio E: booth or not?** `Room Type` includes `Recording Booth`, but the
`Vocal Booth` flag is not set. The flag covers Studio A, B and D only. Jessie
answers "which rooms are vocal booths" from the flag, so E is excluded. The old
prompt said "A, B, D or E", which is where the wrong answer came from.

**4. `Studio 2 ` has a trailing space in `Room Name`.** Any exact-match query
for "Studio 2" fails. It's currently only reachable by a partial match.

## Tel — Airtable, linked fields

**5. `Clients.Preferred Rooms` needs a companion field. Do not delete anything.**

The field is a link to Rooms & Studios, so what Airtable's API returns is record
ids — `reced8Jk7wG24KpdE` — not names. Jessie cannot read those. When she tried,
she reported Sasa Abella's preferred rooms as "Studio 1, Studio 2, Studio 3";
they are Studio 8, Studio F and one other. She is no longer sent the field at
all, which is why she asks which room instead of proposing one.

*What to add:* a new **Lookup** field on the Clients table — call it
`Preferred Room Names` — configured as:

    Field type:        Lookup
    Linked record:     Preferred Rooms
    Field to look up:  Room Name

That returns the same rooms as readable text. It is read-only and computed, so
it cannot drift from the link.

*What not to do:* do not delete or convert `Preferred Rooms`. The link is where
the data actually lives, and the lookup reads through it — remove the link and
both fields go. Nothing about the existing field changes.

*What it unlocks:* Jessie can go back to proposing a room instead of always
asking, which is the behaviour the prompt was originally written for. Until
then, always-ask is correct and is what she does.

**6. Same pattern for `Session Types.Priority` and `.Last Resort`.** Also links,
also record ids. The workflow resolves these itself now — Room Table reads every
room and maps the ids back to names on each message — so this one is optional.
A pair of lookup fields would let that node get simpler, nothing more.

**7. `Session Types.Room Requirements` holds a capability, not a room class.**
Post Mixing's value is "Stereo Mixing". Section 6 of HANDOFF.md records it as
"Post Mixing = Studio", which does not match the table. Worth confirming what
that field is meant to express before anything else is built on it.

**8. Still proposed, from HANDOFF 9.6:** a `Department` field on Session Types,
so the role→department inference becomes a returned value rather than a prompt
rule.

---

## Howard — Slack app

**9. Does the bot have `reactions:write`?** v57 adds a 👀 reaction to each
incoming message and removes it when the reply is sent, so people can see their
message landed during the 7–12s a turn takes. Without the scope the reaction
silently doesn't appear — the reply still works. Needs the scope added in the
Slack app config and a reinstall.

**10. The connector appends a suffix.** Messages sent through the Claude Slack
connector arrive as `reset *Sent using* <@U0AVDBNH1K4>`. That breaks the exact
match on `reset`, and it can flip a short approval into something the
confirmation gate reads as a new request. Only affects automated QA, not real
users — but it means QA driven that way can't test approvals.

## Howard — n8n

**11. Upgrading n8n would unblock the model swap.** Two node limitations, both
verified by probe against the live instance:

- the OpenAI Chat Model node force-sends `frequency_penalty` and
  `presence_penalty`, which Gemini's OpenAI-compatible endpoint rejects with
  `Unknown name "frequency_penalty": Cannot find field` — so that node cannot
  talk to Gemini at all in this version
- neither that node nor the Gemini node exposes a thinking/reasoning setting

Gemini itself accepts `reasoning_effort` and tool calling works through that
endpoint — both returned 200 in testing. So the blocker is entirely n8n's node
versions. Worth checking the changelog for both nodes against the installed
version before scheduling an upgrade, since it needs a restart.

**12. Task runner warm-up costs ~3.5s per turn.** The first Code node in every
execution takes about 3.5 seconds; later ones take 0.05s. That's the runner
starting, and it's paid on every message including "hi". If it can be kept warm
that's 3.5s off every turn — the single biggest remaining latency item now that
the conflict query is fixed.

**13. Tool schema changes need an Active toggle.** Saving a workflow does not
reload the tool definitions the agent uses. After changing any `$fromAI` input,
toggle the workflow Active off and on, or the agent keeps calling the old
schema. Verified: two runs after an import still sent the previous input names.

**14. Slack Trigger scope, from HANDOFF 9.4.** Still `any_event` with
`watchWorkspace: true`. Measured at roughly 107 executions/day, not the
thousands the handoff feared, so it's tidying rather than urgent — and scoping
it wrong makes Jessie deaf, so it should be changed while watching executions.
