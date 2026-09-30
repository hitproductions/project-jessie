#!/usr/bin/env python3
"""main v201 (next card + engineer fix) - live QA 30 Sep 17:04-17:07 PHT.
  scripts/build-next-card-yes.py <main-live> <main-out>

v200 held: the yes to the 2 Nov card moved 2 Nov only. Then:
1. The yes to the 9 Nov card - sent with 'Moved "QASER / HL" on ... 2 Nov ...' - got "That's already moved - nothing
   else was changed." and 9 Nov did not move. Prepared Cancel's repeated-yes check (QA bug 17) answers any yes whose
   last Jessie message starts with "Moved"; since v198 such a message can end in the next card, waiting for its yes.
   Now a message that ends in a "... Reply yes or no." card is never "already done".
2. The series summary said "*Engineer:* Howard" (the events carry "Howard Luistro (Post Engineer)"). Series summaries
   are still model-written (PENDING 59); Guard Probe now puts the staff member's full name on a series summary's
   Engineer / Arranger line when the name given is one person in Bookers (name, first name, "Goes by", initials).
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

PC_OLD = "  if (g2.saidYes === true && !d.use) {"
PC_NEW = ("  // v201: a message that ends in a card waiting for a yes is not a finished action - since v198 a series move sends\n"
          "  // 'Moved ...' with the next date's card, and its yes was answered \"That's already moved\" (30 Sep 17:07).\n"
          "  const _waits = /(?:(?:Book|Cancel|Move) it\\? Reply yes or no\\.|Confirm to (?:book|cancel|move)\\.(?:\\s*\\((?:y\\/n|yes\\/no)\\))?)\\s*$/i.test(bt);\n"
          "  if (g2.saidYes === true && !d.use && !_waits) {")

GP_ANCHOR = "  text = text.replace(/^[ \\t]*\\*?(Time|Rooms?|Session Type|Client|Project|Engineer|Arranger|Department|Booking Type)\\*?:\\*?[ \\t]*/gim, '*$1:* ');"
GP_ADD = GP_ANCHOR + r"""
// v201 (live QA 30 Sep 17:04): a series summary said "*Engineer:* Howard". It is model-written (PENDING 59); the events
// carry the full name. The Engineer / Arranger line gets the staff member's full name when what it says is one person.
if (!_prepared && /\*Dates \(\d+\):\*/.test(text)) {
  try {
    const _nz = s => String(s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9ñ]+/g, ' ').trim();
    const _st = $('All Bookers').all().map(i => (i.json && i.json.fields) || {}).filter(f => f.Name);
    const _who = v => {
      const k = _nz(String(v).replace(/\s*\([^)]*\)\s*$/, ''));
      if (!k) return '';
      const hits = _st.filter(f => { const gb = String(f.Info || '').match(/goes by\s+([^\n]*)/i);
        const keys = [_nz(f.Name), _nz(String(f.Name).split(/\s+/)[0]), _nz(f.Initials)].concat(gb ? gb[1].split(/,|\band\b/i).map(_nz) : []);
        return keys.indexOf(k) !== -1; });
      return hits.length === 1 ? String(hits[0].Name).trim() : '';
    };
    text = text.replace(/^(\*(?:Engineer|Arranger):\*[ \t]*)([^\n]+)$/gim, (m, lab, v) => { const n = _who(v); return n && _nz(n) !== _nz(v) ? lab + n : m; });
  } catch (e) {}
}"""

def fix(w):
    w["name"] = "Project Jessie — v201 (next card + engineer fix)"
    p = node(w, "Prepared Cancel")["parameters"]; p["jsCode"] = sub1(p["jsCode"], PC_OLD, PC_NEW, "prepared cancel")
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_ANCHOR, GP_ADD, "guard")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
