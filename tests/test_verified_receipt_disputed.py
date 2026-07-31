from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from relay import InjectedCrash, Relay, VerificationMismatch


class VerifiedReceiptDisputedTest(unittest.TestCase):
    """Reproduces fixtures/deployment_events.jsonl case
    "verified_receipt_disputed": a receipt said verified=true for a
    campaign whose drafts did not match what was approved. run_once()
    currently hardcodes verified=True and never reads back and compares
    what the provider actually stored against the approved asset.
    """

    def test_verified_reflects_whether_stored_drafts_actually_match_approved(
        self,
    ) -> None:
        payload = json.loads(
            Path("fixtures/deployment_request.json").read_text()
        )
        # The real approved landing-page name is already 47 chars, so this
        # exercises the 40-char truncation path with nothing else wrong -
        # the correct answer for it alone is still verified=True.
        self.assertGreater(len(payload["assets"][0]["display_name"]), 40)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            db_path = root / "deployments.db"
            provider_path = root / "fake-hubspot.json"
            relay = Relay(db_path, provider_path)

            run_id = relay.submit("deploy-verify", payload)

            # Crash after the first (long-name) asset is written, so it is
            # on record in the provider but the run has not finished or
            # produced a receipt yet.
            with self.assertRaises(InjectedCrash):
                relay.run_once(run_id, crash_at="after_first_provider_write")

            # Simulate the provider ending up with something other than
            # what was approved for that first draft - exactly what
            # fixtures/deployment_events.jsonl's "provider_readback" event
            # for run-11 describes
            # (stored_display_name_matches_approved: false). This edits the
            # provider's on-disk state directly, not the FakeHubSpot class.
            provider_state = json.loads(provider_path.read_text())
            tampered_key = f"{run_id}:asset-lp-001"
            provider_state[tampered_key]["source_sha256"] = "0" * 64
            provider_path.write_text(json.dumps(provider_state))

            with self.assertRaises(VerificationMismatch) as failure:
                relay.run_once(run_id)

            message = str(failure.exception)
            self.assertIn("asset-lp-001", message)
            self.assertIn("source_sha256", message)

            # No receipt was written, and the run was not silently marked
            # done for content that does not match what was approved.
            self.assertIsNone(relay.get(run_id)["receipt"])
            self.assertNotEqual(relay.get(run_id)["status"], "done")


if __name__ == "__main__":
    unittest.main()
