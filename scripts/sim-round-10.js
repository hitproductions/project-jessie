#!/usr/bin/env node
// Round 10 offline (Slack Interactions v27, 19 Oct): Tara's lost question (execution 50920 - NEED_DEPARTMENT after Book, the window
// closed, views.update `not_found`). The department asked in step 2 for types that span departments; a question / problem that
// cannot be shown goes to the DM with a "Book a room" button that opens the form filled in; the working lines say "in your DM".
// Usage: node scripts/sim-round-10.js [slack-interactions v27]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v27.json', 'utf8'));
const V29 = /v29: no Department field/.test(JSON.stringify(si.nodes));   // round 11: the department from the people picked (sim-round-11)
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
async function run(name, input, outs) {
  const js = si.nodes.find(x => x.name === name).parameters.jsCode;
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;
const ST = (t, pri, roles) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': [], 'Engineer Role Required': roles, 'Room Requirements': '' } });
const sessionTypes = [ST('Celebrity Recording', ['rf', 'rc'], ['Music Engineer', 'Post Engineer', 'Music Arranger']), ST('Van Recording', ['sm'], ['Post Engineer', 'Music Arranger']),
  ST('VO Recording', ['r7'], ['Post Engineer']), ST('Band Recording', ['rf'], ['Music Engineer', 'Music Arranger'])];
const rooms = FX.rooms.concat([{ id: 'sm', fields: { 'Room Name': 'Studio M', 'Room Type': ['Van'] } }]);
const B = (id, name, ini, slack, info, dept) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: dept } });
const bookers = [B('b1', 'Tara Lim', 'TL', 'U026N6E1R', 'Post Engineer, Goes by Tara.', ['Audio Post']), B('b2', 'Joaquin Santos', 'JS', 'U9', 'Music Arranger', ['Music']),
  B('b3', 'Camy Caridad', 'CC', 'U5', 'Coordinator', ['Marketing'])];
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
const tv = v => ({ selected_option: { value: v } });
const S = (purpose, kind, req) => ({ date: '2027-10-19', t0: '11:30', t1: '12:30', purpose, kind, requester: req || 'U026N6E1R', channel: 'D1', ext: 'x', msg: { ch: 'D1', ts: '1.1' } });
const step2 = async (s, ra) => (await j1('Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': [] })).view;
const blk = (v, id) => v.blocks.find(b => b.block_id === id);

(async () => {
  console.log('1: the department in step 2');
  let v, d;
  if (!V29) {
  v = await step2(S('Celebrity Recording', 'studio'), { free_priority: ['Studio F'] });
  d = blk(v, 'department');
  ok(d && !d.optional && d.element.options.map(o => o.value).join() === 'Music,Audio Post' && d.element.initial_option.value === 'Audio Post', 'Celebrity Recording - Department (Music, Audio Post), set to Tara\'s (Audio Post)');
  const ids = v.blocks.map(b => b.block_id);
  ok(ids.indexOf('department') > ids.indexOf('client') && ids.indexOf('department') < ids.indexOf('engineer'), 'under Client, above the engineer');
  v = await step2(S('Celebrity Recording', 'studio', 'U5'), { free_priority: ['Studio F'] });
  ok(blk(v, 'department') && !blk(v, 'department').element.initial_option && blk(v, 'department').element.placeholder.text === 'Select a department', 'a booker from another department (Marketing) - asked, nothing set');
  v = await step2(S('Van Recording', 'studio'), { free_priority: ['Studio M'] });
  ok(blk(v, 'department') && blk(v, 'department').element.options.map(o => o.value).join() === 'Audio Post,Music', 'Van Recording - Audio Post or Music');
  }
  for (const t of ['VO Recording', 'Band Recording']) { v = await step2(S(t, 'studio'), { free_priority: ['Studio 7', 'Studio F'] }); ok(!blk(v, 'department'), t + ' - one department, not asked'); }
  const read2 = async (vv, meta) => j1('Read Step 2', [], { 'Check Signature': [{ json: { user: 'U026N6E1R' } }], 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta), blocks: [], state: { values: vv } } } } }], 'Read Cache 3': cacheRow });
  const M = Object.assign(S('Celebrity Recording', 'studio'), { label: 'Celebrity Recording' });
  let r = await read2({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'qatest' } }, client: { client_in: { value: 'jem lim' } }, department: { department_pick: tv('Audio Post') }, engineer: { engineer_pick: tv('U026N6E1R') } }, M);
  ok(r.valid && r.prep.department === 'Audio Post', 'the department goes to Book Session - it never asks after Book');
  ok(r.again && r.again.d === '2027-10-19' && r.again.s === '11:30' && r.again.e === '12:30' && r.again.p === 'Celebrity Recording' && r.again.r === 'Studio F' && r.again.pj === 'qatest' && r.again.c === 'Jem Lim' && r.again.en === 'U026N6E1R',
     'the form\'s answers kept for "Book a room" again', r.again);

  console.log('2: the window is gone -> the DM');
  const AP = { go: false, view_id: 'V1', warn: 'Which department is this booking for?' };
  let q = await run('Question DM', [{ json: { ok: false, error: 'not_found' } }], { 'Read Step 2': [{ json: r }], 'After Prepare': [{ json: AP }] });
  ok(q.length === 1 && q[0].json.channel === 'U026N6E1R' && q[0].json.blocks[0].text.text === '⚠️ *Not booked yet.* Which department is this booking for?', 'Show Question not_found (Tara, 16:07) -> "Not booked yet." in the DM', q[0] && q[0].json);
  const btn = q[0].json.blocks[1].elements[0];
  ok((btn.action_id === 'open_book' || (btn.action_id === 'book_continue' && btn.text.text === 'Continue booking')) && JSON.parse(btn.value).p === 'Celebrity Recording' && JSON.parse(btn.value).r === 'Studio F',
     '"Book a room" opens the form filled in (v45: "Continue booking" - step 2 again)');
  const s1 = await j1('Build Step 1', [], { 'Check Signature': [{ json: { user: 'U026N6E1R', triggerId: 'T', channel: 'D1' } }], 'Read Cache': cacheRow, 'Read Request': [{ json: { payload: { actions: [{ action_id: 'open_book', value: btn.value }], container: { channel_id: 'D1', message_ts: '9.9' } } } }] });
  const pb = s1.view.blocks.find(b => b.block_id === 'purpose');
  ok(pb.element.initial_option.value === 'Celebrity Recording' && s1.view.blocks.find(b => b.block_id === 'date').element.initial_date === '2027-10-19'
     && s1.view.blocks.find(b => b.block_id === 'start').element.initial_option.value === '11:30', 'step 1 opens at Celebrity Recording, Oct 19, 11:30');
  q = await run('Question DM', [{ json: { ok: true } }], { 'Read Step 2': [{ json: r }], 'After Prepare': [{ json: AP }] });
  ok(q.length === 0, 'the window still open (ok) -> no DM');
  let x = await run('Result DM', [{ json: { ok: false, error: 'not_found' } }], { 'Read Step 2': [{ json: r }], 'After Book': [{ json: { ok: false, warn: 'That room was just taken. Pick another room, or go *Back*.' } }] });
  ok(x.length === 1 && /^⚠️ \*Not booked\.\* That room was just taken/.test(x[0].json.blocks[0].text.text), 'a problem after Book, window gone -> "Not booked." in the DM');
  x = await run('Result DM', [{ json: { ok: false, error: 'not_found' } }], { 'Read Step 2': [{ json: r }], 'After Book': [{ json: { ok: true } }] });
  ok(x.length === 0, 'booked, window gone -> nothing extra (the Booked card is DM\'d already)');
  const rs = Object.assign({}, r, { s: Object.assign({}, r.s, { series: { dates: ['2027-10-19', '2027-10-26', '2027-11-02'] } }) });
  x = await run('Series DM', [{ json: { ok: false, error: 'not_found' } }], { 'Read Step 2': [{ json: rs }], 'After Prepare Series': [{ json: { view_id: 'V1', view: {} } }] });
  ok(x.length === 1 && /Your 3 dates were checked, but the window was closed before you confirmed them/.test(x[0].json.blocks[0].text.text), 'a series checked, window gone -> "Your 3 dates were checked…" in the DM');
  x = await run('Change DM', [{ json: { ok: false, error: 'not_found' } }], { 'After Move': [{ json: { ok: false, why: 'Studio 7 is taken then.' } }], 'Read Change': [{ json: { user: 'U026N6E1R', b: { t: 'QATEST / HL' } } }] });
  ok(x.length === 1 && x[0].json.blocks[0].text.text === '⚠️ *QATEST / HL* was not changed. Studio 7 is taken then.', 'a change refused, window gone -> "… was not changed." in the DM');
  x = await run('Change DM', [{ json: { ok: false } }], { 'After Move': [{ json: { ok: true } }], 'Read Change': [{ json: { user: 'U1', b: {} } }] });
  ok(x.length === 0, 'changed, window gone -> nothing extra (DM Changed)');

  if (/v28: not booked and the window/.test(JSON.stringify(si.nodes))) {   // v28: the message keeps the details when not booked
    const head = { type: 'section', block_id: 'src_head', text: { type: 'mrkdwn', text: 'Your booking details:\n🗓️ *Studio F · Tuesday, October 19, 2027 · 11:30 AM – 12:30 PM*' } };
    const orig = [{ type: 'section', text: { type: 'mrkdwn', text: 'Hi, I’m Jessie!' } }, { type: 'actions', elements: [{ action_id: 'open_book', value: 'menu' }] }];
    const MS = { ok: true, channel: 'D1', ts: '1.1', blocks: [head], text: 'x', original: orig, offer: false, head };
    let sd = await run('Source Done', [{ json: { ok: false, error: 'not_found' } }], { 'Mark Source': [{ json: MS }], 'After Prepare': [{ json: AP }] });
    ok(sd[0].json.blocks[0].text.text === head.text.text && sd[0].json.blocks[1].elements[0].text === '⚠️ Not booked yet – see below', 'v28: not booked, window gone -> the message keeps the details, "⚠️ Not booked yet – see below"');
    sd = await run('Source Done', [{ json: { ok: true } }], { 'Mark Source': [{ json: MS }], 'After Prepare': [{ json: AP }] });
    ok(sd[0].json.blocks === orig, 'v28: the question shown in the window -> the message back as it was (as before)');
    sd = await run('Source Done', [{ json: { ok: false, error: 'not_found' } }], { 'Mark Source': [{ json: Object.assign({}, MS, { offer: true }) }], 'After Book': [{ json: { ok: true } }] });
    ok(sd[0].json.blocks[1].elements[0].text === '✅ Booked.', 'v28: booked (window gone) -> "✅ Booked." as before');
  }
  console.log('wiring and wording');
  const C = si.connections, outs = n => [].concat(...((C[n] || {}).main || []).map(o => (o || []).map(c => c.node)));
  ok(['Show Question', 'Show Result', 'Show Series Step', 'Show Change Result'].every((n, i) => outs(n).indexOf(['Question DM', 'Result DM', 'Series DM', 'Change DM'][i]) !== -1)
     && ['Question DM', 'Result DM', 'Series DM', 'Change DM'].every(n => outs(n)[0] === 'DM Not Shown'), 'each view update -> its DM step -> DM Not Shown (chat.postMessage)');
  const dm = si.nodes.find(n => n.name === 'DM Not Shown');
  ok(dm.parameters.url === 'https://slack.com/api/chat.postMessage' && /\$json\.channel/.test(dm.parameters.jsonBody) && dm.onError === 'continueRegularOutput', 'DM Not Shown sends what its step built');
  ok(outs('Show Question').indexOf('Source Done') !== -1 && outs('Show Result').indexOf('Booked?') !== -1, 'the old paths unchanged (Source Done, Booked?)');
  const rsj = si.nodes.find(n => n.name === 'Read Step 2').parameters.jsCode;
  ok(/we’ll let you know in your DM once it’s done/.test(rsj) && /Checking availability for each date\. (?:' \+ _wait \+ ' )?You can close this window – we’ll let you know in your DM\./.test(rsj), 'the working lines say "in your DM"');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
