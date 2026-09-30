#!/usr/bin/env python3
"""main v200 (approved move fix) - live QA 30 Sep 16:56 PHT.
  scripts/build-approved-move.py <main-live> <main-out>

v199: after "all", the first series card was right (2 Nov, written by code, "_Next: ... November 9"). At the yes the
model was told "move that date only, once" - and moved both dates again, as on v198 ("Moved both sessions ..."), and
the 9 Nov card that followed still showed 10-12 although 9 Nov had just moved. Telling the model does not hold.

Every move card is code-written now (Move Booking v25's, and Guard Probe's series cards), so at the yes the move is
what the card showed, as a booking is what its summary showed (Prepared Booking) and a cancel is its card: Booked For
reads the last card from Jessie's message - title, current date, new date and times, new room - and Move Booking's
title / booking_date / new_start_iso / new_end_iso / new_rooms take those, whatever the model passes. A second call
in the same turn gets the same card, so no other date can move. On a series, the reply is written by code too:
'Moved "TITLE" on DATE to TIME.' and the next card.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

BF_ANCHOR = "      let __serPick = false;"
BF_BLOCK = r"""      // v200: a yes to a move card - the move is what the card showed. Read the LAST card in Jessie's newest message
      // (a Move Booking card, or a series card sent with "Moved ..."); Move Booking takes these over the model's values.
      try {
        const _lb = theirs.length ? String(theirs[0] || '') : String(__movedText || '');
        if (YES_RE.test(String(mine[0] || '')) && /(?:Move it\? Reply yes or no\.|Confirm to move\.)\s*$/i.test(_lb.trim()) && _lb.lastIndexOf('*Now:*') !== -1) {
          const _c = _lb.slice(_lb.lastIndexOf('\n*', _lb.lastIndexOf('*Now:*') - 2) + 1);
          const _MN2 = ['january','february','march','april','may','june','july','august','september','october','november','december'];
          const _pl = s => String(s || '').trim().match(/^(?:[A-Za-z]+day,\s*)?([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4}),\s*(\d{1,2}):(\d{2})\s*([AP]M)\s*[–-]\s*(\d{1,2}):(\d{2})\s*([AP]M)(?:,\s*(.+))?$/i);
          const _h = (h, mi, ap) => { let x = +h % 12; if (/p/i.test(ap)) x += 12; return String(x).padStart(2, '0') + ':' + mi; };
          const _ti3 = ((_c.match(/^\s*\*([^*\n]+)\*\s*$/m) || [])[1] || '').trim();
          const _nl = (_c.match(/\*Now:\*\s*([^\n]+)/) || [])[1], _ml = (_c.match(/\*Moving to:\*\s*([^\n]+)/) || [])[1];
          const _n3 = _pl(_nl), _m3 = _pl(_ml);
          const _d3 = m => m && _MN2.indexOf(m[1].toLowerCase()) !== -1 ? m[3] + '-' + String(_MN2.indexOf(m[1].toLowerCase()) + 1).padStart(2, '0') + '-' + String(+m[2]).padStart(2, '0') : '';
          if (_ti3 && _n3 && _m3 && _d3(_n3) && _d3(_m3)) {
            const _r0 = String(_n3[10] || '').trim(), _r1 = String(_m3[10] || '').trim();
            out.approvedMove = { title: _ti3, booking_date: _d3(_n3),
              new_start_iso: _d3(_m3) + 'T' + _h(_m3[4], _m3[5], _m3[6]) + ':00+08:00', new_end_iso: _d3(_m3) + 'T' + _h(_m3[7], _m3[8], _m3[9]) + ':00+08:00',
              new_rooms: (_r1 && _r1.toLowerCase() !== _r0.toLowerCase()) ? _r1 : '',
              date_label: String(_nl).trim().split(/,\s*\d{1,2}:\d{2}/)[0], to_label: _m3[4] + ':' + _m3[5] + ' ' + _m3[6].toUpperCase() + ' – ' + _m3[7] + ':' + _m3[8] + ' ' + _m3[9].toUpperCase() };
          }
        }
      } catch (e) {}
"""

GP_OLD = """    if (_bf8.seriesNextCard && _moved8 && !/Move it\\? Reply yes or no\\.\\s*$/i.test(text))
      text = text.trim() + '\\n\\n' + String(_bf8.seriesNextCard);"""
GP_NEW = """    // v200: the reply is written here too - the model wrote "Moved both sessions ..." after one approved move
    const _am8 = _bf8.approvedMove || {};
    if (_bf8.seriesNextCard && _moved8 && _am8.title && _am8.date_label && _am8.to_label)
      text = 'Moved "' + _am8.title + '" on ' + _am8.date_label + ' to ' + _am8.to_label + '.';
    if (_bf8.seriesNextCard && _moved8 && !/Move it\\? Reply yes or no\\.\\s*$/i.test(text))
      text = text.trim() + '\\n\\n' + String(_bf8.seriesNextCard);"""

def wrap_input(v, key):
    # ={{ EXPR }} -> ={{ ((a, v) => (a && a.KEY && GATE) ? a.KEY : v)(BF.approvedMove, EXPR) }}
    assert v.startswith("={{ ") and v.endswith(" }}"), key
    inner = v[4:-3]
    return ("={{ ((a, v) => (a && $('Gate Context').first().json.confirmedMove === true && typeof a." + key + " === 'string'"
            + (" && a." + key if key != "new_rooms" else "") + ") ? a." + key + " : v)(($('Booked For').first().json || {}).approvedMove, " + inner + ") }}")

def fix(w):
    w["name"] = "Project Jessie — v200 (approved move fix)"
    b = node(w, "Booked For")["parameters"]; b["jsCode"] = sub1(b["jsCode"], BF_ANCHOR, BF_BLOCK + BF_ANCHOR, "bf")
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_OLD, GP_NEW, "gp")
    v = node(w, "Move Booking")["parameters"]["workflowInputs"]["value"]
    for k in ("title", "booking_date", "new_start_iso", "new_end_iso", "new_rooms"):
        v[k] = wrap_input(v[k], k)
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
