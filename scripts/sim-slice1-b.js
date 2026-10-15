#!/usr/bin/env node
// Slice 1 step B offline (Slack Interactions v7/v8): Read Step 2 -> Book Session prepare inputs; After Prepare (PREPARED ->
// the booking inputs from prepare's fields; a question -> the form again, values kept, the question on top, an extra field
// when needed); After Book (CREATED -> Booked + DM; declined / taken -> the form again).
// Since v8 every refusal goes through Book Session's real Return Rejection first - the shape the form actually receives
// (gotcha 29: v7's sim fed Check Conflicts' raw output and missed the blank "Did you mean" notice).
// Usage: node scripts/sim-slice1-b.js [slack interactions] [book session]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v10.json', 'utf8'));
const V10 = si.nodes.some(n => n.name === 'Note Toggle');   // v10: a blank line after Booked.
const bs = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/book-session-v110.json', 'utf8'));
const bs109 = JSON.parse(fs.readFileSync('workflows/imported/book-session-v109-imported.json', 'utf8'));
const rejectVia = (wf, raw) => new Function('$input', wf.nodes.find(n => n.name === 'Return Rejection').parameters.jsCode)({ first: () => ({ json: raw }) })[0].json;
const reject = raw => rejectVia(bs, raw);
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = n => si.nodes.find(x => x.name === n).parameters.jsCode;
async function run(name, input, outs) {
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}

(async () => {
  const bookers = [
    { id: 'b1', fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer, Goes by Howard.', Authority: ['HAIST Dev'] } },
    { id: 'b2', fields: { Name: 'Daryl Reyes', Initials: 'DR', 'Slack User ID': 'U2', Info: 'Music Engineer, Post Engineer.' } },
    { id: 'b4', fields: { Name: 'Peter Legaste', Initials: 'PL', 'Slack User ID': 'U4', Info: 'Music Arranger.' } }];
  const rooms = [{ id: 'r8', fields: { 'Room Name': 'Studio 8' } }, { id: 'r4', fields: { 'Room Name': 'Studio 4' } }, { id: 'rl', fields: { 'Room Name': 'Likha', 'Room Type': ['Conference Room'] } }];
  const sessionTypes = [{ id: 's1', fields: { Type: 'VO Recording', Priority: ['r8'], 'Last Resort': ['r4'], 'Engineer Role Required': ['Post Engineer'] } }];
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
  const chk = [{ json: { user: 'U1', channel: 'D1' } }];
  const meta = { date: '2027-10-14', t0: '14:00', t1: '16:00', purpose: 'VO Recording', kind: 'studio', requester: 'U1', channel: 'D1',
    when: 'Thursday, Oct 14 · 2:00 PM–4:00 PM', label: 'VO Recording' };
  const roomBlock = { type: 'input', block_id: 'room', label: { type: 'plain_text', text: 'Room' }, element: { type: 'radio_buttons', action_id: 'room_radio',
    options: [{ text: { type: 'plain_text', text: 'Studio 8' }, value: 'Studio 8', description: { type: 'plain_text', text: 'Recommended · usual for VO Recording' } },
              { text: { type: 'plain_text', text: 'Studio 4' }, value: 'Studio 4', description: { type: 'plain_text', text: 'can do VO Recording · not a usual room' } }] } };
  const txt = (bid, a) => ({ type: 'input', block_id: bid, label: { type: 'plain_text', text: bid }, element: { type: 'plain_text_input', action_id: a } });
  const engBlock = { type: 'input', block_id: 'engineer', label: { type: 'plain_text', text: 'Engineer' }, element: { type: 'static_select', action_id: 'engineer_pick',
    options: [{ text: { type: 'plain_text', text: 'Daryl Reyes' }, value: 'U2' }, { text: { type: 'plain_text', text: 'Howard Luistro' }, value: 'U1' }] } };
  const blocks = [{ type: 'section', text: { type: 'mrkdwn', text: '🗓️' } }, roomBlock, { type: 'divider' }, txt('project', 'project_in'), txt('client', 'client_in'), engBlock, txt('notes', 'notes_in')];
  const state = (room, project, client, eng, notes) => ({ values: { room: { room_radio: { selected_option: { value: room } } }, project: { project_in: { value: project } },
    client: { client_in: { value: client } }, engineer: { engineer_pick: { selected_option: eng ? { value: eng } : null } }, notes: { notes_in: { value: notes || null } } } });
  const payload = (st, m) => ({ type: 'view_submission', view: { id: 'V1', callback_id: 'book_step2', private_metadata: JSON.stringify(m || meta), blocks, state: st } });
  const outs = { 'Check Signature': chk, 'Read Cache 3': cache };

  // ---- Read Step 2
  outs['Read Request'] = [{ json: { payload: payload(state('Studio 8', 'project qaw1', 'jem lim', 'U1', 'bring headphones')) } }];
  outs['Read Step 2'] = await run('Read Step 2', [], outs);
  let R = outs['Read Step 2'][0].json;
  ok(R.valid && R.answer.response_action === 'update' && /Booking Studio 8/.test(JSON.stringify(R.answer.view)), 'valid -> "Booking Studio 8…" at once');
  const P = R.prep;
  ok(P.mode === 'prepare' && ['QAW1 / jem lim / HL', 'QAW1 / Jem Lim / HL'].indexOf(P.summary) !== -1 && P.start_iso === '2027-10-14T14:00:00+08:00' && P.rooms === 'Studio 8', 'prepare: title, window, room');
  ok(P.description === 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1 | team: U1 | Notes: bring headphones', 'description: engineer, booker, ref, team, notes - ' + P.description);
  ok(/client jem lim/i.test(P.requester_text) && /2:00 pm-4:00 pm/.test(P.requester_text) && /engineer Howard Luistro/.test(P.requester_text), 'what the requester "typed": ' + P.requester_text);
  ok(P.authority === 'HAIST Dev' && P.expected_date === '2027-10-14' && P.confirmed === false && P.require_prepared === false && P.room_override === false, 'flags');
  outs['Read Request'] = [{ json: { payload: payload(state('Studio 4', 'X', '', 'U1')) } }];
  R = (await run('Read Step 2', [], outs))[0].json;
  ok(R.prep.room_override === true && /no client/.test(R.prep.requester_text), 'a room offered as not usual -> booked as asked; empty client -> "no client"');

  // ---- To Prepare
  outs['Read Request'] = [{ json: { payload: payload(state('Studio 8', 'project qaw1', 'jem lim', 'U1')) } }];
  outs['Read Step 2'] = await run('Read Step 2', [], outs);
  outs['To Prepare'] = await run('To Prepare', [], outs);
  const T = outs['To Prepare'][0].json;
  ok(T.mode === 'prepare' && JSON.parse(T.reference_data).types[0].priority[0] === 'r8', 'prepare inputs carry the reference data');

  // ---- After Prepare: PREPARED
  const F = { Title: 'QAW1 / Jem Lim / HL', Client: 'Jem Lim', Project: 'QAW1', 'Session Type': 'VO Recording', Date: 'Thursday, October 14, 2027',
    Time: '2:00 PM – 4:00 PM', Room: 'Studio 8', Engineer: 'Howard Luistro', Arranger: '', Department: 'Audio Post', 'Booking Type': 'Advertising', 'Booked by': 'Howard Luistro', Override: '' };
  let A = (await run('After Prepare', [{ json: { status: 'PREPARED', prep_payload: JSON.stringify({ v: 2, F }), title: F.Title } }], outs))[0].json;
  ok(A.go && A.book.mode === '' && A.book.confirmed === true && A.book.summary === 'QAW1 / Jem Lim / HL' && A.book.client === 'Jem Lim', 'book from prepare: canonical client and title');
  ok(A.book.start_iso === '2027-10-14T14:00:00+08:00' && A.book.end_iso === '2027-10-14T16:00:00+08:00' && A.book.department === 'Audio Post' && A.book.bookingType === 'Advertising', 'book: window, department, type from prepare');
  ok(A.book.description === 'Engineer: Howard Luistro | Booked by: Howard Luistro | ref: U1 | team: U1', 'book: description keeps ref and team - ' + A.book.description);

  // ---- After Prepare: questions -> the form again
  const CC = { verdict: 'REJECTED', reason: 'CLIENT_CHECK', typed: 'jem lin', suggestions: ['Jem Lim'],
    human: 'Nothing was prepared - "jem lin" is not in the client list, but it is close to Jem Lim. Ask the requester once, naming both: "Did you mean Jem Lim, or is jem lin a new client?" Then call Prepare Booking again.' };
  A = (await run('After Prepare', [{ json: reject(CC) }], outs))[0].json;
  const V = A.view;
  ok(!A.go && A.view_id === 'V1' && /Did you mean \*Jem Lim\*/.test(V.blocks[0].text.text), 'CLIENT_CHECK -> "Did you mean Jem Lim?" on top');
  ok(JSON.parse(V.private_metadata).asked === 'Did you mean Jem Lim, or is jem lin a new client?', 'the question is remembered, so Book again keeps the new name');
  ok(!/""|\*\*/.test(V.blocks[0].text.text), 'never blank quotes or ** - ' + V.blocks[0].text.text);
  // the same refusal through v109's Return Rejection (fields dropped): read back from Book Session's sentence
  let A9 = (await run('After Prepare', [{ json: rejectVia(bs109, CC) }], outs))[0].json;
  ok(/"jem lin" isn’t in the client list\. Did you mean \*Jem Lim\*/.test(A9.view.blocks[0].text.text)
     && JSON.parse(A9.view.private_metadata).asked === 'Did you mean Jem Lim, or is jem lin a new client?', 'v109 shape (fields dropped) -> still "Did you mean Jem Lim?", read from the sentence');
  ok(rejectVia(bs109, CC).typed === undefined && reject(CC).typed === 'jem lin' && reject(CC).suggestions[0] === 'Jem Lim', 'Book Session v110 passes typed and suggestions; v109 did not');
  A9 = (await run('After Prepare', [{ json: rejectVia(bs109, { verdict: 'REJECTED', reason: 'CLIENT_CHECK', human: 'something else' }) }], outs))[0].json;
  ok(/"jem lim" isn’t in the client list\. Check the spelling/.test(A9.view.blocks[0].text.text) && !/""|\*\*/.test(A9.view.blocks[0].text.text),
     'nothing to read -> the client from the form, plain words, never blank');
  ok(reject({ verdict: 'REJECTED', reason: 'ROOM_OCCUPIED', human: 'x' }).typed === undefined
     && !('typed' in JSON.parse(JSON.stringify(reject({ verdict: 'REJECTED', reason: 'ROOM_OCCUPIED', human: 'x' })))), 'v110: no empty fields added to other refusals');
  const vb = id => V.blocks.find(b => b.block_id === id);
  ok(vb('project').element.initial_value === 'project qaw1' && vb('client').element.initial_value === 'jem lim' && vb('room').element.initial_option.value === 'Studio 8'
     && vb('engineer').element.initial_option.value === 'U1', 'entries kept (project, client, room, engineer)');
  ok(V.submit && V.close.text === 'Back' && V.callback_id === 'book_step2', 'still the step-2 form with Book');
  const ND = { verdict: 'REJECTED', reason: 'NEED_DEPARTMENT', options: ['Audio Post', 'Music'],
    human: 'Nothing was prepared - VO Recording can be Audio Post or Music. Ask the requester once: "Is this a Audio Post or a Music session?" Then call Prepare Booking again.' };
  A = (await run('After Prepare', [{ json: reject(ND) }], outs))[0].json;
  const di = A.view.blocks.findIndex(b => b.block_id === 'department'), ni = A.view.blocks.findIndex(b => b.block_id === 'notes');
  ok(di !== -1 && di < ni && A.view.blocks[di].element.options.map(o => o.value).join() === 'Audio Post,Music', 'NEED_DEPARTMENT -> a Department choice before Notes');
  A9 = (await run('After Prepare', [{ json: rejectVia(bs109, ND) }], outs))[0].json;
  ok(A9.view.blocks.find(b => b.block_id === 'department').element.options.map(o => o.value).join() === 'Audio Post,Music', 'v109 shape -> departments read from the sentence');
  A = (await run('After Prepare', [{ json: reject({ verdict: 'REJECTED', reason: 'NEED_BOOKING_TYPE', options: ['Advertising', 'Personal'], askClient: true, human: 'x' }) }], outs))[0].json;
  ok(A.view.blocks.some(b => b.block_id === 'kind') && /client/.test(A.view.blocks[0].text.text), 'NEED_BOOKING_TYPE -> Kind of booking, and asks the client');
  A = (await run('After Prepare', [{ json: { status: 'REJECTED', reason: 'NEED_ARRANGER' } }], outs))[0].json;
  ok(/No arranger/.test(A.view.blocks[0].text.text), 'NEED_ARRANGER -> pick one or No arranger');
  A = (await run('After Prepare', [{ json: { status: 'REJECTED', reason: 'SOMETHING_NEW', human: 'Ask the requester to …' } }], outs))[0].json;
  ok(!/Ask the requester/.test(JSON.stringify(A.view)) && (/SOMETHING_NEW/.test(A.view.blocks[0].text.text) || /^⚠️ This couldn’t be booked\. Check the details/.test(A.view.blocks[0].text.text)), "Book Session's own (chat) texts are never shown (v15: nor its code)");

  // a second problem replaces the first, never stacks
  outs['Read Request'] = [{ json: { payload: Object.assign(payload(state('Studio 8', 'p', 'c', 'U1')), {}) } }];
  outs['Read Request'][0].json.payload.view.blocks = [{ type: 'section', block_id: 'problem', text: { type: 'mrkdwn', text: 'old' } }, { type: 'divider', block_id: 'problem_div' }].concat(blocks);
  A = (await run('After Prepare', [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED' } }], outs))[0].json;
  ok(A.view.blocks.filter(b => b.block_id === 'problem').length === 1 && /just booked/.test(A.view.blocks[0].text.text), 'one problem line at a time');

  // ---- After Book
  outs['Read Request'] = [{ json: { payload: payload(state('Studio 8', 'project qaw1', 'jem lim', 'U1')) } }];
  outs['After Prepare'] = await run('After Prepare', [{ json: { status: 'PREPARED', prep_payload: JSON.stringify({ v: 2, F }), title: F.Title } }], outs);
  let B = (await run('After Book', [{ json: { status: 'CREATED', event_id: 'E1', title: 'QAW1 / Jem Lim / HL', duration_note: '' } }], outs))[0].json;
  ok(B.ok && /✅ \*Booked\.\*/.test(B.view.blocks[0].text.text) && B.view.clear_on_close, 'CREATED -> Booked on the form; Done closes it');
  const CARD = '✅ *Booked.*\n' + (V10 ? '\n' : '') + '*QAW1 / Jem Lim / HL*\n*Date:* Thursday, October 14, 2027\n*Time:* 2:00 PM – 4:00 PM\n*Room:* Studio 8';
  ok(B.text === CARD && B.channel === 'U1', 'v8 DM: the card - title, Date, Time, Room, nothing else - ' + B.text.replace(/\n/g, ' | '));
  ok(B.view.blocks[0].text.text === CARD, 'v8 form: the same card');
  if (V10) ok(B.view.blocks.length === 1, 'v10: no "A copy is in your DM" line');
  B = (await run('After Book', [{ json: { status: 'CREATED', event_id: 'E1', title: 'QAW1 / Jem Lim / HL', duration_note: 'Heads up: 9 hours is longer than usual.' } }], outs))[0].json;
  ok(B.text === CARD + '\nHeads up: 9 hours is longer than usual.', 'v8 DM: an unusual length still says so, under the card');
  B = (await run('After Book', [{ json: { status: 'ROOM_DECLINED', removed: true } }], outs))[0].json;
  ok(!B.ok && /turned the booking down/.test(B.view.blocks[0].text.text) && /taken off the calendar/.test(B.view.blocks[0].text.text), 'ROOM_DECLINED -> the form again: declined, removed');
  B = (await run('After Book', [{ json: reject({ verdict: 'REJECTED', reason: 'ROOM_OCCUPIED', human: 'x' }) }], outs))[0].json;
  ok(!B.ok && /just booked/.test(B.view.blocks[0].text.text), 'taken at the last second -> the form again');

  // ---- wiring
  const C = si.connections;
  const next = n => (C[n] && C[n].main || []).map(o => o.map(c => c.node));
  ok(JSON.stringify(next('Step 2 OK?')) === '[["To Prepare"]]' && JSON.stringify(next('Prepared?')) === '[["To Book"],["Show Question"]]'
     && JSON.stringify(next('Booked?')) === '[["DM Booked"]]', 'wiring: prepare -> book or question; DM only when booked');
  ok(si.nodes.find(n => n.name === 'Prepare').parameters.workflowId.value === 'EUG3sGXkfsJSYIMz' && si.nodes.find(n => n.name === 'Book').parameters.workflowId.value === 'EUG3sGXkfsJSYIMz', 'both calls go to Book Session');
  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
