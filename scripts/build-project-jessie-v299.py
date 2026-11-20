#!/usr/bin/env python3
"""main v299 (Howard, 20 Nov): guests typed in the first message of a meeting / event fill the form's Guests.
  "book a meeting with camy this sunday", "with camy, lea and nicole", "attendees are camy, lea", "guests: …", "invite camy and lea",
  "w/ camy" - and any email typed. People in Bookers (full name, first name when it is one person, "Goes by" alias, first name +
  surname initial, initials in capitals; "sir / ms / …" dropped) -> Guests (gu, Slack ids); emails -> Other guests (ge). A name not
  on the staff list, or one shared by several people, is named under the offer so it can be added in the form. Only for a Meeting
  or an Event (the form has Guests only there). The offer shows "Guests: …".
Form Offer only. Built on project-jessie-v298 (== live)."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
w = json.load(open(os.path.join(ROOT, "workflows", "project-jessie-v298.json")))
def rep(nd, old, new):
    n = [x for x in w["nodes"] if x["name"] == nd][0]; c = n["parameters"]["jsCode"]
    assert c.count(old) == 1, (nd, old[:70], c.count(old)); n["parameters"]["jsCode"] = c.replace(old, new)

GUESTS = r"""
    // v299 (Howard, 20 Nov): a meeting's / an event's guests typed in this message - "with camy, lea and nicole", "attendees are camy,
    // lea", "guests: …", "invite …", "w/ …", and any email. Bookers -> Guests (gu), emails -> Other guests (ge); a name not found (or
    // shared by several people) is named under the offer, to add in the form.
    if (P.p === 'Meeting' || P.p === 'Event') { try {
      const _gp = staff.map(f => ({ name: String(f.Name).trim(), id: String(f['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean)[0] || '', ini: String(f.Initials || '').trim(),
        alias: (((String(f.Info || '').match(/goes by\s+([^\n]*)/i) || [])[1]) || '').split(/,|\bor\b/).map(a => a.trim().replace(/[.]+$/, '').toLowerCase()).filter(Boolean) })).filter(p => p.name && p.id);
      const _HON = /^(?:sir|ma'?am|maam|ms\.?|mr\.?|mrs\.?|miss|dr\.?|direk|boss|kuya|ate|mam)\s+/i;
      const _who = raw => { const orig = String(raw).trim(), w = orig.replace(_HON, '').trim().toLowerCase(); if (!w) return null;
        const ws = w.split(/\s+/), hit = f => { const u = []; for (const p of _gp) if (f(p) && u.indexOf(p) === -1) u.push(p); return u; };
        for (const f of [p => p.name.toLowerCase() === w, p => p.alias.indexOf(w) !== -1,
                         p => ws.length === 1 && p.name.toLowerCase().split(/\s+/)[0] === w,
                         p => ws.length === 2 && p.name.toLowerCase().split(/\s+/)[0] === ws[0] && p.name.toLowerCase().split(/\s+/).slice(-1)[0].indexOf(ws[1].replace(/\.$/, '')) === 0,
                         p => /^[A-Z]{2,3}$/.test(orig) && p.ini === orig]) { const u = hit(f); if (u.length) return u; }
        return []; };
      const _STOPG = /^(?:for|at|in|on|from|this|next|coming|tomorrow|tmrw|today|tonight|every|weekly|daily|until|till|starting|about|regarding|re|to|titled|title|called|named|room|rooms|studio|meeting|meetings|event|sync|huddle|call|discuss|ng|sa|po|pls|please|etc|monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|february|march|april|june|july|august|september|october|november|december|am|pm|noon|nn|morning|afternoon|evening|lunch|likha|katha|salin|lobby|all|whole|full|day)$/i;
      const _THING = /^(?:projector|tv|screen|monitor|mic|mics|microphone|speaker|speakers|zoom|gmeet|meet|teams|lunch|snacks?|food|coffee|merienda|whiteboard|laptop|hdmi|aircon|chairs?|tables?|catering|video|online|hybrid|setup|set-up)$/i;   // things, not people
      const _SKIP = /^(?:me|myself|us|we|everyone|everybody|all|others|other|the|team|client|clients|guests?|people|etc\.?)$/i;
      const _em = (t.match(/[^\s@,;<>()"':]+@[^\s@,;<>()"']+\.[A-Za-z]{2,}/g) || []).map(x => x.toLowerCase()).filter((x, i, a) => a.indexOf(x) === i && !/@resource\.calendar\.google\.com$/.test(x));
      const _ids = [], _names = [], _miss = [], _two = [];
      const _trig = /(?:^|[^a-z])(?:with|w\/|together with|along with|attendees?|guests?|invitees?|participants?|invite|inviting|include|including)(?![a-z])\s*(?:(?:are|is|will be|would be)\b)?\s*[:\-–]?\s*/gi;
      let _m;
      while ((_m = _trig.exec(t))) {
        const rest = t.slice(_m.index + _m[0].length).split(/[\n.;!?](?:\s|$)|\n/)[0];
        const pieces = rest.split(/\s*(?:,|&|\+|\/|\band\b|\bat saka\b|\bsaka\b)\s*/i);
        let stop = false;
        for (const pc0 of pieces) {
          if (stop) break;
          const words = []; for (const wd0 of String(pc0).trim().split(/\s+/)) { const wd = wd0.replace(/[)(\]\[!?]+$/, ''); if (!wd) continue;
            if (/@/.test(wd)) break; if (_STOPG.test(wd) || /\d/.test(wd)) { stop = true; break; } if (words.length >= 3) break; words.push(wd); }
          while (words.length && /^(?:the|a|an|my|our|and)$/i.test(words[0])) words.shift();
          if (!words.length || words.some(x => _SKIP.test(x)) || /\b(?:team|dept|department)\b/i.test(words.join(' '))) continue;
          if (words.some(x => _THING.test(x))) { stop = true; continue; }
          // the longest start of it that is one person ("ana tom" -> Ana, and the list ends there)
          let hitP = null, hitK = 0, amb = '';
          for (let k = words.length; k >= 1 && !hitP; k--) { const u = _who(words.slice(0, k).join(' ')) || []; if (u.length === 1) { hitP = u[0]; hitK = k; } else if (u.length > 1 && !amb) amb = words.slice(0, k).join(' '); }
          const nm = words.join(' ');
          if (hitP) { if (_ids.indexOf(hitP.id) === -1) { _ids.push(hitP.id); _names.push(hitP.name); } if (hitK < words.length) stop = true; }
          else if (amb) { if (_two.indexOf(amb) === -1) _two.push(amb); }
          else if (/^[\p{L}][\p{L}'’.\-]*(?:\s+[\p{L}][\p{L}'’.\-]*){0,2}$/u.test(nm) && _miss.indexOf(nm) === -1) _miss.push(nm);
        }
      }
      if (_ids.length) { P.gu = _ids.join(','); P.guN = cut(_names.join(', '), 300); }
      if (_em.length) P.ge = cut(_em.join(', '), 500);
      const _cap = s => s.replace(/(^|[\s\-'’])(\p{Ll})/gu, (m, p, c) => p + c.toUpperCase());
      const _gn = [].concat(_miss.length ? ['Not on the staff list: ' + _miss.map(_cap).join(', ') + ' – type their email in the form to invite them.'] : [],
        _two.length ? ['More than one person called ' + _two.map(x => '"' + _cap(x) + '"').join(', ') + ' – pick them under Guests in the form.'] : []);
      if (_gn.length) fo.gNote = _gn.join('\n');
    } catch (e) {} }
"""
ANCHOR = "    if (P.p === '__booth' && !P.s && !P.e && !P.ad) P.ad = 1;   // v298 (Howard, 20 Nov): an M booth with no times typed is All day\n"
rep("Form Offer", ANCHOR, ANCHOR + GUESTS.lstrip("\n"))
rep("Form Offer", "(/^(?:post processing|multimedia post)$/i.test(String(P.p || '')) || P.p === '__booth') && P.fn ? 'For: ' + P.fn : (P.fidN ? 'For: ' + P.fidN : '')].filter(Boolean).join(' · ');",
    "(/^(?:post processing|multimedia post)$/i.test(String(P.p || '')) || P.p === '__booth') && P.fn ? 'For: ' + P.fn : (P.fidN ? 'For: ' + P.fidN : ''),\n"
    "        (P.guN || P.ge) ? 'Guests: ' + [P.guN, P.ge].filter(Boolean).join(', ') : ''].filter(Boolean).join(' · ');   // v299: the guests")
rep("Form Offer", "fo.text = lines.concat(fo.mNote ? ['⚠️ ' + fo.mNote] : []).join('\\n');",
    "fo.text = lines.concat(fo.mNote ? ['⚠️ ' + fo.mNote] : []).concat(fo.gNote ? fo.gNote.split('\\n').map(x => '⚠️ ' + x) : []).join('\\n');   // v299: guests not found")
w["name"] = "Project Jessie — v299 (typed guests)"
with open(os.path.join(ROOT, "workflows", "project-jessie-v299.json"), "w") as fh:
    json.dump(w, fh, indent=2, ensure_ascii=False); fh.write("\n")
print("wrote workflows/project-jessie-v299.json", len(w["nodes"]), "nodes")
