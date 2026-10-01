#!/usr/bin/env python3
"""main v203 (types + short summary) - PENDING 69, 70, with Book Session v73. For the DIGICON demo, 2 Oct.
  scripts/build-short-main.py <main-live> <main-out>

69 - the summary no longer prints its check code or any line beyond the title, Date, Time and Room. At the yes,
     Prepared Key works out the same fingerprint Book Session stored the full booking under (the requester + the four
     lines shown), Read Prepared fetches it from the reference-cache data table, and Prepared Booking books every
     stored detail - only if the four lines still match and the stored record is intact and under 12 hours old.
     A summary with a printed code (sent before this build) still books the old way. A "no" to a summary is still
     recognised without the code (Guard Probe compares the summary lines).
70 - the prompt's External / Personal section becomes the four types, worked out by Prepare Booking; the bookingType
     tool inputs and the Clients tool say so.
Small fixes found 1 Oct:
- a requester who is an engineer and named nobody is the engineer - said to the model, so a series no longer asks
  "Who is the assigned engineer?" (Book Session v71 already did this for single bookings);
- a change typed while a move card is showing is a change to THAT booking (it went to the date just moved);
- a move card whose new time and room are where the booking already is becomes "That's already at ...".
- the prompt asks for missing details in as few words as possible.
"""
import json, sys, copy, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

PREP_KEY = r"""// Prepared Key (main v203, PENDING 69): the short summary prints no check code. Book Session stored the full booking
// under prep-<fingerprint of the requester + the title, Date, Time and Room shown>; this works out the same fingerprint
// from Jessie's newest message so Read Prepared can fetch it. Keep pbKey identical in Book Session's Render Summary.
const PB_SALT = '4539361661025d1d';
const pbNorm = s => String(s == null ? '' : s).replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/[*_]/g, '').replace(/\s+/g, ' ').trim();
const pbKey = (ref, f) => { let h = 0x811c9dc5; const s = PB_SALT + '|key|' + String(ref || '').trim() + '|' + ['Title', 'Date', 'Time', 'Room'].map(k => pbNorm(f[k])).join('|');
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return ('0000000' + h.toString(16)).slice(-8); };
let key = '';
try {
  let msgs = []; try { msgs = $('Get Recent Messages').all().map(i => (i && i.json) || {}); } catch (e) {}
  const isBot = m => Boolean(m.bot_id || (m.message && m.message.bot_id)) || m.subtype === 'bot_message';
  const bot = msgs.find(isBot);
  const t = bot ? String(bot.text || (bot.message && bot.message.text) || '').replace(/\r/g, '') : '';
  if (/(?:Confirm to book\.\s*(?:\(yes\/no\)\s*)?|Book it\? Reply yes or no\.\s*)$/i.test(t.trim()) && !/_check [0-9a-f]{8}_/.test(t)) {
    const lines = t.split('\n').map(l => l.trim());
    const val = k => { const re = new RegExp('^\\*?' + k + ':\\*?\\s*(.*)$', 'i'); for (const l of lines) { const m = l.match(re); if (m) return m[1]; } return ''; };
    const title = (lines.find(l => /^\*[^*\n]+\*$/.test(l) && !/:\*/.test(l)) || '');
    const F = { Title: title, Date: val('Date'), Time: val('Time'), Room: val('Room') };
    const ref = String((($('Slack Trigger').first() || {}).json || {}).user || '');
    if (ref && F.Title && F.Date && F.Time && F.Room) key = 'prep-' + pbKey(ref, F);
  }
} catch (e) { key = ''; }
return [{ json: { prep_key: key } }];
"""

PB_OLD = """    const code = (t.match(/_check ([0-9a-f]{8})_/) || [])[1];
    if (!code) out.reason = 'the summary has no check code - it was not prepared';
    else if (code !== pbCode(F)) out.reason = 'the check code does not match - the summary was changed after it was prepared';
    else {"""
PB_NEW = """    const code = (t.match(/_check ([0-9a-f]{8})_/) || [])[1];
    // v203 (PENDING 69): the short summary prints no code. The full booking was stored at preparation (Book Session
    // Store Prepared) under a key over the requester and the four lines shown; Prepared Key + Read Prepared fetched it.
    // Used only if it is intact (its own code), under 12 hours old, and its four lines are exactly the ones shown.
    let stored = null;
    if (!code) { try {
      const _k = (($('Prepared Key').first() || {}).json || {}).prep_key || '';
      const _row = _k ? $('Read Prepared').all().map(i => (i && i.json) || {}).find(r => r.cache_key === _k && r.payload) : null;
      if (_row) { const _P = JSON.parse(_row.payload); const _age = Date.now() - Date.parse(_row.refreshed_at || _P.at || '');
        if (_P && _P.F && _age >= -60000 && _age < 12 * 3600000 && pbCode(_P.F) === _P.code
            && ['Title', 'Date', 'Time', 'Room'].every(k => pbNorm(_P.F[k]) === F[k])) stored = _P; }
    } catch (e) { stored = null; } }
    if (stored) Object.keys(F).forEach(k => { F[k] = pbNorm(stored.F[k]); });
    if (!code && !stored) out.reason = 'the summary has no check code and nothing intact was stored for it - it was not prepared';
    else if (code && code !== pbCode(F)) out.reason = 'the check code does not match - the summary was changed after it was prepared';
    else {"""

GP_DEC_OLD = """    const _code = (text.match(/_check ([0-9a-f]{6,})_/) || [])[1];
    const _bt = String((($('Booked For').first() || {}).json || {}).botText || '');
    if (_code && _bt.indexOf('_check ' + _code + '_') !== -1) {"""
GP_DEC_NEW = """    const _code = (text.match(/_check ([0-9a-f]{6,})_/) || [])[1];
    const _bt = String((($('Booked For').first() || {}).json || {}).botText || '');
    // v203: the short summary has no code - the same summary is its title, Date, Time and Room block again
    const _core = text.split(/\\n\\s*\\n/)[0].trim();
    if ((_code && _bt.indexOf('_check ' + _code + '_') !== -1) || (!_code && _core.length > 20 && _bt.indexOf(_core) !== -1)) {"""

# Guard: a move card that changes nothing
GP_SAME_ANCHOR = "// v194: a compact list of this turn's tool calls"
GP_SAME = r"""// --- v203: a move card whose new time and room are where the booking already is --------------------------------------
// 1 Oct (QAMD): "make it 3pm" on a series already at 3-5 PM gave 3-5 -> 3-5 cards, and a yes re-created the event.
try {
  const _nw = (text.match(/\*Now:\*\s*([^\n]+)/) || [])[1], _mv = (text.match(/\*Moving to:\*\s*([^\n]+)/) || [])[1];
  if (_nw && _mv && _nw.trim() === _mv.trim() && /Move it\? Reply yes or no\.\s*$/i.test(text)) {
    const _at = _nw.trim().replace(/^[A-Za-z]+,\s*/, '');
    text = 'That’s already at ' + _at + ' - nothing to change.';
  }
} catch (e) {}

"""

BF_SERIES_ENG_ANCHOR = "  out.saidWords = String(out.requesterText"
BF_SERIES_ENG = r"""  // v203: a requester who is an engineer and named nobody is the engineer (decided 30 Sep). Book Session does it for a
  // single booking; told here too, so a series (Expand Series, model-written) does not ask "Who is the assigned engineer?".
  try {
    if (!out.engineer && !out.bookedFor && mine.length) {
      const _me2 = staff.find(f => norm(f.Name) === requester);
      const _role2 = _me2 ? String(_me2.Info || '').split(/,|\bgoes by\b/i)[0] : '';
      const _noEng = /\b(?:no|without(?:\s+an?)?)\s+engineer\b/i.test(mine.join('\n'));
      if (_me2 && /engineer/i.test(_role2) && !_noEng) {
        out.engineer = String(_me2.Name).trim(); out.engineerResolved = true; out.engineerDefault = true;
        notes.push('THE ENGINEER IS ' + out.engineer + ' - the requester, an engineer who named no one else. Do not ask who is engineering; if they name someone else later, use that person.');
      }
    }
  } catch (e) {}
"""

BF_CARD_OLD = """        if (_ti && _dt && _tm) sum = '*' + _ti + '*\\n*Date:* ' + _dt + '\\n*Time:* ' + _tm.replace(/\\s*(?:to|—)\\s*/i, ' – ') + (_rm ? '\\n*Room:* ' + _rm : '');
      }"""
BF_CARD_NEW = """        if (_ti && _dt && _tm) sum = '*' + _ti + '*\\n*Date:* ' + _dt + '\\n*Time:* ' + _tm.replace(/\\s*(?:to|—)\\s*/i, ' – ') + (_rm ? '\\n*Room:* ' + _rm : '');
        // v203 (1 Oct, QAMD): "Moved ..." sent with the next card - a change typed now is a change to the CARD's booking
        // (it went to the date just moved). The card's title and Now line are where that booking is now.
        const _ni = _mt.lastIndexOf('*Now:*');
        if (_ni !== -1) {
          const _cd = _mt.slice(Math.max(0, _mt.lastIndexOf('\\n*', _ni - 2) + 1));
          const _ct = ((_cd.match(/^\\s*\\*([^*\\n]+)\\*\\s*$/m) || [])[1] || '').trim();
          const _nl = ((_cd.match(/\\*Now:\\*\\s*([^\\n]+)/) || [])[1] || '').match(/^(.*?\\d{4}),\\s*(\\d{1,2}:\\d{2}\\s*[AP]M\\s*[–-]\\s*\\d{1,2}:\\d{2}\\s*[AP]M)(?:,\\s*(.+))?$/i);
          if (_ct && _nl) sum = '*' + _ct + '*\\n*Date:* ' + _nl[1] + '\\n*Time:* ' + _nl[2] + (_nl[3] ? '\\n*Room:* ' + _nl[3] : '');
        }
      }"""

PROMPT_TYPE_OLD_START = "## Client type — External or Personal"
PROMPT_TYPE_NEW = ("## Booking type\n\nEvery booking is *Advertising*, *Entertainment*, *Internal* or *Personal*. Prepare Booking works it out "
                   "(the requester's words, the client, the session, the requester's department). Leave `bookingType` empty unless the "
                   "requester said it in so many words; when Prepare Booking asks, ask exactly its question and pass the answer.\n\n")
PROMPT_ENG_OLD = "*Never suggest engineer names.* Ask \"Who is the assigned engineer?\" and stop — no examples, no list."
PROMPT_ENG_NEW = "*Never suggest engineer names.* Ask \"Who's engineering?\" and stop — no examples, no list. When a notice says who the engineer is, do not ask."
PROMPT_ASK_OLD = "*Ask for everything missing in one message,* as a short list — never one field per turn."
PROMPT_ASK_NEW = ("*Ask for everything missing in one message,* in as few words as possible — e.g. \"What's the session, and who's the "
                  "client?\" — never one field per turn, and no examples or explanations unless asked.")

BT_DESC_OLD = "'External for Hit Productions client work, Personal for a personal project outside Hit. Leave empty for internal rooms.'"
BT_DESC_NEW = "'Advertising, Entertainment, Internal or Personal - only when the requester said it outright. Otherwise empty: it is worked out.'"
BS_DESC_OLD = "'External or Personal for a studio session, empty for internal rooms.'"
BS_DESC_NEW = "'Advertising, Entertainment, Internal or Personal - only when the requester said it outright. Otherwise empty.'"
CL_OLD = "Search the Clients table for a client's Client Type (External or Personal),"
CL_NEW = "Search the Clients table for a client's Client Type (Advertising, Entertainment, Internal or Personal),"

def fix(w):
    w["name"] = "Project Jessie — v203 (types + short summary)"
    # prepared key + read
    pb = node(w, "Prepared Booking"); pb["parameters"]["jsCode"] = sub1(pb["parameters"]["jsCode"], PB_OLD, PB_NEW, "prepared booking")
    x, y = pb["position"]
    pk = copy.deepcopy(pb); pk["id"] = str(uuid.uuid4()); pk["name"] = "Prepared Key"; pk["position"] = [x - 448, y + 192]; pk["parameters"] = {"jsCode": PREP_KEY}
    for k in ("executeOnce", "alwaysOutputData", "onError"): pk.pop(k, None)
    rrc = node(w, "Read Reference Cache")
    rp = copy.deepcopy(rrc); rp["id"] = str(uuid.uuid4()); rp["name"] = "Read Prepared"; rp["position"] = [x - 224, y + 192]
    rp["parameters"]["filters"] = {"conditions": [{"keyName": "cache_key", "keyValue": "={{ $('Prepared Key').first().json.prep_key || 'prep-none' }}"}]}
    rp["executeOnce"] = True; rp["alwaysOutputData"] = True; rp["onError"] = "continueRegularOutput"
    w["nodes"] += [pk, rp]
    c = w["connections"]
    if [t["node"] for t in c["Booked For"]["main"][0]] != ["Prepared Booking"]: raise SystemExit("Booked For wiring changed")
    c["Booked For"] = {"main": [[{"node": "Prepared Key", "type": "main", "index": 0}]]}
    c["Prepared Key"] = {"main": [[{"node": "Read Prepared", "type": "main", "index": 0}]]}
    c["Read Prepared"] = {"main": [[{"node": "Prepared Booking", "type": "main", "index": 0}]]}
    # guard
    g = node(w, "Guard Probe")["parameters"]
    g["jsCode"] = sub1(sub1(g["jsCode"], GP_DEC_OLD, GP_DEC_NEW, "decline"), GP_SAME_ANCHOR, GP_SAME + GP_SAME_ANCHOR, "same")
    # booked for
    b = node(w, "Booked For")["parameters"]
    b["jsCode"] = sub1(sub1(b["jsCode"], BF_SERIES_ENG_ANCHOR, BF_SERIES_ENG + BF_SERIES_ENG_ANCHOR, "series eng"), BF_CARD_OLD, BF_CARD_NEW, "card")
    # prompt
    a = node(w, "Jessie AI Agent")["parameters"]["options"]; sm = a["systemMessage"]
    i = sm.find(PROMPT_TYPE_OLD_START); j = sm.find("## Who is who", i)
    if i < 0 or j < 0 or sm.count(PROMPT_TYPE_OLD_START) != 1: raise SystemExit("prompt type section")
    sm = sm[:i] + PROMPT_TYPE_NEW + sm[j:]
    sm = sub1(sub1(sm, PROMPT_ENG_OLD, PROMPT_ENG_NEW, "prompt eng"), PROMPT_ASK_OLD, PROMPT_ASK_NEW, "prompt ask")
    a["systemMessage"] = sm
    # tool inputs
    for t in ("Prepare Booking", "Book Session"):
        v = node(w, t)["parameters"]["workflowInputs"]["value"]; v["bookingType"] = sub1(v["bookingType"], BT_DESC_OLD, BT_DESC_NEW, t)
    v = node(w, "Book Series")["parameters"]["workflowInputs"]["value"]; v["bookingType"] = sub1(v["bookingType"], BS_DESC_OLD, BS_DESC_NEW, "series")
    cl = node(w, "Clients")["parameters"]; cl["toolDescription"] = sub1(cl["toolDescription"], CL_OLD, CL_NEW, "clients")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
