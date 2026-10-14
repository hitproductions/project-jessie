# Slack app — the hello-form test

**Result (14 Oct, 17:01-17:02 PHT): passed.** Workflow `PyxSPoAMtSE1gzaH`. Signature OK (request age 1 s), raw body
from binary (2733 chars), date picker opened on 2027-10-14 (year ahead), form updated 3.6 s after Send (3 s pretend work),
views.update OK, clicks reached n8n through Cloudflare. The payload was read from n8n's parsed body, not the raw text
(the sandbox likely lacks URLSearchParams) - fine: the signature uses the raw bytes, the contents n8n's parsed copy.

The first build step of the Slack-app pivot ([`slack-app-v1-scope.md`](slack-app-v1-scope.md), "Before the first slice").
A small, separate workflow - **Jessie — Slack Interactions — v1 (hello form)**, `workflows/slack-interactions-v1.json` -
that proves the parts every later screen depends on, before any real screen is built:

1. a click and a form submission reach n8n through Cloudflare
2. Slack's signature can be checked in n8n (no server change: the Webhook's Raw Body + the Crypto node)
3. n8n answers Slack within 3 seconds, and does the slow part after
4. a form opens, updates after the answer, and a DM follows
5. the date picker opens a year ahead (the QA year shift)

It does not touch main, the chat, or any booking. It only acts on its own button.

## Setup (the owner, ~15 minutes)

**1. Slack app - turn on Interactivity.** api.slack.com/apps → the Jessie app → **Interactivity & Shortcuts** → On →
Request URL:

```
https://signal.hitpromanila.net/webhook/jessie-interactions
```

→ **Save Changes**. Nothing else in the app changes (no new scopes, no shortcuts, no slash commands).

**2. Cloudflare - make sure Slack can reach that URL.** Open the exemption (skip) rule set on 1 Oct for Jessie's and
Posty's webhooks (Security → WAF → Custom rules). If it matches every `/webhook/` path, nothing to do. If it lists
specific paths, add `/webhook/jessie-interactions`. (Without it, Cloudflare can answer Slack with 403 - the outage
mechanism in PENDING 21.) **Checked 14 Oct:** the rule matches every path starting with `/webhook/`, so this URL is
already covered - nothing to add. The expression is now in `docs/outages/OUTAGES.md`.

**3. n8n - import into a new workflow** (not into main or any existing workflow):
- Workflows → **Create workflow** → ⋯ → **Import from File** → `workflows/slack-interactions-v1.json`.
- Open the **Signature** node → **Secret** → replace `PASTE-THE-SLACK-SIGNING-SECRET-HERE` with the app's **Signing
  Secret** (api.slack.com/apps → Jessie → Basic Information → App Credentials → Signing Secret → Show). Never paste
  it in Slack, a chat or a commit.
- Check the four Slack nodes (Send Button, Open Form, Update Form, DM …) use the credential **Jessie Slack (signed)**.
- **Save**, then **Publish / activate** (the production URL only listens on an active workflow).
- Download it once (⋯ → Download) into `workflows/imported/slack-interactions-v1-imported.json` and send the new
  workflow's id - it goes into CLAUDE.md's workflow table. (`check-import after` will show one difference: the secret.)

## The test (the owner, in Slack)

1. In n8n, open the workflow and click **Execute workflow** on **Post Test Button**. A message with an **Open test form**
   button appears in your DM with Jessie.
2. Tap **Open test form**. A form opens; the date should show **next year's** date.
3. Pick any date, type anything, press **Send**. The form should change to **"⏳ Working…"** at once, then to **"✅ Done"**
   about 3 seconds later.
4. A DM arrives: **"Hello form - result"**, with the signature check, the raw-body source, the date and the timings.

**Send back:** a screenshot of the result DM (or of whatever happened instead). If something fails, Slack's own message
("This app didn't respond…") or a "Hello form - a request was refused" DM says where.

## What each outcome means

| You see | It means | Next |
|---|---|---|
| Result DM, signature OK | Everything works | Start slice 1 |
| "request was refused", signature did not match | The secret is wrong, or Raw Body did not give the exact bytes | Check the pasted secret; if it is right, the raw-body reading needs another way (the DM's "Raw body" line says which was used) |
| Tapping the button does nothing / "didn't respond" | The click never reached n8n | Cloudflare rule, the Request URL, or the workflow is not active |
| Button works, form doesn't open | `views.open` failed; a DM says why | Usually the 3-second trigger window or the credential |
| "Working…" never changes to "Done" | `views.update` failed; the result DM says why | Credential or view id |

## Built and checked offline

`python3 scripts/build-slack-interactions-v1.py` writes the file; `node scripts/sim-hello-form.js` runs the Code nodes
on signed requests (a click, a submission, a forged signature, a 10-minute-old request, a request without Raw Body):
14 checks. Not checked offline: the real Crypto, Webhook and Respond nodes, Cloudflare and Slack - that is what this
test is for.

**Known follow-up for the real build:** the signing secret lives in the Signature node, so every re-import of this
workflow means pasting it again. Before slice 1, decide where it lives for good (an n8n environment variable needs IT;
otherwise keep the paste step in the import routine).
