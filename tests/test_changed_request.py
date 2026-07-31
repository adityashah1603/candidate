from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from relay import IdempotencyConflict, Relay


class ChangedRequestTest(unittest.TestCase):
    """Reproduces fixtures/deployment_events.jsonl case "changed_request":
    the same idempotency key resubmitted with different asset content (the
    operator edited the selection and retried from the same UI request).
    That must not be silently accepted under the old run - it should be
    refused, since the key no longer identifies one unambiguous request.
    """

    def test_same_key_with_different_payload_raises_idempotency_conflict(
        self,
    ) -> None:
        payload = json.loads(
            Path("fixtures/deployment_request.json").read_text()
        )
        changed_payload = copy.deepcopy(payload)
        changed_payload["assets"][3]["source_sha256"] = "f" * 64

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            db_path = root / "deployments.db"
            provider_path = root / "fake-hubspot.json"
            relay = Relay(db_path, provider_path)

            first_run_id = relay.submit("deploy-303", payload)

            with self.assertRaises(IdempotencyConflict):
                relay.submit("deploy-303", changed_payload)

            # The original run must be untouched - no new/overwritten row.
            self.assertEqual(relay.get(first_run_id)["payload"], payload)


if __name__ == "__main__":
    unittest.main()
