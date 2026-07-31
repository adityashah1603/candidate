from __future__ import annotations

import json
import tempfile
from pathlib import Path

from relay import InjectedCrash, Relay


def main() -> None:
    payload = json.loads(
        Path("fixtures/deployment_request.json").read_text()
    )
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        db_path = root / "deployments.db"
        provider_path = root / "fake-hubspot.json"
        relay = Relay(db_path, provider_path)
        run_id = relay.submit("campaign-deploy-001", payload)

        try:
            relay.run_once(
                run_id,
                crash_at="after_first_provider_write",
            )
        except InjectedCrash as error:
            print(f"INJECTED CRASH: {error}")

        restarted = Relay(db_path, provider_path)
        restarted.recover()
        print("FINAL STATE")
        print(json.dumps(restarted.get(run_id), indent=2))
        print("FAKE HUBSPOT OBJECTS")
        print(json.dumps(restarted.provider.list_objects(), indent=2))


if __name__ == "__main__":
    main()
