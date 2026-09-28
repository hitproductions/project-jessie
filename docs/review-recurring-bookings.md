# Recurring bookings review (from ChatGPT, for Howard)

*Not yet checked against the code. Linked from [`handoff-tara-2026-09-29.md`](handoff-tara-2026-09-29.md).*

> Next, improve Jessie's recurring-booking workflows. Use the latest files and preserve the previous caching, booking,
> consent, confirmation, background-job, and AI optimizations. Focus on Expand Series, Book Series, and their
> connections to Project Jessie and Book Session.
>
> 1. **Fix recurrence validation.** Reject nonexistent dates instead of silently normalizing them (February 30 must
>    not become March 2). Validate hours 00–23 and minutes 00–59. Require a positive integer count when using count.
>    Require exactly one end condition: count or until_date, preserving the caller's existing "unused count"
>    convention, such as 0. Reject invalid weekday codes rather than silently dropping them. Preserve the existing
>    16-occurrence limit and one-year maximum. Handle overnight sessions explicitly according to existing booking
>    policy; never silently reinterpret reversed times.
> 2. **Keep preview and execution consistent.** Use one shared recurrence implementation, or verify both copies with
>    identical tests. The exact dates, times, rooms, and booking details confirmed by the requester must be the ones
>    executed. Do not regenerate a different series from new AI arguments after confirmation. Apply the existing
>    structured confirmation mechanism to series where needed.
> 3. **Resolve shared details once.** Resolve staff, client, session type, and room reference information once per
>    series and pass it to each occurrence. Use the existing cache and staff_data mechanism where appropriate. Inspect
>    Book Session's actual inputs and update mappings so the information reaches it. Preserve live authorization and
>    fresh conflict checks for each calendar mutation.
> 4. **Make partial completion and retries reliable.** Assign a stable series action ID and occurrence IDs. Persist
>    each occurrence's outcome and created event ID. On retry, reconcile uncertain outcomes and resume unfinished
>    occurrences without recreating successful ones. Preserve the existing behavior of retaining successful bookings
>    when other dates fail or conflict. Do not introduce automatic rollback of the entire series.
> 5. **Report every occurrence accurately.** Correlate results by occurrence ID rather than array position alone.
>    Distinguish created, conflict/skipped, pending consent, rejected, failed, and uncertain outcomes. Never say the
>    whole series was booked unless every occurrence succeeded. A failure after some successful writes must still
>    leave a recoverable record of those successes.
> 6. **Optimize without introducing booking races.** Reuse shared lookups first. Do not blindly parallelize calendar
>    writes. Any concurrency must respect resource overlap, existing locking, API limits, and retry behavior. Use the
>    background-job mechanism for reporting and secondary notifications.
> 7. **Test.** Cover leap years, invalid dates/times, fractional counts, both/neither end conditions, weekday
>    selection, overnight policy, Manila all-day boundaries, occurrence limits, partial conflicts, mid-series API
>    failure, duplicate requests, and retry after partial completion. Measure external lookup counts and execution
>    time where possible.
>
> Return corrected importable JSONs, tests and results, any required state-schema changes, and a short summary of the
> improvement.

Notes for checking it:
- The **series summary is still model-written** (the "after launch" item in CLAUDE.md). Point 2 is really "Prepare
  Series": code writes the series summary with a check code, like Prepare Booking and Prepare Cancel.
- "Background-job mechanism" and "existing locking" do not exist in Jessie — nothing like that was built tonight.
- Tonight's series test (Nov 2027, 5 Tuesdays) booked correctly; its summary lacked Booked by (bug 14).
