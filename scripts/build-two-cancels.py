#!/usr/bin/env python3
"""main v187 (two cancels, start time) - live QA 29 Sep.
  scripts/build-two-cancels.py <main-pull> <main-out>

PENDING 55  "qamove - november 17 / qatime - nov 16": both cards were prepared, only the last reached Slack, and the
            yes cancelled that one only. Now the first card is shown with a "_Next: ..._" line for each other one. At
            the yes, Cancel Direct cancels the card's booking, then Prepare Next Cancel (Cancel Booking, prepare mode)
            renders the next card, and the reply is "Cancelled ..." followed by that card - so each booking still gets
            its own card, its own check code and its own yes. Any number of cancels chain this way.
QA bug 15   "is studio 7 free next thursday at 2pm?" -> "free ... from 2:00 PM to 4:00 PM": an end time nobody gave
            (Room Availability was asked for a 2-hour window). With only a start time given, an availability line that
            shows start-to-end is rewritten to "at 2:00 PM (checked until 4:00 PM)", and asks how long if nothing
            else is asked. A busy line (someone else's real booking) is never touched.
"""
import json, sys, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# --- Guard Probe: every prepared card this turn, the first shown, the rest queued ---------------------------------
GP_CARD_OLD = """  for (let i = _s1.length - 1; i >= 0; i--) {
    const _t = String(((_s1[i] || {}).action || {}).tool || '').replace(/[_\\s]+/g, ' ').toLowerCase();
    if (_t !== 'prepare cancel' && _t !== 'cancel booking') continue;   // v183: Cancel Booking unconfirmed = Prepare Cancel
    let _o = null; try { _o = [].concat(JSON.parse(String((_s1[i] || {}).observation || '')))[0]; } catch (e) {}
    if (_o && _o.status === 'PREPARED' && _o.card_text) { text = String(_o.card_text); _prepared = true; }
    break;
  }"""
GP_CARD_NEW = """  // v187 (PENDING 55): two cancels in one message showed only the last card. Every card prepared this turn is
  // kept, in the order asked; the first is shown and each other one is queued as a "_Next: ..._" line, which
  // Prepared Cancel reads back at the yes to show the next card. Still decided by the latest cancel call: if that
  // one was not PREPARED, no card at all, as before.
  const _cards = []; let _lastOk = false;
  for (let i = 0; i < _s1.length; i++) {
    const _t = String(((_s1[i] || {}).action || {}).tool || '').replace(/[_\\s]+/g, ' ').toLowerCase();
    if (_t !== 'prepare cancel' && _t !== 'cancel booking') continue;   // v183: Cancel Booking unconfirmed = Prepare Cancel
    let _o = null; try { _o = [].concat(JSON.parse(String((_s1[i] || {}).observation || '')))[0]; } catch (e) {}
    _lastOk = !!(_o && _o.status === 'PREPARED' && _o.card_text);
    if (_lastOk) {
      const _ct = String(_o.card_text), _k = (_ct.match(/_check ([0-9a-f]{8})_/) || [])[1] || _ct;
      if (!_cards.some(c => c.k === _k)) _cards.push({ k: _k, ct: _ct });
    }
  }
  if (_lastOk && _cards.length) {
    text = _cards[0].ct; _prepared = true;
    if (_cards.length > 1) {
      const _q = _cards.slice(1).map(c => {
        const _ti = ((c.ct.split('\\n').find(l => /^\\*[^*\\n]+\\*$/.test(l.trim())) || '').trim().replace(/^\\*|\\*$/g, ''));
        const _dt = ((c.ct.match(/^\\*Date:\\*\\s*([^\\n]+)$/m) || [])[1] || '').trim();
        return _ti && _dt ? "_Next: " + _ti + " on " + _dt + " - I'll show it after this one._" : '';
      }).filter(Boolean);
      if (_q.length) text = text.replace(/(_check [0-9a-f]{8}_)/, '$1\\n' + _q.join('\\n'));
    }
  }"""

GP_15_ANCHOR = "// --- a note that contradicts the ranking ---------------------------------"
GP_15_NEW = r"""// --- v187 (QA bug 15): a start time only, and the reply shows an end nobody gave -----------------------------------
// "is studio 7 free next thursday at 2pm?" -> "free ... from 2:00 PM to 4:00 PM" (exec 15881): Room Availability was
// asked about a 2-hour window and the model reported the window as if it had been asked for. An availability line that
// runs from the requester's start to a time they never typed says "at 2:00 PM (checked until 4:00 PM)" instead.
// Someone else's booking ("taken from 1:00 PM to 3:00 PM") is a real time and is never touched.
try {
  const _so = String($('Gate Context').first().json.startOnlyNotice || '').length > 0;
  if (_so && !_prepared && !/Confirm to (book|cancel|move)\./i.test(text) && !/\*Time:\*/.test(text)) {
    let _said = '';
    try { _said = String($('Slack Trigger').first().json.text || ''); } catch (e) {}
    try { _said += '\n' + String((($('Booked For').first() || {}).json || {}).requesterText || ''); } catch (e) {}
    const _typed = x => {
      const m = String(x).match(/(\d{1,2})(?::(\d{2}))?\s*([AP])M/i); if (!m) return true;
      const mm = m[2] && m[2] !== '00' ? ':' + m[2] : '(?::00)?';
      return new RegExp('(^|[^0-9:])' + (+m[1]) + mm + '\\s*' + m[3] + '\\.?\\s*m\\b', 'i').test(_said)
        || (m[3].toUpperCase() === 'P' && +m[1] === 12 && (!m[2] || m[2] === '00') && /\b(?:12\s*nn|noon)\b/i.test(_said));
    };
    let _chg = false;
    text = text.split('\n').map(l => {
      if (!/\b(free|available|open)\b/i.test(l) || /\b(taken|busy|booked by|occupied)\b/i.test(l)) return l;
      return l.replace(/\b(?:from\s+)?(\d{1,2}:\d{2}\s*[AP]M)\s*(?:to|until|till|-|–|—)\s*(\d{1,2}:\d{2}\s*[AP]M)/gi, (w, s, e) => {
        if (!_typed(s) || _typed(e)) return w;
        _chg = true; return 'at ' + s + ' (checked until ' + e + ')';
      });
    }).join('\n');
    if (_chg && !/\?/.test(text)) text = text.trim() + '\n\nHow long do you need it?';
  }
} catch (e) {}

"""

# --- Prepared Cancel: read the queue back off the card --------------------------------------------------------
PC_OLD = "  else d = { use: true, reason: '', title, booking_date: ymd, check_code: code };"
PC_NEW = """  else {
    // v187 (PENDING 55): the other bookings asked for in the same message, queued on the card by Guard Probe.
    const next = lines.map(l => l.match(/^_Next: (.+) on (?:[A-Za-z]+day, )?([A-Za-z]+)\\s+(\\d{1,2}),\\s*(\\d{4}) - I'll show it after this one\\._$/))
      .filter(Boolean).map(m => { const k = M.indexOf(m[2].toLowerCase());
        return { title: m[1].trim(), date_text: m[0].replace(/^_Next: .+ on /, '').replace(/ - I'll show.*$/, ''), booking_date: k >= 0 ? m[4] + '-' + String(k + 1).padStart(2, '0') + '-' + String(+m[3]).padStart(2, '0') : '' }; })
      .filter(x => x.title && x.booking_date);
    d = { use: true, reason: '', title, booking_date: ymd, check_code: code, next };
  }"""

# --- Cancel Direct Reply: the result, then the next card -------------------------------------------------------
CDR_OLD = "const r = (() => { try { const j = $input.first().json || {}; return Array.isArray(j) ? (j[0] || {}) : j; } catch (e) { return {}; } })();"
CDR_NEW = ("// v187: read Cancel Direct by name - the input is now Prepare Next Cancel's result when a next card was queued.\n"
           "const r = (() => { try { const j = $('Cancel Direct').first().json || {}; return Array.isArray(j) ? (j[0] || {}) : j; } catch (e) { return {}; } })();")
CDR_TAIL_OLD = "return [{ json: { output: text, directCancel: { status: st, reason: why } } }];"
CDR_TAIL_NEW = """// v187 (PENDING 55): more bookings were asked for in the same message - show the next card, with its own code and
// its own yes. Whatever is still queued after it rides along as "_Next: ..._" lines, so any number chain.
let nextShown = '';
try {
  const q = ((($('Prepared Cancel').first() || {}).json || {})._cancelDirect || {}).next || [];
  if (q.length) {
    let nx = {}; try { const j = $('Prepare Next Cancel').first().json || {}; nx = Array.isArray(j) ? (j[0] || {}) : j; } catch (e) {}
    const rest = q.slice(1).map(x => "_Next: " + x.title + " on " + x.date_text + " - I'll show it after this one._");
    if (String(nx.status || nx.verdict || '').toUpperCase() === 'PREPARED' && nx.card_text) {
      let card = String(nx.card_text);
      if (rest.length) card = card.replace(/(_check [0-9a-f]{8}_)/, '$1\\n' + rest.join('\\n'));
      card = card.replace(/\\n*Reply only with "yes" to cancel\\b[^\\n]*\\n\\s*Confirm to cancel\\.\\s*$/i, '\\n\\nCancel it? Reply yes or no.')
                 .replace(/\\n*Confirm to cancel\\.\\s*$/i, '\\n\\nCancel it? Reply yes or no.');
      text += '\\n\\nNext:\\n\\n' + card.trim();
      nextShown = q[0].title;
    } else {
      text += '\\n\\nI couldn\\'t get "' + q[0].title + '" (' + q[0].date_text + ') ready to cancel, so it is untouched.'
        + (q.length > 1 ? ' Still to do: ' + q.slice(1).map(x => '"' + x.title + '"').join(', ') + '.' : '')
        + ' Ask me again for ' + (q.length > 1 ? 'them' : 'it') + '.';
    }
  }
} catch (e) {}
return [{ json: { output: text, directCancel: { status: st, reason: why, nextShown } } }];"""

def main_fix(w):
    w["name"] = "Project Jessie — v187 (two cancels, start time)"
    g = node(w, "Guard Probe")["parameters"]
    c = sub1(g["jsCode"], GP_CARD_OLD, GP_CARD_NEW, "guard cards")
    c = sub1(c, GP_15_ANCHOR, GP_15_NEW + GP_15_ANCHOR, "guard bug 15")
    g["jsCode"] = c
    p = node(w, "Prepared Cancel")["parameters"]; p["jsCode"] = sub1(p["jsCode"], PC_OLD, PC_NEW, "prepared cancel")
    r = node(w, "Cancel Direct Reply")
    rc = sub1(r["parameters"]["jsCode"], CDR_OLD, CDR_NEW, "reply input")
    r["parameters"]["jsCode"] = sub1(rc, CDR_TAIL_OLD, CDR_TAIL_NEW, "reply tail")

    cd = node(w, "Cancel Direct"); cdq = node(w, "Cancel Direct?")
    x, y = cd["position"]
    r["position"] = [x + 528, y]
    nq = json.loads(json.dumps(cdq)); nq.update(id=str(uuid.uuid4()), name="Next Cancel?", position=[x + 176, y])
    nq["parameters"]["conditions"]["conditions"][0].update(id=str(uuid.uuid4()),
        leftValue="={{ ((($('Prepared Cancel').first().json._cancelDirect || {}).next) || []).length > 0 ? 'yes' : 'no' }}")
    pn = json.loads(json.dumps(cd)); pn.update(id=str(uuid.uuid4()), name="Prepare Next Cancel", position=[x + 352, y + 144])
    v = pn["parameters"]["workflowInputs"]["value"]
    v.update(title="={{ $('Prepared Cancel').first().json._cancelDirect.next[0].title }}",
             booking_date="={{ $('Prepared Cancel').first().json._cancelDirect.next[0].booking_date }}",
             check_code="", mode="prepare", confirmed="={{ false }}")
    w["nodes"] += [nq, pn]
    C = w["connections"]
    C["Cancel Direct"] = {"main": [[{"node": "Next Cancel?", "type": "main", "index": 0}]]}
    C["Next Cancel?"] = {"main": [[{"node": "Prepare Next Cancel", "type": "main", "index": 0}],
                                  [{"node": "Cancel Direct Reply", "type": "main", "index": 0}]]}
    C["Prepare Next Cancel"] = {"main": [[{"node": "Cancel Direct Reply", "type": "main", "index": 0}]]}
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
