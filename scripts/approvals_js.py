"""Shared JavaScript for slice 2 - approvals and shared rooms (21 Oct 2026, docs/design/slice-2-approvals.md).

Imported by the builders of Jessie — Request Messages v1, Open Consent Request v12, Finalize Consent v11, Consent Sweep v3 and
Slack Interactions v37, so the same rules and wording are used everywhere.
"""

ALLOW = "['U08V3CKDGJF','U098UFMKQHZ','U08JL17A50A','U0B4S0EKSAY','U098UFLG70B','U026N6E1R','U045A3VQER3']"

# The deadlines, exactly as Open Consent Request has computed them since 25 Sep (priority: the earlier of now + 24 h and the
# start - 1 h, never before now; M booth: same day 3 h, tomorrow 10:00 AM on the day, later 24 h, never past the start).
DEADLINE_JS = r"""
function computeDeadline(now,start,cfg){const n=new Date(now).getTime();const s=new Date(start).getTime();const w=(cfg&&cfg.maxWindowH?cfg.maxWindowH:24)*3600*1000;const l=(cfg&&cfg.minLeadMin?cfg.minLeadMin:60)*60*1000;return new Date(Math.max(n,Math.min(n+w,s-l))).toISOString();}
const MNL_TZ = 8 * 3600 * 1000;
function manilaDayIndex(ms) { return Math.floor((ms + MNL_TZ) / 86400000); }
function mboothDeadline(nowISO, startISO, cfg) {
  const k = cfg || {};
  const sameDayH = k.sameDayH == null ? 3 : k.sameDayH;
  const farWindowH = k.farWindowH == null ? 24 : k.farWindowH;
  const dayBeforeHour = k.dayBeforeHour == null ? 10 : k.dayBeforeHour;
  const now = new Date(nowISO).getTime();
  const start = new Date(startISO).getTime();
  const daysAhead = manilaDayIndex(start) - manilaDayIndex(now);
  let deadline;
  if (daysAhead >= 2) deadline = now + farWindowH * 3600 * 1000;
  else if (daysAhead === 1) deadline = (manilaDayIndex(start) * 86400000 - MNL_TZ) + dayBeforeHour * 3600 * 1000;
  else deadline = now + sameDayH * 3600 * 1000;
  deadline = Math.max(now, Math.min(deadline, start));
  return new Date(deadline).toISOString();
}
function requestDeadline(kind, nowISO, startISO) {
  return String(kind || '').toUpperCase() === 'MBOOTH' ? mboothDeadline(nowISO, startISO) : computeDeadline(nowISO, startISO, { maxWindowH: 24, minLeadMin: 60 });
}
"""

# Manila date / time words shared by the messages.
TIME_JS = r"""
const _DL = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'], _ML = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const _DS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'], _MS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const _mnl = iso => new Date((/^\d{4}-\d{2}-\d{2}$/.test(String(iso || '')) ? Date.parse(iso + 'T00:00:00+08:00') : Date.parse(iso)) + 8 * 3600000);
const _ymd = iso => { const x = _mnl(iso); return isNaN(x) ? '' : x.toISOString().slice(0, 10); };
const _hm = iso => { const x = _mnl(iso); return isNaN(x) ? '' : x.toISOString().slice(11, 16); };
const _t12 = hm => { if (!hm) return ''; let [h, m] = String(hm).split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
const _dayLong = d => { const x = new Date(d + 'T12:00:00Z'); return isNaN(x) ? '' : _DL[x.getUTCDay()] + ', ' + _ML[x.getUTCMonth()] + ' ' + x.getUTCDate() + ', ' + x.getUTCFullYear(); };
const _dayShort = d => { const x = new Date(d + 'T12:00:00Z'); return isNaN(x) ? '' : _DS[x.getUTCDay()] + ', ' + _MS[x.getUTCMonth()] + ' ' + x.getUTCDate(); };
const _isAllDay = (s, e) => /^\d{4}-\d{2}-\d{2}$/.test(String(s || '')) || (_hm(s) === '00:00' && _hm(e) === '00:00');
const _times = (s, e) => _isAllDay(s, e) ? 'All day' : _t12(_hm(s)) + ' – ' + _t12(_hm(e));
const _deadlineText = iso => { const x = _mnl(iso); return isNaN(x) ? '' : _DS[x.getUTCDay()] + ', ' + _MS[x.getUTCMonth()] + ' ' + x.getUTCDate() + ', ' + _t12(x.toISOString().slice(11, 16)); };
"""

# Jessie — Request Messages: Render.
RENDER_JS = r"""// Render (Jessie — Request Messages v1, slice 2, 21 Oct): every message of a room request, written in one place.
//   mode "open": the requester's card (Requested) and the request to the booker and engineer (priority) or the booth's holder
//                (shared booth) - posted.
//   mode "end":  every message of the request updated in place to how it ended (the row's Status + extra.how / extra.by);
//                a request with no stored messages (made before slice 2) gets new ones instead.
// Called by Open Consent Request (open), Finalize Consent, Consent Sweep and Slack Interactions (end).
const T = $('When Executed by Another Workflow').first().json || {};
const mode = String(T.mode || 'open').trim().toLowerCase();
const J = x => { if (x && typeof x === 'object') return x; try { return JSON.parse(x || '{}') || {}; } catch (e) { return {}; } };
const row = J(T.row), X = J(T.extra);
const M = J(row['Messages']);
const inc = (X.inc && X.inc.id) ? X.inc : (M.inc || {});
// LAUNCH SWITCH: DEV_REDIRECT '' at launch (scripts/flip-launch-switches). During QA every request message goes to
// DEV_REDIRECT - Howard, 21 Oct: all of them, the ALLOW roster too (ALL_TO_DEV) - each marked who it is really for.
// ALL_TO_DEV does nothing once DEV_REDIRECT is ''.
const DEV_REDIRECT = 'U08V3CKDGJF';
const ALL_TO_DEV = true;
const ALLOW = __ALLOW__;
const route = id => (DEV_REDIRECT && (ALL_TO_DEV || ALLOW.indexOf(String(id)) === -1)) ? DEV_REDIRECT : id;
__TIME__
const md = t => ({ type: 'mrkdwn', text: t });
const pt = t => ({ type: 'plain_text', text: t });
const sec = t => ({ type: 'section', text: md(String(t).slice(0, 2900)) });
const ctx = t => ({ type: 'context', elements: [md(String(t).slice(0, 2900))] });
const btn = (aid, text, value, o) => Object.assign({ type: 'button', action_id: aid, text: pt(text), value: String(typeof value === 'string' ? value : JSON.stringify(value)).slice(0, 2000) }, o || {});
const confirm = (title, text, yes, no, danger) => Object.assign({ title: pt(title), text: md(String(text).slice(0, 290)), confirm: pt(yes), deny: pt(no) }, danger ? { style: 'danger' } : {});

const P = J(row['Req Payload']);
const rid = String(row['Request ID'] || '');
const isMB = String(row['Kind'] || '').toUpperCase() === 'MBOOTH';
const room = String(row['Room/Booth'] || '');
const rs = row['Req Start'], re = row['Req End'];
const day = _ymd(rs);
const when = _dayLong(day) + ' · ' + _times(rs, re);
const whenShort = _dayShort(day) + ' · ' + _times(rs, re);
const title = String(P.summary || '').trim();
const type = String(P.session_type || '').trim();
const R = { r: 'r', u: String(row['Requester'] || ''), name: String(row['Requester Name'] || '').trim() || 'Someone' };
const A1 = { r: 'a1', u: String(row['Approver'] || ''), name: String(row['Approver Name'] || '').trim() };
const A2 = { r: 'a2', u: String(row['Approver 2'] || ''), name: String(row['Approver 2 Name'] || '').trim() };
const first = n => String(n || '').trim().split(/\s+/)[0] || '';
const dl = _deadlineText(row['Deadline']);
const incWhen = inc.d ? _dayShort(inc.d) + ' · ' + (inc.s && !(inc.s === '00:00' && inc.e === '00:00') ? _t12(inc.s) + ' – ' + _t12(inc.e) : 'All day') : '';
const incTitle = String(inc.t || row['Incumbent Title'] || '').trim();
const holder = A1.name || first(String(row['Incumbent Title'] || '').replace(/^\s*M\d+\s*-\s*/i, '')) || 'the holder';
const asked = isMB ? holder + ' (their standing hold)'
  : [A1.name ? A1.name + ' (booker)' : '', A2.u && A2.u !== A1.u && A2.name ? A2.name + ' (engineer)' : ''].filter(Boolean).join(', ');
const testLine = (to, p) => to !== p.u && p.u ? [ctx('_Test: this is for ' + (p.name || p.u) + '._')] : [];
const bkv = { id: String(inc.id || row['Incumbent Event Id'] || ''), d: inc.d || '', s: inc.s || '', e: inc.e || '', r: inc.r || room, t: incTitle.slice(0, 150), st: inc.st || '' };
const pick = { d: day, s: _isAllDay(rs, re) ? '' : _hm(rs), e: _isAllDay(rs, re) ? '' : _hm(re), p: isMB ? '__booth' : type };
Object.keys(pick).forEach(k => { if (!pick[k]) delete pick[k]; });
const reqHead = '*' + title + '*\n' + when + ' · ' + room;

function requesterOpen() {
  const lines = ['⏳ *Requested – ' + room + '*', reqHead,
    isMB ? 'Asked: ' + asked + '. No answer by *' + dl + '* and it’s booked for you.'
         : 'Asked: ' + (asked || 'its booker') + ' · they have until *' + dl + '* to answer.'];
  const cleared = isMB
    ? btn('cr_attest', 'I’ve cleared it with them', { id: rid, w: 'r' }, { confirm: confirm('Cleared it with them?', holder + ' said you can use ' + room + ' then? It will be booked for you now.', 'Yes, book it', 'Not yet') })
    : btn('cr_cleared', 'I’ve cleared it with them', { id: rid, w: 'r', as: A1.u, inc: bkv });
  return [sec(lines.join('\n')), { type: 'actions', block_id: 'cra_' + rid, elements: [cleared,
    btn('cr_withdraw', 'Withdraw request', { id: rid, w: 'r' }, { confirm: confirm('Withdraw this request?', 'Nobody will be asked for ' + room + ' any more.', 'Withdraw', 'Keep it open') }),
    btn('cr_pick', 'Pick another room', pick)] }];
}
function approverOpen(p) {
  if (isMB) return [sec('🙋 *' + R.name + ' asks to use ' + room + '* · ' + whenShort + ' – during your standing hold.\n'
      + 'If you don’t need it that day, let them use it. *No answer by ' + dl + ': it’s booked for them.*'),
    { type: 'actions', block_id: 'crq_' + rid, elements: [
      btn('cr_allow', 'Let them use it', { id: rid, w: p.r }, { style: 'primary', confirm: confirm('Let ' + first(R.name) + ' use ' + room + '?', 'Your hold on ' + _dayShort(day) + ' is taken off for that day only, and ' + room + ' is booked for ' + R.name + '.', 'Let them use it', 'Not yet') }),
      btn('cr_keep', 'Keep it', { id: rid, w: p.r }, { confirm: confirm('Keep ' + room + '?', R.name + ' is told you need it.', 'Keep it', 'Not yet') })] }];
  const lines = ['🙋 *' + R.name + ' asks for ' + room + '* · ' + whenShort,
    'For *' + (type || 'a session') + '*' + (title ? ' (' + title + ')' : '') + ', which takes priority' + (inc.st ? ' over ' + inc.st : '') + '.',
    '', 'Your booking: *' + incTitle + '*' + (incWhen ? ' · ' + incWhen : ''),
    'Move it to a time or room that doesn’t clash, give it up, or keep it. Please answer by *' + dl + '* – no answer keeps your booking.'];
  return [sec(lines.join('\n')), { type: 'actions', block_id: 'crq_' + rid, elements: [
    btn('cr_move', 'Move my booking', Object.assign({}, bkv, { rid, w: p.r }), { style: 'primary' }),
    btn('cr_giveup', 'Give it up', { id: rid, w: p.r }, { confirm: confirm('Give up your booking?', '*' + incTitle + '*' + (incWhen ? ' (' + incWhen + ')' : '') + ' is cancelled and ' + room + ' booked for ' + R.name + '.', 'Give it up', 'Not yet', true) }),
    btn('cr_keep', 'Keep my booking', { id: rid, w: p.r }, { confirm: confirm('Keep your booking?', R.name + ' is told you need ' + room + ' then.', 'Keep it', 'Not yet') })] }];
}

// How it ended
const st = String(row['Status'] || '').toUpperCase();
const how = String(X.how || row['Resolved Via'] || '').toLowerCase();
const by = String(X.by || '').trim();
const ev = X.event || {};
const nav = book => ({ type: 'actions', elements: [btn('open_book', book, 'menu'), btn('my_bookings', 'My bookings', 'menu')] });
function requesterEnd() {
  if (st === 'DONE') {
    const t = String(ev.title || title), id = String(ev.id || '');
    const card = '✅ *Booked.*' + (how === 'sweep-timeout' ? ' No answer by ' + dl + ', so it’s yours.' : how === 'attestation' || how === 'cleared-gave-up' ? ''
        : isMB ? ' ' + holder + ' let you use it.' : how === 'move-hook' ? ' ' + (A1.name || 'They') + ' moved their booking.'
        : /gave-up/.test(how) ? ' ' + (by || A1.name || 'They') + ' gave it up.' : '')
      + '\n\n*' + t + '*\n*Date:* ' + _dayLong(day) + '\n*Time:* ' + _times(rs, re) + '\n*Room:* ' + room;
    const bk = { id, d: day, s: _isAllDay(rs, re) ? '' : _hm(rs), e: _isAllDay(rs, re) ? '' : _hm(re), r: room, t: t.slice(0, 150), st: type };
    const out = [{ type: 'section', block_id: 'bk_' + (id || 'new'), text: md(card) }];
    if (id) out.push({ type: 'actions', block_id: 'bka_' + id, elements: [btn('bk_change', 'Change', bk),
      btn('bk_cancel', 'Cancel', bk, { style: 'danger', confirm: confirm('Cancel this booking?', '*' + t + '*\n' + whenShort, 'Cancel booking', 'Keep it', true) })] });
    out.push(nav('Book another'));
    return out;
  }
  const lead = st === 'REJECTED' ? '❌ *' + (by || (isMB ? holder : A1.name) || 'They') + ' ' + 'is keeping ' + room + '.*'
    : st === 'EXPIRED' ? '⌛ *No answer by ' + dl + ' – ' + room + ' stays booked.*'
    : st === 'WITHDRAWN' ? '*Request withdrawn* – nothing was booked.'
    : st === 'FAILED' ? '⚠️ *Couldn’t book ' + room + ' after all*' + (X.why ? ' – ' + X.why : ' – it’s still taken then.')
    : '⏳ *Requested – ' + room + '*';
  return [sec(lead + '\n' + reqHead), { type: 'actions', elements: [btn('cr_pick', 'Pick another room', pick), btn('my_bookings', 'My bookings', 'menu')] }];
}
function approverEnd(p) {
  const head = (isMB ? '*' + R.name + ' asked to use ' + room + '*' : '*' + R.name + ' asked for ' + room + '*') + ' · ' + whenShort;
  let line;
  if (st === 'DONE') line = isMB ? (how === 'sweep-timeout' ? '⌛ No answer by ' + dl + ' – ' + room + ' was booked for ' + first(R.name) + ' that day. Your hold stays on the other days.'
      : '✓ ' + first(R.name) + ' is using ' + room + ' that day. Your hold stays on the other days.')
    : '✓ Done – ' + room + ' is ' + first(R.name) + '’s from ' + _t12(_hm(rs)) + '.' + (how === 'move-hook' ? ' Your booking was moved.' : /gave-up/.test(how) ? ' Your booking was cancelled.' : '');
  else if (st === 'REJECTED') line = '✓ ' + (by && by !== p.name ? by + ' kept it.' : 'You kept it.') + ' ' + first(R.name) + ' was told.';
  else if (st === 'EXPIRED') line = '⌛ The request ended with no answer – your booking stays.';
  else if (st === 'WITHDRAWN') line = 'Withdrawn – nothing to do.';
  else if (st === 'FAILED') line = 'The request ended – nothing changed for ' + first(R.name) + '.';
  else line = '⏳ Waiting for an answer.';
  return [sec(head), ctx(line)];
}
const textOf = (role, open) => open ? (role === 'r' ? 'Requested ' + room + ' · ' + whenShort : R.name + ' asks for ' + room + ' · ' + whenShort)
  : (role === 'r' ? (st === 'DONE' ? 'Booked ' + room + ' · ' + whenShort : 'Your request for ' + room + ': ' + st.toLowerCase()) : 'The request for ' + room + ' ended');

const people = [R, A1].concat(!isMB && A2.u && A2.u !== A1.u ? [A2] : []);
const out = [];
if (mode === 'open') {
  for (const p of people) { if (!p.u) continue; const to = route(p.u);
    out.push({ op: 'post', r: p.r, u: p.u, channel: to, text: textOf(p.r, true), blocks: (p.r === 'r' ? requesterOpen() : approverOpen(p)).concat(testLine(to, p)) }); }
} else {
  const stored = Array.isArray(M.m) ? M.m.filter(x => x && x.c && x.t) : [];
  if (stored.length) for (const m of stored) { const p = people.find(x => x.r === m.r) || { r: m.r, u: m.u, name: '' }; const to = route(p.u);
    out.push({ op: 'update', r: m.r, u: m.u, channel: m.c, ts: m.t, text: textOf(m.r, false), blocks: (m.r === 'r' ? requesterEnd() : approverEnd(p)).concat(testLine(to, p)) }); }
  else for (const p of people) { if (!p.u) continue; const to = route(p.u);   // a request from before slice 2: new messages
    out.push({ op: 'post', r: p.r, u: p.u, channel: to, text: textOf(p.r, false), blocks: (p.r === 'r' ? requesterEnd() : approverEnd(p)).concat(testLine(to, p)) }); }
}
return out.map(x => ({ json: x }));
""".replace("__ALLOW__", ALLOW).replace("__TIME__", TIME_JS)

COLLECT_JS = r"""// Collect: where each message went (channel + ts), so the request's messages can be updated when it ends.
const sent = $('Render').all().map(i => i.json || {});
const res = $input.all().map(i => i.json || {});
const m = sent.map((x, i) => ({ r: x.r, u: x.u, c: (res[i] || {}).channel || x.channel, t: (res[i] || {}).ts || x.ts || '', ok: (res[i] || {}).ok === true,
  error: (res[i] || {}).error || '' }));
return [{ json: { messages: m.filter(x => x.ok && x.t).map(x => ({ r: x.r, u: x.u, c: x.c, t: x.t })), sent: m.length,
  failed: m.filter(x => !x.ok).map(x => x.r + ': ' + (x.error || 'not sent')) } }];
"""

# Slack Interactions v37: the rooms a request can be made for, and the line under one picked. Wrapped in one object so its
# names never clash with the node's own (several nodes already define _DS, _t12, ...).
ASK_JS = r"""
// v37 (slice 2): "Booked – ask to use" - the booked rooms a request can be made for, worked out with Book Session's own rules
// (Decide Preempt): a shared booth - an M booth whose only bookings then are standing (recurring) holds, not yours; a priority
// request - you are a Dept Head / Client Booking / HAIST Dev, one booking is in the way, it is not yours, and its booking type's
// Preemption Rank (Airtable Session Types) is lower than this one's. Only rooms that normally do this booking type (a request
// is never booked with room_override - that would also ignore a standing hold). Not for a series (decided 21 Oct).
const ASK = (() => {
__TIME__
__DEADLINE__
  const nt = x => String(x == null ? '' : x).trim().toLowerCase().replace(/\s+/g, ' ');
  function rooms(ra, data, s, fits) {
    if (!ra || ra.status !== 'OK' || !Array.isArray(ra.busy_detail) || (s.series && (s.series.dates || []).length > 1)) return [];
    const ranks = {}; for (const r of (data && data.sessionTypes) || []) { const f = r.fields || {}; const n = Number(f['Preemption Rank']); if (f.Type && Number.isFinite(n)) ranks[nt(f.Type)] = n; }
    const me = ((data && data.bookers) || []).map(b => b.fields || {}).find(f => String(f['Slack User ID'] || '').split(/[\s,]+/).indexOf(String(s.requester || '')) !== -1) || {};
    const auth = /(dept head|client booking|haist dev)/i.test([].concat(me.Authority || []).map(a => (a && a.name) || a).join(', '));
    const rq = s.kind === 'booth' ? 0 : (Number.isFinite(ranks[nt(s.purpose)]) ? ranks[nt(s.purpose)] : 0);
    const out = [];
    for (const d of ra.busy_detail) {
      const room = String(d.room || ''), evs = [].concat(d.events || []);
      if (!room || !evs.length || !fits(room)) continue;
      if (/^M\d+$/i.test(room)) {
        const holds = evs.filter(e => e.recurring), non = evs.filter(e => !e.recurring);
        if (holds.length) { if (non.length) continue;
          const h = holds.find(e => e.ref); if (!h || h.ref === s.requester) continue;
          const who = (String(h.title || '').match(/^\s*M\d+\s*-\s*(.+?)\s*$/i) || [])[1] || 'someone';
          out.push({ k: 'M', room, text: (room + ' · ' + who + '’s standing hold').slice(0, 75) }); continue; }
      }
      if (!auth || evs.length !== 1) continue;
      const e = evs[0], ib = ranks[nt(e.stype)];
      if (!e.ref || e.ref === s.requester || !Number.isFinite(ib) || !(rq > ib)) continue;
      out.push({ k: 'P', room, text: (room + ' · ' + e.stype + ', ' + (e.allDay ? 'all day' : _t12(_hm(e.start)) + '–' + _t12(_hm(e.end)))).slice(0, 75) });
    }
    return out.slice(0, 20);
  }
  const value = a => ('ask:' + a.k + '|' + a.room).slice(0, 150);
  const parse = v => { const m = String(v || '').match(/^ask:([PM])\|(.+)$/); return m ? { k: m[1], room: m[2] } : null; };
  function line(k, room, info, m) {
    const start = String(m.date || '') + 'T' + (m.allDay ? '00:00' : String(m.t0 || '00:00')) + ':00+08:00';
    const dl = _deadlineText(requestDeadline(k === 'M' ? 'MBOOTH' : 'PREEMPT', new Date().toISOString(), start));
    return k === 'M' ? '🔒 *' + room + ' is held then*' + (info ? ' (' + info + ')' : '') + '. Jessie will ask them – no answer by *' + dl + '* and it’s booked for you.'
      : '🔒 *' + room + ' is booked then*' + (info ? ' (' + info + ')' : '') + '. Jessie will ask its booker and engineer – they have until *' + dl + '* to answer. No answer keeps their booking.';
  }
  return { rooms, value, parse, line };
})();
""".replace("__TIME__", TIME_JS).replace("__DEADLINE__", DEADLINE_JS)
