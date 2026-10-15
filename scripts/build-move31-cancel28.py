#!/usr/bin/env python3
"""Move Booking v31 + Cancel Booking v28 (build B of the 15 Oct Slack-test notes).

Both - **everyone on the session is told about someone else's change** (Howard 15 Oct: the engineer and arranger should
be notified, also when the booker changes or cancels): the booker when someone else did it, and every team member
("team:" ids - the engineer and arranger of a form booking; for an older booking the engineer found by the title's
initials) except the person who did it. During QA the same DEV_REDIRECT / ALLOW as before (Howard; ALLOW testers get
their own). Build Recipients never returns nothing (a "skip" item keeps the reply flowing).

Move Booking v31 also:
  - **free stretches**: a taken room's whole free time that day (8 AM - 10 PM, the booking being moved not counting,
    each stretch at least the session's length) as free_gaps, beside the nearest two slots (same_day_slots) the chat uses.
    Slack test: "Free that day: 12:00 PM – 2:00 PM, 8:00 AM – 10:00 AM" for a room free from 2 PM on.
  - **a new title and details** (new_summary, new_details = {"Engineer": name|"", "Arranger": name|"", "team": "U.. U.."}):
    the replacement gets them - the description's other segments (Booked by, ref, Notes, Type, Dept) stay the
    booker's. For the Change form's "Change other session details".
Built on the live downloads (workflows/imported/move-booking-v30-imported.json, cancel-booking-v27-imported.json).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load(name):
    return json.load(open(os.path.join(ROOT, "workflows", "imported", name)))


def patcher(wf):
    by = {n["name"]: n for n in wf["nodes"]}

    def patch(node, pairs):
        js = by[node]["parameters"]["jsCode"]
        for a, b in pairs:
            assert js.count(a) == 1, (node, a[:70], js.count(a))
            js = js.replace(a, b)
        by[node]["parameters"]["jsCode"] = js
    return by, patch


RECIPIENTS = r"""// Notification recipients (v28 Cancel / v31 Move, decided 15 Oct): everyone on the session except the person who made the
// change - the booker (when someone else did it) and each team member ("team:" ids; an older booking's engineer by its
// title's initials). DEV_REDIRECT reroutes to one dev inbox while building; ALLOW = ids that receive their OWN real DM.
// At launch DEV_REDIRECT='' -> all real. Never returns nothing: a "skip" item keeps the reply flowing.
const DEV_REDIRECT = 'U08V3CKDGJF';                 // '' at launch
const ALLOW = ['U08V3CKDGJF','U098UFMKQHZ','U08JL17A50A','U0B4S0EKSAY','U098UFLG70B','U026N6E1R','U045A3VQER3'] /* QA round 2 2026-09-24: Howard,Trish,Camy,Jess,Tel,Tara,Genzo. Launch bypass = DEV_REDIRECT='' (ALLOW then moot). */ ;
const route = (id, honorAllow) => (!DEV_REDIRECT || (honorAllow && ALLOW.indexOf(id) !== -1)) ? id : DEV_REDIRECT;
const co = $('__NODE__').first().json;
const trig = $('When Executed by Another Workflow').first().json;
const actor = String(trig.requester_name || 'someone');
const actorId = String(trig.requester || '');
const dateStr = String(trig.booking_date || '');
const title = co.title;
const VERB = '__VERB__';
const roomNote = co.roomNote || '';
const out = [], told = new Set();
const push = (id, name, body) => {
  if (!id || id === actorId || told.has(id)) return;
  told.add(id);
  const to = route(id, true); const redirected = to !== id;
  out.push({ to, text: (redirected ? ('[DEV] would notify ' + name + ' (' + id + '):\n') : '') + body });
};
const bookerId = co.bookerRef;
push(bookerId, co.bookerName || 'the booker', 'Heads up - your booking "' + title + '" on ' + dateStr + ' was ' + VERB + roomNote + ' by ' + actor + '.');
const names = {};
let eng = {};
try { eng = $('Lookup Engineer').first().json || {}; } catch (e) {}
const ef = eng.fields || {};
if (ef['Slack User ID']) names[String(ef['Slack User ID']).split(/[\s,]+/)[0]] = ef['Name'] || '';
const team = [].concat(co.team || []);
const engId = String(ef['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean)[0] || '';
if (!team.length && engId) team.push(engId);
for (const id of team) push(id, names[id] || 'a team member', 'Heads up - "' + title + '" on ' + dateStr + ', a session you are on, was ' + VERB + roomNote + ' by ' + actor + '.');
if (!out.length) return [{ json: { to: '', text: '', skip: true } }];
return out.map(o => ({ json: o }));"""

NOTIFY_OLD = "const notify = !owner && (onTeam || coordInDept || isHaistDev);"
NOTIFY_NEW = ("// v28 / v31 (decided 15 Oct): anyone else on the session is told - the booker when someone else acts, each team\n"
              "// member (or an older booking's engineer, by initials) except the person who acted\n"
              "const notify = !owner || team.some(id => id !== me) || (!team.length && !!(engInitials0 || engName0));")

# ------------------------------------------------------------------ Cancel Booking v28
cx = load("cancel-booking-v27-imported.json")
by, patch = patcher(cx)
patch("Check Ownership", [
    (NOTIFY_OLD, "const engInitials0 = (title.split('/').pop() || '').trim(), engName0 = ((desc.match(/Engineer:\\s*([^(|]+)/) || [])[1] || '').trim();\n" + NOTIFY_NEW),
    ("return [{ json: { verdict:'CLEAR', event_id: ev.id, title, matched_on: how,",
     "return [{ json: { verdict:'CLEAR', event_id: ev.id, title, matched_on: how, team,   // v28: the team, for the notices"),
])
by["Build Recipients"]["parameters"]["jsCode"] = RECIPIENTS.replace("__NODE__", "Check Ownership").replace("__VERB__", "cancelled")
cx["name"] = "Jessie — Cancel Booking — v28 (everyone on it told)"
json.dump(cx, open(os.path.join(ROOT, "workflows", "cancel-booking-v28.json"), "w"), indent=2, ensure_ascii=False)
print("wrote workflows/cancel-booking-v28.json")

# ------------------------------------------------------------------ Move Booking v31
mv = load("move-booking-v30-imported.json")
by, patch = patcher(mv)
trig = by["When Executed by Another Workflow"]["parameters"]["workflowInputs"]["values"]
assert not any(v["name"] in ("new_summary", "new_details") for v in trig)
trig.extend([{"name": "new_summary"}, {"name": "new_details"}])
patch("Resolve Booking", [
    (NOTIFY_OLD, "const engInitials0 = (title.split('/').pop() || '').trim(), engName0 = ((desc.match(/Engineer:\\s*([^(|]+)/) || [])[1] || '').trim();\n" + NOTIFY_NEW),
    ("return [{ json: { verdict:'CLEAR', matched_on: how, original_id: ev.id, title,\n  description: desc,",
     """// v31: a new title and details from the Change form - the replacement gets them; the other segments (Booked by, ref,
// Notes, Type, Dept) stay the booker's
let __title = title, __desc = desc;
try {
  if (String(REQ.new_summary || '').trim()) __title = String(REQ.new_summary).trim();
  const nd = typeof REQ.new_details === 'string' ? (REQ.new_details ? JSON.parse(REQ.new_details) : null) : REQ.new_details;
  if (nd && typeof nd === 'object') {
    let segs = desc.split('|').map(s => s.trim()).filter(Boolean);
    const put = (key, val, front) => { segs = segs.filter(s => !new RegExp('^' + key + ':', 'i').test(s));
      if (String(val || '').trim()) { const seg = key + ': ' + String(val).trim(); if (front) segs.unshift(seg); else segs.push(seg); } };
    if ('Arranger' in nd) put('Arranger', nd.Arranger, true);
    if ('Engineer' in nd) put('Engineer', nd.Engineer, true);
    if ('team' in nd) put('team', nd.team, false);
    __desc = segs.join(' | ');
  }
} catch (e) { __title = title; __desc = desc; }
return [{ json: { verdict:'CLEAR', matched_on: how, original_id: ev.id, title: __title, team,   // v31: team for the notices
  description: __desc,"""),
])
patch("Check New Window", [
    ("// v28 (PENDING 102): the new day is read 8 AM - 10 PM, so a clash comes with the room's nearest free times that day\nlet __sameDay = [];",
     "// v28 (PENDING 102): the new day is read 8 AM - 10 PM, so a clash comes with the room's nearest free times that day\nlet __sameDay = [], __gaps = [];   // v31: and every free stretch"),
    ("    __sameDay = [b4, af]",
     """    // v31 (Slack 15 Oct): every free stretch that day at least the session's length (the booking being moved does not block)
    { const iv = blk.map(b => [Math.max(b.s, lo), Math.min(b.e, hi)]).filter(x => x[0] < x[1]).sort((x, y) => x[0] - y[0]);
      let cur = lo; const isoG = ms => new Date(ms + 8 * 3600000).toISOString().slice(0, 19) + '+08:00';
      for (const [a, b] of iv) { if (a - cur >= D) __gaps.push({ start: isoG(cur), end: isoG(a) }); cur = Math.max(cur, b); }
      if (hi - cur >= D) __gaps.push({ start: isoG(cur), end: isoG(hi) }); }
    __sameDay = [b4, af]"""),
    ("  return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', conflicts: clashes, same_day_slots: __sameDay,",
     "  return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', conflicts: clashes, same_day_slots: __sameDay, free_gaps: __gaps,"),
])
patch("Return Rejection", [
    ("  same_day_slots: Array.isArray(v.same_day_slots) ? v.same_day_slots : undefined,   // v28: the room's nearest free times that day",
     "  same_day_slots: Array.isArray(v.same_day_slots) ? v.same_day_slots : undefined,   // v28: the room's nearest free times that day\n"
     "  free_gaps: Array.isArray(v.free_gaps) ? v.free_gaps : undefined,   // v31: every free stretch that day"),
])
by["Build Recipients"]["parameters"]["jsCode"] = RECIPIENTS.replace("__NODE__", "Resolve Booking").replace("__VERB__", "moved")
mv["name"] = "Jessie — Move Booking — v31 (free stretches, details, everyone told)"
json.dump(mv, open(os.path.join(ROOT, "workflows", "move-booking-v31.json"), "w"), indent=2, ensure_ascii=False)
print("wrote workflows/move-booking-v31.json")
