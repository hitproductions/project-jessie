#!/usr/bin/env python3
"""Builds Slack Interactions v42 (times from 6 AM, 11:59 PM, Lobby all day) and main v281 (typed "whole day"), 22 Oct.

Howard (22 Oct):
  1. "for all time dropdowns, let's start it at 6:00 AM instead of 8:00 AM" - every Start / End list (Book a room, Change,
     the step-1 redraw) opens at 6:00 AM and runs round to 5:30 AM.
  2. "for lobby bookings, let's allow an All day option in step 1" - the Lobby is a usual room only for Event (Airtable), so
     Event gets an "All day (Lobby only)" box under What's it for? (like the M booth's). Ticked: no Start / End, and step 2
     offers only the Lobby (when it is free). Book Session books it as an all-day event, as it does an M booth's.
  3. "book studio 7 for me the whole day" did not fill in a time; "12:00AM start 12:00AM end ... technically it should be
     11:59 end". The End list's 12:00 AM is now 11:59 PM (value 23:59): 12:00 AM to 11:59 PM is the whole day, and anything
     can end at midnight (before, "The end has to be after the start"). A form still open from before sends 00:00 - read
     as 23:59. main v281: "all day / whole day / full day / entire day" typed (no times) -> an M booth or an Event (the
     Lobby) gets All day ticked; anything else 12:00 AM to 11:59 PM. Also: "for me" is no longer read as a name ("Me" as who
     it is for).
Built on workflows/slack-interactions-v41.json (the roster build, not yet imported) and the live main v280 download.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MID = "{ type: 'plain_text', text: '11:59 PM' }"

SI_REPS = [
    # 1. the lists open at 6:00 AM
    ("(8 * 60 + i * 30)", "(6 * 60 + i * 30)", 8),
    ("- 480 + 1440", "- 360 + 1440", 7),
    ("the list opening at 8:00 AM and running round to 7:30 AM", "the list opening at 6:00 AM and running round to 5:30 AM (v42)", 1),
    ("// the list's order: from 8:00 AM round", "// the list's order: from 6:00 AM round (v42)", 1),
    # 3. the End list: 11:59 PM in place of 12:00 AM - Build Step 1
    ("const timeEl = (id, o) => Object.assign({ type: 'static_select', action_id: id, placeholder: { type: 'plain_text', text: id === 'end_pick' ? 'Select an end time' : 'Select a start time' }, options: times }, o ? { initial_option: o } : {});",
     "// v42: the End list ends the day at 11:59 PM (in place of 12:00 AM) - 12:00 AM to 11:59 PM is the whole day\n"
     "const END_MID = { text: " + MID + ", value: '23:59' };\n"
     "const timeEl = (id, o) => Object.assign({ type: 'static_select', action_id: id, placeholder: { type: 'plain_text', text: id === 'end_pick' ? 'Select an end time' : 'Select a start time' }, options: id === 'end_pick' ? times.map(x => x.value === '00:00' ? END_MID : x) : times }, o ? { initial_option: o } : {});", 1),
    ("const startOpt = preS ? tOpt(preS) : null, endOpt = preE ? tOpt(preE) : null;",
     "const startOpt = preS ? tOpt(preS) : null, endOpt = preE ? (preE === '23:59' || preE === '00:00' ? END_MID : tOpt(preE)) : null;   // v42", 1),
    # the Change form (changeView, six copies)
    ("[b.s, b.e].forEach(tOpt);\n  const so = tOpt(cur.s), eo = tOpt(cur.e);",
     "const END_MID = { text: pt('11:59 PM'), value: '23:59' };   // v42: the End list ends the day at 11:59 PM\n"
     "  [b.s, b.e].filter(v => v !== '23:59').forEach(tOpt);\n"
     "  const so = tOpt(cur.s), eo = (cur.e === '23:59' || cur.e === '00:00') ? END_MID : tOpt(cur.e);", 6),
    ("action_id: 'end_pick', placeholder: pt('Select an end time'), options: times }",
     "action_id: 'end_pick', placeholder: pt('Select an end time'), options: times.map(x => x.value === '00:00' ? END_MID : x) }", 6),
    # Note Toggle's step-1 redraw
    ("const el = id => ({ type: 'static_select', action_id: id, placeholder: pt(id === 'end_pick' ? 'Select an end time' : 'Select a start time'), options: times });",
     "const el = id => ({ type: 'static_select', action_id: id, placeholder: pt(id === 'end_pick' ? 'Select an end time' : 'Select a start time'),\n"
     "      options: id === 'end_pick' ? times.map(x => x.value === '00:00' ? { text: pt('11:59 PM'), value: '23:59' } : x) : times });   // v42", 1),
    # Read Step 1: All day for Event too; an old form's 12:00 AM end is 11:59 PM
    ("  && ((v.purpose && v.purpose.purpose_pick && v.purpose.purpose_pick.selected_option && v.purpose.purpose_pick.selected_option.value) === '__booth');",
     "  && ['__booth', 'Event'].indexOf((v.purpose && v.purpose.purpose_pick && v.purpose.purpose_pick.selected_option && v.purpose.purpose_pick.selected_option.value) || '') !== -1;   // v42: an Event (the Lobby) too", 1),
    ("const t1 = allDay ? '23:59' : pickT('end', 'end_pick');",
     "const t1 = allDay ? '23:59' : (pickT('end', 'end_pick') === '00:00' ? '23:59' : pickT('end', 'end_pick'));   // v42: a 12:00 AM end is the day's end", 1),
    # 2. the Lobby's All day box
    ("const ALLDAY_BLOCK = { type: 'actions', block_id: 'allday_toggle', elements: [{ type: 'checkboxes', action_id: 'allday_toggle',\n  options: [{ text: { type: 'plain_text', text: 'All day booking' }, value: 'allday' }] }] };",
     "const ALLDAY_BLOCK = { type: 'actions', block_id: 'allday_toggle', elements: [{ type: 'checkboxes', action_id: 'allday_toggle',\n  options: [{ text: { type: 'plain_text', text: 'All day booking' }, value: 'allday' }] }] };\n"
     "// v42: an Event can be all day in the Lobby (the one room for it) - the same box, saying so\n"
     "const ALLDAY_LOBBY = { type: 'actions', block_id: 'allday_toggle', elements: [{ type: 'checkboxes', action_id: 'allday_toggle',\n  options: [{ text: { type: 'plain_text', text: 'All day (Lobby only)' }, value: 'allday' }] }] };", 3),
    ("if (purposeOpt && purposeOpt.value === '__booth') { const pi = view.blocks.findIndex(b => b.block_id === 'purpose'); view.blocks.splice(pi + 1, 0, JSON.parse(JSON.stringify(ALLDAY_BLOCK))); }",
     "if (purposeOpt && (purposeOpt.value === '__booth' || purposeOpt.value === 'Event')) {   // v42: an Event too (the Lobby); typed \"all day\" ticks it\n"
     "  const ab = JSON.parse(JSON.stringify(purposeOpt.value === 'Event' ? ALLDAY_LOBBY : ALLDAY_BLOCK));\n"
     "  if (pre.ad) { ab.elements[0].initial_options = ab.elements[0].options; view.blocks = view.blocks.filter(b => b.block_id !== 'start' && b.block_id !== 'end'); }\n"
     "  const pi = view.blocks.findIndex(b => b.block_id === 'purpose'); view.blocks.splice(pi + 1, 0, ab); }", 1),
    ("if (which === 'purpose_pick') { if (String((a.selected_option || {}).value || '') === '__booth') blocks.splice(at + 1, 0, JSON.parse(JSON.stringify(ALLDAY_BLOCK))); else ensureTimes(); }",
     "if (which === 'purpose_pick') { const pv = String((a.selected_option || {}).value || '');\n"
     "    if (pv === '__booth') blocks.splice(at + 1, 0, JSON.parse(JSON.stringify(ALLDAY_BLOCK)));\n"
     "    else { if (pv === 'Event') blocks.splice(at + 1, 0, JSON.parse(JSON.stringify(ALLDAY_LOBBY))); ensureTimes(); } }   // v42: an Event can be all day (the Lobby)", 1),
    # step 2: an all-day Event -> the Lobby only
    ("const ONLY = onlyRoom(s.purpose);   // v25: Atmos -> Studio C, Van Recording -> Studio M; nothing else offered",
     "const ONLY = (s.allDay && s.kind === 'meeting') ? 'Lobby' : onlyRoom(s.purpose);   // v25: Atmos -> Studio C, Van Recording -> Studio M; nothing else offered; v42: an all-day Event -> the Lobby", 1),
    # the form again (a DM when the window is gone) keeps All day
    ("const again = { d: s.date, s: s.allDay ? '' : s.t0, e: s.allDay ? '' : s.t1,",
     "const again = { d: s.date, s: s.allDay ? '' : s.t0, e: s.allDay ? '' : s.t1, ad: s.allDay ? 1 : 0,", 1),
]

MAIN_REPS = [
    ("P.s = bf.timeStart; P.e = bf.timeEnd; }", "P.s = bf.timeStart; P.e = bf.timeEnd; delete P.ad; }", 1),
    ("    if (P.r === 'Studio M' && !P.p) P.p = 'Van Recording';\n",
     "    if (P.r === 'Studio M' && !P.p) P.p = 'Van Recording';\n"
     "    // v281 (22 Oct): \"all day / whole day / full day\" with no times - an M booth or an Event (the Lobby) is booked all day;\n"
     "    // anything else 12:00 AM to 11:59 PM (studios and conference rooms are not all-day bookings)\n"
     "    if (/\\b(?:all|whole|full|entire)[\\s-]?day\\b/i.test(t) && !/\\bhalf[\\s-]?day\\b/i.test(t) && !(bf.timeInNewest && bf.timeStart)) {\n"
     "      if (P.r === 'Lobby' && (!P.p || (P.p === 'Meeting' && !tyNow))) P.p = 'Event';\n"
     "      if (P.p === '__booth' || P.p === 'Event') { P.ad = 1; delete P.s; delete P.e; } else { P.s = '00:00'; P.e = '23:59'; delete P.ad; }\n"
     "    }\n", 1),
    ("P.s ? fmtT(P.s) + ' – ' + fmtT(P.e) : ''].filter(Boolean).join(' · ');",
     "P.s ? fmtT(P.s) + ' – ' + fmtT(P.e) : (P.ad ? 'All day' : '')].filter(Boolean).join(' · ');   // v281", 1),    # "book studio 7 for me ..." filled "Me" as who it is for
    ("const _SF = /^(?:tomorrow|today|", "const _SF = /^(?:me|myself|us|tomorrow|today|", 1),
]
# Build Reply's Book a room under an answer ("is studio 7 free the whole day tomorrow?") - the same 12:00 AM to 11:59 PM
REPLY_REPS = [
    ("  if (rm.length === 1) P.r = rm[0];\n  if (Object.keys(P).length) bookValue = JSON.stringify(P);",
     "  if (rm.length === 1) P.r = rm[0];\n"
     "  // v281: \"the whole day\" with no times - 12:00 AM to 11:59 PM (an M booth or the Lobby: the form's All day box instead)\n"
     "  if (!P.s && /\\b(?:all|whole|full|entire)[\\s-]?day\\b/i.test(tx) && !/\\bhalf[\\s-]?day\\b/i.test(tx) && !/^(?:M[1-8]|Lobby)$/.test(String(P.r || ''))) { P.s = '00:00'; P.e = '23:59'; }\n"
     "  if (Object.keys(P).length) bookValue = JSON.stringify(P);", 1),
]


def build(src, out, name, reps, only=None):
    wf = json.load(open(os.path.join(ROOT, "workflows", src)))
    hits = [0] * len(reps)
    for n in wf["nodes"]:
        js = n.get("parameters", {}).get("jsCode")
        if not js or (only and n["name"] != only):
            continue
        for i, (a, b, _) in enumerate(reps):
            c = js.count(a)
            if c:
                js = js.replace(a, b)
                hits[i] += c
        n["parameters"]["jsCode"] = js
    bad = [(i, hits[i], r[2], r[0][:70]) for i, r in enumerate(reps) if hits[i] != r[2]]
    assert not bad, bad
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", out), "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote workflows/" + out, hits)


build("slack-interactions-v41.json", "slack-interactions-v42.json",
      "Jessie — Slack Interactions — v42 (times from 6 AM, 11:59 PM, Lobby all day)", SI_REPS)
build("imported/project-jessie-v280-imported.json", "project-jessie-v281.json",
      "Project Jessie — v281 (typed whole day)", MAIN_REPS, only="Form Offer")
build("project-jessie-v281.json", "project-jessie-v281.json", "Project Jessie — v281 (typed whole day)", REPLY_REPS, only="Build Reply")
