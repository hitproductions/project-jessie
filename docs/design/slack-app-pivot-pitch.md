# Jessie: from conversation to forms — the pitch

**The ask:** approve moving Jessie's booking flows from chat to Slack forms and buttons, so the build can start.

## Recommendation

Keep typing for the first message and for questions; use forms and buttons for everything that books, cancels, moves or
approves. Three reasons:

1. **It removes the failures we keep chasing.** Most of the 12 failures in the 13 Oct wide test came from two causes a
   form cannot have: details carrying over from earlier requests, and misreading free text.
2. **Nothing that protects a booking changes.** Every check (double booking, room suitability, ownership, approvals) lives
   in the back end, and the forms call the same back end.
3. **Fixes to the chat have stopped converging.** Over the last ten builds, moving a job into code held; patching the AI's
   wording went in circles, one phrasing at a time.

## Will it solve the problems?

| Problem (13 Oct wide test, 20 scenarios, 8 passed) | Why a form fixes it | Confidence | What is left |
|---|---|---|---|
| Details carried over between requests (6) - an old session type looped a question; a declined request's details were reused; availability answered for an old time | Each form submission stands alone; nothing reads the earlier thread | High | Typed questions keep a short, question-only memory |
| Free text misread (4) - "bukas", "stdio 7", "9am for 2 hours", two bookings in one message | Date and time pickers, lists from Airtable; nothing to parse | High | The first message is still read, but only to pre-fill the form, which the person sees and can fix |
| The AI's own wording (3) - working notes leaked, questions phrased its own way | Code writes every question, result and error | High | Small talk and off-topic replies |
| Approvals looping, blank names, duplicate requests (open bugs) | Approve / Decline buttons; messages written from the record | High | The approval deadlines still need one live test |

## Options considered

| Option | Pros | Cons |
|---|---|---|
| A. Keep patching the chat | No new build | The same failure types keep returning; every fix covers one phrasing |
| B. Forms only, no AI | Most predictable | Loses quick typed requests and questions people like |
| **C. Hybrid (recommended)** | Typing where it helps, forms where it must be exact | New front end to build and test |

## Pros and cons of the recommendation

**Pros**
- Reliable bookings: no carry-over, no misreads, no AI wording in what people read.
- Fewer steps: one form and one tap instead of a back-and-forth and a typed "yes".
- Nothing lost: every back-end check, record and approval rule is kept.
- New things become easy: only free rooms offered, a day view of the studios, buttons on every booking, reminders that
  free up unused rooms, moving or cancelling a whole series.
- Several open bugs close by design (approvals, booking lists, "which one?" questions).

**Cons and risks**
- **Build effort:** a new front end (one new workflow for clicks and forms, plus the screens). The back end - 11 of the
  12 workflows - is reused; the chat side shrinks.
- **Less free-form:** people fill in a form instead of chatting. Typing still starts a request.
- **Slack's rules:** forms must be answered within 3 seconds (handled by acknowledging at once), and dropdowns cap at 100
  options (client and project code stay typed text fields, checked on submit).
- **Testing needs people:** forms can't be clicked by the automated tester; each flow gets a short script.
- **Setup and change:** one Slack app setting and one Cloudflare rule; the SOP and orientation are redone around the forms.

## Cost and next steps

1. **Setup (owner):** turn on Slack Interactivity; add its URL to the Cloudflare exemption.
2. **Build in order, each tested before the next:** Book a room → results, My bookings, cancel and move → availability
   answers → internal and paired rooms, series → approvals, notices, reminders.
3. **Switch flow by flow:** the chat keeps working until each form passes its test.

**Decision needed:** go / no-go on the hybrid direction.

---

Appendix (for anyone who wants depth): the before / after deck `docs/design/slack-app-pivot-deck.html`, the full design
`docs/design/slack-app-processes.md`, the test log `docs/qa/wide-test-2026-10-13.md`, build notes
`docs/design/slack-app-build-notes.md`.
