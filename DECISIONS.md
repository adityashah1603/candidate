# Decisions

Short notes are fine. Fill this in before you submit.

- Time actually spent: Around 1 hr 20 mins

- What changed between your roadmap and what you shipped: What i promised was one delivery per request, i shipped one delivery per idempotency key, something which wasnt anticipated in the roadmap is the double_submit_new_key feature, for two different keys the relay cant know that its the same approval without using a stricter deduplication, this was identified during testing and left open.

I also didnt consider the Windows SQLite connection leak, i found it when trying the inital run and fixed it, included in the road map after a trial test.

- What you had the coding agent do, and where you overrode it: For every bug i asked the agent to reproduce it using a test and saw the failure, i asked it to show the code and give me what changed after review i would confirm and verify if it goes in or not, I over rode the agent for the verfied=true/false flag, i asked the agent to skip rewriting existing objects on resume and add a real comparison pass to raise a new verification mismatch.

- What your implementation actually promises an operator:
One delivery per idempotency key
Diff payload under a old key is refused and throws idempotency conflict
crash safe recovery
once cancelled no further writes
verfied=true only if all assets match
Failurs/success are never assumed

- For each promise, the check that fails first if it stops holding:
idempotency_key lookup in submit() and retry() before insert - if bypass you see duplicate rows sharing the idempotency key = duplicate provider objects
payload hashcomparison in submit against existing row
run_oce() read before write asset, recover() status = 'running'
status = cancelled checks at top of run once and inside the asset loop.

- What you fixed at the cause, and what you only stopped from showing:
Windows connect leak, duplicate delivery, retry duplication, silent payload accept, cancellation overwrite, hardcoded verify, unambiguous write

- What is still unsafe, including anything that came up during the session and
  stayed open:
  double_submit_new_key - new idempotecy key per retry still produces duplicate drafts, could add content based dedup
  cancellation prevents further write- doesnt cancel mid write
  no test for provider response which is a failure



- The next failure you would inject:
real deployment where two concurrent processes are submitted at once on same run_id to check if hubspots non atomic rw can be made to lose or corrupt update