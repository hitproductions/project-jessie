#!/usr/bin/env python3
"""Builds the calendar notes layout, 26 Oct: Book Session v122, Move Booking v37, Cancel Booking v31.

Howard (26 Oct): "for notes placement on the calendar, could we lay that out better so that's it's easy to spot? right now
it's just piled up with all the other technical info" - the event description becomes

    Engineer: … | Rooms: … | Booked by: … | ref: … | team: … | Type: … | Dept: …
    SType: Localization Dubbing

    Notes:
    <the note>

  - Book Session v122: Check Conflicts takes the "Notes: …" segment the form sends out of the technical line (final_notes);
    Create Event writes it two line breaks under the SType line, after "Notes:".
  - Move Booking v37: a change reads either layout (the note inline, as before, or the block) and writes the block; a new
    note from the Change form replaces it.
  - Cancel v31 / Move v37 (found on the way): the booking's department was read up to the next "|" - Dept is the last item on
    the line, so it took the SType line too and a Dept Head's "my department" never matched on a form booking. Read to the
    line's end now (team too).
Built on the live downloads (workflows/imported/*-imported.json).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load(f):
    return json.load(open(os.path.join(ROOT, "workflows", "imported", f)))


def node(wf, name):
    return [x for x in wf["nodes"] if x["name"] == name][0]


def sub(wf, name, a, b, n=1):
    nd = node(wf, name)
    js = nd["parameters"]["jsCode"]
    assert js.count(a) == n, (name, js.count(a), a[:80])
    nd["parameters"]["jsCode"] = js.replace(a, b)


def save(wf, out, title):
    wf["name"] = title
    with open(os.path.join(ROOT, "workflows", out), "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote workflows/" + out)


# ---- Book Session v122
bs = load("book-session-v121-imported.json")
sub(bs, "Check Conflicts", "const segs = String(REQ.description || '').split('|').map(s => s.trim()).filter(Boolean);",
    "const segs = String(REQ.description || '').split('|').map(s => s.trim()).filter(Boolean);\n"
    "// v122 (26 Oct, Howard: the note easy to spot): \"Notes: …\" leaves the technical line - Create Event writes it on its own,\n"
    "// two line breaks under the SType line (a note already in that block is kept too)\n"
    "var __notes = '';\n"
    "{ const _ni = segs.findIndex(s => /^Notes?:/i.test(s));\n"
    "  if (_ni !== -1) { const _nb = segs[_ni].match(/^Notes?:\\s*([\\s\\S]*)$/i); __notes = (_nb ? _nb[1] : '').trim(); segs.splice(_ni, 1); } }")
sub(bs, "Check Conflicts", "final_description: finalDescription,", "final_description: finalDescription, final_notes: typeof __notes === 'string' ? __notes : '' /* v122 */,", n=2)
ce = node(bs, "Create Event")
old = ce["parameters"]["additionalFields"]["description"]
assert old.endswith(" }}"), old
ce["parameters"]["additionalFields"]["description"] = old[:-3] + " + ($('Check Conflicts').first().json.final_notes ? '\\n\\nNotes:\\n' + $('Check Conflicts').first().json.final_notes : '') }}"
save(bs, "book-session-v122.json", "Jessie — Book Session — v122 (notes on their own)")

# ---- Move v37
DEPT_OLD = "bookingDept = ((desc.match(/Dept:\\s*([^|]+)/) || [])[1] || '')"
DEPT_NEW = "bookingDept = ((desc.match(/Dept:\\s*([^|\\n]+)/) || [])[1] || '')   /* v31 Cancel / v37 Move: to the line's end - not the SType line */"
TEAM_OLD = "const team = ((desc.match(/team:\\s*([^|]+)/) || [])[1] || '')"
TEAM_NEW = "const team = ((desc.match(/team:\\s*([^|\\n]+)/) || [])[1] || '')"
mv = load("move-booking-v36-imported.json")
sub(mv, "Resolve Booking", DEPT_OLD, DEPT_NEW)
sub(mv, "Resolve Booking", TEAM_OLD, TEAM_NEW)
sub(mv, "Resolve Booking", """    const _stM = desc.match(/\\n\\s*SType:\\s*([^\\n]*)\\s*$/), _desc0 = _stM ? desc.slice(0, _stM.index) : desc;   // v33: the SType line stays last
    let segs = _desc0.split('|').map(s => s.trim()).filter(Boolean);""",
    """    // v37 (26 Oct): the note's own block ("\\n\\nNotes:\\n…", Book Session v122) comes off first, then the SType line
    const _nbM = desc.match(/\\n\\s*\\n\\s*Notes?:\\s*([\\s\\S]*)$/i), _descN = _nbM ? desc.slice(0, _nbM.index) : desc;
    const _stM = _descN.match(/\\n\\s*SType:\\s*([^\\n]*)\\s*$/), _desc0 = _stM ? _descN.slice(0, _stM.index) : _descN;   // v33: the SType line after the technical line
    let segs = _desc0.split('|').map(s => s.trim()).filter(Boolean);
    let _notes = _nbM ? _nbM[1].trim() : '';
    { const _ni = segs.findIndex(s => /^Notes?:/i.test(s)); if (_ni !== -1) { if (!_notes) _notes = segs[_ni].replace(/^Notes?:\\s*/i, '').trim(); segs.splice(_ni, 1); } }   // an older booking's inline note""")
sub(mv, "Resolve Booking", "    if ('Notes' in nd) put('Notes', nd.Notes, false);   // v33: a new note from the Change form\n",
    "    if ('Notes' in nd) _notes = String(nd.Notes || '').trim() || _notes;   // v33: a new note from the Change form (v37: in its own block)\n")
sub(mv, "Resolve Booking", "    if (_st) __desc += '\\nSType: ' + _st;\n",
    "    if (_st) __desc += '\\nSType: ' + _st;\n    if (_notes) __desc += '\\n\\nNotes:\\n' + _notes;   // v37\n")
save(mv, "move-booking-v37.json", "Jessie — Move Booking — v37 (notes on their own)")

# ---- Cancel v31
cx = load("cancel-booking-v30-imported.json")
sub(cx, "Check Ownership", DEPT_OLD, DEPT_NEW)
sub(cx, "Check Ownership", TEAM_OLD, TEAM_NEW)
save(cx, "cancel-booking-v31.json", "Jessie — Cancel Booking — v31 (department read right)")
