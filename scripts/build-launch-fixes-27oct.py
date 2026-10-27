#!/usr/bin/env python3
"""Builds the launch-fix round of 27 Oct (PENDING 125, 127, 128, 129) from the live downloads:

  workflows/slack-interactions-v46.json  Jessie — Slack Interactions — v46 (launch fixes)
  workflows/move-booking-v39.json        Jessie — Move Booking — v39 (launch fixes)
  workflows/cancel-booking-v33.json      Jessie — Cancel Booking — v33 (people from the first line)
  workflows/reminders-v7.json            Jessie — Reminders — v7 (people from the first line)
  workflows/project-jessie-v284.json     Project Jessie — v284 (people from the first line)

125 - a sub-workflow call that fails no longer stops the run on the "⏳ … we'll let you know in your DM" message. Slack
      Interactions' calls (Room Availability, Prepare, Book, Prepare Series, Book Series, Move, Cancel, Cancel G) continue on
      error; the error reaches the usual answer (the form, or the DM when the window is gone) in words - "Something went wrong
      on our side …", "check My bookings" where it may have gone through - and Howard gets the error (Ops Alert).
127 - who is on a booking is read from the description's first line only (Engineer, Arranger, Booked by (for …), ref, team,
      Dept), never from the note (its own block since Book Session v122, or an older inline "| Notes: …"): Reminders, My
      bookings (Slack Interactions and main), Series Notices, Cancel's ownership check, Move's.
128 - the Change form's question ("Did you mean …?") reaches the DM when the window was closed, with Continue changing (the
      Change form again, filled in, the question on it); step 2 reaches the DM with Continue booking when the "Finding free
      rooms…" window was closed; a cancel whose message could not be updated is said in the DM.
129 - notices: Series / Change Notices say "booked this for you" like Booked Notices (one notices()); a series' "for" person
      is no longer "the arranger"; a details change keeps who it is for on the booking (Read Change sends teamWas, Move keeps
      the rest of team:); Move's notice says "changed" when only the details changed, and an engineer / arranger taken off
      is told "You were taken off this session".
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMP = os.path.join(ROOT, "workflows", "imported")

# the first line of a description, without an older inline note - who is on the booking is read from here only
HD = r"String(%s || '').split(/\n|<br\s*\/?>/i)[0].replace(/(?:^|\|)\s*Notes?:.*$/i, '')"


def load(name):
    wf = json.load(open(os.path.join(IMP, name)))
    return wf, {n["name"]: n for n in wf["nodes"]}, wf["connections"]


def mk_sub(by):
    def sub(node, a, b, n=1):
        js = by[node]["parameters"]["jsCode"]
        assert js.count(a) == n, (node, js.count(a), a[:90])
        by[node]["parameters"]["jsCode"] = js.replace(a, b)
    return sub


def save(wf, title, out):
    wf["name"] = title
    p = os.path.join(ROOT, "workflows", out)
    with open(p, "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", os.path.relpath(p, ROOT), len(wf["nodes"]), "nodes")


def code_node(name, js, pos):
    return {"parameters": {"jsCode": js}, "id": str(uuid.uuid4()), "name": name, "type": "n8n-nodes-base.code",
            "typeVersion": 2, "position": pos}


def link(C, a, b, out=0):
    C.setdefault(a, {"main": []})
    while len(C[a]["main"]) <= out:
        C[a]["main"].append([])
    C[a]["main"][out].append({"node": b, "type": "main", "index": 0})


FIRST_LINE_NOTE = "   // v46 / Move v39 / Cancel v33 / Reminders v7 / main v284 (PENDING 127): the first line only - never the note"

# ---------------------------------------------------------------- Slack Interactions v46
wf, by, C = load("slack-interactions-v45-imported.json")
sub = mk_sub(by)

# 125: the calls continue on error; the error reaches the usual answer
CALLS = ["Room Availability", "Prepare", "Book", "Prepare Series", "Book Series", "Move", "Cancel", "Cancel G"]
for nm in CALLS:
    assert by[nm]["type"].endswith("executeWorkflow") and not by[nm].get("onError"), nm
    by[nm]["onError"] = "continueRegularOutput"

ERR_PREP = "Something went wrong on our side – nothing was booked. Press *Book* again in a moment."
ERR_BOOK = "Something went wrong on our side, so it may or may not have gone through. Check *My bookings* before you press *Book* again."
for nm, txt in [("After Prepare", ERR_PREP), ("After Prepare Series", ERR_PREP), ("After Book", ERR_BOOK)]:
    sub(nm, "const r = $input.first().json || {};",
        "const r = (j => (j.error && j.status === undefined) ? { status: 'ERROR', reason: 'CALL_ERROR', human: '%s' } : j)($input.first().json || {});"
        "   // v46 (PENDING 125): the call failed - said in words" % txt.replace("'", "\\'"))
    sub(nm, "function problemFor(r) {\n  const reason = r.reason || r.status || '';",
        "function problemFor(r) {\n  const reason = r.reason || r.status || '';\n"
        "  if (reason === 'CALL_ERROR') return { warn: String(r.human || '') };   // v46 (PENDING 125)")
# the DM when the window is gone: not "Not booked." in front of "it may have gone through"
sub("Result DM", "blocks: [{ type: 'section', text: md('⚠️ *Not booked.* ' + warn) }, bookBtn(R)]",
    "blocks: [{ type: 'section', text: md((/^Something went wrong/.test(warn) ? '⚠️ ' : '⚠️ *Not booked.* ') + warn) }, bookBtn(R)]   /* v46 */")

sub("After Book Series", "const r = T.go ? ($input.first().json || {}) : { status: 'NOT_BOOKED', human: '' };",
    "const r = T.go ? ($input.first().json || {}) : { status: 'NOT_BOOKED', human: '' };\n"
    "const _callErr = !!(T.go && r.error && r.status === undefined && !r.booked);   // v46 (PENDING 125): the call failed - some dates may be in")
sub("After Book Series", "else if (!booked.length) text = '❌ *Nothing was booked.*",
    "else if (_callErr) text = '⚠️ *Something went wrong on our side* while booking *' + title + '*. Some dates may have gone in – check *My bookings* before you try again.';\n"
    "else if (!booked.length) text = '❌ *Nothing was booked.*")

sub("After Move", "const r = $input.first().json || {};",
    "const r = $input.first().json || {};\n"
    "if (r.error && r.status === undefined && r.verdict === undefined) r.reason = 'CALL_ERROR';   // v46 (PENDING 125): the call failed")
sub("After Move", "NO_REFERENCE: 'This booking has no booker on it, so it has to be changed by hand.' }[r.reason]",
    "NO_REFERENCE: 'This booking has no booker on it, so it has to be changed by hand.',\n"
    "       CALL_ERROR: 'Something went wrong on our side, so it may or may not have changed. Check *My bookings* before you try again.' }[r.reason]")
sub("After Cancel", "let r = {}; try { r = $('Cancel').first().json || {}; } catch (e) { r = ($input.first() || {}).json || {}; }",
    "let r = {}; try { r = $('Cancel').first().json || {}; } catch (e) { r = ($input.first() || {}).json || {}; }\n"
    "if (r.error && r.status === undefined) r = Object.assign({}, r, { reason: 'CALL_ERROR' });   // v46 (PENDING 125): the call failed")
sub("After Cancel", "NO_REFERENCE: 'This booking has no booker on it, so it has to be cancelled by hand.' }[r.reason]",
    "NO_REFERENCE: 'This booking has no booker on it, so it has to be cancelled by hand.',\n"
    "  CALL_ERROR: 'Something went wrong on our side. Check *My bookings* to see if it’s still there.' }[r.reason]")

HOWARD = "U08V3CKDGJF"
OPS = r"""// Ops Alert (v46, 27 Oct, PENDING 125): a sub-workflow call failed (Room Availability, Prepare, Book, a series, Move, Cancel).
// The person is told by the usual answer (the form, or the DM when the window is gone); Howard gets the error here - after launch
// too (an ops message, like Report Refused). Nothing failed -> no item.
const j = ($input.first() || {}).json || {};
if (!(j.error && j.status === undefined && j.verdict === undefined && j.ok === undefined && j.booked === undefined)) return [];
let c = {}; try { c = $('Check Signature').first().json || {}; } catch (e) { c = {}; }
const err = typeof j.error === 'string' ? j.error : JSON.stringify(j.error);
const at = new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 16).replace('T', ' ');
const text = '⚠️ Jessie: a step failed (' + (c.action || c.cb || c.type || 'unknown') + ') for <@' + (c.user || '?') + '>, ' + at + ' PHT:\n' + String(err).slice(0, 1500);
return [{ json: { channel: '%s', text, blocks: [{ type: 'section', text: { type: 'mrkdwn', text: text.slice(0, 2900) } }] } }];""" % HOWARD
dm_pos = by["DM Not Shown"]["position"]
wf["nodes"].append(code_node("Ops Alert", OPS, [dm_pos[0] - 300, dm_pos[1] + 400]))
for nm in CALLS:
    link(C, nm, "Ops Alert")
link(C, "Ops Alert", "DM Not Shown")

# 128a: the Change form's question -> the DM, with Continue changing
sub("To Move", "return [{ json: { go: false, view_id: R.viewId, view: changeView(R.b, R.n, warn, Object.assign({}, R.meta, { askedClient: t }), roomLists(data), { data, vals: R.d, open: true }) } }];",
    "return [{ json: { go: false, view_id: R.viewId, view: changeView(R.b, R.n, warn, Object.assign({}, R.meta, { askedClient: t }), roomLists(data), { data, vals: R.d, open: true }), warn, askedClient: t } }];   // v46: warn, askedClient - for Ask DM")
ASK = r"""// Ask DM (v46, 27 Oct, PENDING 128): the Change form's question ("Did you mean …?") could not be shown - the window was closed
// (gotcha 49). It goes to the DM with Continue changing: the Change form again, with what was filled in and the question.
const shown = ($input.first() || {}).json || {};
if (shown.ok !== false) return [];
const T = $('To Move').first().json || {}, R = $('Read Change').first().json || {};
const b = R.b || {};
if (!R.user || !b.id) return [];
const base = { id: b.id, d: b.d, s: b.s || '', e: b.e || '', r: b.r || '', t: String(b.t || '').slice(0, 150), st: b.st || '', n: R.n || {},
  ac: String(T.askedClient || '').slice(0, 150), w: String(T.warn || '').slice(0, 400) };
const vals = Object.assign({}, R.d || {}); delete vals.teamShown;
let val = JSON.stringify(Object.assign({}, base, { v: vals }));
if (val.length > 1990) { delete vals.notes; val = JSON.stringify(Object.assign({}, base, { v: vals })); }
if (val.length > 1990) val = JSON.stringify(base);
const DS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'], MS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const t12 = hm => { let [h, m] = String(hm).split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
const x = new Date(String(b.d) + 'T12:00:00Z');
const when = isNaN(x) ? '' : DS[x.getUTCDay()] + ', ' + MS[x.getUTCMonth()] + ' ' + x.getUTCDate() + ' · ' + (b.s && !(b.s === '00:00' && b.e === '00:00') ? t12(b.s) + ' – ' + t12(b.e) : 'all day')
  + (b.r ? ' · ' + String(b.r).split(',').map(y => y.trim()).filter(Boolean).join(' + ') : '');
const warn = String(T.warn || 'One thing needs an answer first.');
const md = t => ({ type: 'mrkdwn', text: t }), pt = t => ({ type: 'plain_text', text: t });
return [{ json: { channel: R.user, text: 'Not changed yet: ' + warn.replace(/\*/g, ''), blocks: [
  { type: 'section', block_id: 'bk_' + b.id, text: md('*' + (b.t || 'Your booking') + '*' + (when ? '\n' + when : '')) },
  { type: 'context', block_id: 'bkn_' + b.id, elements: [md('⚠️ *Not changed yet.* ' + warn)] },
  { type: 'actions', block_id: 'bka_' + b.id, elements: [{ type: 'button', style: 'primary', action_id: 'bk_change', value: val, text: pt('Continue changing') },
    { type: 'button', action_id: 'my_bookings', value: 'menu', text: pt('My bookings') }] }] } }];"""
aa = by["Ask Again"]["position"]
wf["nodes"].append(code_node("Ask DM", ASK, [aa[0] + 200, aa[1] + 200]))
link(C, "Ask Again", "Ask DM")
link(C, "Ask DM", "DM Not Shown")
# Build Change takes it: the filled-in values, the question, the client it asked about
sub("Build Change", "const nIn = (b.n && typeof b.n === 'object') ? b.n : null; delete b.n;",
    "const nIn = (b.n && typeof b.n === 'object') ? b.n : null; delete b.n;\n"
    "// v46 (PENDING 128): Continue changing (Ask DM) - what was filled in, the question, the client it asked about\n"
    "const vIn = (b.v && typeof b.v === 'object') ? b.v : null, wIn = String(b.w || ''), acIn = String(b.ac || ''); delete b.v; delete b.w; delete b.ac;")
sub("Build Change", "return [{ json: { trigger_id: c.triggerId, view: changeView(b, cur, '', meta, roomLists(data), { data: data || { bookers: [], sessionTypes: [], rooms: [] } }) } }];",
    "if (acIn) meta.askedClient = acIn;   // v46\n"
    "return [{ json: { trigger_id: c.triggerId, view: changeView(b, cur, wIn, meta, roomLists(data), Object.assign({ data: data || { bookers: [], sessionTypes: [], rooms: [] } }, vIn ? { vals: vIn, open: true } : {})) } }];   // v24: the details shown at once; v46: Continue changing")

# 128b: step 2 could not be shown -> the DM, with Continue booking
STEP2 = r"""// Step 2 DM (v46, 27 Oct, PENDING 128): step 2 could not be shown - the "Finding free rooms…" window was closed. The DM gets
// Continue booking (step 2 again, rooms checked again); a repeating booking gets Book a room (its dates are not on the button).
const shown = ($input.first() || {}).json || {};
if (shown.ok !== false) return [];
const s = ($('Read Step 1').first().json || {}).s || {};
if (!s.requester) return [];
const series = !!(s.series && (s.series.dates || []).length > 1);
const g = Object.assign({}, s.pre || {}, { d: s.date, s: s.allDay ? '' : s.t0, e: s.allDay ? '' : s.t1, ad: s.allDay ? 1 : 0, p: s.kind === 'booth' ? '__booth' : s.purpose });
Object.keys(g).forEach(k => { if (!g[k]) delete g[k]; });
let val = JSON.stringify(g); if (val.length > 1900) val = JSON.stringify({ d: g.d, s: g.s, e: g.e, ad: g.ad, p: g.p });
const cont = !series && !!(g.d && g.p && ((g.s && g.e) || g.ad));
const pt = t => ({ type: 'plain_text', text: t });
const text = '⚠️ *Not booked yet* – the window closed before the rooms came up.';
return [{ json: { channel: s.requester, text: 'Not booked yet - the window closed before the rooms came up.', blocks: [{ type: 'section', text: { type: 'mrkdwn', text } },
  { type: 'actions', elements: [{ type: 'button', style: 'primary', action_id: cont ? 'book_continue' : 'open_book', value: series ? 'menu' : val, text: pt(cont ? 'Continue booking' : 'Book a room') },
    { type: 'button', action_id: 'my_bookings', value: 'menu', text: pt('My bookings') }] }] } }];"""
s2 = by["Show Step 2"]["position"]
wf["nodes"].append(code_node("Step 2 DM", STEP2, [s2[0] + 200, s2[1] + 200]))
link(C, "Show Step 2", "Step 2 DM")
link(C, "Step 2 DM", "DM Not Shown")

# 128c: a cancel whose message could not be updated -> said in the DM
CANCEL_DM = r"""// Cancel DM (v46, 27 Oct, PENDING 128): the message the Cancel button was in could not be updated - the result goes to the DM.
const shown = ($input.first() || {}).json || {};
if (shown.ok !== false) return [];
const A = $('After Cancel').first().json || {};
let c = {}; try { c = $('Check Signature').first().json || {}; } catch (e) { c = {}; }
const p = $('Read Request').first().json.payload || {};
let b = {}; try { b = JSON.parse(((p.actions || [])[0] || {}).value || '{}'); } catch (e) { b = {}; }
if (!c.user) return [];
const row = (A.blocks || []).find(x => x.block_id === 'bk_' + b.id), w = (A.blocks || []).find(x => x.block_id === 'bkw_' + b.id);
const why = String((((w || {}).elements || [])[0] || {}).text || '').replace(/^⚠️\s*/, '');
const text = A.ok ? String((row && row.text && row.text.text) || ('❌ *Cancelled.*\n\n*' + (b.t || 'Your booking') + '*'))
  : '⚠️ *' + (b.t || 'The booking') + '* was not cancelled. ' + (why || 'Try again in a moment.');
const pt = t => ({ type: 'plain_text', text: t });
return [{ json: { channel: c.user, text: text.replace(/\*/g, '').slice(0, 300), blocks: [{ type: 'section', text: { type: 'mrkdwn', text: text.slice(0, 2900) } },
  { type: 'actions', elements: [{ type: 'button', action_id: 'open_book', value: 'menu', text: pt('Book a room') }, { type: 'button', action_id: 'my_bookings', value: 'menu', text: pt('My bookings') }] }] } }];"""
uc = by["Update Cancelled"]["position"]
wf["nodes"].append(code_node("Cancel DM", CANCEL_DM, [uc[0] + 200, uc[1] + 200]))
link(C, "Update Cancelled", "Cancel DM")
link(C, "Cancel DM", "DM Not Shown")

# 127: the people from the first line
sub("Render My Bookings", "    const desc = String(e.description || '');\n    const ref",
    "    const desc = " + (HD % "e.description") + ";" + FIRST_LINE_NOTE + "\n    const ref")

# 129: one notices() - Series / Change Notices take x.line like Booked Notices
def text_line(js):
    ls = [l for l in js.split("\n") if l.startswith("    const text = (to !== x.id")]
    assert len(ls) == 1, ls
    return ls[0]
booked_line = text_line(by["Booked Notices"]["parameters"]["jsCode"])
assert "x.line ||" in booked_line
for nm in ["Series Notices", "Change Notices"]:
    sub(nm, text_line(by[nm]["parameters"]["jsCode"]), booked_line)
sub("Series Notices", "const desc = String(T.description || '');",
    "const desc = " + (HD % "T.description") + ";" + FIRST_LINE_NOTE)
sub("Series Notices", "return notices(team.map(id => ({ id, role: whoIs(data, id).toLowerCase() === engName ? 'engineer' : 'arranger', verb: 'booked', name: whoIs(data, id),\n"
    "  extra: n ? ' for ' + n + ' dates' : '' })), R.user, whoIs(data, R.user) || 'Someone', body);",
    "// v46 (PENDING 129): who it is for (\"Booked by: … (for X)\") is told \"booked these dates for you\", not \"as the arranger\"\n"
    "const forName = ((desc.match(/\\(for\\s+([^)]+)\\)/i) || [])[1] || '').trim().toLowerCase();\n"
    "return notices(team.map(id => { const nm = whoIs(data, id), lc = nm.toLowerCase();\n"
    "  if (lc && lc === engName) return { id, role: 'engineer', verb: 'booked', name: nm, extra: n ? ' for ' + n + ' dates' : '' };\n"
    "  if (lc && lc === forName) return { id, line: n ? 'booked ' + n + ' dates for you' : 'booked this for you', name: nm };\n"
    "  return { id, role: 'arranger', verb: 'booked', name: nm, extra: n ? ' for ' + n + ' dates' : '' }; }), R.user, whoIs(data, R.user) || 'Someone', body);")
# a details change keeps who it is for: Move keeps the team: ids that were not the engineer / arranger
sub("Read Change", "[d.en === 'none' ? '' : d.en, d.ar && d.ar !== 'none' ? d.ar : ''].filter(Boolean).join(' ') } : null;",
    "[d.en === 'none' ? '' : d.en, d.ar && d.ar !== 'none' ? d.ar : ''].filter(Boolean).join(' '),\n"
    "  teamWas: [O.en, O.ar].filter(x => x && x !== 'none') } : null;   // v46 (PENDING 129): Move v39 keeps the rest of team: (who it is for)")

save(wf, "Jessie — Slack Interactions — v46 (launch fixes)", "slack-interactions-v46.json")

# ---------------------------------------------------------------- Move Booking v39
wf, by, C = load("move-booking-v38-imported.json")
sub = mk_sub(by)
sub("Resolve Booking", "const desc = String(ev.description || '');",
    "const desc = String(ev.description || '');\n"
    "const _hd = x => " + (HD % "x") + ";" + FIRST_LINE_NOTE + "\n"
    "const descH = _hd(desc);")
for a in ["const ref = desc.match(/ref:", "const by = desc.match(", "const bookingDept = ((desc.match(", "const team = ((desc.match(",
          "engName0 = ((desc.match(", "const engName = ((desc.match("]:
    sub("Resolve Booking", a, a.replace("desc.match(", "descH.match("))
sub("Resolve Booking", "let __title = title, __desc = desc;", "let __title = title, __desc = desc, __teamChanged = false;   // v39")
sub("Resolve Booking", "    if ('team' in nd) put('team', nd.team, false);",
    "    if ('team' in nd) { const _was = Array.isArray(nd.teamWas) ? nd.teamWas : null;   // v39 (PENDING 129): who it is for stays on the booking\n"
    "      const _keep = _was ? team.filter(id => _was.indexOf(id) === -1) : [];\n"
    "      put('team', String(nd.team || '').split(/\\s+/).concat(_keep).filter((x, i, a) => x && a.indexOf(x) === i).join(' '), false); __teamChanged = true; }")
sub("Resolve Booking", "} catch (e) { __title = title; __desc = desc; }", "} catch (e) { __title = title; __desc = desc; __teamChanged = false; }")
sub("Resolve Booking", "  old_start: (ev.start && (ev.start.dateTime || ev.start.date)) || '',",
    "  old_start: (ev.start && (ev.start.dateTime || ev.start.date)) || '',\n"
    "  old_end: (ev.end && (ev.end.dateTime || ev.end.date)) || '', old_location: ev.location || '',   // v39: moved or only changed\n"
    "  new_team: ((_hd(__desc).match(/team:\\s*([^|\\n]+)/) || [])[1] || '').split(/[\\s,]+/).filter(Boolean), team_changed: __teamChanged,   // v39: taken off")
sub("Build Recipients", "const VERB = 'moved';", "let VERB = 'moved';   // v39: 'changed' below when only the details changed")
br = by["Build Recipients"]["parameters"]["jsCode"]
rl = [l for l in br.split("\n") if l.startswith("const _room = r =>")]
assert len(rl) == 1, rl
sub("Build Recipients", rl[0], rl[0] + "\n"
    "// v39 (27 Oct, PENDING 129): \"changed\" when the date, time and rooms stayed - only the details (title, people, type, note) changed\n"
    "{ const _t = x => { const d = _mnl(x); return isNaN(d) ? NaN : d.getTime(); };\n"
    "  const _rs = r => String(r || '').split(',').map(x => x.replace(/^KDC Plaza-Top Level-/i, '').replace(/(?:\\s*\\([^)]*\\))+\\s*$/, '').trim().toLowerCase()).filter(Boolean).sort().join('|');\n"
    "  if (co.old_end !== undefined && _t(co.old_start) === _t(co.new_start) && _t(co.old_end) === _t(co.new_end) && _rs(co.old_location) === _rs(co.location || trig.new_rooms)) VERB = 'changed'; }")
sub("Build Recipients", "for (const id of team) push(id, names[id] || 'a team member', 'A session you are on was ' + VERB + ' by ' + actor + ':');",
    "const _off = id => co.team_changed === true && Array.isArray(co.new_team) && co.new_team.indexOf(id) === -1;   // v39 (PENDING 129): taken off in a change\n"
    "for (const id of team) push(id, names[id] || 'a team member', _off(id) ? 'You were taken off this session by ' + actor + ':' : 'A session you are on was ' + VERB + ' by ' + actor + ':');")
save(wf, "Jessie — Move Booking — v39 (launch fixes)", "move-booking-v39.json")

# ---------------------------------------------------------------- Cancel Booking v33
wf, by, C = load("cancel-booking-v32-imported.json")
sub = mk_sub(by)
sub("Check Ownership", "const desc = String(ev.description || '');",
    "const desc = " + (HD % "ev.description") + ";" + FIRST_LINE_NOTE)
save(wf, "Jessie — Cancel Booking — v33 (people from the first line)", "cancel-booking-v33.json")

# ---------------------------------------------------------------- Reminders v7
wf, by, C = load("reminders-v6-imported.json")
sub = mk_sub(by)
sub("Build Reminders", "  const desc = String(e.description || '');\n  const ref",
    "  const desc = " + (HD % "e.description") + ";" + FIRST_LINE_NOTE + "\n  const ref")
save(wf, "Jessie — Reminders — v7 (people from the first line)", "reminders-v7.json")

# ---------------------------------------------------------------- main v284
wf, by, C = load("project-jessie-v283-imported.json")
sub = mk_sub(by)
sub("Mine Reply", "    const desc = String(e.description || '');\n    const ref",
    "    const desc = " + (HD % "e.description") + ";" + FIRST_LINE_NOTE + "\n    const ref")
sub("Change Reply", "  const desc = String(e.description || '');\n  const ref",
    "  const desc = " + (HD % "e.description") + ";" + FIRST_LINE_NOTE + "\n  const ref")
save(wf, "Project Jessie — v284 (people from the first line)", "project-jessie-v284.json")
