#!/usr/bin/env python3
"""main v223 (availability times from the requester) - live 6 Oct 14:46 PHT on main v222 (PENDING 88): after "post", Jessie
asked "The end time needs to be after the start time. Did you mean 10:00 AM to 12:00 PM, or 10:00 PM to midnight?" for
"10-12pm". Booked For reads 10:00-12:00 and Book Session / Prepare Booking times are corrected from it (v167), but Room
Availability's window was not - so a model guess of 10 PM-12 PM came back as a bad window.
  Room Availability's window_start / window_end now get the same correction as Book Session (Booked For's timeStart /
  timeEnd replace the model's time unless the model's time is one the requester typed), only for a timed window on one
  day - a whole-day check ("what's free tomorrow", 00:00-23:59) is left alone. The date pin (v213) still runs first.
  scripts/build-ra-time.py <main-v222> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
WRAP = ("={{ ((b, v, k) => { try { const s = String(v || ''); const m = s.match(/^(\\d{4}-\\d{2}-\\d{2})T(\\d{2}):(\\d{2})/); const t = b[k]; "
        "if (!t || !b.timeStart || !b.timeEnd || !m) return v; "
        "if ((k === 'timeStart' && m[2] + ':' + m[3] === '00:00') || (k === 'timeEnd' && /^23:|^00:00/.test(m[2] + ':' + m[3]))) return v; "   # whole-day window
        "return (!b.timeForced && [].concat(b.timesMentioned || []).includes(m[2] + ':' + m[3])) ? v : m[1] + 'T' + t + ':00+08:00'; } catch (x) { return v; } })"
        "(($('Booked For').first().json || {}), (%s), '%s') }}")
def main(w):
    w["name"] = "Project Jessie — v223 (availability times)"
    v = node(w, "Room Availability")["parameters"]["workflowInputs"]["value"]
    for k, bk in (("start_iso", "timeStart"), ("end_iso", "timeEnd")):
        e = v[k]
        assert e.startswith("={{ ") and e.endswith(" }}"), k
        v[k] = WRAP % (e[4:-3], bk)
    return w
if __name__ == "__main__":
    json.dump(main(json.load(open(sys.argv[1]))), open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
