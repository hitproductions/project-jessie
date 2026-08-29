const raw = $input.first().json.output;
const text = (typeof raw === 'string' ? raw : '').trim();
const fallback = "Sorry — I lost the thread on that one. Could you say it again?";
return [{ json: { output: text.length ? text : fallback } }];
