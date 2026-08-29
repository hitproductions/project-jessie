const v = $input.first().json || {};
return [{ json: {
  status: v.verdict || 'FAILED',
  reason: v.reason || 'CREATE_FAILED',
  conflicts: v.conflicts || null,
  unverifiable: v.unverifiable || null,
  human: v.human || 'The booking failed and nothing was created. Tell the requester it did not go through.'
} }];
