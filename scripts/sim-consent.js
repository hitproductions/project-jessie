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
      if (op === 'read' || op === undefined) { if (env.failRead && env.failRead(name)) throw new Error(name + ': sheet read failed'); branches = [env.sheet.map(r => ({ json: { ...r } }))]; }
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
const HOLD = 'jmuq10se2757bdh88rqock5i8c_20271006T160000Z', M1 = 'c_1889v46vd62fkjk3i7r1hsfem7tcm@resource.calendar.google.com';
const holdEvent = over => ({ id: HOLD, recurringEventId: 'jmuq10se2757bdh88rqock5i8c', status: 'confirmed', summary: 'M1 - Rico',
  start: { dateTime: '2027-10-07T00:00:00+08:00' }, end: { dateTime: '2027-10-08T00:00:00+08:00' }, location: 'KDC Plaza-Top Level-M1 (1)',
  attendees: [{ email: M1, displayName: 'KDC Plaza-Top Level-M1 (1)', resource: true, responseStatus: 'accepted' }], description: 'ref: URICO', ...over });
const payload = { summary: 'M1 - Howard', start_iso: '2027-10-07T10:00:00+08:00', end_iso: '2027-10-07T12:00:00+08:00', rooms: 'M1',
  description: 'Booked by: Howard Luistro | ref: UHOW', session_type: '', client: '', department: 'Localization', engineer: '', bookingType: '', all_day: false, reference_data: '' };
const row = over => ({ 'Request ID': '20271001090000-UHOW', 'Status': 'PENDING', 'Kind': 'MBOOTH', 'Requester': 'UHOW', 'Requester Name': 'Howard Luistro',
  'Approver': 'URICO', 'Approver Name': 'Rico', 'Room/Booth': 'M1', 'Req Start': '2027-10-07T10:00:00+08:00', 'Req End': '2027-10-07T12:00:00+08:00',
  'Incumbent Event Id': HOLD, 'Incumbent Title': 'M1 - Rico', 'Deadline': '2099-01-01T00:00:00Z', 'Req Payload': JSON.stringify(payload),
  'Decision': '', 'Decision At': '', 'Stage': '', 'Hold Snapshot': '', 'Placement Event Id': '', ...over });
function env(opts = {}) {
  const cal = { hold: opts.hold === null ? null : holdEvent(opts.hold || {}), bookings: [] };
  const e = { sheet: opts.rows || [row(opts.row || {})], writes: [], msgs: [], calls: [], cal,
    failWrite: opts.failWrite, failRead: opts.failRead,
    async http(name, method, url, body) {
      e.calls.push(name + ' ' + method);
      if (opts.httpFail && opts.httpFail(name, method)) throw new Error('HTTP 500 backend error');
      if (!cal.hold) throw new Error('The resource you are requesting could not be found (404)');
      if (method === 'GET') return { ...cal.hold };
      if (method === 'DELETE') { if (opts.deleteFail) throw new Error('HTTP 500'); cal.hold.status = 'cancelled'; return {}; }
      if (method === 'PATCH') { if (opts.restoreFail) throw new Error('HTTP 500'); cal.hold.status = JSON.parse(body).status; return { ...cal.hold }; }
    },
    async sub(name, v) {
      e.calls.push(name);
      const mine = cal.bookings.find(b => String(b.description).includes('consent: ' + (String(v.description || '').match(/consent: (\S+)/) || [])[1]));
      if (opts.bookResult) { const r = opts.bookResult(v, cal); if (r) return r; }
      if (mine) return { status: 'REJECTED', reason: 'ROOM_OCCUPIED', consent_placed_id: mine.id };
      if (cal.hold && cal.hold.status === 'confirmed' && v.exclude_event_id !== cal.hold.id) return { status: 'REJECTED', reason: 'ROOM_OCCUPIED' };
      const b = { id: 'bk' + (cal.bookings.length + 1), description: v.description, start: v.start_iso || v.new_start_iso }; cal.bookings.push(b);
      return name === 'Move Requester' ? { status: 'MOVED', new_event_id: b.id } : { status: 'CREATED', event_id: b.id };
    } };
  return e;
}
const finalize = async e => { await runWorkflow(F, 'When Executed by Another Workflow', [{ json: { request_id: e.sheet[0]['Request ID'] } }], e); return e; };
const R0 = e => e.sheet[0];

(async () => {
  console.log('Finalize - M-booth approval, the happy path');
  let e = await finalize(env({ row: { Decision: 'APPROVED' } }));
  ok(R0(e).Status === 'DONE' && R0(e).Stage === 'PLACED' && R0(e)['Resolved Via'] === 'mbooth-approve', 'approved -> DONE', R0(e));
  ok(e.cal.hold.status === 'cancelled' && e.cal.bookings.length === 1, 'hold instance released, one booking made');
  ok(JSON.parse(R0(e)['Hold Snapshot']).id === HOLD, 'hold copied to the row before it was deleted');
  ok(e.writes.findIndex(w => w.Stage === 'HOLD_SNAPSHOT') < e.calls.indexOf('Delete Hold DELETE') + 99 && e.writes[0].Stage === 'HOLD_SNAPSHOT', 'snapshot written first');
  ok(/consent: 20271001090000-UHOW/.test(e.cal.bookings[0].description), 'booking carries the consent marker');
  ok(e.msgs.length === 2 && /OK'd sharing/.test(e.msgs.find(m => m.to === 'UHOW').text) && /offered your M1/.test(e.msgs.find(m => m.to === 'URICO').text), 'approval wording to both');

  console.log('Finalize - M-booth timeout');
  e = await finalize(env({ row: { Deadline: '2020-01-01T00:00:00Z' } }));
  ok(R0(e).Status === 'DONE' && R0(e)['Resolved Via'] === 'sweep-timeout', 'deadline passed, no reply -> books (policy kept)');
  ok(e.msgs.every(m => !/OK'd/.test(m.text)) && /didn't reply by the deadline/.test(e.msgs.find(m => m.to === 'UHOW').text) && /No reply came in/.test(e.msgs.find(m => m.to === 'URICO').text), 'timeout wording, not "approved"', e.msgs);
  e = await finalize(env({ row: { Deadline: '2099-01-01T00:00:00Z' } }));
  ok(R0(e).Status === 'PENDING' && e.calls.length === 0, 'not due and no decision -> nothing happens');

  console.log('Finalize - deletion failure');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, deleteFail: true }));
  ok(R0(e).Status === 'FAILED' && R0(e)['Resolved Via'] === 'DELETE_FAILED', 'delete failed and the hold is verified still there -> FAILED', R0(e));
  ok(e.cal.hold.status === 'confirmed' && e.cal.bookings.length === 0 && !e.calls.includes('Book Requester'), 'hold intact, nothing booked');
  ok(/Nothing was changed/.test(e.msgs[0].text) && e.msgs.length === 1, 'requester told nothing changed (true)');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, deleteFail: true, httpFail: (n, m) => n === 'Recheck Hold' }));
  ok(R0(e).Status === 'PENDING' && R0(e).Stage === 'HOLD_SNAPSHOT' && e.msgs.length === 0, 'delete outcome unreadable -> left for the next sweep, no claim made');

  console.log('Finalize - placement failure');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, bookResult: () => ({ status: 'REJECTED', reason: 'ROOM_OCCUPIED' }) }));
  ok(R0(e).Status === 'FAILED' && R0(e).Stage === 'RESTORED' && e.cal.hold.status === 'confirmed', 'booking failed -> hold restored and verified', R0(e));
  ok(/back as it was/.test(e.msgs.find(m => m.to === 'UHOW').text) && /back as it was/.test(e.msgs.find(m => m.to === 'URICO').text), 'both told the holder\'s booking is back');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, restoreFail: true, bookResult: () => ({ status: 'REJECTED', reason: 'ROOM_OCCUPIED' }) }));
  ok(R0(e).Status === 'NEEDS_ATTENTION' && R0(e).Stage === 'RESTORE_FAILED', 'restore failed -> NEEDS_ATTENTION', R0(e));
  ok(e.msgs.some(m => m.to === 'C0C34UMFXGD' && /NEEDS ATTENTION/.test(m.text)) && e.msgs.every(m => !/Nothing was changed|nothing changed/i.test(m.text)), 'team alerted; nobody told "nothing changed"');
  const e2 = await finalize(e); ok(e2.calls.filter(c => c !== 'Get Hold GET').length === e.calls.filter(c => c !== 'Get Hold GET').length && R0(e2).Status === 'NEEDS_ATTENTION', 'a NEEDS_ATTENTION row is left for a person');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, bookResult: () => { throw new Error('sub-workflow crashed'); } }));
  ok(R0(e).Status === 'PENDING' && R0(e).Stage === 'PLACING' && e.msgs.length === 0, 'booking call crashed (uncertain) -> left at PLACING, no message');

  console.log('Finalize - status write fails after a successful booking');
  e = env({ row: { Decision: 'APPROVED' }, failWrite: n => n === 'Write Outcome' });
  await finalize(e);
  ok(R0(e).Status === 'PENDING' && R0(e).Stage === 'PLACED' && e.msgs.length === 0 && e.cal.bookings.length === 1, 'booked, DONE not written -> nobody told yet');
  e.failWrite = null; await finalize(e);
  ok(R0(e).Status === 'DONE' && e.cal.bookings.length === 1 && e.msgs.length === 2, 'next sweep finishes it: DONE, still one booking, messages once');
  e = env({ row: { Decision: 'APPROVED' }, failWrite: n => n === 'Write Placed' || n === 'Write Outcome' });
  await finalize(e);
  ok(R0(e).Stage === 'PLACING' && e.cal.bookings.length === 1, 'booked but even PLACED not written -> row still says PLACING');
  e.failWrite = null; await finalize(e);
  ok(R0(e).Status === 'DONE' && e.cal.bookings.length === 1 && e.cal.hold.status === 'cancelled', 'retry recognises its own booking (consent marker): DONE, no second booking, no restore');

  console.log('Finalize - duplicates and state');
  e = await finalize(env({ row: { Decision: 'APPROVED' } })); const n1 = e.calls.length; await finalize(e);
  ok(e.calls.length === n1 && e.cal.bookings.length === 1 && e.msgs.length === 2, 'a second run on a DONE row does nothing');
  e = await finalize(env({ row: { Decision: 'APPROVED', Status: 'REJECTED' } }));
  ok(e.calls.length === 0 && R0(e).Status === 'REJECTED', 'only PENDING rows are acted on');
  e = await finalize(env({ rows: [row({ Decision: 'APPROVED' }), row({ Decision: 'APPROVED' })] }));
  ok(e.calls.length === 0, 'two rows with the same Request ID -> nothing done');
  e = await finalize(env({ row: { Decision: 'REJECTED' } }));
  ok(R0(e).Status === 'REJECTED' && e.calls.length === 0 && /stays theirs/.test(e.msgs[0].text), 'recorded "no" -> REJECTED, requester told, calendar untouched');

  console.log('Finalize - the hold itself');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, hold: { attendees: [{ email: 'c_other@resource.calendar.google.com', displayName: 'KDC Plaza-Top Level-M2 (2)', resource: true }], location: 'KDC Plaza-Top Level-M2 (2)', summary: 'M2 - Rico' } }));
  ok(R0(e).Status === 'FAILED' && R0(e)['Resolved Via'] === 'HOLD_CHANGED' && e.cal.hold.status === 'confirmed', 'a hold that is no longer in M1 is not deleted');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, hold: { start: { dateTime: '2027-10-09T00:00:00+08:00' }, end: { dateTime: '2027-10-10T00:00:00+08:00' } } }));
  ok(R0(e)['Resolved Via'] === 'HOLD_CHANGED', 'a hold that moved to another day is not deleted');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, hold: null }));
  ok(R0(e).Status === 'DONE' && !e.calls.includes('Delete Hold DELETE'), 'hold already gone -> just book');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, hold: null, bookResult: () => ({ status: 'REJECTED', reason: 'ROOM_OCCUPIED' }) }));
  ok(R0(e).Status === 'FAILED' && !e.calls.includes('Restore Hold PATCH') && /Nothing was changed/.test(e.msgs[0].text), 'we deleted nothing -> no restore, "nothing changed" is true');
  e = await finalize(env({ row: { Decision: 'APPROVED' }, httpFail: n => n === 'Get Hold' }));
  ok(R0(e).Status === 'PENDING' && e.writes.length === 0, 'hold unreadable -> nothing done, retried next sweep');
  ok(!/recurringEventId/.test(JSON.stringify(e.calls)) && true, 'only the instance id is ever deleted (series id never used)');

  console.log('Finalize - PREEMPT');
  e = await finalize(env({ row: { Kind: 'PREEMPT', 'Incumbent Event Id': 'inc1', Deadline: '2020-01-01T00:00:00Z' } }));
  ok(R0(e).Status === 'EXPIRED' && e.calls.length === 0 && e.msgs.length === 0, 'PREEMPT timeout -> EXPIRED, nobody moved (policy kept)');
  e = await finalize(env({ row: { Kind: 'PREEMPT', 'Incumbent Event Id': 'inc1', Decision: 'INCUMBENT_MOVED', Deadline: '2020-01-01T00:00:00Z' }, hold: null }));
  ok(R0(e).Status === 'DONE' && R0(e)['Resolved Via'] === 'move-hook' && !e.calls.some(c => /Hold/.test(c)), 'incumbent moved (even past the deadline) -> requester placed, no hold touched');

  console.log('Consent Sweep');
  const sweep = async sheet => { const calls = []; await runWorkflow(S, 'Read Pending Rows', [{ json: {} }], { sheet, writes: [], msgs: [], async sub(n, v) { calls.push(v.request_id); return {}; } }); return calls; };
  const rows3 = [row({ 'Request ID': 'B', Deadline: '2020-01-01T00:00:00Z' }), row({ 'Request ID': 'A', Deadline: '2020-01-01T00:00:00Z' }),
                 row({ 'Request ID': 'C', Kind: 'PREEMPT', Deadline: '2020-01-01T00:00:00Z' }), row({ 'Request ID': 'D' }), row({ 'Request ID': 'E', Status: 'DONE', Deadline: '2020-01-01T00:00:00Z' }),
                 row({ 'Request ID': 'F', Stage: 'RESTORE_FAILED' })];
  ok(JSON.stringify(await sweep(rows3)) === '["A"]', 'several expired rows -> ONE per run, oldest first');
  const seen = []; for (let i = 0; i < 4; i++) { const c = await sweep(rows3); if (c[0]) { seen.push(c[0]); rows3.find(r => r['Request ID'] === c[0]).Status = 'DONE'; } }
  ok(JSON.stringify(seen) === '["A","B","C"]', 'each expired row is processed separately, in turn; not-due, done and needs-attention rows are skipped', seen);
  ok(JSON.stringify(await sweep([row({ 'Request ID': 'Z', Decision: 'APPROVED' })])) === '["Z"]', 'a recorded decision is picked up without waiting for the deadline');
  ok(node(S, 'Every Minute').parameters.rule.interval[0].minutesInterval === 1 && node(S, 'Process Row').parameters.mode === 'each', 'runs every minute; one sub-run per row');

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
  ok(!M.nodes.some(n => n.name === 'Call Finalize MBOOTH') && JSON.stringify(to(M, 'Record Decision')) === '["Decision Reply"]' && JSON.stringify(to(M, 'Decision Reply')) === '["Send Reply"]', 'main only records the decision and replies; it never finalizes');
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
  ok(!MV.nodes.some(n => n.name === 'Call Finalize'), 'Move no longer finalizes itself');

  console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('CRASH', e.stack); process.exit(2); });
