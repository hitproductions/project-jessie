#!/usr/bin/env python3
"""Builds the 20 Nov round (Howard):

1. Slack Interactions v82 - "What's it for?" (Build Step 1): the group that was last, "Other bookings", is first and is called
   "Bookings", in the order M booth, Meeting, Event; the session types ("Sessions") after it.
2. **Post Processing is renamed Multimedia Post** (Airtable Session Types, done 20 Nov). **Post Mixing is unchanged.** Everything
   that reads the types from Airtable followed on its own; every rule written in code for Post Processing now holds for Multimedia
   Post (and still for "Post Processing", which older bookings and calendar titles carry):
   - Studio E only for it; its own form fields (Booker, Who is it for?) and title; no client lookups; department **Marketing**
     (Howard: its Airtable role, Multimedia Specialist, now maps to Marketing - before, it mapped to nothing and the booking had no
     department; Book Session's type list moves it from Audio Post to Marketing);
     the Lavender colour; "Studio E is only for Multimedia Post." - Slack Interactions v82, Book Session v131, Move v45,
     Book Series v12, Room Check v3, main v295.
   - New calendar titles read "MULTIMEDIA POST - <PROJECT> / <who>"; "POST PROCESSING - ..." titles are still read, and a change to
     one keeps its "POST PROCESSING" prefix (an untouched Change stays "Nothing changed").
   - main v295: the Session Types tool's list for the AI says Multimedia Post; a typed "post processing" finds Multimedia Post;
     Studio E typed with no type -> Multimedia Post.
Built on the live builds: slack-interactions-v81, project-jessie-v294, book-session-v130, move-booking-v44, book-series-v11,
room-check-v2.
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RULES = [   # (old, new) on every Code node's text - each must hit at least once in the workflows it is meant for
    ("/^post processing$/i", "/^(?:post processing|multimedia post)$/i"),
    ("POST PROCESSING\\s+-", "(?:POST PROCESSING|MULTIMEDIA POST)\\s+-"),
    ("'POST PROCESSING - '", "'MULTIMEDIA POST - '"),
    ("X[k] === String(t || '').trim().toLowerCase(); }", "X[k] === String(t || '').trim().toLowerCase().replace(/^multimedia post$/, 'post processing'); }"),
    ("if (t === 'post processing') return '1';", "if (t === 'post processing' || t === 'multimedia post') return '1';"),
    ("'Studio E is only for Post Processing. Nothing was booked.'", "'Studio E is only for Multimedia Post. Nothing was booked.'"),
    ("/^(localization|qc|post processing|meeting|event)\\b/i", "/^(localization|qc|post processing|multimedia post|meeting|event)\\b/i"),
    ("P.p = 'Post Processing';", "P.p = 'Multimedia Post';"),
    ("again.p = again.p || 'Post Processing';", "again.p = again.p || 'Multimedia Post';"),
    # Multimedia Post is Marketing (Howard, 20 Nov) - its Airtable role is Multimedia Specialist (Dilan, Marketing)
    ("'audio post': ['VO Recording', 'Post Mixing', 'Post Processing', 'Celebrity Recording', 'Atmos Mixing'],",
     "'audio post': ['VO Recording', 'Post Mixing', 'Celebrity Recording', 'Atmos Mixing'], 'marketing': ['Multimedia Post', 'Post Processing'],"),
    ("'music arranger': 'Music' }", "'music arranger': 'Music', 'multimedia specialist': 'Marketing' }"),
    ("  'music':        ['music engineer', 'music arranger']\n};", "  'music':        ['music engineer', 'music arranger'],\n  'marketing':    ['multimedia specialist']\n};"),
    ("'localization': /loc(?:alization)? engineer/i })", "'localization': /loc(?:alization)? engineer/i, 'marketing': /multimedia specialist/i })"),
]


def load(f):
    return json.load(open(os.path.join(ROOT, "workflows", f)))


def save(wf, f, name):
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", f), "w") as fh:
        json.dump(wf, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("wrote workflows/" + f, len(wf["nodes"]), "nodes")


def node(wf, n):
    return [x for x in wf["nodes"] if x["name"] == n][0]


def code_refs(wf):   # Post Processing in code (not // comments), outside the accept-both forms
    out = []
    for n in wf["nodes"]:
        c = n["parameters"].get("jsCode", "")
        for line in c.split("\n"):
            code = line.split("//")[0] if "//" in line and "://" not in line else line
            code = code.replace("post processing|multimedia post", "").replace("POST PROCESSING|MULTIMEDIA POST", "") \
                       .replace("'post processing' || t === 'multimedia post'", "").replace("replace(/^multimedia post$/, 'post processing')", "") \
                       .replace("|post processing|multimedia post|", "").replace("'Multimedia Post', 'Post Processing'", "") \
                       .replace("'studio e': 'post processing'", "")   # roomAllowed's map - its comparison reads Multimedia Post as it (checked below)
            if re.search(r"(?i)post[ _-]?processing", code):
                out.append(n["name"] + ": " + line.strip()[:160])
    return out


def rename(src, dst, title):
    wf = load(src)
    pm_before = json.dumps(wf).count("Post Mixing") + json.dumps(wf).lower().count("post mixing")
    hits = 0
    for n in wf["nodes"]:
        p = n["parameters"]
        if "jsCode" in p:
            for old, new in RULES:
                k = p["jsCode"].count(old)
                if k:
                    hits += k
                    p["jsCode"] = p["jsCode"].replace(old, new)
    for n in wf["nodes"]:   # every roomAllowed map must sit with the comparison that maps Multimedia Post onto it
        c = n["parameters"].get("jsCode", "")
        assert c.count("'studio e': 'post processing'") == c.count("replace(/^multimedia post$/, 'post processing')"), (src, n["name"], "roomAllowed")
    left = code_refs(wf)
    assert not left, (src, left)
    pm_after = json.dumps(wf).count("Post Mixing") + json.dumps(wf).lower().count("post mixing")
    assert pm_before == pm_after, (src, "Post Mixing changed", pm_before, pm_after)
    print(src, "->", dst, ":", hits, "rewrites; Post Mixing references kept:", pm_after // 2 if pm_after else 0)
    return wf


# ---- Slack Interactions v82
si = rename("slack-interactions-v81.json", "slack-interactions-v82.json", "")
p = node(si, "Build Step 1")["parameters"]
OLD = ("const groups = [];\n"
       "if (sessions.length) groups.push({ label: { type: 'plain_text', text: 'Sessions' }, options: sessions.slice(0, 100).map(t => opt(t)) });\n"
       "groups.push({ label: { type: 'plain_text', text: 'Other bookings' },\n"
       "  options: NOT_SESSION.filter(t => types.indexOf(t) !== -1).map(t => opt(t)).concat([opt('M booth', '__booth')]) });\n")
assert p["jsCode"].count(OLD) == 1
p["jsCode"] = p["jsCode"].replace(OLD,
    "const groups = [];\n"
    "// v82 (Howard, 20 Nov): \"Bookings\" first - M booth, Meeting, Event - then the session types\n"
    "groups.push({ label: { type: 'plain_text', text: 'Bookings' },\n"
    "  options: [opt('M booth', '__booth')].concat(['Meeting', 'Event'].filter(t => types.indexOf(t) !== -1).map(t => opt(t))) });\n"
    "if (sessions.length) groups.push({ label: { type: 'plain_text', text: 'Sessions' }, options: sessions.slice(0, 100).map(t => opt(t)) });\n")
# a change keeps an existing booking's own prefix ("POST PROCESSING - ..." stays, so an untouched Change is still "Nothing changed")
_n = 0
for n in si["nodes"]:
    c = n["parameters"].get("jsCode", "")
    OLDT = "if (_who) return 'MULTIMEDIA POST - ' + (_pj ? _pj + ' / ' : '') + _who; }"
    if OLDT in c:
        _n += c.count(OLDT)
        n["parameters"]["jsCode"] = c.replace(OLDT, "if (_who) return (/^\\s*POST PROCESSING\\s+-/i.test(String((b && b.t) || '')) ? 'POST PROCESSING - ' : 'MULTIMEDIA POST - ') + (_pj ? _pj + ' / ' : '') + _who; }   // v82: an existing booking keeps its prefix")
assert _n == 6, _n
save(si, "slack-interactions-v82.json", "Jessie — Slack Interactions — v82 (Bookings first, Multimedia Post)")

# ---- main v295
mn = rename("project-jessie-v294.json", "project-jessie-v295.json", "")
st = node(mn, "Session Types")["parameters"]
s = json.dumps(st, ensure_ascii=False)
assert s.count("Music Recording, Post Mixing, Post Processing, QC") == 1 and s.count("Meeting, Music Arranging") == 1
node(mn, "Session Types")["parameters"] = json.loads(s.replace("Music Recording, Post Mixing, Post Processing, QC", "Music Recording, Post Mixing, QC")
                                                      .replace("Meeting, Music Arranging", "Meeting, Multimedia Post, Music Arranging"))
fo = node(mn, "Form Offer")["parameters"]
OLD = "    const typeIn = s => {\n      let best = '';\n"
assert fo["jsCode"].count(OLD) == 1
fo["jsCode"] = fo["jsCode"].replace(OLD, OLD +
    "      // v295 (20 Nov): Post Processing is Multimedia Post - a typed \"post processing\" still finds it\n"
    "      if (TYPES.indexOf('Multimedia Post') !== -1 && TYPES.indexOf('Post Processing') === -1) s = String(s).replace(/\\bpost[\\s-]*processing\\b/gi, 'Multimedia Post');\n")
save(mn, "project-jessie-v295.json", "Project Jessie — v295 (Multimedia Post)")

# ---- the sub-workflows
save(rename("book-session-v130.json", "book-session-v131.json", ""), "book-session-v131.json", "Jessie — Book Session — v131 (Multimedia Post)")
save(rename("move-booking-v44.json", "move-booking-v45.json", ""), "move-booking-v45.json", "Jessie — Move Booking — v45 (Multimedia Post)")
save(rename("book-series-v11.json", "book-series-v12.json", ""), "book-series-v12.json", "Jessie — Book Series — v12 (Multimedia Post)")
save(rename("room-check-v2.json", "room-check-v3.json", ""), "room-check-v3.json", "Jessie — Room Check — v3 (Multimedia Post)")

# ---- the colour rule's source
cp = os.path.join(ROOT, "scripts", "jessie_colour.py")
c = open(cp).read()
if "multimedia post" not in c:
    assert c.count("if t == 'post processing'") + c.count("if (t === 'post processing') return '1';") >= 1, "colour rule not found"
    c = c.replace("if (t === 'post processing') return '1';", "if (t === 'post processing' || t === 'multimedia post') return '1';")
    open(cp, "w").write(c)
