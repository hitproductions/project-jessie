#!/usr/bin/env python3
"""main v300 + Slack Interactions v87 (Howard, 20 Nov: "yes do both, title and tom").

1. "tom" is tomorrow (main v300: Gate Context, Booked For, Form Offer read the message through one rule). Also tmrw, tmr, tmw,
   tmrow, tomorow, tommorow, tommorrow, 2moro, 2morrow, 2mrw. "Tom" with a capital, or "tom" after for / with / and / a comma /
   engineer / arranger / invite / guests / attendees, stays a name ("with ana and tom", "engineer tom").
2. A meeting's / an event's title typed in the first message fills the form's title box: "titled X" / "title: X" / "called X" /
   "named X" first, then "for X" (not a colleague, a room, a type or a date - "for test meeting"), then "about X" / "re X" /
   "regarding X" / "to discuss X". It ends at a date, time, room or "with" (the guests). main v300 Form Offer: P.ti, and
   "Title: …" in the offer; Slack Interactions v87 Build Step 2: the title box starts with it.
Built on project-jessie-v299 and slack-interactions-v86 (each == live)."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W = lambda f: json.load(open(os.path.join(ROOT, "workflows", f)))
def save(wf, f, name):
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", f), "w") as fh:
        json.dump(wf, fh, indent=2, ensure_ascii=False); fh.write("\n")
    print("wrote workflows/" + f, len(wf["nodes"]), "nodes")
def rep(wf, nd, old, new):
    n = [x for x in wf["nodes"] if x["name"] == nd][0]; c = n["parameters"]["jsCode"]
    assert c.count(old) == 1, (nd, old[:70], c.count(old)); n["parameters"]["jsCode"] = c.replace(old, new)

TMR = (r""".replace(/(^|[^\w@.\-\/])(?:tmrw|tmrow|tmr|tmw|tomorow|tommorow|tommorrow|tomorrw|2moro|2morrow|2mrw)(?![\w@])/gi, '$1tomorrow')"""
       r""".replace(/(^|[^\w@])(tom)(?![\w@'’])/gi, (m, a, w, off, str) => { if (w === 'Tom') return m;   /* v300: "tom" = tomorrow, not after for / with / and / a comma / engineer … */"""
       r""" const bef = str.slice(0, off + a.length).replace(/\s+$/, ''); if (/,$/.test(bef) || /(?:^|\s)(?:for|with|and|&|w\/|engineer|engr|eng|arranger|invite|inviting|guests?:?|attendees?:?|by|si|ni|kay)$/i.test(bef)) return m;"""
       r""" return a + 'tomorrow'; })""")

mn = W("project-jessie-v299.json")
rep(mn, "Gate Context", "const clean = s => String(s || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').trim();",
    "const clean = s => String(s || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').trim()" + TMR + ";   // v300: tom / tmrw = tomorrow")
rep(mn, "Booked For", "  const clean = s => String(s || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').trim()\n",
    "  const clean = s => String(s || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').trim()" + TMR + "   // v300: tom / tmrw = tomorrow\n")
rep(mn, "Form Offer", "  const clean = s => String(s || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').replace(/<[^>]+>/g, ' ').trim();",
    "  const clean = s => String(s || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').replace(/<[^>]+>/g, ' ').trim()" + TMR + ";   // v300: tom / tmrw = tomorrow")

TITLE = r"""
    // v300 (Howard, 20 Nov): a meeting's / an event's title typed - "titled X" / "title: X" / "called X" / "named X", else "for X" (not a
    // colleague, room, type or date: "for test meeting"), else "about X" / "re X" / "regarding X" / "to discuss X". Ends at a date, a
    // time, a room or "with" (the guests). Fills the form's title box (Slack Interactions v87).
    if ((P.p === 'Meeting' || P.p === 'Event') && !P.ti) { try {
      const _TS = /^(?:with|w\/|at|in|on|from|this|next|coming|tomorrow|today|tonight|every|weekly|daily|until|till|starting|room|likha|katha|salin|lobby|studio|attendees?|guests?|invite|inviting|including|monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun|jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december|am|pm|noon|nn|all|whole|full|please|pls|po)$/i;
      const _isTime = w => /^\d{1,2}(?::\d{2})?(?:\s*(?:am|pm|nn))?(?:\s*[-–]\s*\d{1,2}(?::\d{2})?(?:am|pm|nn)?)?$/i.test(w) || /^\d{1,2}(?:st|nd|rd|th)$/i.test(w) || /^\d{1,2}[\/\-]\d{1,2}(?:[\/\-]\d{2,4})?$/.test(w);
      const _take = s => { const out = [];
        for (const w0 of String(s).split(/\s+/)) { const w = w0.replace(/[,;!?]+$/, ''); if (!w) continue; if (_TS.test(w) || _isTime(w)) break; out.push(w); if (out.length >= 8 || w0 !== w) break; }
        while (out.length && /^(?:the|a|an|our|my|and|for)$/i.test(out[0])) out.shift();
        while (out.length && /^(?:the|a|an|our|my|and|for|meeting|event)$/i.test(out[out.length - 1]) && out.length > 1 && /^(?:the|a|an|our|my|and|for)$/i.test(out[out.length - 1])) out.pop();
        return out.join(' ').replace(/[.:]+$/, '').trim(); };
      const _staffK = new Set(); for (const f of staff) { const n0 = String(f.Name).trim().toLowerCase(); _staffK.add(n0); _staffK.add(n0.split(/\s+/)[0]);
        (((String(f.Info || '').match(/goes by\s+([^\n]*)/i) || [])[1]) || '').split(/,|\bor\b/).forEach(a => { a = a.trim().replace(/\.$/, '').toLowerCase(); if (a) _staffK.add(a); }); }
      const _okT = x => { const lx = String(x || '').toLowerCase(); return !!x && x.length >= 2 && !_staffK.has(lx) && !_staffK.has(lx.replace(/^(?:sir|ms|mr|mrs|ma'?am|miss)\s+/, ''))
        && !/^(?:me|myself|us|them|him|her|someone|a meeting|meeting|an event|event|the team|everyone|\d+\s*(?:hours?|hrs?|mins?|minutes?))$/i.test(lx) && !roomsIn(x).length; };
      let _ti = '';
      // "titled / called / named / title: X" - a quoted title whole, else every word up to with / at / on / from / a date or time word
      const _e = t.match(/\b(?:titled|entitled|called|named|title\s*(?:is\b|:|-))\s*(.+)/i);
      if (_e) { const q = _e[1].match(/^["“']([^"”'\n]+)["”']/);
        if (q) _ti = q[1].trim();
        else { const out = []; for (const w0 of _e[1].split(/\s+/)) { const w = w0.replace(/[,;!?]+$/, ''); if (!w) continue;
            if (/^(?:with|w\/|at|on|from|in|this|next|tomorrow|today|tonight|attendees?|guests?|invite)$/i.test(w) || _isTime(w)) break; out.push(w); if (out.length >= 10 || w0 !== w || /[.]$/.test(w)) break; }
          _ti = out.join(' ').replace(/[.:]+$/, '').trim(); } }
      if (!_okT(_ti)) { _ti = ''; const re = /\bfor\s+([^\n.;!?]+)/gi; let m; while ((m = re.exec(t))) { const x = _take(m[1]); if (_okT(x) && TYPES.every(ty => ty.toLowerCase() !== x.toLowerCase()) && !/^(?:a|an|the)?\s*(?:meeting|event|day|while)$/i.test(x)) { _ti = x; break; } } }
      if (!_ti) { const m = t.match(/\b(?:about|re:?|regarding|to discuss)\s+([^\n.;!?]+)/i); if (m) { const x = _take(m[1]); if (_okT(x)) _ti = x; } }
      if (_ti) P.ti = cut(_ti, 120);
    } catch (e) {} }
"""
ANCHOR = "    if (P.p === '__booth' && !P.s && !P.e && !P.ad) P.ad = 1;   // v298 (Howard, 20 Nov): an M booth with no times typed is All day\n"
rep(mn, "Form Offer", ANCHOR, ANCHOR + TITLE.lstrip("\n"))
rep(mn, "Form Offer", "      const more = [P.p === '__booth' ? 'M booth' : P.p, ",
    "      const more = [P.p === '__booth' ? 'M booth' : P.p, P.ti ? 'Title: ' + P.ti.charAt(0).toUpperCase() + P.ti.slice(1) : '',   /* v300 */ ")
save(mn, "project-jessie-v300.json", "Project Jessie — v300 (typed title, tom)")

si = W("slack-interactions-v86.json")
rep(si, "Build Step 2", "    blocks.push(input('title', s.purpose === 'Event' ? 'Event title' : 'Meeting title', txtIn('title_in', '')));",
    "    blocks.push(input('title', s.purpose === 'Event' ? 'Event title' : 'Meeting title', txtIn('title_in', String(pre.ti || '').trim().replace(/^./, c => c.toUpperCase()))));   // v87: the title typed (main v300)")
save(si, "slack-interactions-v87.json", "Jessie — Slack Interactions — v87 (typed meeting title)")
