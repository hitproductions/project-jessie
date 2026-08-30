# Big changes

New behavior in Jessie that anyone using her in Slack will notice.

## `reset`

Type `reset` on its own to clear the conversation. She forgets the client,
session type, room and everything else, and the next message starts clean.

Use it between unrelated bookings. Memory otherwise persists through a
completed booking — that is deliberate, so "actually cancel that" works — and
it clears on its own at midnight Manila time.

*v55, reversed in v79, and made to work through the Claude Slack connector in v84.*

## yes / no confirmations

Every summary now ends `Confirm to book. (yes/no)`, `Confirm to cancel. (yes/no)` or
`Confirm to move. (yes/no)`. Answer **yes** or **no**.

Accepted as yes: yes · y · yeah · yep · ok · sure · sige · oo · opo · confirm ·
correct · go · go ahead · do it · proceed · 👍 · ✅
Accepted as no: no · n · nope · nah · hindi · wait · stop · hold on · not yet ·
never mind

Anything else counts as neither, and nothing is booked or cancelled. A reply
like "yes but move it to 3pm" is a change request, not an approval — she will
ask again rather than book the time you just corrected.

*v81, changed from (y/n) to (yes/no) in v99. Before v81, any reply at all counted as
approval — including "no".*

## She says when she is guessing a length

Give her a start time and no end — "book a VO session next Thursday at 2pm" — and
the summary now opens with what she assumed:

> Assuming 3 hours — tell me if that is wrong.

She used to pick a length silently, so a three-hour room booking could come from
a message that never mentioned three hours. If the length is wrong, say so before
you confirm; if she asks how long instead of guessing, that is the same fix.

*v105, made to survive follow-up turns in v106.*

## Asking what rooms exist gives you all of them

"List all the rooms" or "which rooms can do Atmos?" answers from the room list
itself. Previously, if you had just asked what was free at a particular time, she
carried that time over and answered with only the rooms free *then* — so Salin,
Katha and a few M booths simply vanished from a list that looked complete.

Anything that asks what is *free* still uses the time under discussion, as before.

*v102.*

## 👀 while she works

She reacts to your message with 👀 as soon as it lands, and removes it when she
replies. A turn takes 7–12 seconds, so the reaction is how you know she has it
and is not sitting idle.

If the reaction never appears, the Slack app is missing the `reactions:write`
scope — see PENDING. Replies still work either way, so its absence is not a
fault you would otherwise notice.

*v57.*

## Numbered choices

When something you said matches more than one record — a client name, usually —
she lists the matches numbered and asks you to pick one:

    1. Ino Magno - Advertising
    2. Ino Magno - Post

Reply with the number. Before this she would ask the same open question again
each time, with no way to move forward.

An exact match still resolves silently and does not ask.

*v67.*
