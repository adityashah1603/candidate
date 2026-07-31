Before running anything i read core.py and noticed:

1) submit() - incorrectly creates a new deployment everytime
2) retry() - reruns same approval request under a fresh deployment
3) recover() - not safe for other cases just for the demo
4) RunCancelled - defined and exported but incomplemte (dont see in core.py)
5) "verified=True" is hardcoded
6) FakeHubSpot.DISPLAY_NAME_LIMIT = 40 - shortens the display nam from requests
7) cancel in core.py isnt actually cancelling just writes it there
8) objects are identified by run_id instead of idempotency key, causes duplicates.

Pre Req: couldnt run the demo file- gave an error of database being used by other process (googled this error - windows error) - need to fix connection leak
How and what to fix:
1) submit() should look up esiting rows using idempotency key, reuse if it matches
2) retry() should also work like that instead of always create a new run
3) Write idempotency conflict when same key used with different task
4) Run once should check run status before write, when cancelled overwrite should be prevented
5) Verified = true is hardcoded, it should be set when when it actually is true
6) resolving ambiguous writes, service should perform a readback before finalizing runs status.

What I can promise:
By the end of the coding session the code would:
1) Give only one delivery per request
2) Edited resubmission would be refused - new request needs to be started to deploy edited content
3) Crash safe recovery - if process is terminated anywhere it restarts the run to a consistent state without duplicating
4) Once cancelled no further writes
5) Verified = true only after every objects field have been validates against the apporved assets
6) Ambiguous responses by the provider are resolved (assumed now)
