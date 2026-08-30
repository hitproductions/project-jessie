# Pending

Things found while working on Jessie that can't be fixed inside the workflow —
they need a change in Airtable, in the Slack app, in Google Calendar, or on the
n8n server.

Raised 2026-08-30, all checked against the build that is live now. Each one says
how it was found and what it breaks.

---

## Airtable

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
reported one client's preferred rooms as three studios that were not the right
ones. She is no longer sent the field at all, which is why she asks which room
instead of proposing one.

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

**6. A client's Technical Requirements points at a field Jessie cannot read.**

Jem Lim's `Technical Requirements` reads:

    Long sessions. Prefers no separate vocal booth — room preference already
    noted in Preferred Room.

`Preferred Rooms` is withheld from Jessie because it returns record ids (item 5),
so that last clause dangles. Asked why she had picked a room, she completed it:
*"Jem Lim's client notes specifically mention a preference for rooms noted in
their profile"* — which reads as though the room was chosen to suit the client.
She cannot know that. The prompt tells her never to claim a room is a client's
preferred one, and the data invites her to anyway.

Fix either end: add the `Preferred Room Names` lookup from item 5 so the
reference resolves, or remove the clause from the Technical Requirements text.
Until then expect the claim to reappear — it is the data prompting it, not the
model inventing freely.

**7. Four session types list the same rooms as both Priority and Last Resort.**

```
Event         both lists: Lobby, Katha, Likha, Salin   (identical)
VO Recording  both lists: Studio 7, 8, F, C            (identical)
Meeting       both lists: Salin, Katha
QC            both lists: Studio 5
```

Where the two lists are identical, "last resort" means nothing, and Jessie could
truthfully describe a room as both the usual choice and the fallback — she called
Studio 7 "a last-resort choice for VO Recording" when VO can be recorded
anywhere. The wording no longer reaches requesters, but the ranking still drives
which room she offers first and which the guards allow.

Decide per session type whether the second list should be empty, or a genuinely
different set of rooms.

---

## Slack app

**8. Does the bot have `reactions:write`?**

Jessie puts 👀 on an incoming message and removes it when she replies, so people
can see it landed during the 7–12 seconds a turn takes. Without the scope the
reaction silently never appears — replies still work, so it fails invisibly.
Needs the scope added in the Slack app config and a reinstall.

**9. The Claude Slack connector appends a suffix to messages. Fixed.**

Messages sent through it arrive as `reset *Sent using* <@U0AVDBNH1K4>`.

Fixed as of v81: the confirmation gate strips that suffix before deciding
whether a reply was a yes or a no, so approval and refusal steps *can* now be
driven through the connector.

Also fixed in v84: the memory `reset` command strips the suffix too, so `reset`
sent through the connector clears memory. Nothing outstanding here — kept as a
record of why the gate strips that suffix at all.

---

## Google Calendar

**10. Bookings Jessie did not create can never be cancelled through her.**

`Cancel Booking` reads a `ref:` marker out of the event description to decide
whose booking it is. Events created before this build, or added directly in
Google Calendar since, carry no marker, so the guard refuses them with
`NO_REFERENCE` and tells the requester it has to be done by hand.

Confirmed live on 2026-08-30 against a pre-existing booking, and the refusal was
correct — with no marker there is no way to tell whose booking it is, and
guessing is worse than refusing.

The decision needed before launch: is "booked by hand, cancel it by hand" an
acceptable answer for the existing calendar? If not, the descriptions of
existing events need a `ref:` added, which is a bulk edit against the calendar
and needs someone to map each booking to a Slack user id first.

---

## n8n server

**11. Worth exploring an update — we don't know what the current version can do.**

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

**12. `PUT /api/v1/workflows/:id` reports success and changes nothing.**

Seen on 2026-08-30 pushing the main workflow: the request returned without an
error, the response carried no `name` or `updatedAt`, and pulling the workflow
back showed every node unchanged. The same JSON imported through the browser UI
applied correctly.

Until this is understood, `./scripts/n8n push` cannot be trusted and every
workflow change has to be imported by hand — which is slow and is itself a
source of mistakes, since it depends on importing the right file in the right
order. Reading via the API is unaffected and remains reliable.

---

## Withdrawn

**Task-runner warm-up was measured wrong.** An earlier version of this file
claimed the first Code node in every execution costs about 3.5 seconds and
called it the largest remaining source of latency. Re-measuring across
executions put the first Code node at about 0.05s, the same as later ones. The
original figure came from reading a whole-execution duration as if it were one
node's. There is nothing here to fix — noted so it does not get raised again.
