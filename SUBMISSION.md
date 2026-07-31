# Submission

- Transcript (file or link): https://github.com/adityashah1603/candidate


- `make demo` output:
INJECTED CRASH: crashed after provider write and before local receipt
FINAL STATE
{
  "id": "ba01c776-4709-440e-be81-2ae35b497ce8",
  "idempotency_key": "campaign-deploy-001",
  "payload_hash": "87f488377edf2d6541e245d030ebf20b246549077442c22356528138014798ad",
  "status": "done",
  "payload": {
    "assets": [
      {
        "asset_id": "asset-lp-001",
        "display_name": "Summer 2026 ABM campaign - primary landing page",
        "source_sha256": "3c75dbe870788ce56574fbf4b66e0646b053b8dde6befc7fbe7b7fd8ff015b71",
        "type": "landing_page"
      },
      {
        "asset_id": "asset-email-001",
        "display_name": "Summer 2026 ABM email 1 - warm intro",
        "source_sha256": "8a19d18fc82d447579f3bc2f8e3af2e38fd5930a0d70ecda24e0c2c39f081ca8",
        "type": "email"
      },
      {
        "asset_id": "asset-email-002",
        "display_name": "Summer 2026 ABM email 2 - product deep dive",
        "source_sha256": "384c042f088907da48c34ea8726c97b944eb9e0a33c2a8272af18cce1cd95793",
        "type": "email"
      },
      {
        "asset_id": "asset-email-003",
        "display_name": "Summer 2026 ABM email 3 - book a call ",
        "source_sha256": "facc744a28fa499897819c280688855618446cb569c7bca603e77e81f044096d",
        "type": "email"
      }
    ],
    "destination": "hubspot-marketing",
    "mode": "draft"
  },
  "receipt": {
    "objects": [
      {
        "display_name": "Summer 2026 ABM campaign - primary landi",
        "external_key": "ba01c776-4709-440e-be81-2ae35b497ce8:asset-lp-001",
        "object_id": "hs-592284b4c8ac",
        "object_type": "landing_page",
        "source_asset_id": "asset-lp-001",
        "source_sha256": "3c75dbe870788ce56574fbf4b66e0646b053b8dde6befc7fbe7b7fd8ff015b71",
        "status": "draft"
      },
      {
        "display_name": "Summer 2026 ABM email 1 - warm intro",
        "external_key": "ba01c776-4709-440e-be81-2ae35b497ce8:asset-email-001",
        "object_id": "hs-26fa251639bd",
        "object_type": "email",
        "source_asset_id": "asset-email-001",
        "source_sha256": "8a19d18fc82d447579f3bc2f8e3af2e38fd5930a0d70ecda24e0c2c39f081ca8",
        "status": "draft"
      },
      {
        "display_name": "Summer 2026 ABM email 2 - product deep d",
        "external_key": "ba01c776-4709-440e-be81-2ae35b497ce8:asset-email-002",
        "object_id": "hs-d92a49605847",
        "object_type": "email",
        "source_asset_id": "asset-email-002",
        "source_sha256": "384c042f088907da48c34ea8726c97b944eb9e0a33c2a8272af18cce1cd95793",
        "status": "draft"
      },
      {
        "display_name": "Summer 2026 ABM email 3 - book a call",
        "external_key": "ba01c776-4709-440e-be81-2ae35b497ce8:asset-email-003",
        "object_id": "hs-0210288d0e2c",
        "object_type": "email",
        "source_asset_id": "asset-email-003",
        "source_sha256": "facc744a28fa499897819c280688855618446cb569c7bca603e77e81f044096d",
        "status": "draft"
      }
    ],
    "payload_sha256": "87f488377edf2d6541e245d030ebf20b246549077442c22356528138014798ad",
    "run_id": "ba01c776-4709-440e-be81-2ae35b497ce8",
    "verified": true
  }
}
FAKE HUBSPOT OBJECTS
[
  {
    "display_name": "Summer 2026 ABM email 1 - warm intro",
    "external_key": "ba01c776-4709-440e-be81-2ae35b497ce8:asset-email-001",
    "object_id": "hs-26fa251639bd",
    "object_type": "email",
    "source_asset_id": "asset-email-001",
    "source_sha256": "8a19d18fc82d447579f3bc2f8e3af2e38fd5930a0d70ecda24e0c2c39f081ca8",
    "status": "draft"
  },
  {
    "display_name": "Summer 2026 ABM email 2 - product deep d",
    "external_key": "ba01c776-4709-440e-be81-2ae35b497ce8:asset-email-002",
    "object_id": "hs-d92a49605847",
    "object_type": "email",
    "source_asset_id": "asset-email-002",
    "source_sha256": "384c042f088907da48c34ea8726c97b944eb9e0a33c2a8272af18cce1cd95793",
    "status": "draft"
  },
  {
    "display_name": "Summer 2026 ABM email 3 - book a call",
    "external_key": "ba01c776-4709-440e-be81-2ae35b497ce8:asset-email-003",
    "object_id": "hs-0210288d0e2c",
    "object_type": "email",
    "source_asset_id": "asset-email-003",
    "source_sha256": "facc744a28fa499897819c280688855618446cb569c7bca603e77e81f044096d",
    "status": "draft"
  },
  {
    "display_name": "Summer 2026 ABM campaign - primary landi",
    "external_key": "ba01c776-4709-440e-be81-2ae35b497ce8:asset-lp-001",
    "object_id": "hs-592284b4c8ac",
    "object_type": "landing_page",
    "source_asset_id": "asset-lp-001",
    "source_sha256": "3c75dbe870788ce56574fbf4b66e0646b053b8dde6befc7fbe7b7fd8ff015b71",
    "status": "draft"
  }
]

- `make test` output:
test_retry_on_a_stalled_run_resumes_it_instead_of_starting_a_new_one (test_admin_retry.AdminRetryTest.test_retry_on_a_stalled_run_resumes_it_instead_of_starting_a_new_one) ... ok
test_cancelled_run_gets_no_further_writes_and_stays_cancelled (test_cancel_after_write.CancelAfterWriteTest.test_cancelled_run_gets_no_further_writes_and_stays_cancelled) ... ok
test_same_key_with_different_payload_raises_idempotency_conflict (test_changed_request.ChangedRequestTest.test_same_key_with_different_payload_raises_idempotency_conflict) ... ok
test_same_key_same_payload_submitted_twice_yields_one_set_of_drafts (test_duplicate_delivery.DuplicateDeliveryTest.test_same_key_same_payload_submitted_twice_yields_one_set_of_drafts) ... ok
test_run_once_reads_back_after_a_timed_out_write_instead_of_guessing (test_provider_ambiguous_write.ProviderAmbiguousWriteTest.test_run_once_reads_back_after_a_timed_out_write_instead_of_guessing) ... ok
test_verified_reflects_whether_stored_drafts_actually_match_approved (test_verified_receipt_disputed.VerifiedReceiptDisputedTest.test_verified_reflects_whether_stored_drafts_actually_match_approved) ... ok
test_reported_deployment_recovers_without_duplicate_drafts (test_visible.ReportedDeploymentFailureTest.test_reported_deployment_recovers_without_duplicate_drafts) ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.724s

OK


- The claim in this submission you are least sure of, and how you checked it:
'Timeour error' in run once is the only way to handle ambiguous write as hubspot doesnt model provider failures, this was simulated with a test that performs real write.

- Anything a reviewer should know before opening the repository:
If running on windows you need to fix the Windows SQlite connection leak to ensure demo runs
double_submit_new_key and unrelated_tooling are untouched
