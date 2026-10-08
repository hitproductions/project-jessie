#!/usr/bin/env python3
"""main v243 (transcript, no memory) - PENDING 99, second pass. v242 put short notes in the conversation memory in place of
cards; Haiku 5.5 then copied the notes' style ("[Availability check run by its tool ... Result to follow.]", 8 Oct 19:49).
Whatever sits in the model's own earlier turns gets copied: cards, then notes. So the model gets no earlier turns at all.

1. Conversation Memory is removed (with v242's Tidy Memory? / Forget Card / Note Card). The agent runs without memory.
2. Get Transcript (Slack history, last 25 messages - its own fetch, so Get Recent Messages' 12 and everything that reads
   them is unchanged) -> Build Transcript (code) between Booked For and Prepared Key. It writes the conversation so far,
   oldest first, as a third-person transcript: the requester's words exactly (the "Sent using" footer dropped), Jessie's
   cards as one-line summaries ("Jessie showed a cancel card (waiting for yes or no): ..."), Jessie's other replies
   flattened to one line. Only messages after the last reset (Gate Context's epoch), from today (Manila), before this
   message; at most the last 20 lines. It covers every reply in the DM - also the ones sent straight from code ("Booked.",
   "Cancelled ...", "Moved ..."), which memory never had. Passes Booked For's item on unchanged, plus `transcript`.
3. The agent's prompt is that transcript (when there is one) followed by the new message.
4. Prompt: the v242 card paragraph now describes the transcript; cancelling - a named booking goes straight to Prepare
   Cancel (no Find Booking, no "shall I prepare it?" - 8 Oct 19:45 / 19:46), Find Booking only when they give no booking.
5. Guard Probe: a reply that is only a bracketed line, or written in the transcript's format ("Jessie showed ...",
   "Requester: ..."), is withdrawn like a card no tool made.
  scripts/build-v243.py <main-v242> <main-out>
"""
import json, sys, uuid
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

TRANSCRIPT_JS = r"""// Build Transcript (main v243, PENDING 99): the conversation so far, for the agent, written by code. The agent has no
// memory since v243 - Claude copied whatever its own earlier turns looked like (cards, then v242's notes). This is a
// third-person transcript instead: the requester's words exactly, Jessie's cards as one-line summaries, her other
// replies on one line. After the last reset, today (Manila), before this message, at most the last 20 lines. Never throws.
const isBot = m => Boolean(m.bot_id) || m.subtype === 'bot_message';
const clean = s => String(s || '').replace(/\*sent using\*[\s\S]*$/i, '').replace(/\s+$/, '').trim();
const flat = s => String(s || '').split('\n').map(l => l.trim()).filter(Boolean).join(' / ');
const cut = (s, n) => s.length > n ? s.slice(0, n - 3) + '...' : s;
let transcript = '', lines = 0, source = 'none';
try {
  let msgs = [];
  try { msgs = $('Get Transcript').all().map(i => (i && i.json) || {}).filter(m => m.ts); source = 'Get Transcript'; } catch (e) { msgs = []; }
  if (!msgs.length) { try { msgs = $('Get Recent Messages').all().map(i => (i && i.json) || {}).filter(m => m.ts); source = 'Get Recent Messages'; } catch (e) { msgs = []; } }
  const trigTs = parseFloat(String(($('Slack Trigger').first().json || {}).ts || '0')) || Infinity;
  let epoch = 0; try { epoch = parseFloat(String(($('Gate Context').first().json || {}).epoch || '0')) || 0; } catch (e) {}
  const manilaDay = sec => new Date(sec * 1000 + 8 * 3600 * 1000).toISOString().slice(0, 10);
  const today = manilaDay(Date.now() / 1000);
  const seen = new Set();
  const rows = msgs
    .filter(m => { const t = parseFloat(m.ts); return t && t < trigTs && t > epoch && manilaDay(t) === today && !seen.has(m.ts) && seen.add(m.ts); })
    .sort((a, b) => parseFloat(a.ts) - parseFloat(b.ts))
    .map(m => {
      if (!isBot(m)) { const t = clean(m.text); return t ? 'Requester: ' + cut(flat(t), 500) : ''; }
      const t = String(m.text || '').trim();
      if (!t) return '';
      if (/check that against the calendar just now/.test(t)) return 'Jessie said she could not check it against the calendar, so nothing was done.';
      const mk = t.match(/\b(Book|Cancel|Move) it\? Reply yes or no\.\s*$|Confirm to (book|cancel|move)\.(?:\s*\((?:y\/n|yes\/no)\))?\s*$/i);
      if (mk) {
        const kind = /\*Dates(?: \(\d+\))?:\*/.test(t) ? 'series booking' : ({ book: 'booking', cancel: 'cancel', move: 'move' })[String(mk[1] || mk[2]).toLowerCase()];
        const body = t.split('\n').map(l => l.replace(/[*_]/g, '').trim())
          .filter(l => l && !/Reply yes or no\.|^Reply only with|^Confirm to (?:book|cancel|move)\./i.test(l) && !/^check [0-9a-f]{8}$/i.test(l)).join(' | ');
        return 'Jessie showed a ' + kind + ' card (waiting for yes or no): ' + cut(body, 500);
      }
      return 'Jessie: ' + cut(flat(t.replace(/[*_]/g, '')), 500);
    })
    .filter(Boolean);
  const last = rows.slice(-20);
  lines = last.length;
  transcript = last.join('\n');
} catch (e) { transcript = ''; source = 'error: ' + e.message; }
return $('Booked For').all().map(i => ({ json: Object.assign({}, i.json, { transcript, transcriptLines: lines, transcriptSource: source }) }));
"""

PROMPT = ("={{ $('Build Transcript').first().json.transcript ? 'Earlier in this conversation, oldest first (context only - "
          "the tools are the truth; never write your reply in this format):\\n' + $('Build Transcript').first().json.transcript "
          "+ '\\n\\nTheir new message:\\n' : '' }}{{ $('Slack Trigger').first().json.text }}")

OLD_CARDS = ("Cards - the booking, series, cancel and move summaries that end with a yes/no question - only ever come from Prepare "
             "Booking, Prepare Series, Prepare Cancel and Move Booking, and they are sent to the requester automatically. In the "
             "earlier turns of this conversation a card shows as a short note in square brackets. Never write a card or a "
             "bracketed note yourself, and never repeat an earlier one: for every new, repeated or changed request, call the tool "
             "again.")
NEW_CARDS = ("Cards - the booking, series, cancel and move summaries that end with a yes/no question - only ever come from Prepare "
             "Booking, Prepare Series, Prepare Cancel and Move Booking, and they are sent to the requester automatically. The "
             "conversation so far comes with each message as a short transcript (\"Requester: ...\", \"Jessie: ...\", \"Jessie "
             "showed a cancel card ...\"). Use it to understand what they mean - \"that one\", \"move it\", \"make it 3pm\" - but "
             "never write your reply in its format, never write a card yourself, and never repeat an earlier one: for every new, "
             "repeated or changed request, call the tool again.")

OLD_CANCEL = ("1. Ask which booking and its date — if they give only a project, client or room, ask for the date first.\n"
              "2. Call Find Booking for that date. If nothing comes back, say the search was empty and ask them to check the date — don't attempt a delete, and don't claim the booking doesn't exist.\n"
              "3. If several bookings match, list them and ask which one. Once it is one booking, call Prepare Cancel with its title exactly as Find Booking returned it and its date. It checks the booking and whether they may cancel it, and returns a card, which is sent to the requester automatically: reply with one short line such as \"Here it is.\" and stop. Never write a cancel confirmation yourself.")
NEW_CANCEL = ("1. When they name the booking - its title or project - call Prepare Cancel straight away, with the title as they gave it and the date if they gave one (leave the date empty rather than guess: it then finds the booking by its title). Don't call Find Booking first, and don't ask them to confirm which booking: Prepare Cancel finds it, checks whether they may cancel it, and asks them itself when more than one booking matches.\n"
              "2. If they give only a client or a room, ask for the date, call Find Booking for that date, and once it is one booking call Prepare Cancel with its title exactly as Find Booking returned it and its date. If the search comes back empty, say so and ask them to check the date - don't claim the booking doesn't exist.\n"
              "3. Prepare Cancel returns a card, which is sent to the requester automatically: reply with one short line such as \"Here it is.\" and stop. If it refuses or asks a question, relay that and stop. Never write a cancel confirmation yourself.")

def main(w):
    w["name"] = "Project Jessie — v243 (transcript, no memory)"
    names = {n["name"] for n in w["nodes"]}
    gone = ["Conversation Memory", "Tidy Memory?", "Forget Card", "Note Card"]
    if not set(gone) <= names: raise SystemExit(f"missing: {set(gone) - names}")
    w["nodes"] = [n for n in w["nodes"] if n["name"] not in gone]
    c = w["connections"]
    for g in gone: c.pop(g, None)
    ef = c["Error filter"]["main"][1]
    c["Error filter"]["main"][1] = [e for e in ef if e["node"] != "Tidy Memory?"]
    for src, cc in c.items():
        for k, v in cc.items():
            for t in v:
                if any(e["node"] in gone for e in (t or [])): raise SystemExit(f"{src} still points at a removed node")

    # transcript nodes between Booked For and Prepared Key
    grm, bf = node(w, "Get Recent Messages"), node(w, "Booked For")
    bx, by = bf["position"]
    gt = json.loads(json.dumps(grm))
    gt.update({"id": str(uuid.uuid4()), "name": "Get Transcript", "position": [bx + 240, by - 200], "executeOnce": True,
               "alwaysOutputData": True, "onError": "continueRegularOutput"})
    gt["parameters"]["limit"] = 25
    bt = {"parameters": {"jsCode": TRANSCRIPT_JS}, "id": str(uuid.uuid4()), "name": "Build Transcript",
          "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [bx + 480, by - 200], "alwaysOutputData": True}
    code_tv = next((n["typeVersion"] for n in w["nodes"] if n["type"] == "n8n-nodes-base.code"), 2)
    bt["typeVersion"] = code_tv
    w["nodes"] += [gt, bt]
    if [e["node"] for e in c["Booked For"]["main"][0]] != ["Prepared Key"]: raise SystemExit("Booked For wiring changed")
    c["Booked For"]["main"][0] = [{"node": "Get Transcript", "type": "main", "index": 0}]
    c["Get Transcript"] = {"main": [[{"node": "Build Transcript", "type": "main", "index": 0}]]}
    c["Build Transcript"] = {"main": [[{"node": "Prepared Key", "type": "main", "index": 0}]]}

    # agent prompt + system message
    ag = node(w, "Jessie AI Agent")["parameters"]
    if ag.get("text") != "={{ $('Slack Trigger').first().json.text }}": raise SystemExit(f"agent prompt: {ag.get('text')}")
    ag["text"] = PROMPT
    sm = ag["options"]["systemMessage"]
    sm = once(sm, OLD_CARDS, NEW_CARDS, "cards paragraph")
    sm = once(sm, OLD_CANCEL, NEW_CANCEL, "cancel steps")
    ag["options"]["systemMessage"] = sm

    # Guard Probe: bracket-only or transcript-format replies are withdrawn
    gp = node(w, "Guard Probe")["parameters"]
    gp["jsCode"] = once(gp["jsCode"],
        "  const _noteOnly = /^\\s*\\[(?:(?:book|booking|cancel|move|series) card shown|Nothing was done:)/i.test(text);",
        "  // v243 (transcript): also a reply that is only a bracketed line (\"[Availability check run by its tool ...]\", 8 Oct\n"
        "  // 19:49 on v242) or written in the transcript's format (\"Jessie showed ...\", \"Requester: ...\").\n"
        "  const _noteOnly = /^\\s*\\[(?:(?:book|booking|cancel|move|series) card shown|Nothing was done:)/i.test(text)\n"
        "    || /^\\s*\\[[^\\]\\n]{8,}\\]\\s*$/.test(text) || /^\\s*(?:Jessie (?:showed|said)\\b|Requester:)/.test(text);",
        "note guard")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
