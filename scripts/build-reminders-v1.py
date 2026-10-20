#!/usr/bin/env python3
"""Builds workflows/reminders-v1.json - "Jessie — Reminders", v1 (new, slice 2, 20 Oct).

Decided 20 Oct:
  - **4:00 PM daily** - tomorrow's studio sessions: one DM per person, each booking with **Still on** / **Change** / **Free up the
    room** (Free up = Cancel, after Slack's "Are you sure?").
  - **Monday 9:00 AM** - the week's bookings (Monday to Sunday): studios, M booths (standing holds too - each week's instance)
    and meeting rooms, one DM per person, each with **Keep** / **Change** / **Free up the room**.
  - To the booker (ref:), the engineer / arranger (team: and the Engineer / Arranger lines), and a staff member named as who it
    is for ("(for X)", "For: X", Post Processing's Who is it for? - a name that is one person in Bookers).
  - Only bookings made through Jessie (they carry ref:). A calendar that cannot be read sends nothing (never a wrong reminder).
  - Still on / Keep: Slack Interactions v35 (rm_keep) marks the row; Change / Free up are its existing Change / Cancel.
LAUNCH SWITCHES (Build Reminders + Window - `scripts/check-launch-switches` reads them):
  - DEV_REDIRECT 'U08V3CKDGJF' -> '' : during QA a reminder goes to its person only when on ALLOW, else to Howard (marked "Test:
    for <name>"); the same ALLOW roster as Cancel / Move / the notices.
  - YEAR_SHIFT 1 -> 0 (Window): QA bookings are a year ahead, so "tomorrow" / "this week" are read a year ahead during QA.
Nodes copied from Slack Interactions v34 (the reference cache read, the calendar read, the DM) - the live credentials.
Import into a NEW workflow and publish; it runs on its own (no other workflow calls it). Settings: timezone Asia/Manila.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SI = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v34-imported.json")))["nodes"]}
OUT = os.path.join(ROOT, "workflows", "reminders-v1.json")


def node(name, ntype, ver, params, pos, extra=None):
    n = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": ntype, "typeVersion": ver, "position": pos}
    n.update(extra or {})
    return n


def copy(name, newname, pos, params=None):
    n = json.loads(json.dumps(SI[name]))
    n.update({"id": str(uuid.uuid4()), "name": newname, "position": pos})
    if "webhookId" in n:
        n["webhookId"] = str(uuid.uuid4())
    if params is not None:
        n["parameters"] = params
    return n


allow_src = SI["Booked Notices"]["parameters"]["jsCode"]
ALLOW = allow_src[allow_src.index("const ALLOW = "):allow_src.index(";", allow_src.index("const ALLOW = ")) + 1]
helpers = SI["Render My Bookings"]["parameters"]["jsCode"]
HELPERS = helpers[:helpers.index("// Render My Bookings (v11)")]

WINDOW = r"""// Window (Reminders v1): which reminder this is, and the days it covers (Manila).
// LAUNCH SWITCH: YEAR_SHIFT 1 during QA (bookings are a year ahead), 0 at launch - with main's Gate Context and Slack Interactions'.
const YEAR_SHIFT = 1;
let kind = 'daily'; try { const m = $('Monday 9 AM').first(); kind = (m && m.json) ? 'weekly' : 'daily'; } catch (e) { kind = 'daily'; }   // the Monday trigger ran -> weekly
const add = (d, n) => new Date(Date.parse(d + 'T12:00:00Z') + n * 86400000).toISOString().slice(0, 10);
const today0 = new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 10);
const today = (Number(today0.slice(0, 4)) + YEAR_SHIFT) + today0.slice(4);
let start, end;
if (kind === 'daily') { start = add(today, 1); end = add(start, 1); }
else { const dow = new Date(today + 'T12:00:00Z').getUTCDay(); start = add(today, -((dow + 6) % 7)); end = add(start, 7); }
return [{ json: { kind, start, end, timeMin: start + 'T00:00:00+08:00', timeMax: end + 'T00:00:00+08:00', yearShift: YEAR_SHIFT } }];"""

BUILD = HELPERS + r"""
// ---- Build Reminders (v1, 20 Oct): one DM per person - tomorrow's studio sessions (daily) or the week's bookings (Monday)
// LAUNCH SWITCH: DEV_REDIRECT '' at launch. During QA a reminder goes to its person only when on ALLOW, else to DEV_REDIRECT.
const DEV_REDIRECT = 'U08V3CKDGJF';
""" + ALLOW + r"""
const W = $('Window').first().json;
const res = $('List Events R').first().json || {};
const items = Array.isArray(res.items) ? res.items : null;
if (!items) return [];   // the calendar could not be read - nothing sent, never a wrong reminder
const data = readCache($('Read Cache R').all().map(i => i.json || {})) || { bookers: [], rooms: [] };
const staff = (data.bookers || []).map(b => b.fields || {}).filter(f => f.Name);
const idOf = f => String(f['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean)[0] || '';
const byName = n => { const q = String(n || '').trim().toLowerCase(); if (!q) return '';
  const h = staff.filter(f => { const full = String(f.Name).trim().toLowerCase(), fst = full.split(/\s+/)[0];
    const al = ((String(f.Info || '').match(/goes by\s+([^\n]*)/i) || [])[1] || '').split(/,|\band\b/).map(x => x.trim().replace(/\.$/, '').toLowerCase()).filter(Boolean);
    return q === full || q === fst || al.indexOf(q) !== -1; });
  return h.length === 1 ? idOf(h[0]) : ''; };
const nameOf = id => { const f = staff.find(x => idOf(x) === id); return f ? String(f.Name).trim() : ''; };
const roomRec = n => (data.rooms || []).map(r => r.fields || {}).find(f => String(f['Room Name'] || '').trim().toLowerCase() === String(n || '').trim().toLowerCase()) || {};
const kindOf = n => { if (/^M\d+$/i.test(String(n || '').trim())) return 'booth';
  const t = [].concat(roomRec(n)['Room Type'] || []).map(x => String((x && x.name) || x).toLowerCase());
  return t.some(x => /conference|lobby/.test(x)) ? 'common' : 'studio'; };
const per = {};
for (const e of items) {
  if (!e || e.status === 'cancelled') continue;
  const desc = String(e.description || '');
  const ref = (desc.match(/ref:\s*([A-Za-z0-9]+)/) || [])[1] || '';
  if (!ref) continue;   // only bookings made through Jessie
  const b = evBooking(e);
  if (W.kind === 'daily' && (kindOf(roomList(b.r)[0] || '') !== 'studio' || b.d !== W.start)) continue;
  const team = ((desc.match(/team:\s*([^|]+)/) || [])[1] || '').split(/[\s,]+/).filter(x => /^U[A-Z0-9]+$/.test(x));
  const named = [(desc.match(/Engineer:\s*([^(|]+)/) || [])[1], (desc.match(/Arranger:\s*([^(|]+)/) || [])[1],
    (desc.match(/\(for\s+([^)]+)\)/i) || [])[1], (desc.match(/(?:^|\|)\s*For:\s*([^|]+)/) || [])[1]].map(byName).filter(Boolean);
  for (const id of [...new Set([ref].concat(team, named))]) { per[id] = per[id] || {}; per[id][b.id] = b; }
}
const md = t => ({ type: 'mrkdwn', text: t });
const pt = t => ({ type: 'plain_text', text: t });
const out = [];
for (const id of Object.keys(per)) {
  const rows = Object.values(per[id]).sort((x, y) => (x.d + (x.s || '00:00')).localeCompare(y.d + (y.s || '00:00')));
  const to = DEV_REDIRECT && ALLOW.indexOf(id) === -1 ? DEV_REDIRECT : id;
  const blocks = [];
  if (to !== id) blocks.push({ type: 'context', elements: [md('_Test: this reminder is for ' + (nameOf(id) || id) + '._')] });
  blocks.push({ type: 'section', text: md(W.kind === 'daily'
    ? '📅 *Tomorrow* · ' + dayLong(W.start) + '\nStill on? If plans changed, free up the room so someone else can book it.'
    : '📅 *Your week* · ' + dayShort(W.start) + ' – ' + dayShort(addDays(W.end, -1)) + '\nStill need these? Free up anything you won’t use.') });
  for (const b of rows.slice(0, 20)) {
    blocks.push({ type: 'section', block_id: 'bk_' + b.id, text: md('*' + b.t + '*\n' + whenLine(b)) });
    blocks.push({ type: 'actions', block_id: 'bka_' + b.id, elements: [
      { type: 'button', style: 'primary', action_id: 'rm_keep', value: JSON.stringify({ id: b.id, w: W.kind }), text: pt(W.kind === 'daily' ? 'Still on' : 'Keep') },
      { type: 'button', action_id: 'bk_change', value: bkValue(b), text: pt('Change') },
      { type: 'button', action_id: 'bk_cancel', style: 'danger', value: bkValue(b), text: pt('Free up the room'),
        confirm: { title: pt('Free up this room?'), text: md(('*' + b.t + '*\n' + whenLine(b)).slice(0, 290)), confirm: pt('Free it up'), deny: pt('Keep it'), style: 'danger' } }] });
  }
  if (rows.length > 20) blocks.push({ type: 'context', elements: [md('And ' + (rows.length - 20) + ' more - see *My bookings*.')] });
  blocks.push({ type: 'actions', block_id: 'rm_nav', elements: [{ type: 'button', action_id: 'my_bookings', value: 'menu', text: pt('My bookings') }] });
  const n = rows.length;
  out.push({ json: { channel: to, person: id, text: (W.kind === 'daily' ? 'Tomorrow: ' : 'Your week: ') + n + ' booking' + (n === 1 ? '' : 's') + ' - still on?', blocks } });
}
return out;"""

nodes = [
    node("Daily 4 PM", "n8n-nodes-base.scheduleTrigger", 1.2, {"rule": {"interval": [{"field": "cronExpression", "expression": "0 16 * * *"}]}}, [0, 0]),
    node("Monday 9 AM", "n8n-nodes-base.scheduleTrigger", 1.2, {"rule": {"interval": [{"field": "cronExpression", "expression": "0 9 * * 1"}]}}, [0, 220]),
    node("Window", "n8n-nodes-base.code", 2, {"jsCode": WINDOW}, [240, 110]),
    copy("Read Cache 4", "Read Cache R", [480, 110]),
]
lst = copy("List My Events", "List Events R", [720, 110])
lst["parameters"]["url"] = lst["parameters"]["url"].replace("$json.timeMin", "$('Window').first().json.timeMin").replace("$json.timeMax", "$('Window').first().json.timeMax")
assert "$('Window').first().json.timeMin" in lst["parameters"]["url"] and "$('Window').first().json.timeMax" in lst["parameters"]["url"]
lst["executeOnce"] = True
nodes.append(lst)
nodes.append(node("Build Reminders", "n8n-nodes-base.code", 2, {"jsCode": BUILD}, [960, 110]))
dm = copy("DM Booked", "Send Reminder", [1200, 110])
dm["parameters"]["jsonBody"] = "={{ JSON.stringify({ channel: $json.channel, text: $json.text, blocks: $json.blocks }) }}"
dm["onError"] = "continueRegularOutput"
nodes.append(dm)
nodes.append(node("Note", "n8n-nodes-base.stickyNote", 1, {"content": (
    "## Jessie — Reminders\n4:00 PM daily: tomorrow's studio sessions. Monday 9:00 AM: the week's bookings (studios, M booths, meeting "
    "rooms). One DM per person - booker, engineer / arranger, who it is for - each booking with Still on / Keep, Change, Free up the room.\n\n"
    "LAUNCH: DEV_REDIRECT '' (Build Reminders) and YEAR_SHIFT 0 (Window) - run scripts/check-launch-switches."), "width": 520}, [0, -300]))
L = lambda a: [{"node": a, "type": "main", "index": 0}]
C = {"Daily 4 PM": {"main": [L("Window")]}, "Monday 9 AM": {"main": [L("Window")]}, "Window": {"main": [L("Read Cache R")]},
     "Read Cache R": {"main": [L("List Events R")]}, "List Events R": {"main": [L("Build Reminders")]}, "Build Reminders": {"main": [L("Send Reminder")]}}
wf = {"name": "Jessie — Reminders — v1 (day before + Monday)", "nodes": nodes, "connections": C, "pinData": {}, "active": False,
      "settings": {"executionOrder": "v1", "timezone": "Asia/Manila"}, "meta": {}, "tags": []}
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(nodes), "nodes")
