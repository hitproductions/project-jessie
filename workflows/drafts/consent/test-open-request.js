// Offline tests for Open Consent Request builders. Run: node workflows/drafts/consent/test-open-request.js
const { COLUMNS, requestId, buildRow, incumbentDM, requesterReply, approvalsLog } = require('./open-request');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

const now = '2027-10-20T09:00:00+08:00';
const cfg = { maxWindowH: 24, minLeadMin: 60 };
const c = {
  requester: 'ULETTY', requesterName: 'Ms. Letty',
  approver: 'UJC', approverName: 'JC',
  room: 'Studio F', reqStart: '2027-10-22T14:00:00+08:00', reqEnd: '2027-10-22T17:00:00+08:00',
  incumbentEventId: 'evt123', incumbentTitle: 'NET-PUSO / JC',
  reqType: 'Celebrity Recording', reqPriority: 100, incPriority: 50,
  requesterDM: 'D_LETTY', approverDM: 'D_JC',
};

console.log('requestId');
ok('sortable compact stamp + requester', requestId(now, 'ULETTY') === '20271020010000-ULETTY');
ok('unknown requester falls back', requestId(now, '') === '20271020010000-unknown');

console.log('\nbuildRow');
const { id, deadline, row } = buildRow(c, now, cfg);
ok('row has exactly the 23 header keys', JSON.stringify(Object.keys(row)) === JSON.stringify(COLUMNS));
ok('Status PENDING', row['Status'] === 'PENDING');
ok('Kind PREEMPT', row['Kind'] === 'PREEMPT');
ok('Approver is the incumbent booker', row['Approver'] === 'UJC' && row['Approver Name'] === 'JC');
ok('priorities carried', row['Req Priority'] === 100 && row['Inc Priority'] === 50);
ok('incumbent new slot blank at open', row['Incumbent New Start'] === '' && row['Incumbent New End'] === '');
ok('resolution fields blank at open', row['Resolved Via'] === '' && row['Attested By'] === '' && row['Decided At'] === '');
ok('Request ID matches helper', row['Request ID'] === id && id === '20271020010000-ULETTY');
ok('Deadline set (capped by window: now+24h < start-1h)', row['Deadline'] === deadline && deadline === new Date('2027-10-21T09:00:00+08:00').toISOString());

console.log('\nmessages');
ok('incumbent DM names both sides + room + asks yes/no', (() => { const m = incumbentDM(c); return m.includes('JC') && m.includes('Ms. Letty') && m.includes('Studio F') && m.includes('NET-PUSO / JC') && /yes or no/i.test(m); })());
ok('requester reply gives the attestation phrase', (() => { const m = requesterReply(c); return m.includes('cleared with JC') && m.includes('Studio F'); })());
ok('approvals log is tagged PREEMPT + PENDING with ranks', (() => { const m = approvalsLog(c, id, deadline); return m.includes('[PREEMPT]') && m.includes('PENDING') && m.includes('rank 100') && m.includes('rank 50'); })());
ok('when-phrase renders Manila time, not raw ISO', !incumbentDM(c).includes('2027-10-22T14:00:00'));

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
