# Big changes

New behavior in Jessie that anyone using her in Slack will notice.

## `reset`

Type `reset` on its own to clear the conversation. She forgets the client,
session type, room and everything else, and the next message starts clean.

Use it between unrelated bookings. Memory otherwise persists through a
completed booking — that is deliberate, so "actually cancel that" works — and
it clears on its own at midnight Manila time.

*v55, reversed in v79, and made to work through the Claude Slack connector in v84.*

## y / n confirmations

Every summary now ends `Confirm to book. (y/n)` or `Confirm to cancel. (y/n)`.
Answer **y** or **n**.

Accepted as yes: y · yes · yeah · yep · ok · sure · sige · oo · opo · confirm ·
correct · go · go ahead · do it · proceed · 👍 · ✅
Accepted as no: n · no · nope · nah · hindi · wait · stop · hold on · not yet ·
never mind

Anything else counts as neither, and nothing is booked or cancelled. A reply
like "yes but move it to 3pm" is a change request, not an approval — she will
ask again rather than book the time you just corrected.

*v81. Before this, any reply at all counted as approval, including "no".*

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
