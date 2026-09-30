#!/usr/bin/env python3
"""main v198 (series change fix) - PENDING 63, decided 30 Sep: ask which date.
  scripts/build-series-change.py <main-live> <main-out>

29 Sep 23:13 PHT: a 2-date series (QATYPE2, Tue 2 + 9 Nov) was booked, then "make it 3pm instead" -> a move card for
9 Nov only, nothing asked. Booked For reads the booking just made from the summary before "Booked." - a series summary
has "*Dates (2):*", not "*Date:*", so nothing was found and the model picked a date itself.

Now, right after "Booked N sessions", a change:
- names no date -> Jessie asks, in code: "That was a series of 2. Which date should change? - Tuesday, November 2 ...
  Or say "all" to change every date." The model's reply (even a move card it prepared) is replaced.
- names a date ("the 9th", "nov 9", "9 November", the weekday when it is unique, "first" / "second" / "last") -> that
  date is the booking just made, and the normal move card follows.
- says all / both / every date -> one date at a time: the first date's card carries "_Next: ... - I'll show it after
  this one._" lines; once a move goes through, the next date's card is added to the "Moved ..." reply (same new time
  and room, same card format), and it needs its own yes. A date change (not a time change) is not chained.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

BF_ANCHOR = "      if (sum && CHANGE.test(said2) && !NEWREQ.test(said2)) {"
BF_BLOCK = r"""      // v198 (PENDING 63): right after a SERIES ("Booked 2 sessions: ..."), a change names one date, several, or all -
      // or none, and then it is asked. Before, the model picked a date itself (29 Sep: the last one).
      let __serPick = false;
      {
        const _MN = ['january','february','march','april','may','june','july','august','september','october','november','december'];
        const _DN = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday'];
        const _long = d => { const x = new Date(d + 'T12:00:00Z'); return _DN[x.getUTCDay()].replace(/^./, c => c.toUpperCase()) + ', '
          + _MN[x.getUTCMonth()].replace(/^./, c => c.toUpperCase()) + ' ' + x.getUTCDate() + ', ' + x.getUTCFullYear(); };
        const _isoOf = s => { const m = String(s || '').toLowerCase().match(/([a-z]+)\s+(\d{1,2}),?\s+(\d{4})/); const k = m ? _MN.indexOf(m[1]) : -1;
          return k === -1 ? '' : m[3] + '-' + String(k + 1).padStart(2, '0') + '-' + String(+m[2]).padStart(2, '0'); };
        const _bt = __bookedAt > 0 ? textOf(msgs[__bookedAt - 1]) : '';
        let _ser = null;
        if (!__movedText && /^\s*\*?booked\s+\d+\s+sessions?\b/i.test(_bt)) {
          const _ds = [...new Set([..._bt.matchAll(/\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),\s*(\d{4})/gi)]
            .map(m => m[3] + '-' + String(_MN.indexOf(m[1].toLowerCase()) + 1).padStart(2, '0') + '-' + String(+m[2]).padStart(2, '0')))].sort();
          let _sm = '';
          for (let k = __bookedAt; k < msgs.length && k < __bookedAt + 6; k++) { const mm = msgs[k]; if (!isBot(mm)) continue; const tx = textOf(mm); if (/\*Dates?\s*\(\d+\):\*/i.test(tx)) { _sm = tx; break; } }
          const _g = re => ((_sm.match(re) || [])[1] || '').trim();
          if (_ds.length >= 2 && _sm) _ser = { dates: _ds, title: _g(/^\s*\*([^*\n]+)\*\s*$/m), time: _g(/\*Time:\*\s*([^\n]+)/), room: _g(/\*Rooms?:\*\s*([^\n]+)/) };
        }
        // "the second one" names a date of the series, not a second booking
        if (_ser && _ser.title && CHANGE.test(said2) && !/\b(another|also|too|as well|new booking|one more)\b/i.test(said2)) {
          // which date(s) they named, anywhere in what they typed since the booking
          const _t = said2;
          let _picks = [];
          if (/\b(?:all|both|every|each)\b(?!\s+day)|\ball of them\b|\bthe whole series\b/i.test(_t)) _picks = _ser.dates.slice();
          else {
            for (const d of _ser.dates) {
              const [, mo, da] = d.split('-').map(Number), mn = _MN[mo - 1], ab = mn.slice(0, 3), dd = da + '(?:st|nd|rd|th)?';
              if (new RegExp('\\b(?:' + mn + '|' + ab + ')\\.?\\s+0?' + dd + '\\b|\\b0?' + dd + '\\s+(?:of\\s+)?(?:' + mn + '|' + ab + ')\\b|\\bthe\\s+' + dd + '\\b|\\b' + da + '(?:st|nd|rd|th)\\b', 'i').test(_t)) _picks.push(d);
            }
            if (!_picks.length) {
              const _wd = _ser.dates.map(d => _DN[new Date(d + 'T12:00:00Z').getUTCDay()]);
              _ser.dates.forEach((d, i) => { if (_wd.filter(w => w === _wd[i]).length === 1 && new RegExp('\\b' + _wd[i] + '\\b', 'i').test(_t)) _picks.push(d); });
            }
            if (!_picks.length) {
              const _o = [[/\bfirst\b/i, 0], [/\bsecond\b/i, 1], [/\bthird\b/i, 2], [/\blast\b/i, _ser.dates.length - 1]].find(([re]) => re.test(_t));
              if (_o && _ser.dates[_o[1]]) _picks.push(_ser.dates[_o[1]]);
            }
          }
          _picks = [...new Set(_picks)].sort();
          // the move card already shown this booking, if any - its date is the one being moved now
          const _card = /\*Now:\*/.test(String(theirs[0] || '')) && /\*Moving to:\*/.test(String(theirs[0] || '')) ? String(theirs[0]) : '';
          const _cur = _card ? _isoOf((_card.match(/\*Now:\*\s*([^\n]+)/) || [])[1]) : '';
          if (!_picks.length) {
            out.seriesAsk = 'That was a series of ' + _ser.dates.length + '. Which date should change?\n'
              + _ser.dates.map(d => '- ' + _long(d).replace(/, \d{4}$/, '')).join('\n') + '\nOr say "all" to change every date.';
            notes.push('THEY WANT TO CHANGE THE SERIES THEY JUST BOOKED ("' + _ser.title + '", ' + _ser.dates.length + ' dates) BUT DID NOT SAY WHICH DATE. Ask which date - do not call Move Booking yet.');
            sum = '';
          } else {
            const _now = (_cur && _picks.indexOf(_cur) !== -1) ? _cur : _picks[0];
            __serPick = true;
            sum = '*' + _ser.title + '*\n*Date:* ' + _long(_now) + '\n*Time:* ' + _ser.time + (_ser.room ? '\n*Room:* ' + _ser.room : '');
            const _rest = _picks.filter(d => d > _now);
            if (_rest.length) {
              out.seriesQueueNext = _rest.map(d => '_Next: ' + _ser.title + ' on ' + _long(d) + " - I'll show it after this one._");
              // the yes to this date's card: the next date's card goes out with "Moved ..." (same new time and room)
              const _mt = _card ? ((_card.match(/\*Moving to:\*\s*([^\n]+)/) || [])[1] || '') : '';
              const _mv = _mt.match(/^(.*?\d{4}),\s*(\d{1,2}:\d{2}\s*[AP]M\s*[–-]\s*\d{1,2}:\d{2}\s*[AP]M)(?:,\s*(.+))?$/i);
              const _nw = ((_card.match(/\*Now:\*\s*([^\n]+)/) || [])[1] || '').match(/^(.*?\d{4}),\s*(\d{1,2}:\d{2}\s*[AP]M\s*[–-]\s*\d{1,2}:\d{2}\s*[AP]M)(?:,\s*(.+))?$/i);
              if (_mv && _nw && _isoOf(_mv[1]) === _cur && _cur === _now && YES_RE.test(String(mine[0] || ''))) {
                const _nx = _rest[0];
                out.seriesNextCard = '*' + _ser.title + '*\n*Now:* ' + _long(_nx) + ', ' + _nw[2] + (_nw[3] ? ', ' + _nw[3] : '')
                  + '\n*Moving to:* ' + _long(_nx) + ', ' + _mv[2] + (_mv[3] ? ', ' + _mv[3] : '')
                  + (_rest.length > 1 ? '\n' + _rest.slice(1).map(d => '_Next: ' + _ser.title + ' on ' + _long(d) + " - I'll show it after this one._").join('\n') : '')
                  + '\n\nMove it? Reply yes or no.';
              }
            }
          }
        }
        // a yes to a next-date card that went out with "Moved ...": say which one, and queue the one after it
        if (__movedText && /\*Now:\*/.test(__movedText) && /\*Moving to:\*/.test(__movedText) && YES_RE.test(String(mine[0] || ''))) {
          const _cd = __movedText.slice(Math.max(0, __movedText.lastIndexOf('\n\n', __movedText.indexOf('*Now:*')) + 2));
          const _ti2 = ((_cd.match(/^\s*\*([^*\n]+)\*\s*$/m) || [])[1] || '').trim();
          const _nw2 = ((_cd.match(/\*Now:\*\s*([^\n]+)/) || [])[1] || '').match(/^(.*?\d{4}),\s*(\d{1,2}:\d{2}\s*[AP]M\s*[–-]\s*\d{1,2}:\d{2}\s*[AP]M)(?:,\s*(.+))?$/i);
          const _mv2 = ((_cd.match(/\*Moving to:\*\s*([^\n]+)/) || [])[1] || '').match(/^(.*?\d{4}),\s*(\d{1,2}:\d{2}\s*[AP]M\s*[–-]\s*\d{1,2}:\d{2}\s*[AP]M)(?:,\s*(.+))?$/i);
          if (_ti2 && _nw2 && _mv2) {
            notes.push('THE MOVE THEY JUST APPROVED IS THE CARD AT THE END OF YOUR LAST MESSAGE: "' + _ti2 + '" on ' + _nw2[1] + ', from ' + _nw2[2]
              + ' to ' + _mv2[2] + '. Call Move Booking for that booking only - not the one already moved.');
            const _q = [..._cd.matchAll(/^_Next: (.+) on ([A-Za-z]+day, [A-Za-z]+ \d{1,2}, \d{4}) - I'll show it after this one\._$/gm)];
            if (_q.length) {
              out.seriesNextCard = '*' + _ti2 + '*\n*Now:* ' + _q[0][2] + ', ' + _nw2[2] + (_nw2[3] ? ', ' + _nw2[3] : '')
                + '\n*Moving to:* ' + _q[0][2] + ', ' + _mv2[2] + (_mv2[3] ? ', ' + _mv2[3] : '')
                + (_q.length > 1 ? '\n' + _q.slice(1).map(q => q[0]).join('\n') : '') + '\n\nMove it? Reply yes or no.';
            }
          }
        }
      }
"""
YES_DEF_ANCHOR = "      const said2 = mine.join('\\n');"
YES_DEF = YES_DEF_ANCHOR + "\n      const YES_RE = /^\\s*(y|yes|yeah|yep|yup|ok|okay|sure|sige|oo|opo|confirm|go|go ahead|do it|proceed)\\s*[.!]*\\s*$/i;   // v198"

GP_ANCHOR = "// v194: a compact list of this turn's tool calls"
GP_BLOCK = r"""// --- v198 (PENDING 63): a change right after a series ------------------------------------------------------------
// Booked For decides it from what the requester typed: no date named -> the question, in place of whatever the model
// wrote (even a move card for one date); several dates -> the first card carries "_Next:" lines; a move that went
// through this turn -> the next date's card goes out with the "Moved ..." reply, for its own yes.
try {
  const _bf8 = (($('Booked For').first() || {}).json) || {};
  const _s8 = (($input.first().json || {}).intermediateSteps) || [];
  const _moved8 = _s8.some(s => { const t = String(((s || {}).action || {}).tool || '').replace(/[_\s]+/g, ' ').toLowerCase();
    if (t !== 'move booking') return false; let o = null; try { o = [].concat(JSON.parse(String((s || {}).observation || '')))[0]; } catch (e) {}
    return !!o && o.status === 'MOVED'; });
  if (_bf8.seriesAsk) text = String(_bf8.seriesAsk);
  else {
    if (Array.isArray(_bf8.seriesQueueNext) && _bf8.seriesQueueNext.length && !_moved8 && /\*Moving to:\*/.test(text) && /Move it\? Reply yes or no\.\s*$/i.test(text) && !/_Next: /.test(text))
      text = text.replace(/\s*Move it\? Reply yes or no\.\s*$/i, '\n' + _bf8.seriesQueueNext.join('\n') + '\n\nMove it? Reply yes or no.');
    if (_bf8.seriesNextCard && _moved8 && !/Move it\? Reply yes or no\.\s*$/i.test(text))
      text = text.trim() + '\n\n' + String(_bf8.seriesNextCard);
  }
} catch (e) {}

"""

BF_COND_NEW = "      if (sum && CHANGE.test(said2) && (!NEWREQ.test(said2) || __serPick)) {   // v198: a series date picked"

def fix(w):
    w["name"] = "Project Jessie — v198 (series change fix)"
    b = node(w, "Booked For")["parameters"]
    s = sub1(b["jsCode"], YES_DEF_ANCHOR, YES_DEF, "yes def")
    b["jsCode"] = sub1(s, BF_ANCHOR, BF_BLOCK + BF_COND_NEW, "bf anchor")
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_ANCHOR, GP_BLOCK + GP_ANCHOR, "gp anchor")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
