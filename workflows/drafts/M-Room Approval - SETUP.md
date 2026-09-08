# M-Room shared-use approval — build handoff

Two new sub-workflows implement the timed approval window that a Slack agent turn can't
hold open. Nothing here has touched the live n8n — these are import-and-review drafts.

## Files
- `Jessie - M-Room Approval.json` — async workflow: notify approver → wait for the window
  → book (approved / no response) or decline. This is the piece that holds the request open.
- `Jessie - Book M-Room.json` — the tool the agent calls for M2/M6/M7. Checks the hold and
  either books it, fires the approval workflow, or reports the room taken.
- `jessie_mroom_approval_section.txt` (in Downloads) — the prompt section, matched to the
  tool contract above. Paste it into the `Internal rooms` part of the Jessie AI Agent system
  message, after the `### M Booths (M1–M8)` block.

## How it flows
1. Agent routes an M2/M6/M7 request to **Book M-Room** (immediately, like any M booth).
2. Book M-Room runs List Events on that booth's window:
   - no overlap with the hold → creates the booking → returns `CREATED`.
   - overlaps the hold → POSTs the request to the Approval webhook, returns `PENDING_APPROVAL`.
   - overlapped by a *non-hold* booking → returns `ROOM_TAKEN`.
3. Approval workflow DMs the approver with the details and two links (Approve / Decline),
   then a **Wait** node holds until a link is clicked **or** the deadline passes:
   - same-day request → 1 hour · day before → 10:00 AM on the booking day · 2+ days → 24 hours
     (all PST; the window is also capped so it never runs past the session start).
   - Approve **or** no response by the deadline → re-checks availability, creates the booking,
     DMs the requester.
   - Decline → DMs the requester, offers another booth/time. Never books.

The approve/decline links point at the Wait node's own resume URL, so **no Slack app change is
needed** — no interactivity URL, no signing secret. A click opens a short n8n confirmation page.
(If you'd rather have in-Slack Approve/Decline buttons later, that's a Block Kit upgrade plus the
Slack app's Interactivity URL — say the word and I'll wire it.)

## You must fill in before it runs
1. **Approver Slack member IDs** (Uxxxxxxxx) — in `Jessie - M-Room Approval.json`, the `Compute`
   node's `ROOMS` map: `<<M2_APPROVER_SLACK_ID>>` (Peemo), `<<M6_APPROVER_SLACK_ID>>` (Nicole),
   `<<M7_APPROVER_SLACK_ID>>` (Ana Cadelina).
2. **n8n webhook base URL** — in `Jessie - Book M-Room.json`, the `Fire Approval` node's URL:
   replace `<<N8N_WEBHOOK_BASE>>` with your instance origin (e.g. `https://n8n.hitproductions.net`).
   Final URL: `<base>/webhook/jessie-mroom-approval`.
3. **Book M-Room's workflow id** — after importing Book M-Room, add the tool node below to the
   main workflow and set its `workflowId` to the imported id.

## Confirm these assumptions (they drive detection)
- **Hold event titles (CONFIRMED 2026-09-08).** Detection tells the standing hold apart from a
  real booking by keyword in the event title: M2 → `peemo` (title `M2 - Peemo`), M6 →
  `marketing` (title `M6 - Marketing`), M7 → `bd` / `business development` (title
  `M7 - BD` / `Business Development`). Note M6's hold is titled after the Marketing department,
  NOT the approver Nicole Miller — she is still the approver, but the keyword is `marketing`.
  If a title doesn't contain the keyword, an overlap won't be seen as the hold. Keywords live in
  the `holdWords` / `HOLD_KEYWORDS` arrays in both files.
- Internal-room events are titled starting with the room name (`M2 - …`), which is how each event
  is matched to its booth. That's the existing convention in the prompt, so it should hold.

## The tool node to add to the main workflow (`Project Jessie v2`)
Add this node, wire its **ai_tool** output into the `Jessie AI Agent` node (same as Book Session),
and set `workflowId.value` to the imported Book M-Room id.

```json
{
  "parameters": {
    "description": "Book an M2, M6 or M7 booth — these three carry a standing recurring hold and are NOT first-come. Use this INSTEAD of Book Session for M2, M6 and M7 only; every other room still uses Book Session. Call it immediately once you have the booth and date, like any M booth (no summary/confirmation step). It checks the booth's hold for you and returns one of: CREATED (booked — no overlap or the owner is booking), PENDING_APPROVAL (overlaps the hold; the approver has been asked and a timed window opened — relay that nothing is booked yet and you'll confirm when it resolves), ROOM_TAKEN (an ordinary booking already has that window), or BLOCKED (past date). Relay the 'human' field close to verbatim. Never re-call it after PENDING_APPROVAL.",
    "workflowId": { "__rl": true, "value": "PASTE_BOOK_M_ROOM_WORKFLOW_ID", "mode": "list", "cachedResultName": "Jessie — Book M-Room" },
    "workflowInputs": {
      "mappingMode": "defineBelow",
      "value": {
        "room": "={{ $fromAI('room', 'The booth: one of M2, M6, M7.', 'string', '') }}",
        "summary": "={{ $fromAI('summary', 'The event title, e.g. \"M2 - Howard\" (Room - Booking Owner, hyphen with a space each side).', 'string', '') }}",
        "start_iso": "={{ $fromAI('start', 'ISO 8601 start with +08:00. For an all-day booking, just the date.', 'string', '') }}",
        "end_iso": "={{ $fromAI('end', 'ISO 8601 end with +08:00. For all-day, the day after the booking date.', 'string', '') }}",
        "all_day": "={{ $fromAI('all_day', 'True for an M booth with no time given (all-day).', 'boolean', false) }}",
        "description": "={{ $fromAI('description', 'Usually empty for an M booth. Do NOT write Booked by — it is added automatically.', 'string', '') }}",
        "requester_name": "={{ $('Get Booker').first().json.fields.Name }}",
        "requester_slack_id": "={{ $('Slack Trigger').first().json.user }}"
      },
      "matchingColumns": [],
      "schema": [
        { "id": "room", "displayName": "room", "required": false, "display": true, "type": "string", "canBeUsedToMatch": true },
        { "id": "summary", "displayName": "summary", "required": false, "display": true, "type": "string", "canBeUsedToMatch": true },
        { "id": "start_iso", "displayName": "start_iso", "required": false, "display": true, "type": "string", "canBeUsedToMatch": true },
        { "id": "end_iso", "displayName": "end_iso", "required": false, "display": true, "type": "string", "canBeUsedToMatch": true },
        { "id": "all_day", "displayName": "all_day", "required": false, "display": true, "type": "boolean", "canBeUsedToMatch": true },
        { "id": "description", "displayName": "description", "required": false, "display": true, "type": "string", "canBeUsedToMatch": true },
        { "id": "requester_name", "displayName": "requester_name", "required": false, "display": true, "type": "string", "canBeUsedToMatch": true },
        { "id": "requester_slack_id", "displayName": "requester_slack_id", "required": false, "display": true, "type": "string", "canBeUsedToMatch": true }
      ],
      "attemptToConvertTypes": false,
      "convertFieldsToString": false
    }
  },
  "id": "book-m-room-tool",
  "name": "Book M-Room",
  "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
  "typeVersion": 2.2,
  "position": [1600, 700],
  "credentials": {}
}
```

## Import order
1. Import **Jessie — Book M-Room**. Fix credentials (Google Calendar) if the id doesn't resolve.
2. Import **Jessie — M-Room Approval**. Fix Slack + Google Calendar credentials; **Activate** it
   (the webhook only listens on the production URL when active). Fill the three approver Slack IDs.
3. In **Jessie — Book M-Room** → `Fire Approval`, set the real webhook base URL.
4. In the main workflow, add the **Book M-Room** tool node above, set its `workflowId`, connect it
   to the agent, and paste the prompt section.

## Verify on a test run (points I couldn't test without your n8n)
- **`$execution.resumeUrl` in `Notify Approver`** resolves to a working link before the Wait node.
  This is the standard n8n "wait for webhook" pattern, but confirm the DM's links are clickable and
  resume the right execution.
- **Wait resume reads the decision** — after clicking Approve, `Resolve Outcome` should see
  `decision=approve` (it reads `query.decision` with fallbacks). Confirm approve vs decline vs
  timeout all land on the right branch. **Timeout = book** is the intended, load-bearing behavior.
- **Slack DM to a user** (`select: user`) opens a DM from the Jessie bot — the bot needs `im:write`
  and the approver must accept DMs.
- **Google Calendar create** attaches the booth resource and, for all-day, uses the exclusive end
  date (handled in code).

## Test cases worth running
1. M2 request that does NOT overlap the hold → `CREATED`, booked immediately.
2. M2 request overlapping the `M2 - Peemo` hold, made same-day → approver DM'd, 1-hour window;
   click Approve → booked; requester DM'd.
3. Same as (2) but click Decline → not booked; requester offered alternatives.
4. Same as (2) but let the window lapse → auto-booked; requester DM'd "no word back… booked".
5. Day-before request → window ends 10:00 AM booking day. 2+ days → 24-hour window.
6. M2 overlapped by a real (non-hold) booking → `ROOM_TAKEN`.
