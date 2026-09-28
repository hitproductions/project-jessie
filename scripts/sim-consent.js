#!/usr/bin/env node
// Offline tests for the consent rebuild (main v176, Open v11, Finalize v10, Sweep v2, Book Session v57, Move v25).
//
//   node scripts/sim-consent.js <book-session-execution.json>
//
// Finalize and Sweep are EXECUTED node by node by a small n8n-like runner (code, if, and mocked googleSheets /
// httpRequest / executeWorkflow / slack nodes, with onError, alwaysOutputData and executeOnce honoured), against a
// fake Consent Requests sheet and a fake calendar - so a failed delete, a failed booking, a failed status write or a
// second run can be injected and the resulting sheet, calendar and messages checked. Nothing live is touched.
const fs = require('fs'), path = require('path');
const WF = f => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'workflows', f)));
const M = WF('project-jessie-v176.json'), O = WF('open-consent-request-v11.json'), F = process.env.FIN ? JSON.parse(fs.readFileSync(process.env.FIN)) : WF('finalize-consent-v10.json'),
      S = WF('consent-sweep-v2.json'), B = WF('book-session-v57.json'), B56 = WF('book-session-v56.json'), MV = WF('move-booking-v25.json');
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const node = (w, n) => w.nodes.find(x => x.name === n);
const AsyncFn = Object.getPrototypeOf(async function () {}).constructor;
const wrap = it => ({ first: () => { if (!it.length) throw new Error('no items'); return it[0]; }, last: () => it[it.length - 1], all: () => it, item: it[0] });

// ------------------------------------------------------------ a tiny n8n runner
async function runWorkflow(w, startNode, startItems, env) {
  const out = {}, order = [];
  const $ = n => { if (!out[n]) throw new Error('Referenced node is unexecuted: ' + n); return wrap(out[n]); };
  const expr = (v, item) => {
    if (typeof v !== 'string' || !v.startsWith('=')) return v;
    const body = v.slice(1), whole = /^\{\{([\s\S]*)\}\}$/.exec(body.trim());
    const ev = e => new Function('$', '$json', '$input', 'return (' + e + ');')($, (item && item.json) || {}, wrap([item]));
    return whole ? ev(whole[1]) : body.replace(/\{\{([\s\S]*?)\}\}/g, (m, e) => String(ev(e)));
  };
  const deep = (o, item) => Array.isArray(o) ? o.map(x => deep(x, item)) : (o && typeof o === 'object') ? Object.fromEntries(Object.entries(o).map(([k, x]) => [k, deep(x, item)])) : expr(o, item);
  async function exec(name, items) {
    const n = node(w, name); if (!n) throw new Error('no node ' + name);
    if (n.executeOnce) items = items.slice(0, 1);
    let branches;
    const perItem = async fn => { const r = []; for (const it of items) { try { r.push(...await fn(it)); } catch (e) { if (n.onError === 'continueRegularOutput') r.push({ json: { error: { message: String(e.message || e) } } }); else throw new Error(name + ': ' + e.message); } } return r; };
    const t = n.type.split('.').pop();
    if (t === 'code') {
      let r; try { r = await new AsyncFn('$input', '$', '$json', n.parameters.jsCode)(wrap(items), $, (items[0] || {}).json || {}); }
      catch (e) { if (n.onError === 'continueRegularOutput') r = [{ json: { error: { message: e.message } } }]; else throw new Error(name + ': ' + e.message); }
      branches = [r || []];
    } else if (t === 'if') {
      const T = [], Fb = [];
      for (const it of items) { const c = n.parameters.conditions.conditions[0]; const l = expr(c.leftValue, it);
        const pass_ = c.operator.operation === 'true' ? l === true : String(l) === String(c.rightValue); (pass_ ? T : Fb).push(it); }
      branches = [T, Fb];
    } else if (t === 'googleSheets') {
      const op = n.parameters.operation || 'read';
      if (op === 'read' || op === undefined) { if (env.failRead && env.failRead(name)) throw new Error(name + ': sheet read failed'); const src = (env.readFor && env.readFor(name)) || env.sheet; branches = [src.map(r => ({ json: { ...r } }))]; }
      else branches = [await perItem(async it => { if (env.failWrite && env.failWrite(name, it.json)) throw new Error('sheet write failed');
        const r = env.sheet.find(x => x['Request ID'] === it.json['Request ID']); if (r) Object.assign(r, it.json); env.writes.push({ node: name, ...it.json }); return [{ json: { ...(r || it.json) } }]; })];
    } else if (t === 'httpRequest') {
      branches = [await perItem(async it => { const p = deep(n.parameters, it); return [{ json: await env.http(name, p.method || 'GET', p.url, p.jsonBody) }]; })];
    } else if (t === 'executeWorkflow') {
      branches = [await perItem(async it => { const v = deep(n.parameters.workflowInputs.value, it); return [{ json: await env.sub(name, v) }]; })];
    } else if (t === 'slack') {
      branches = [await perItem(async it => { const p = deep(n.parameters, it); env.msgs.push({ to: (p.channelId || p.user || {}).value, text: p.text }); return [{ json: { ok: true } }]; })];
    } else if (t === 'executeWorkflowTrigger' || t === 'scheduleTrigger' || t === 'manualTrigger') { branches = [items];
    } else throw new Error('runner: unsupported node type ' + t);
    if (n.alwaysOutputData && !(branches[0] || []).length) branches[0] = [{ json: {} }];
    out[name] = branches.flat().length ? branches.find(b => b.length) : []; order.push(name);
    const conns = (w.connections[name] || {}).main || [];
    for (let i = 0; i < conns.length; i++) { const its = branches[i] || []; if (!its.length) continue; for (const c of conns[i]) await exec(c.node, its); }
  }
  await exec(startNode, startItems);
  return { out, order };
}

// ------------------------------------------------------------ fakes
const HOLD = 'jmuq10se2757bdh88rqock5i8c_20271006T160000Z';
const payload = { summary: 'M1 - Howard', start_iso: '2027-10-07T10:00:00+08:00', end_iso: '2027-10-07T12:00:00+08:00', rooms: 'M1',
  description: 'Booked by: Howard Luistro | ref: UHOW', session_type: '', client: '', department: 'Localization', engineer: '', bookingType: '', all_day: false, reference_data: '' };
const row = over => ({ 'Request ID': '20271001090000-UHOW', 'Status': 'PENDING', 'Kind': 'MBOOTH', 'Requester': 'UHOW', 'Requester Name': 'Howard Luistro',
  'Approver': 'URICO', 'Approver Name': 'Rico', 'Room/Booth': 'M1', 'Req Start': '2027-10-07T10:00:00+08:00', 'Req End': '2027-10-07T12:00:00+08:00',
  'Incumbent Event Id': HOLD, 'Incumbent Title': 'M1 - Rico', 'Deadline': '2099-01-01T00:00:00Z', 'Req Payload': JSON.stringify(payload),
  'Decision': '', 'Decision At': '', 'Placement Event Id': '', ...over });
// The fake calendar: the standing hold (transparent unless told otherwise) and our bookings. Book Session is
// modelled on the real one: a clash with an event that is not the excluded hold is ROOM_OCCUPIED (and names our own
// consent booking when that is the clash); an opaque hold makes the booth decline, leaving a declined event behind.
function env(opts = {}) {
  const cal = { hold: { id: HOLD, status: 'confirmed', transparency: opts.opaque ? 'opaque' : 'transparent' }, bookings: [] };
  const e = { sheet: opts.rows || [row(opts.row || {})], writes: [], msgs: [], calls: [], cal, failWrite: opts.failWrite, readFor: opts.readFor,
    async http(name, method, url) {
      e.calls.push(name + ' ' + method + ' ' + decodeURIComponent(url.split('/events/')[1] || ''));
      const id = decodeURIComponent(url.split('/events/')[1] || ''); const b = cal.bookings.find(x => x.id === id);
      if (opts.httpFail && opts.httpFail(name, method)) throw new Error('HTTP 500 backend error');
      if (id === HOLD) throw new Error('test: the hold must never be touched');
      if (!b) throw new Error('The resource you are requesting could not be found (404)');
      if (method === 'DELETE') { b.status = 'cancelled'; return {}; }
      return { ...b };
    },
    async sub(name, v) {
      e.calls.push(name + ' exclude=' + (v.exclude_event_id || ''));
      if (opts.bookResult) { const r = opts.bookResult(v, cal); if (r) return r; }
      const tag = (String(v.description || '').match(/consent: (\S+)/) || [])[1];
      const mine = cal.bookings.find(b => b.status !== 'cancelled' && tag && String(b.description).includes('consent: ' + tag));
      if (mine) return { status: 'REJECTED', reason: 'ROOM_OCCUPIED', consent_placed_id: mine.id };
      if (cal.bookings.some(b => b.status !== 'cancelled')) return { status: 'REJECTED', reason: 'ROOM_OCCUPIED' };
      if (!opts.noHold && v.exclude_event_id !== HOLD && name !== 'Move Requester') return { status: 'REJECTED', reason: 'ROOM_OCCUPIED' };   // the hold is in the room
      const b = { id: 'bk' + (cal.bookings.length + 1), description: v.description, status: 'confirmed' }; cal.bookings.push(b);
      if (cal.hold.transparency === 'opaque') return { status: 'ROOM_DECLINED', event_id: b.id };
      return name === 'Move Requester' ? { status: 'MOVED', new_event_id: b.id } : { status: 'CREATED', event_id: b.id };
    } };
  return e;
}
const finalize = async e => { await runWorkflow(F, 'When Executed by Another Workflow', [{ json: { request_id: e.sheet[0]['Request ID'] } }], e); return e; };
const R0 = e => e.sheet[0];
const live = e => e.cal.bookings.filter(b => b.status !== 'cancelled');

(async () => {
  console.log('Finalize - M-booth approval');
  let e = await finalize(env({ row: { Decision: 'APPROVED' } }));
  ok(R0(e).Status === 'DONE' && R0(e)['Resolved Via'] === 'mbooth-approve' && R0(e)['Placement Event Id'] === 'bk1', 'approved -> DONE, booking id recorded', R0(e));
  ok(live(e).length === 1 && /consent: 20271001090000-UHOW/.test(live(e)[0].description), 'one booking, carrying the consent marker');
  ok(e.cal.hold.status === 'confirmed' && !e.calls.some(c => c.includes(HOLD) && !c.includes('exclude=')), 'the hold is never touched');
  ok(e.calls.includes('Book Requester exclude=' + HOLD), 'only that exact hold is excluded from the clash check');
  ok(e.msgs.length === 2 && /OK'd sharing/.test(e.msgs.find(m => m.to === 'UHOW').text) && /offered your M1/.test(e.msgs.find(m => m.to === 'URICO').text), 'approval wording to both');

  console.log('Finalize - timeout, not due, reject');
  e = await finalize(env({ row: { Deadline: '2020-01-01T00:00:00Z' } }));
  ok(R0(e).Status === 'DONE' && R0(e)['Resolved Via'] === 'sweep-timeout', 'M-booth deadline passed, no reply -> books (policy kept)');
  ok(e.msgs.every(m => !/OK'd/.test(m.text)) && /didn't reply by the deadline/.test(e.msgs.find(m => m.to === 'UHOW').text) && /No reply came in/.test(e.msgs.find(m => m.to === 'URICO').text), 'timeout wording, not "approved"', e.msgs);
  e = await finalize(env({}));
  ok(R0(e).Status === 'PENDING' && e.calls.length === 0 && e.msgs.length === 0, 'not due and no decision -> nothing happens');
  e = await finalize(env({ row: { Decision: 'REJECTED' } }));
  ok(R0(e).Status === 'REJECTED' && e.calls.length === 0 && /stays theirs/.test(e.msgs.find(m => m.to === 'UHOW').text) && /stays yours/.test(e.msgs.find(m => m.to === 'URICO').text), 'recorded "no" -> REJECTED, both told, calendar untouched');

  console.log('Finalize - failures');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, bookResult: () => ({ status: 'REJECTED', reason: 'ROOM_OCCUPIED' }) }));
  ok(R0(e).Status === 'FAILED' && live(e).length === 0 && e.cal.hold.status === 'confirmed' && /Nothing was changed/.test(e.msgs[0].text), 'booking refused -> FAILED, "nothing changed" (true: nothing was touched)');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, opaque: true }));
  ok(R0(e).Status === 'FAILED' && live(e).length === 0 && e.calls.some(c => c.startsWith('Remove Own Booking DELETE bk1')), 'hold still blocking the booth -> our declined booking is removed, FAILED', e.calls);
  ok(/Nothing was changed/.test(e.msgs[0].text) && e.cal.hold.status === 'confirmed', '...and the hold is untouched');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, opaque: true, httpFail: n => n === 'Remove Own Booking' || n === 'Recheck Own' }));
  ok(R0(e).Status === 'NEEDS_ATTENTION' && e.msgs.some(m => m.to === 'C0C34UMFXGD') && e.msgs.every(m => !/Nothing was changed/.test(m.text)), 'our declined booking could not be removed -> NEEDS_ATTENTION, team alerted, no "nothing changed"');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, bookResult: () => { throw new Error('sub-workflow crashed'); } }));
  ok(R0(e).Status === 'PENDING' && e.msgs.length === 0 && e.writes.length === 0, 'booking call crashed (uncertain) -> row left PENDING for the sweep, no message');

  console.log('Finalize - status write fails after a successful booking');
  e = env({ row: { Decision: 'APPROVED' }, failWrite: n => n === 'Write Outcome' });
  await finalize(e);
  ok(R0(e).Status === 'PENDING' && live(e).length === 1 && e.msgs.length === 0, 'booked but DONE not written -> nobody told yet');
  e.failWrite = null; await finalize(e);
  ok(R0(e).Status === 'DONE' && live(e).length === 1 && e.msgs.length === 2, 'the retry recognises its own booking: DONE, still one booking, messages once');

  console.log('Finalize - duplicates and races');
  e = await finalize(env({ row: { Decision: 'APPROVED' } })); const n1 = e.calls.length; await finalize(e);
  ok(e.calls.length === n1 && live(e).length === 1 && e.msgs.length === 2, 'a second run on a DONE row does nothing');
  e = await finalize(env({ row: { Decision: 'APPROVED' } }));
  const stale = [row({ Decision: 'APPROVED' })];
  e.readFor = n => n === 'Read Rows' ? stale : null;             // run 2 started before run 1 wrote DONE (approval + timeout together)
  await finalize(e);
  ok(live(e).length === 1 && R0(e).Status === 'DONE' && e.msgs.length === 2, 'approval and timeout racing: one booking, row stays DONE, messages sent once');
  e = await finalize(env({ row: { Decision: 'APPROVED' } }));
  e.readFor = n => n === 'Read Rows' ? stale : null;
  const e3 = Object.assign(e, {}); const keep = e3.sub; e3.sub = async (nm, v) => ({ status: 'REJECTED', reason: 'ROOM_OCCUPIED' });
  await finalize(e3);
  ok(R0(e3).Status === 'DONE' && e3.msgs.length === 2, 'a racing run whose booking fails does not overwrite DONE with FAILED');
  e = await finalize(env({ row: { Decision: 'APPROVED', Status: 'REJECTED' } }));
  ok(e.calls.length === 0, 'only PENDING rows are acted on');
  e = await finalize(env({ rows: [row({ Decision: 'APPROVED' }), row({ Decision: 'APPROVED' })] }));
  ok(e.calls.length === 0, 'two rows with the same Request ID -> nothing done');

  console.log('Finalize - PREEMPT');
  e = await finalize(env({ row: { Kind: 'PREEMPT', 'Incumbent Event Id': 'inc1', Deadline: '2020-01-01T00:00:00Z' } }));
  ok(R0(e).Status === 'EXPIRED' && e.calls.length === 0 && e.msgs.length === 0, 'PREEMPT timeout -> EXPIRED, nobody moved (policy kept)');
  e = await finalize(env({ noHold: true, row: { Kind: 'PREEMPT', 'Incumbent Event Id': 'inc1', Decision: 'INCUMBENT_MOVED' } }));
  ok((await finalize(env({ row: { Kind: 'PREEMPT', 'Incumbent Event Id': 'inc1', Decision: 'INCUMBENT_MOVED' } }))).sheet[0].Status === 'FAILED', 'PREEMPT: if the incumbent is somehow still there, the requester is NOT booked over it');
  ok(R0(e).Status === 'DONE' && R0(e)['Resolved Via'] === 'move-hook' && e.calls.includes('Book Requester exclude='), 'incumbent moved -> requester placed, nothing excluded');

  console.log('Consent Sweep');
  const sweep = async sheet => { const calls = []; await runWorkflow(S, 'Read Pending Rows', [{ json: {} }], { sheet, writes: [], msgs: [], async sub(n, v) { calls.push(v.request_id); return {}; } }); return calls; };
  const old = new Date(Date.now() - 10 * 60e3).toISOString(), fresh = new Date().toISOString();
  const rows6 = [row({ 'Request ID': 'B', Deadline: '2020-01-01T00:00:00Z' }), row({ 'Request ID': 'A', Deadline: '2020-01-01T00:00:00Z' }),
                 row({ 'Request ID': 'C', Kind: 'PREEMPT', Deadline: '2020-01-01T00:00:00Z' }), row({ 'Request ID': 'D' }),
                 row({ 'Request ID': 'E', Status: 'DONE', Deadline: '2020-01-01T00:00:00Z' }),
                 row({ 'Request ID': 'G', Decision: 'APPROVED', 'Decision At': old }), row({ 'Request ID': 'H', Decision: 'APPROVED', 'Decision At': fresh })];
  const got = await sweep(rows6);
  ok(JSON.stringify(got) === '["A","B","C","G"]', 'every expired row, and a decision left unfinished, each sent separately; not-due, done and just-decided rows skipped', got);
  ok(node(S, 'Process Row').parameters.mode === 'each' && node(S, 'Every 10 min').parameters.rule.interval[0].minutesInterval === 10, 'one sub-run per row; schedule unchanged (10 min)');

  console.log('Consent Router (main)');
  const router = node(M, 'Consent Router').parameters.jsCode;
  const codeFn = new Function(router.match(/function consentCode[\s\S]*?return s; }/)[0] + '; return consentCode;')();
  const openMsg = new Function(node(O, 'Build Messages').parameters.jsCode.match(/function consentCode[\s\S]*?return s; }/)[0] + '; return consentCode;')();
  ok(codeFn('20271001090000-UHOW') === openMsg('20271001090000-UHOW'), 'Open and main compute the same request code');
  const A = row({ 'Request ID': 'RA', Approver: 'URICO' }), Bq = row({ 'Request ID': 'RB', Approver: 'URICO', 'Room/Booth': 'M2' });
  const route = async (text, lastBot, rows = [A]) => (await new AsyncFn('$input', '$', router)(wrap([]), n => wrap(({
    'Read Pending Consent': rows.map(r => ({ json: r })), 'Slack Trigger': [{ json: { user: 'URICO', text } }], 'Get Sender': [{ json: {} }],
    'Consent History': [{ json: { user: 'URICO', text } }, ...(lastBot ? [{ json: { bot_id: 'B1', text: lastBot } }] : [])] })[n] || (() => { throw new Error('unexecuted ' + n); })())))[0].json;
  const prompt = r => 'Hi Rico - Howard would like to use ' + r['Room/Booth'] + '... Reply here with yes or no. (request ' + codeFn(r['Request ID']) + ')';
  let r = await route('yes', prompt(A)); ok(r._consentBranch === 'decide' && r._consentDecision === 'APPROVED' && r._matched['Request ID'] === 'RA', '"yes" right after the request -> approved');
  r = await route('Yes but only after 5pm', prompt(A)); ok(r._consentBranch === 'clarify' && /\(request /.test(r._consentReply), '"Yes but only after 5pm" -> asks again, not approved');
  r = await route('yes, actually no', prompt(A)); ok(r._consentBranch === 'clarify', '"yes, actually no" -> asks again');
  r = await route('No problem', prompt(A)); ok(r._consentBranch === 'clarify' && r._consentDecision === '', '"No problem" -> asks again, not rejected');
  r = await route('no', prompt(A)); ok(r._consentDecision === 'REJECTED', '"no" -> rejected');
  r = await route('yes', 'QATEST / Jem Lim / TL ... Confirm to book. (yes/no)'); ok(r._consentBranch === 'normal', '"yes" to the holder\'s own booking summary is NOT taken as consent');
  r = await route('yes', prompt(Bq), [A, Bq]); ok(r._matched['Request ID'] === 'RB', 'two pending requests -> bound to the one Jessie last asked about');
  r = await route('yes ' + codeFn('RA'), prompt(Bq), [A, Bq]); ok(r._consentDecision === 'APPROVED' && r._matched['Request ID'] === 'RA', 'a reply carrying a request code is bound to that request');
  r = await route('yes', 'Something unrelated', [A, Bq]); ok(r._consentBranch === 'normal', 'two pending, nothing to bind to -> not guessed');
  r = await route('book studio 7 tomorrow 2-4pm', prompt(A)); ok(r._consentBranch === 'normal', 'an unrelated request goes to Jessie as normal');
  r = await route('yes', prompt(A), [row({ 'Request ID': 'RA', Approver: 'URICO', Status: 'DONE' })]); ok(r._consentBranch === 'normal', 'a request that is no longer PENDING is not answered');
  const P1 = row({ 'Request ID': 'RP', Kind: 'PREEMPT', Approver: 'URICO' });
  r = await route('no', prompt(P1), [P1]); ok(r._consentDecision === 'REJECTED', 'PREEMPT "no" -> rejected');
  r = await route('I can move to 3pm', prompt(P1), [P1]); ok(r._consentBranch === 'consent-help' && /CONSENT CONTEXT/.test(r._consentContext), 'PREEMPT reply with a new time -> the move flow, as before');
  const to = (w, n, b = 0) => (((w.connections[n] || {}).main || [])[b] || []).map(t => t.node);
  ok(!M.nodes.some(n => n.name === 'Call Finalize MBOOTH') && JSON.stringify(to(M, 'Record Decision')) === '["Decision Recorded?"]' && JSON.stringify(to(M, 'Decision Recorded?', 0)) === '["Call Finalize"]' && JSON.stringify(to(M, 'Decision Recorded?', 1)) === '["Decision Reply"]', 'main records the decision, then calls Finalize with the request id (or says it could not record it)');
  ok(node(M, 'Call Finalize').parameters.workflowInputs.value.request_id.includes("Decision Row"), 'Finalize gets only the request id - it re-reads the row itself');
  ok(JSON.stringify(to(M, 'Consent Clarify?', 1)) === '["Read Reference Cache"]', 'everything else continues into the normal flow (cache block)');

  console.log('Book Session v57 and Move v25');
  const run = JSON.parse(fs.readFileSync(process.argv[2])).data.resultData.runData;
  const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
  const REQ0 = rec('When Executed by Another Workflow')[0].json;
  const S7 = 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com';
  const cc = (w, events, req) => { const RQ = [{ json: { ...REQ0, ...req } }];
    const $ = n => n === 'When Executed by Another Workflow' ? wrap(RQ) : wrap(rec(n) || (() => { throw new Error('unexecuted ' + n); })());
    const inp = [{ json: { kind: 'calendar#events', items: events } }];
    return new Function('$', '$input', '$getWorkflowStaticData', node(w, 'Check Conflicts').parameters.jsCode)($, wrap(inp), () => ({}))[0].json; };
  const recur = (id, sum) => ({ id, recurringEventId: id.split('_')[0], status: 'confirmed', summary: sum, start: { dateTime: REQ0.start_iso }, end: { dateTime: REQ0.end_iso }, attendees: [{ email: S7, resource: true }] });
  ok(cc(B, [recur('other_1', 'Weekly VO block')], { room_override: true }).reason === 'ROOM_OCCUPIED', 'room_override no longer ignores an unrelated recurring booking');
  ok(cc(B56, [recur('other_1', 'Weekly VO block')], { room_override: true }).verdict === 'CLEAR', '  (v56: it did)');
  ok(cc(B, [recur('hold_1', 'M1 - Rico')], { room_override: true, exclude_event_id: 'hold_1' }).verdict === 'CLEAR', 'the exact approved hold (exclude_event_id) is ignored');
  ok(cc(B, [recur('hold_1', 'M1 - Rico'), recur('other_2', 'Other')], { room_override: true, exclude_event_id: 'hold_1' }).reason === 'ROOM_OCCUPIED', '...and only that one');
  const dp = node(B, 'Decide Preempt').parameters.jsCode;
  const dpr = new Function('$', '$input', dp)(n => wrap([{ json: { ...REQ0, description: REQ0.description + ' | consent: X1' } }]), wrap([{ json: { reason: 'ROOM_OCCUPIED', conflicts: [{ recurring: true, description: 'ref: U1' }] } }]))[0].json;
  ok(dpr.offer === false && dpr.preemptReason === 'CONSENT_PLACEMENT', 'a consent placement never opens another consent request');
  const rr = new Function('$', '$input', node(B, 'Return Rejection').parameters.jsCode)(n => wrap([{ json: { description: 'x | consent: X1' } }]),
    wrap([{ json: { verdict: 'REJECTED', reason: 'ROOM_OCCUPIED', conflicts: [{ id: 'bk9', room: 'M1', summary: 's', description: 'Booked by: H | ref: U | consent: X1' }] } }]))[0].json;
  ok(rr.consent_placed_id === 'bk9', 'a clash with its own earlier consent booking is reported back');
  const cfull = cc(B, [{ ...recur('bk9', 'M1 - Howard'), recurringEventId: undefined, description: 'Booked by: H | ref: UHOW | consent: X1' }], {});
  ok(Array.isArray(cfull.conflicts) && /consent: X1/.test(cfull.conflicts[0].description || ''), 'Check Conflicts keeps the description on a conflict (needed for the line above)', cfull.conflicts);
  const mvRow = new Function('$json', node(MV, 'Incumbent Moved Row').parameters.jsCode)({ matched: { 'Request ID': 'RP' } })[0].json;
  ok(mvRow['Request ID'] === 'RP' && mvRow.Decision === 'INCUMBENT_MOVED' && !('Status' in mvRow), 'Move records "incumbent moved" and never writes Status');
  ok(JSON.stringify(to(MV, 'Record Incumbent Moved')) === '["Call Finalize"]' && JSON.stringify(to(MV, 'Call Finalize')) === '["Notify?"]', 'Move records "incumbent moved", then calls Finalize with the request id');

  console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('CRASH', e.stack); process.exit(2); });
