from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Iterator


class InjectedCrash(RuntimeError):
    pass


class IdempotencyConflict(RuntimeError):
    pass


class RunCancelled(RuntimeError):
    pass


class VerificationMismatch(RuntimeError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class FakeHubSpot:
    """Small durable provider simulation with idempotent draft creation.

    Like the real destination, this provider owns the objects it stores. It
    accepts what you send, applies its own rules to it, and returns what it
    decided to keep.
    """

    DISPLAY_NAME_LIMIT = 40

    def __init__(self, state_path: Path) -> None:
        self.state_path = Path(state_path)
        if not self.state_path.exists():
            self.state_path.write_text("{}")

    def _load(self) -> dict[str, dict[str, str]]:
        return json.loads(self.state_path.read_text())

    def _save(self, objects: dict[str, dict[str, str]]) -> None:
        self.state_path.write_text(_canonical_json(objects))

    def _store_display_name(self, value: str) -> str:
        return str(value).strip()[: self.DISPLAY_NAME_LIMIT]

    def create_draft(
        self,
        *,
        external_key: str,
        asset: dict[str, Any],
    ) -> dict[str, str]:
        objects = self._load()
        existing = objects.get(external_key)
        candidate = {
            "object_id": f"hs-{_digest_text(external_key)[:12]}",
            "external_key": external_key,
            "source_asset_id": str(asset["asset_id"]),
            "source_sha256": str(asset["source_sha256"]),
            "object_type": str(asset["type"]),
            "display_name": self._store_display_name(asset["display_name"]),
            "status": "draft",
        }
        if existing is not None:
            if existing != candidate:
                raise IdempotencyConflict(
                    f"provider key {external_key!r} was reused"
                )
            return dict(existing)
        objects[external_key] = candidate
        self._save(objects)
        return dict(candidate)

    def read(self, external_key: str) -> dict[str, str]:
        return dict(self._load()[external_key])

    def list_objects(self) -> list[dict[str, str]]:
        return [dict(value) for value in self._load().values()]


class Relay:
    def __init__(self, db_path: Path, provider_state_path: Path) -> None:
        self.db_path = Path(db_path)
        self.provider = FakeHubSpot(provider_state_path)
        self._init_db()

    @contextlib.contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Open a connection for one unit of work and always close it.

        A bare sqlite3.Connection used as `with conn:` only commits/rolls
        back the transaction on exit - it does not close the connection.
        Every prior call site leaked an open handle, which is invisible on
        Linux but leaves the db file locked on Windows (callers saw
        "database is being used by another process" when a tempdir tried
        to clean up).
        """
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS deployments (
                    id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    receipt_json TEXT
                )
                """
            )

    def submit(self, idempotency_key: str, payload: dict[str, Any]) -> str:
        """Reuse the existing run for a repeated idempotency key.

        A retried submission (browser retry, double-click, ...) carries the
        same idempotency key as the original and must resolve to the same
        run. But if the payload under that key has changed - the operator
        edited the selection and resubmitted from the same UI request - the
        key no longer names one unambiguous request, so it is refused
        rather than silently deployed under the old run or the new content.
        """
        payload_json = _canonical_json(payload)
        payload_hash = _digest_text(payload_json)
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT id, payload_hash FROM deployments "
                "WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if existing is not None:
                if existing["payload_hash"] != payload_hash:
                    raise IdempotencyConflict(
                        f"idempotency key {idempotency_key!r} was reused "
                        "with a different payload"
                    )
                return str(existing["id"])
            run_id = str(uuid.uuid4())
            connection.execute(
                """
                INSERT INTO deployments
                    (id, idempotency_key, payload_hash, payload_json, status)
                VALUES (?, ?, ?, ?, 'pending')
                """,
                (run_id, idempotency_key, payload_hash, payload_json),
            )
        return run_id

    def get(self, run_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM deployments WHERE id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            raise KeyError(run_id)
        result = dict(row)
        result["payload"] = json.loads(result.pop("payload_json"))
        receipt_json = result.pop("receipt_json")
        result["receipt"] = (
            json.loads(receipt_json) if receipt_json is not None else None
        )
        return result

    def cancel(self, run_id: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE deployments SET status = 'cancelled' WHERE id = ?",
                (run_id,),
            )

    def retry(self, run_id: str) -> str:
        """The admin panel's retry button for a deployment operators call stuck.

        Resumes the existing run for the operator's idempotency key instead
        of starting a fresh deployment - the same lookup submit() does. A
        retry is not a new approval; a second row under the same key would
        mean a second delivery for the same request.
        """
        previous = self.get(run_id)
        return self.submit(
            str(previous["idempotency_key"]), previous["payload"]
        )

    def run_once(
        self,
        run_id: str,
        *,
        crash_at: str | None = None,
    ) -> dict[str, Any]:
        run = self.get(run_id)
        if run["status"] == "cancelled":
            raise RunCancelled(f"run {run_id!r} was cancelled")

        with self._connect() as connection:
            connection.execute(
                "UPDATE deployments SET status = 'running' "
                "WHERE id = ? AND status != 'cancelled'",
                (run_id,),
            )

        readbacks: list[dict[str, str]] = []
        for index, asset in enumerate(run["payload"]["assets"]):
            if self.get(run_id)["status"] == "cancelled":
                raise RunCancelled(f"run {run_id!r} was cancelled")
            external_key = f"{run_id}:{asset['asset_id']}"
            try:
                stored = self.provider.read(external_key)
            except KeyError:
                self.provider.create_draft(
                    external_key=external_key,
                    asset=asset,
                )
                if crash_at == "after_first_provider_write" and index == 0:
                    raise InjectedCrash(
                        "crashed after provider write and before local "
                        "receipt"
                    )
                stored = self.provider.read(external_key)
            readbacks.append(stored)

        mismatches = self._find_mismatches(run["payload"]["assets"], readbacks)
        if mismatches:
            raise VerificationMismatch(
                f"run {run_id!r} does not match the approved assets: "
                + "; ".join(mismatches)
            )

        receipt = {
            "run_id": run_id,
            "payload_sha256": run["payload_hash"],
            "objects": readbacks,
            "verified": True,
        }
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE deployments
                SET status = 'done', receipt_json = ?
                WHERE id = ? AND status != 'cancelled'
                """,
                (_canonical_json(receipt), run_id),
            )
        return receipt

    def _find_mismatches(
        self,
        approved_assets: list[dict[str, Any]],
        stored_objects: list[dict[str, str]],
    ) -> list[str]:
        """Compare what the provider stored against what was approved.

        display_name is compared after applying the provider's documented
        DISPLAY_NAME_LIMIT truncation - a truncated name is not a mismatch,
        it is the provider's known, expected behavior. Every other field is
        compared exactly.
        """
        limit = self.provider.DISPLAY_NAME_LIMIT
        mismatches: list[str] = []
        for asset, stored in zip(approved_assets, stored_objects):
            asset_id = str(asset["asset_id"])
            expected_fields = {
                "display_name": str(asset["display_name"]).strip()[:limit],
                "source_asset_id": str(asset["asset_id"]),
                "source_sha256": str(asset["source_sha256"]),
                "object_type": str(asset["type"]),
            }
            for field, expected_value in expected_fields.items():
                actual_value = stored.get(field)
                if actual_value != expected_value:
                    mismatches.append(
                        f"{asset_id}.{field} expected {expected_value!r}, "
                        f"got {actual_value!r}"
                    )
        return mismatches

    def recover(self) -> None:
        """
        Starter behavior: enough recovery for the happy-path demo.

        Operator evidence reports other cases that this does not make safe.
        """
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id FROM deployments WHERE status = 'running'"
            ).fetchall()
        for row in rows:
            self.run_once(str(row["id"]))
