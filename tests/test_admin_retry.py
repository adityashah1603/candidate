from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from relay import InjectedCrash, Relay


class AdminRetryTest(unittest.TestCase):
    """Reproduces fixtures/deployment_events.jsonl case "admin_retry": an
    operator hits retry in the admin panel on a run that looks stuck. The
    original run is still on record (crashed mid-write, status stuck at
    'running'), so retry must resume it, not start a second delivery under
    the same approval.
    """

    def test_retry_on_a_stalled_run_resumes_it_instead_of_starting_a_new_one(
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

            run_id = relay.submit("deploy-404", payload)

            # Simulate the worker stall from the fixture: the process
            # crashed after writing the first asset, leaving the run stuck
            # with status='running' and no receipt.
            with self.assertRaises(InjectedCrash):
                relay.run_once(run_id, crash_at="after_first_provider_write")
            self.assertEqual(relay.get(run_id)["status"], "running")

            # Operator hits retry in the admin panel on the stuck run.
            retried_run_id = relay.retry(run_id)

            self.assertEqual(
                retried_run_id,
                run_id,
                "retry on a stalled run should resume that run, not start "
                "a second delivery under the same approval",
            )

            with relay._connect() as connection:
                row_count = connection.execute(
                    "SELECT COUNT(*) AS n FROM deployments "
                    "WHERE idempotency_key = ?",
                    ("deploy-404",),
                ).fetchone()["n"]
            self.assertEqual(
                row_count,
                1,
                "retry should not insert a second deployment row for the "
                "same idempotency key",
            )

            relay.run_once(retried_run_id)

            objects = relay.provider.list_objects()
            self.assertEqual(len(objects), len(payload["assets"]))


if __name__ == "__main__":
    unittest.main()
