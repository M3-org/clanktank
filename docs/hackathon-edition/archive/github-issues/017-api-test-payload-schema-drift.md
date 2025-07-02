# 017 - API Test Payload Schema Drift and Alignment

## Context
- The ClankTank hackathon platform backend, ingestion, and main pipeline are now fully versioned, robust, and DRY (see Issue 016).
- All scripts and endpoints use versioned tables and a canonical schema manifest (see `schema.py`).
- The API endpoint tests (`test_api_endpoints.py`) are failing POST/GET tests due to schema drift: test payloads do not match the current v2 manifest (missing/renamed fields, outdated structure).

## Problem Statement
- **API endpoint tests are failing** (422/500 errors, missing fields, IndexError/KeyError) because the test payloads and assertions are not aligned with the latest backend schema.
- This is the last major blocker for a fully green end-to-end test suite.

## Impact
- All downstream GET/list/detail/feedback tests fail if POST fails, masking potential real issues.
- New contributors and CI cannot trust the test suite until this is fixed.

## Proposal / Action Plan
1. **Review the current v2 manifest/schema** in `schema.py` (and any required/optional fields).
2. **Update all test payloads** in `test_api_endpoints.py` to match the v2 manifest exactly (field names, required/optional, types).
3. **Update test assertions** to match the current response structure (e.g., `success` vs `status`, `submission_id` presence, etc.).
4. **Remove or update any deprecated endpoint tests** (e.g., legacy/old field names).
5. **Re-run the test suite** and confirm all API endpoint tests pass.
6. **Document the fix** in this issue and in the test notes (016).

## Acceptance Criteria
- [ ] All POST/GET API endpoint tests pass for v1, v2, and latest routes.
- [ ] Test payloads and assertions are fully aligned with the backend schema.
- [ ] No more 422/500 errors due to schema drift.
- [ ] This issue and 016 are updated with the resolution.

## Checklist
- [ ] Review v2 manifest in `schema.py`
- [ ] Update all test payloads in `test_api_endpoints.py`
- [ ] Update test assertions for response structure
- [ ] Remove/update deprecated tests
- [ ] Re-run and verify all tests pass
- [ ] Update documentation and close this issue

---

**References:**
- [016-api-end-to-end-test-notes.md](016-api-end-to-end-test-notes.md)
- `scripts/hackathon/test/test_api_endpoints.py`
- `scripts/hackathon/schema.py` 