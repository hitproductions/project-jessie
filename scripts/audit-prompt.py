#!/usr/bin/env python3
"""Audit Jessie's system prompt for references that point at nothing.

  scripts/audit-prompt.py <main-workflow.json> <ref.json>

ref.json holds the live reference data (rooms, session types, departments,
Airtable field names, tool names, and every status code the workflows return),
built from a recent execution and the tool sub-workflows. Each check lists what
the prompt names that the live system does not have, so a stray word, a renamed
tool or a stale fact shows up without reading 29,000 characters by eye.
"""
import json, re, sys

wf, ref = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
P = [n for n in wf["nodes"] if n["name"] == "Jessie AI Agent"][0]["parameters"]["options"]["systemMessage"]
body = re.sub(r"\{\{.*?\}\}", " ", P, flags=re.S)          # data insertions are not prompt text
lines = body.splitlines()

def where(pat, flags=0):
    out, head = [], ""
    for i, l in enumerate(lines, 1):
        if l.startswith("#"): head = l.strip("# ").strip()
        for m in re.finditer(pat, l, flags):
            out.append((i, head, m.group(0), l[max(0, m.start() - 70):m.end() + 70].strip()))
    return out

def report(title, hits, note=""):
    print("\n## " + title + (" — " + note if note else ""))
    if not hits: print("   none"); return
    for i, head, word, ctx in hits: print("   line %-4d [%s]  %r\n        ...%s..." % (i, head[:40], word, ctx))

# 1. "see *X*" style references to a section that does not exist
heads = {l.strip("# ").strip().lower() for l in lines if l.startswith("#")}
secrefs = [h for h in where(r"(?:see|follow|under|in|per|→)\s+\*([^*\n]{3,60})\*")
           if re.sub(r"^(see|follow|under|in|per|→)\s+\*|\*$", "", h[2]).strip().lower() not in heads]
report("Section references with no matching heading", secrefs)

# 2. tools named in the prompt that Jessie does not have
KNOWN_TOOLISH = r"\b(Book Session|Book Series|Prepare Booking|Room Availability|Rooms and Studios|Rooms & Studios|Find Booking|Cancel Booking|Move Booking|Expand Series|List Events|Localization Projects|Session Types|Bookers|Clients|Create Event|Delete Event|Search Events|Get Events|Check Availability|Get Booker|Guard Probe|Gate Context|Booked For|Room Table)\b"
tools = set(ref["tools"]) | {"Rooms & Studios"}                       # the table's own name
internal = {"Get Booker", "Guard Probe", "Gate Context", "Booked For", "Room Table"}  # workflow nodes, not tools
report("Tools or nodes named that are not Jessie's tools",
       [h for h in where(KNOWN_TOOLISH) if h[2] not in tools and h[2] not in internal])
report("Internal node names shown to the model", [h for h in where(KNOWN_TOOLISH) if h[2] in internal],
       "not wrong, but the model never calls these")

# 3. status codes the prompt mentions that no workflow returns
report("Status codes no workflow returns",
       [h for h in where(r"\b[A-Z]{2,}(?:_[A-Z]+)+\b|\b(?:CREATED|PARTIAL|REJECTED|CANCELLED|MOVED|PREPARED)\b")
        if h[2] not in ref["codes"] and h[2] != "SYSTEM_ERROR"])

# 4. rooms that do not exist
report("Rooms named that are not in Rooms & Studios",
       [h for h in where(r"\bStudio [A-Z0-9]\b|\bM[1-9]\b|\b(?:Katha|Likha|Salin|Lobby)\b") if h[2] not in ref["rooms"]])

# 5. session types: capitalised "... Recording / Mixing / Editing / Dubbing ..." phrases not on the list
typ = [h for h in where(r"\b(?:[A-Z][a-z]+ ){0,2}(?:Recording|Mixing|Editing|Dubbing|Processing)\b")
       if h[2] not in ref["types"] and not any(t.endswith(h[2]) or h[2].endswith(t) for t in ref["types"])]
report("Session-type-like names not on the Session Types list", typ)

# 6. departments: words used as a department that are not one
DEPTISH = r"\b(Advertising|Audio Post|Video Post|Post|Localization|Loc|Music|Marketing|Finance|IT|Management|Mgmt|Business Development|BD|Sales & Accounts|S&A|People & Culture|P&C|Client Services|CS|Dubbing|Production|Sales)\b"
DEPT_ALIASES = {"Post", "Loc", "Mgmt", "BD", "S&A", "People & Culture", "P&C", "Video", "Client Services", "CS"}
report("Department-like words that are not a department (or a listed alias)",
       [h for h in where(DEPTISH) if h[2] not in ref["depts"] and h[2] not in DEPT_ALIASES])

# 7. Airtable field names in backticks that no table has
fields = set(ref["roomfields"]) | set(ref["typefields"]) | set(ref["bookerfields"]) | {
    "Name", "Importance", "Notes", "Booker Type", "Client Type",                    # Clients (PENDING 50)
    "Project Code", "Project Title", "Client Name", "Service", "Episodes"}           # Localization Projects
code_words = {"booked_for", "bookingType", "room_override", "human", "id", "recording_format", "summary",
              "status", "start", "end", "All Day", "Confirm to book. (yes/no)", "Confirm to cancel. (yes/no)",
              "Confirm to move. (yes/no)", "[SYSTEM_ERROR]", "@"}
bt = [h for h in where(r"`([^`\n]{2,40})`")
      if h[2].strip("`") not in fields and h[2].strip("`") not in code_words
      and not re.search(r"[/\-]| x |\d|\+|\(|<", h[2]) and h[2].strip("`") not in ref["codes"]]
report("Backticked names that are not a known field, input or marker", bt)

# 8. real-looking people in examples (they leak into replies - the 'Dhang' finding)
people = [h for h in where(r"\b[A-Z][a-z]+ (?:Lim|Tan|Cruz|Magno|Sigua|Reyes|Abella|Luistro|Santiago)\b|\b(?:Letty|Sasa|Jem|Dhang|Howard|Tara|Peemo|Rico|Drey|Japs)\b")]
report("Real-looking names in the prompt", people, "check each is meant to be there")
