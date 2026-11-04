#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v66.json - Jessie — Slack Interactions — v66 (series review), 4 Nov.

PENDING 150 (series by design; Howard's "C", decided 4 Nov). With Room Availability v26 and Book Series v9:
- Find rooms for a series is ONE Room Availability call (all the dates, one read); Spread Dates turns its answer back into one
  item per date, so Build Step 2 reads them as before;
- Repeats: up to six months from the first date (was 16 dates; How many times up to 60, or an end date);
- the series is kept in the form's metadata as the first date + day offsets (six months of dates did not fit in Slack's 3,000);
- after Book Series' prepare, a REVIEW screen: every date - free ones listed, a date moved to another room shown
  ("Studio 2 instead of Studio 1"), a date with no room free then asks (the nearest free time that day earlier / later, or skip -
  a required pick), a date with nothing free that day left out; "Are you sure? You're about to book N appointments." from 20;
  one "Book all";
- the picks are applied after the saved series checks out (only an option the review offered is booked);
- skipped and left-out dates come back in the DM, each with "Find another time" (Book a room, filled in, that date);
- wait estimates for the one-call checks (rooms-span / check-span), not per date.
Built on workflows/imported/slack-interactions-v65-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v65-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b, n=1):
    assert js.count(a) == n, (js.count(a), a[:160])
    return js.replace(a, b)


def code(name, f):
    p = by[name]["parameters"]
    p["jsCode"] = f(p["jsCode"])


PACK = r"""// v66: a series is kept in the form's metadata as its first date + day offsets (base 36) - six months of dates did not fit
function __packS(s) { if (!s || !s.series || !Array.isArray(s.series.dates) || s.series.dates.length < 2) return s;
  const d0 = Date.parse(s.series.dates[0] + 'T12:00:00Z'), off = s.series.dates.map(d => Math.round((Date.parse(d + 'T12:00:00Z') - d0) / 86400000).toString(36));
  const ser = Object.assign({}, s.series, { dz: s.series.dates[0] + '|' + off.join('.') }); delete ser.dates; return Object.assign({}, s, { series: ser }); }
function __unpackS(s) { if (!s || !s.series || !s.series.dz || Array.isArray(s.series.dates)) return s;
  const [d0, o] = String(s.series.dz).split('|'), t = Date.parse(d0 + 'T12:00:00Z');
  const dates = String(o || '').split('.').filter(x => x !== '').map(x => new Date(t + parseInt(x, 36) * 86400000).toISOString().slice(0, 10));
  const ser = Object.assign({}, s.series, { dates }); delete ser.dz; return Object.assign({}, s, { series: ser }); }
"""

# ---- Repeats: six months, not 16 dates (Build Step 1, Read Step 1, Note Toggle share these helpers)
OLD_TM = "function repTooMany(n) { return 'That’s ' + n + ' dates – the most is 16. Pick an earlier end date or a number.'; }"
NEW_TM = ("function repTooMany(n) { return 'That runs past 6 months – the most is 6 months from the first date. Pick an earlier end date or fewer times.'; }   // v66\n"
          "function repTooLong(ds) { if (!ds || !ds.length) return false; const l = new Date(ds[0] + 'T12:00:00Z'); l.setUTCMonth(l.getUTCMonth() + 6);\n"
          "  return ds[ds.length - 1] > l.toISOString().slice(0, 10) || ds.length > 200; }   // v66 (PENDING 150): six months, not 16 dates")
for name in ("Build Step 1", "Read Step 1", "Note Toggle"):
    def f(js):
        js = sub(js, OLD_TM, NEW_TM)
        js = sub(js, "Up to 16 dates.", "Up to 6 months.", n=2)
        js = sub(js, "  if (ds.length > 16) return '⚠️ ' + repTooMany(ds.length);", "  if (repTooLong(ds)) return '⚠️ ' + repTooMany(ds.length);")
        return js
    code(name, f)
for name in ("Build Step 1", "Note Toggle"):
    code(name, lambda js: sub(js, "const counts = []; for (let i = 2; i <= 16; i++)", "const counts = []; for (let i = 2; i <= 60; i++)"))
code("Read Step 1", lambda js: sub(js, "    if (dates.length > 16) errors[until ? ruK : rcK] = repTooMany(dates.length);",
    "    if (repTooLong(dates)) errors[until ? ruK : rcK] = repTooMany(dates.length);   // v66"))

# ---- the series in metadata: packed where written, unpacked where read
def rs1(js):
    js = PACK + js
    js = sub(js, "private_metadata: JSON.stringify(s),", "private_metadata: JSON.stringify(__packS(s)),", n=2)
    js = sub(js, "series ? waitLine(_tr, 'rooms-series', series.dates.length, 5) : waitLine(_tr, 'rooms', 1, 10);",
             "series ? waitLine(_tr, 'rooms-span', 1, 15) : waitLine(_tr, 'rooms', 1, 10);   // v66: one call for every date")
    return js
code("Read Step 1", rs1)
code("Build Step 2", lambda js: PACK + sub(js, "private_metadata: JSON.stringify(Object.assign({}, s, { when, label }",
    "private_metadata: JSON.stringify(Object.assign({}, __packS(s), { when, label }"))
def rs2(js):
    js = PACK + js
    js = sub(js, "let s = {}; try { s = JSON.parse((p.view && p.view.private_metadata) || '{}'); } catch (e) {}",
             "let s = {}; try { s = JSON.parse((p.view && p.view.private_metadata) || '{}'); } catch (e) {}\ns = __unpackS(s);   // v66")
    js = sub(js, "  private_metadata: JSON.stringify(s),\n  blocks: (s.series", "  private_metadata: JSON.stringify(__packS(s)),\n  blocks: (s.series")
    js = sub(js, "_wait = _nd > 1 ? waitLine(_tr, 'check', _nd, 5) : waitLine(_tr, 'book', 1, 30);",
             "_wait = _nd > 1 ? waitLine(_tr, 'check-span', 1, 15) : waitLine(_tr, 'book', 1, 30);   // v66: one check for every date")
    return js
code("Read Step 2", rs2)

# ---- "Booked – ask to use" stays off for a series: the check reads the series from the metadata too (packed since v66)
for name in ("Build Step 2", "Note Toggle"):
    code(name, lambda js: sub(js, "|| (s.series && (s.series.dates || []).length > 1)) return [];",
        "|| (s.series && ((s.series.dates || []).length > 1 || s.series.dz))) return [];   // v66: packed series too"))

# ---- timings: the one-call checks are their own scenarios (one sample per run, not per date)
t1 = by["Timings 1"]["parameters"]["filters"]["conditions"][0]
assert "'rooms-series'" in t1["keyValue"]; t1["keyValue"] = t1["keyValue"].replace("'rooms-series'", "'rooms-span'")
t2 = by["Timings 2"]["parameters"]["filters"]["conditions"][0]
old_t2 = "return ((s.series || {}).dates || []).length > 1 ? 'check' : 'book';"
assert old_t2 in t2["keyValue"]
t2["keyValue"] = t2["keyValue"].replace(old_t2, "return (s.series && (((s.series || {}).dates || []).length > 1 || s.series.dz)) ? 'check-span' : 'book';")
code("Timing Sample", lambda js: sub(sub(js,
    "n = dl(s); scenario = n > 1 ? 'rooms-series' : 'rooms'; }", "n = dl(s); scenario = n > 1 ? 'rooms-span' : 'rooms'; if (n > 1) n = 1; }   // v66"),
    "n = dl(s); scenario = n > 1 ? 'check' : 'book'; }", "n = dl(s); scenario = n > 1 ? 'check-span' : 'book'; if (n > 1) n = 1; }   // v66"))
code("Next Estimate", lambda js: sub(js, "const FB = { rooms: 10, 'rooms-series': 5, book: 30, check: 5, series: 30, change: 30 };",
    "const FB = { rooms: 10, 'rooms-series': 5, book: 30, check: 5, series: 30, change: 30, 'rooms-span': 15, 'check-span': 15 };   // v66"))

# ---- Find rooms: one Room Availability call for every date of a series; Spread Dates hands Build Step 2 one item per date
code("To Room Availability", lambda js: sub(js,
    "const out = days.map(d => ({ json: {",
    "// v66 (PENDING 150): a series -> ONE call (Room Availability v26 reads the calendar once for every date)\n"
    "if (days.length > 1) return [{ json: { dates: days.join(','), t0: s.t0, t1: s.t1, start_iso: days[0] + 'T' + s.t0 + ':00+08:00', end_iso: days[days.length - 1] + 'T' + s.t1 + ':00+08:00',\n"
    "  session_type: s.kind === 'booth' ? '' : s.purpose, room: '', scope: '', hours: '', reference_data: ref } }];\n"
    "const out = days.map(d => ({ json: {"))
SPREAD = r"""// Spread Dates (v66, PENDING 150): Room Availability v26 answers a series in one item (per_date) - one item per date again, the
// shape Build Step 2 has always read. One window, a refusal or a failed call pass through unchanged.
const out = [];
for (const it of $input.all()) {
  const j = (it && it.json) || {};
  if (j.span && Array.isArray(j.per_date) && j.per_date.length) for (const x of j.per_date) out.push({ json: x });
  else if (j.span) out.push({ json: { status: j.status || 'CALENDAR_ERROR' } });
  else out.push({ json: j });
}
return out;
"""
ra_pos = by["Room Availability"]["position"]; bs2_pos = by["Build Step 2"]["position"]
by["Build Step 2"]["position"] = [bs2_pos[0] + 120, bs2_pos[1]]
spread = {"parameters": {"jsCode": SPREAD}, "type": "n8n-nodes-base.code", "typeVersion": by["To Room Availability"].get("typeVersion", 2),
          "position": [ra_pos[0] + 200, ra_pos[1] + 120], "id": str(uuid.uuid4()), "name": "Spread Dates"}
wf["nodes"].append(spread)
C = wf["connections"]
ra_out = C["Room Availability"]["main"][0]
assert [c["node"] for c in ra_out] == ["Build Step 2", "Ops Alert"], ra_out
ra_out[0]["node"] = "Spread Dates"
C["Spread Dates"] = {"main": [[{"node": "Build Step 2", "type": "main", "index": 0}]]}

# ---- the review screen (After Prepare Series)
REVIEW = r"""const dates = [].concat(r.dates || []);
const card = String(r.card_text || '').replace(/\n*Confirm to book\.\s*(?:\(yes\/no\))?\s*$/i, '').trim();
const meta = { key: r.prep_stored === false ? '' : (r.prep_key || ''), n: dates.length, title: r.title || '', requester: R.s.requester, channel: R.channel, msg: R.s.msg || null,   // v19: msg
  time: R.s.allDay ? '' : R.s.t0 + '-' + R.s.t1, ad: R.s.allDay ? 1 : 0, rooms: R.rooms || '' };   // v56: ad - all day, no time   // v25: rooms, for the message's details line
let payload = null; try { payload = JSON.parse(r.prep_payload || 'null'); } catch (e) { payload = null; }
if (!meta.key && payload && JSON.stringify(payload.inputs || {}).length < 2400) meta.inputs = payload.inputs;
// v66: the form's answers ride along, for a skipped date's "Find another time" (Book a room filled in, that date)
if (R.again) { meta.ag = Object.assign({}, R.again); if (JSON.stringify(meta).length > 2900) delete meta.ag.nt; if (JSON.stringify(meta).length > 2900) delete meta.ag; }
const RV = r.review && Array.isArray(r.review.items) ? r.review : null;
const pt = x => ({ type: 'plain_text', text: String(x).slice(0, 150) }), md = x => ({ type: 'mrkdwn', text: String(x).slice(0, 2900) });
let blocks, nBook = dates.length;
if (!RV) blocks = [{ type: 'section', text: md(card) }];   // an older Book Series - the card, as before
else {
  // v66 (PENDING 150, Howard's "C"): every date and what happens to it; a taken date with no other room asks
  const DS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'], MS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const sh = d => { const x = new Date(d + 'T12:00:00Z'); return DS[x.getUTCDay()] + ' ' + x.getUTCDate() + ' ' + MS[x.getUTCMonth()]; };
  const byMonth = ds => { const g = []; for (const d of ds) { const x = new Date(d + 'T12:00:00Z'), k = MS[x.getUTCMonth()] + (x.getUTCFullYear() !== new Date().getUTCFullYear() ? ' ' + x.getUTCFullYear() : '');
      const l = g[g.length - 1]; const t = DS[x.getUTCDay()] + ' ' + x.getUTCDate(); if (l && l.k === k) l.v.push(t); else g.push({ k, v: [t] }); }
    return g.map(x => '*' + x.k + ':* ' + x.v.join(', ')).join('\n'); };
  const it = RV.items, okI = it.filter(x => x.kind === 'ok'), mvI = it.filter(x => x.kind === 'moved'), chI = it.filter(x => x.kind === 'choose'), noI = it.filter(x => x.kind === 'none');
  nBook = okI.length + mvI.length + chI.length;
  const room = String(RV.room || '').split(',').map(x => x.trim()).filter(Boolean).join(' + ');
  blocks = [{ type: 'section', text: md('*' + RV.title + '*\n' + [RV.time, room].filter(Boolean).join(' · ')) }];
  if (nBook >= 20) blocks.push({ type: 'section', block_id: 'many', text: md('⚠️ *Are you sure? You’re about to book ' + nBook + ' appointments.*') });
  if (okI.length) blocks.push({ type: 'section', block_id: 'free', text: md('✅ *Free (' + okI.length + '):*\n' + byMonth(okI.map(x => x.d))) });
  if (mvI.length) { const L = mvI.slice(0, 25).map(x => '- ' + sh(x.d) + ' · ' + x.note);
    if (mvI.length > 25) L.push('…and ' + (mvI.length - 25) + ' more in another room');
    blocks.push({ type: 'section', block_id: 'moved', text: md('🔄 *Another room (' + mvI.length + '):*\n' + L.join('\n')) }); }
  if (chI.length) {
    blocks.push({ type: 'section', block_id: 'choose', text: md('⚠️ *Taken then (' + chI.length + ') – pick for each:*') });
    for (const x of chI.slice(0, 40)) blocks.push({ type: 'input', block_id: 'ch_' + x.d, label: pt(sh(x.d) + ' – ' + x.note),
      element: { type: 'static_select', action_id: 'ch_pick', placeholder: pt('Pick one'), options: x.options.map(o => ({ text: { type: 'plain_text', text: String(o.label).slice(0, 75) }, value: o.v })) } });
    if (chI.length > 40) blocks.push({ type: 'context', elements: [md('The other ' + (chI.length - 40) + ' taken dates are skipped.')] });
  }
  if (noI.length) blocks.push({ type: 'section', block_id: 'none', text: md('❌ *Nothing free (' + noI.length + ') – left out:*\n' + byMonth(noI.map(x => x.d))) });
  if (chI.length || noI.length) blocks.push({ type: 'context', elements: [md('Skipped dates come back in your DM, each with *Find another time*.')] });
}
const ok = !!(meta.key || meta.inputs) && nBook > 0;
if (!ok) blocks.push({ type: 'context', elements: [{ type: 'mrkdwn', text: '⚠️ The series could not be saved for booking. Go *Back* and try again.' }] });
const view = { type: 'modal', callback_id: 'series_confirm', title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Back' },
  private_metadata: JSON.stringify(meta), blocks };
if (ok) view.submit = { type: 'plain_text', text: RV ? 'Book all' : 'Book ' + dates.length + (dates.length === 1 ? ' date' : ' dates') };
return [{ json: { view_id: R.viewId, view } }];"""
def aps(js):
    a = js.index("const dates = [].concat(r.dates || []);")
    return js[:a] + REVIEW
code("After Prepare Series", aps)

# ---- Book all: the picks read, the count in the working view
code("Read Series Confirm", lambda js: sub(sub(js,
    "const n = Number(meta.n || 0);",
    "// v66: the review's picks - one per taken date (ch_<date>); applied by To Book Series after the saved series checks out\n"
    "const _sv = (V.state && V.state.values) || {}, choices = {};\n"
    "for (const k of Object.keys(_sv)) { const m = k.match(/^ch_(\\d{4}-\\d{2}-\\d{2})$/); const o = m && ((_sv[k] || {}).ch_pick || {}).selected_option; if (o) choices[m[1]] = o.value; }\n"
    "const n = Number(meta.n || 0) + Object.keys(choices).filter(k => choices[k] !== 'skip').length;"),
    "return [{ json: { meta, user: c.user, viewId: V.id || '', key: meta.key || 'prep-none', answer:",
    "return [{ json: { meta, choices, user: c.user, viewId: V.id || '', key: meta.key || 'prep-none', answer:"))

code("To Book Series", lambda js: sub(sub(js,
    "if (!inputs) return [{ json: { go: false, why } }];",
    "if (!inputs) return [{ json: { go: false, why } }];\n"
    "// v66 (PENDING 150): the review's picks - only an option the review offered (inputs.choices, inside the saved series' own code)\n"
    "let __ch = {}; try { __ch = JSON.parse(inputs.choices || '{}') || {}; } catch (e) { __ch = {}; }\n"
    "const __pick = R.choices || {};\n"
    "const __ds = String(inputs.dates || '').split(',').map(x => x.trim()).filter(Boolean);\n"
    "let __per = {}; try { __per = JSON.parse(inputs.per_date || '{}') || {}; } catch (e) { __per = {}; }\n"
    "const skipped_review = String(inputs.left_out || '').split(',').map(x => x.trim()).filter(Boolean);\n"
    "for (const d of Object.keys(__ch)) { const o = [].concat(__ch[d] || []).find(x => x && x.v === __pick[d] && x.v !== 'skip' && x.start && x.end);\n"
    "  if (o) { if (__ds.indexOf(d) === -1) __ds.push(d); __per[d] = { rooms: o.rooms, start: o.start, end: o.end }; } else skipped_review.push(d); }\n"
    "__ds.sort(); skipped_review.sort();\n"
    "if (!__ds.length) return [{ json: { go: false, why: 'every date was skipped', skipped_review } }];\n"
    "inputs = Object.assign({}, inputs, { dates: __ds.join(','), per_date: JSON.stringify(__per) }); delete inputs.choices; delete inputs.left_out;"),
    "return [{ json: Object.assign({}, inputs, { go: true,", "return [{ json: Object.assign({}, inputs, { go: true, skipped_review,"))

# ---- the result: skipped dates in the DM, each with Find another time
def abs_(js):
    js = sub(js, "const booked = [].concat(r.booked || []), skipped = [].concat(r.skipped || []), failed = [].concat(r.failed || []);",
        "const booked = [].concat(r.booked || []), skipped = [].concat(r.skipped || []), failed = [].concat(r.failed || []);\n"
        "const skippedR = [].concat(T.skipped_review || []);   // v66: skipped on the review (picked, or nothing free that day)")
    js = sub(js, "if (!T.go) text = '❌ *Nothing was booked* - ' + (T.why || 'the series could not be read back') + '. Try again from *Book a room*.';",
        "if (!T.go && T.why === 'every date was skipped') text = '❌ *Nothing was booked* - every date was skipped.';   // v66\n"
        "else if (!T.go) text = '❌ *Nothing was booked* - ' + (T.why || 'the series could not be read back') + '. Try again from *Book a room*.';")
    js = sub(js, "  + (failed.length ? '\\n\\nNot booked: ' + failLine() + '.' : '');\n",
        "  + (failed.length ? '\\n\\nNot booked: ' + failLine() + '.' : '')\n"
        "  + (skippedR.length ? '\\n\\nSkipped: ' + skippedR.map(sh).join(', ') : '');   // v66\n")
    js = sub(js, "const dmBlocks = blocks.concat([{ type: 'actions', elements: [",
        "// v66 (PENDING 150): every date not booked, a Find another time - Book a room filled in with this booking, that date\n"
        "const _again = d => { const g = Object.assign({}, (R.meta || {}).ag || {}, { d }); if (!g.s && !(R.meta || {}).ad) { const t = String((R.meta || {}).time || '').split('-'); if (t[0]) { g.s = t[0]; g.e = t[1]; } }\n"
        "  let v = JSON.stringify(g); if (v.length > 1900) { delete g.nt; v = JSON.stringify(g); } return v.length > 1900 ? JSON.stringify({ d }) : v; };\n"
        "const _redo = [...new Set(skipped.concat(skippedR, failed.map(f => f.date)))].filter(Boolean).sort();\n"
        "const _fat = _redo.slice(0, 20).map(d => ({ type: 'actions', block_id: 'fat_' + d, elements: [{ type: 'button', action_id: 'open_book', value: _again(d), text: { type: 'plain_text', text: 'Find another time – ' + sh(d) } }] }));\n"
        "if (_redo.length > 20) _fat.push({ type: 'context', elements: [{ type: 'mrkdwn', text: 'And ' + (_redo.length - 20) + ' more – use *Book a room* for those.' }] });\n"
        "if (_redo.length) blocks.push({ type: 'context', elements: [{ type: 'mrkdwn', text: 'The dates not booked are in your DM, each with *Find another time*.' }] });\n"
        "const dmBlocks = blocks.filter(b => !(b.type === 'context' && /in your DM, each with/.test(JSON.stringify(b)))).concat(_fat, [{ type: 'actions', elements: [")
    return js
code("After Book Series", abs_)

wf["name"] = "Jessie — Slack Interactions — v66 (series review)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v66.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
