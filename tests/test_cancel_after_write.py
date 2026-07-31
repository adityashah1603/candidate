from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from relay import InjectedCrash, Relay, RunCancelled


class CancelAfterWriteTest(unittest.TestCase):
    """Reproduces fixtures/deployment_events.jsonl case "cancel_after_write":
    the operator cancels after seeing the first landing-page draft, but the
    remaining email drafts appear later anyway and the final status reads
    'done' instead of 'cancelled'.

    recover() alone can't be used to reproduce this: it only picks up rows
    with status='running', and cancel() has already moved the row to
    'cancelled' by the time anything would recover it. The actual gap is
    one level down - run_once() itself has no idea the run was cancelled,
    so anything that calls it again on a cancelled run (a stray retry, a
    duplicate worker, or recover() racing the cancel) finishes the delivery
    anyway. Calling run_once() directly reproduces that deterministically.
    """

    def test_cancelled_run_gets_no_further_writes_and_stays_cancelled(
        self,
    ) -> None:
        payload = json.loads(
            Path("fixtures/deployment_request.json").read_text()
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            db_path = root / "deployments.db"
            provider_path = root / "fake-hubspot.json"
            relay = Relay(db_path, provider_path)

            run_id = relay.submit("deploy-cancel", payload)

            # First asset lands, then the run is interrupted before it can
            # finish - exactly the "provider_write" the operator saw.
            with self.assertRaises(InjectedCrash):
                relay.run_once(run_id, crash_at="after_first_provider_write")

            # Operator cancels the stuck run from the admin panel.
            relay.cancel(run_id)
            self.assertEqual(relay.get(run_id)["status"], "cancelled")

            objects_before = relay.provider.list_objects()
            self.assertEqual(len(objects_before), 1)

            # Something later tries to finish this run anyway.
            with self.assertRaises(RunCancelled):
                relay.run_once(run_id)

            objects_after = relay.provider.list_objects()
            self.assertEqual(
                len(objects_after),
                1,
                "no further HubSpot drafts should be created for a "
                "cancelled run",
            )
            self.assertEqual(
                relay.get(run_id)["status"],
                "cancelled",
                "a cancelled run's status must not be overwritten back to "
                "'done'",
            )


if __name__ == "__main__":
    unittest.main()
