const ev = $input.first().json || {};
const REQ = $('When Executed by Another Workflow').first().json;
if (!ev.id) {
  return [{ json: { status:'FAILED',
    human:'The booking was not created - the calendar returned no event. Tell the requester it failed and ask how they want to proceed. Do not say it is booked.' } }];
}
const got = {
  start: (ev.start && (ev.start.dateTime || ev.start.date)) || '',
  end:   (ev.end   && (ev.end.dateTime   || ev.end.date))   || ''
};
const same = t => new Date(got[t]).getTime() === new Date(REQ[t + '_iso']).getTime();
if (!REQ.all_day && (!same('start') || !same('end'))) {
  return [{ json: { status:'MISMATCH', event_id: ev.id, created: got,
    human:'The event was created but the times do not match what was agreed. It is now ' + got.start + ' to ' + got.end + '. Tell the requester exactly that - do not confirm it as correct.' } }];
}
const declined = (ev.attendees || []).filter(a => a.responseStatus === 'declined').map(a => a.displayName || a.email);
if (declined.length) {
  return [{ json: { status:'ROOM_DECLINED', event_id: ev.id, declined,
    human:'The room declined the booking because it is already taken, so this booking is NOT valid. Tell the requester and offer 2-3 alternatives. Do not delete whatever holds the room.' } }];
}
// Room resources answer the invitation a few seconds after the event is created,
// so responseStatus is always 'needsAction' in this response. Reporting it as pending
// is noise on every booking. A genuine refusal shows up as 'declined', handled above.
return [{ json: { status:'CREATED', event_id: ev.id, title: ev.summary,
  human:'Booked.' } }];
