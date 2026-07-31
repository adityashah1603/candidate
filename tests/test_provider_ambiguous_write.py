from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from relay import FakeHubSpot, Relay


class TimeoutThenFoundHubSpot(FakeHubSpot):
    """Test-only wrapper around FakeHubSpot - not a change to it - that
    simulates a provider timeout: the write actually lands on the provider,
    but the response never reaches the caller. This is exactly
    fixtures/deployment_events.jsonl's "provider_ambiguous_write" case:
    accepted: null, error: gateway_timeout, followed by a readback that
    finds the object anyway.
    """

    def __init__(self, state_path: Path, timeout_external_key: str) -> None:
        super().__init__(state_path)
        self._timeout_external_key = timeout_external_key
        self._already_timed_out = False

    def create_draft(
        self, *, external_key: str, asset: dict[str, Any]
    ) -> dict[str, str]:
        result = super().create_draft(external_key=external_key, asset=asset)
        if (
            external_key == self._timeout_external_key
            and not self._already_timed_out
        ):
            self._already_timed_out = True
            raise TimeoutError("gateway_timeout")
        return result


class ProviderAmbiguousWriteTest(unittest.TestCase):
    """Reproduces fixtures/deployment_events.jsonl case
    "provider_ambiguous_write": a write to the provider times out, so the
    relay does not actually know whether it landed. It must resolve that
    by reading the object back, not by assuming success or assuming
    failure.
    """

    def test_run_once_reads_back_after_a_timed_out_write_instead_of_guessing(
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

            run_id = relay.submit("deploy-timeout", payload)

            # Swap in the timeout-simulating provider for this run only -
            # the underlying state file is unchanged, so this is exactly
            # the same provider, just with one write's response dropped.
            timeout_external_key = f"{run_id}:asset-email-002"
            relay.provider = TimeoutThenFoundHubSpot(
                provider_path, timeout_external_key
            )

            receipt = relay.run_once(run_id)

            self.assertTrue(receipt["verified"])
            self.assertEqual(len(receipt["objects"]), len(payload["assets"]))
            stored_asset_ids = {
                obj["source_asset_id"] for obj in receipt["objects"]
            }
            self.assertEqual(
                stored_asset_ids,
                {asset["asset_id"] for asset in payload["assets"]},
            )


if __name__ == "__main__":
    unittest.main()
