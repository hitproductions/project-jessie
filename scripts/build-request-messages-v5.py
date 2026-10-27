#!/usr/bin/env python3
"""Builds workflows/request-messages-v5.json - Jessie — Request Messages — v5 (who it is for told), 27 Oct.

Howard (27 Oct, a shared-booth request for M7 with "Who is it for?" = Kristine): Kristine, who the booking is for, heard nothing.
  - Who the booking is for (the step-2 "Who is it for?" / "For someone else" matched to a Booker - Read Step 2 puts their Slack id
    on the booking's team: line and "(for <name>)" on Booked by) gets a message when the request opens - "<requester> asked to
    use M7 for you" and the card - and the same message is updated when it ends (booked for you / kept / no answer / withdrawn).
  - PENDING 126: the engineer / arranger on a booking placed by a request get "<requester> booked you as the engineer" once it is
    booked (only on Finalize's placement - the request's event id is there - so a redraw never posts it twice).
  - People are read from the booking's first line (never the note): team: ids in Read Step 2's order (engineer, arranger, who it
    is for), each matched to the Engineer: / Arranger: / (for …) names; when the count does not match, nobody extra is told.
  - The requester, the booker / holder and the engineer asked as approvers are never told twice. QA routing as before (ALLOW,
    DEV_REDIRECT, "Test: this is for …").
Built on workflows/imported/request-messages-v4-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "request-messages-v4-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}
js = by["Render"]["parameters"]["jsCode"]


def sub(a, b):
    global js
    assert js.count(a) == 1, (js.count(a), a[:80])
    js = js.replace(a, b)


sub("const people = [R, A1].concat(!isMB && A2.u && A2.u !== A1.u ? [A2] : []);",
    r"""const people = [R, A1].concat(!isMB && A2.u && A2.u !== A1.u ? [A2] : []);
// v5 (27 Oct, Howard): who the booking is for and its engineer / arranger - from the booking's first line (never the note):
// team: ids in Read Step 2's order (engineer, arranger, who it is for), matched to the Engineer: / Arranger: / (for …) names.
// The count must match, else nobody extra is told. Never someone already told as the requester or an approver.
const _hd = String(P.description || '').split(/\n|<br\s*\/?>/i)[0].replace(/(?:^|\|)\s*Notes?:.*$/i, '');
const _team = ((_hd.match(/team:\s*([^|\n]+)/) || [])[1] || '').split(/[\s,]+/).filter(x => /^U[A-Z0-9]+$/.test(x)).filter((x, i, a) => a.indexOf(x) === i);
const _eng = ((_hd.match(/Engineer:\s*([^(|]+)/) || [])[1] || '').trim(), _arr = ((_hd.match(/Arranger:\s*([^(|]+)/) || [])[1] || '').trim();
const _forN = ((_hd.match(/\(for\s+([^)]+)\)/i) || [])[1] || '').trim();
const _named = [_eng ? 'engineer' : '', _arr ? 'arranger' : '', _forN ? 'for' : ''].filter(Boolean);
const EXTRA = [];
if (_team.length && _team.length === _named.length) _team.forEach((u, i) => { if ([R.u, A1.u, A2.u].indexOf(u) !== -1) return;
  EXTRA.push(_named[i] === 'for' ? { r: 'f', u, name: _forN } : { r: 't', u, name: _named[i] === 'engineer' ? _eng : _arr, as: _named[i] }); });
const F = EXTRA.find(x => x.r === 'f') || null, TEAM = EXTRA.filter(x => x.r === 't');
function forOpen() {
  return [sec('👋 *' + R.name + ' asked to use ' + room + ' for you.*\n\n' + reqCard + '\n\n'
      + (isMB ? holder + ' is being asked (their standing hold). ' : 'Its booker is being asked. ') + 'You’ll hear here when it’s settled.'),
    { type: 'actions', elements: [btn('my_bookings', 'My bookings', 'menu')] }];
}
function forEnd() {
  const t = String(ev.title || title), id = String(ev.id || '');
  const lead = st === 'DONE' ? '✅ *' + room + ' is booked for you* – ' + first(R.name) + ' booked it.'
    : st === 'REJECTED' ? '❌ *Not booked* – ' + (by || (isMB ? holder : A1.name) || 'they') + ' is keeping ' + room + '.'
    : st === 'EXPIRED' ? '⌛ *Not booked* – no answer by ' + dl + '.'
    : st === 'WITHDRAWN' ? '*Not booked* – ' + first(R.name) + ' withdrew the request.'
    : st === 'FAILED' ? '⚠️ *Couldn’t book ' + room + '* – nothing was booked.'
    : '⏳ *' + R.name + ' asked to use ' + room + ' for you.*';
  const card = st === 'DONE' ? bookCard(t, _dayLong(day), _times(rs, re), room) : reqCard;
  const out = [{ type: 'section', block_id: st === 'DONE' && id ? 'bk_' + id : undefined, text: md(lead + '\n\n' + card) }];
  if (!out[0].block_id) delete out[0].block_id;
  if (st === 'DONE' && id) { const bk = { id, d: day, s: _isAllDay(rs, re) ? '' : _hm(rs), e: _isAllDay(rs, re) ? '' : _hm(re), r: room, t: t.slice(0, 150), st: type };
    out.push({ type: 'actions', block_id: 'bka_' + id, elements: [btn('bk_change', 'Change', bk),
      btn('bk_cancel', 'Cancel', bk, { style: 'danger', confirm: confirm('Cancel this booking?', '*' + t + '*\n' + whenShort, 'Cancel booking', 'Keep it', true) })] }); }
  out.push({ type: 'actions', elements: [btn('my_bookings', 'My bookings', 'menu')] });
  return out;
}
function teamDone(p) {
  return [sec('👋 *' + R.name + ' booked you as the ' + p.as + '.*\n\n' + bookCard(String(ev.title || title), _dayLong(day), _times(rs, re), room)),
    { type: 'actions', elements: [btn('my_bookings', 'My bookings', 'menu')] }];
}""")
sub("const textOf = (role, open) => open ? (role === 'r' ?",
    "const textOf = (role, open) => role === 'f' ? (open ? R.name + ' asked to use ' + room + ' for you · ' + whenShort : 'The request for ' + room + ' for you: ' + st.toLowerCase())\n"
    "  : role === 't' ? R.name + ' booked you · ' + room + ' · ' + whenShort\n"
    "  : open ? (role === 'r' ?")
sub("    out.push({ op: 'post', r: p.r, u: p.u, channel: to, text: textOf(p.r, true), blocks: (p.r === 'r' ? requesterOpen() : approverOpen(p)).concat(testLine(to, p)) }); }",
    "    out.push({ op: 'post', r: p.r, u: p.u, channel: to, text: textOf(p.r, true), blocks: (p.r === 'r' ? requesterOpen() : approverOpen(p)).concat(testLine(to, p)) }); }\n"
    "  if (F) { const to = route(F.u); out.push({ op: 'post', r: 'f', u: F.u, channel: to, text: textOf('f', true), blocks: forOpen().concat(testLine(to, F)) }); }   // v5")
sub("  if (stored.length) for (const m of stored) { const p = people.find(x => x.r === m.r) || { r: m.r, u: m.u, name: '' }; const to = route(p.u);\n"
    "    out.push({ op: 'update', r: m.r, u: m.u, channel: m.c, ts: m.t, text: textOf(m.r, false), blocks: (m.r === 'r' ? requesterEnd() : approverEnd(p)).concat(testLine(to, p)) }); }",
    "  if (stored.length) for (const m of stored) { const p = people.concat(F ? [F] : []).find(x => x.r === m.r) || { r: m.r, u: m.u, name: '' }; const to = route(p.u);\n"
    "    out.push({ op: 'update', r: m.r, u: m.u, channel: m.c, ts: m.t, text: textOf(m.r, false), blocks: (m.r === 'r' ? requesterEnd() : m.r === 'f' ? forEnd() : approverEnd(p)).concat(testLine(to, p)) }); }   // v5: f")
sub("return out.map(x => ({ json: x }));",
    "// v5 (PENDING 126): booked by a request - its engineer / arranger told once, on the placement itself (Finalize hands the event)\n"
    "if (mode !== 'open' && st === 'DONE' && ev && ev.id) for (const p of TEAM) { const to = route(p.u);\n"
    "  out.push({ op: 'post', r: 't', u: p.u, channel: to, text: textOf('t', false), blocks: teamDone(p).concat(testLine(to, p)) }); }\n"
    "return out.map(x => ({ json: x }));")
by["Render"]["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Request Messages — v5 (who it is for told)"
out = os.path.join(ROOT, "workflows", "request-messages-v5.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
