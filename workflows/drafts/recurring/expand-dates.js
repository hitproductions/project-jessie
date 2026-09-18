// Expand a structured recurrence into concrete date windows.
// Pure calendar math in UTC (dates only); the +08:00 time is attached at the end,
// so the runtime timezone never shifts a day. Returns a refusal object or {occurrences}.
//
// Guards enforced here (the safety-critical part):
//   - frequency and start_date required
//   - an explicit end required: exactly a count OR an until_date (never open-ended)
//   - the series may not span more than one year from the start
//
// Inputs (from the agent via the Book Series tool):
//   frequency  'daily' | 'weekly'
//   by_days    ['MO','TU',...] for weekly (defaults to the start date's weekday)
//   start_date 'YYYY-MM-DD'
//   count      integer  (one of count / until_date required)
//   until_date 'YYYY-MM-DD'
//   all_day    boolean
//   time_start 'HH:MM'   (required unless all_day)
//   time_end   'HH:MM'
function expandDates(REQ) {
  const DOW = { SU:0, MO:1, TU:2, WE:3, TH:4, FR:5, SA:6 };
  const isDate = s => /^\d{4}-\d{2}-\d{2}$/.test(String(s || '').trim());
  const fmt = d => d.toISOString().slice(0, 10);

  const freq = String(REQ.frequency || '').trim().toLowerCase();
  const start = String(REQ.start_date || '').trim();
  const allDay = REQ.all_day === true || String(REQ.all_day).toLowerCase() === 'true';
  const t0 = String(REQ.time_start || '').trim();
  const t1 = String(REQ.time_end || '').trim();

  if (freq !== 'daily' && freq !== 'weekly')
    return { status: 'MISSING_DETAILS', reason: 'I need to know how often it repeats - daily or weekly.' };
  if (!isDate(start))
    return { status: 'MISSING_DETAILS', reason: 'I need the date the series starts on.' };
  if (!allDay && (!/^\d{1,2}:\d{2}$/.test(t0) || !/^\d{1,2}:\d{2}$/.test(t1)))
    return { status: 'MISSING_DETAILS', reason: 'I need a start and end time (or say it is all-day).' };

  const hasCount = REQ.count != null && String(REQ.count).trim() !== '' && Number(REQ.count) > 0;
  const hasUntil = isDate(REQ.until_date);
  if (!hasCount && !hasUntil)
    return { status: 'MISSING_END', reason: 'A repeating booking needs an end - a number of sessions or a stop date. How many, or until when?' };

  const startD = new Date(start + 'T00:00:00Z');
  if (isNaN(startD.getTime()))
    return { status: 'MISSING_DETAILS', reason: 'The start date is not a real date.' };

  const oneYear = new Date(startD); oneYear.setUTCFullYear(oneYear.getUTCFullYear() + 1);
  const untilD = hasUntil ? new Date(REQ.until_date + 'T00:00:00Z') : null;
  if (untilD && untilD < startD)
    return { status: 'MISSING_DETAILS', reason: 'The stop date is before the start date.' };
  if (untilD && untilD > oneYear)
    return { status: 'SPAN_TOO_LONG', reason: 'A repeating booking can run at most one year. Give a stop date within a year of the start, or a smaller count.' };

  // weekly day-of-week set (default to the start date's weekday).
  // Accepts an array or a comma string ("TU" or "MO,WE"); the agent passes a string.
  let byDays = Array.isArray(REQ.by_days)
    ? REQ.by_days.map(d => String(d).toUpperCase().slice(0, 2))
    : String(REQ.by_days || '').split(',').map(d => d.trim().toUpperCase().slice(0, 2)).filter(Boolean);
  if (freq === 'weekly' && !byDays.length) {
    byDays = [Object.keys(DOW).find(k => DOW[k] === startD.getUTCDay())];
  }
  const wanted = new Set(byDays.map(d => DOW[d]).filter(n => n != null));
  if (freq === 'weekly' && !wanted.size)
    return { status: 'MISSING_DETAILS', reason: 'Which day(s) of the week should it repeat on?' };

  const N = hasCount ? Number(REQ.count) : Infinity;
  const dates = [];
  const cur = new Date(startD);
  // Absolute iteration ceiling: one year of days plus slack. Prevents any runaway.
  for (let guard = 0; guard <= 372 && dates.length < N; guard++) {
    if (cur > oneYear) break;
    if (untilD && cur > untilD) break;
    if (freq === 'daily' || wanted.has(cur.getUTCDay())) dates.push(fmt(cur));
    cur.setUTCDate(cur.getUTCDate() + 1);
  }

  if (hasCount && dates.length < N)
    return { status: 'SPAN_TOO_LONG', reason: 'That many sessions would run past one year. Use a smaller count or a shorter interval.', got: dates.length, wanted: N };
  if (!dates.length)
    return { status: 'MISSING_DETAILS', reason: 'That pattern produced no dates - check the day(s) and range.' };

  const occurrences = dates.map(d => allDay
    ? { date: d, all_day: true }
    : { start_iso: d + 'T' + t0.padStart(5, '0') + ':00+08:00',
        end_iso:   d + 'T' + t1.padStart(5, '0') + ':00+08:00', all_day: false });

  return { status: 'OK', count: occurrences.length, occurrences };
}

module.exports = { expandDates };
