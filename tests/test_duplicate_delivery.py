from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from relay import Relay


class DuplicateDeliveryTest(unittest.TestCase):
    """Reproduces fixtures/deployment_events.jsonl case "duplicate_delivery":
    the same idempotency key and payload submitted twice (e.g. a browser
    retry) should not produce two sets of drafts in HubSpot.
    """

    def test_same_key_same_payload_submitted_twice_yields_one_set_of_drafts(
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

            first_run_id = relay.submit("deploy-202", payload)
            second_run_id = relay.submit("deploy-202", payload)

            relay.run_once(first_run_id)
            relay.run_once(second_run_id)

            objects = relay.provider.list_objects()
            self.assertEqual(
                len(objects),
                len(payload["assets"]),
                f"expected {len(payload['assets'])} objects in HubSpot, "
                f"got {len(objects)}",
            )


if __name__ == "__main__":
    unittest.main()
