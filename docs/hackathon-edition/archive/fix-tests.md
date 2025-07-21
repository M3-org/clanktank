# Plan: Fix and Modernize Hackathon Test Suite

## 1. **Test Server Management**
- **Goal:** Ensure all backend-dependent tests can run without requiring a manually started server.
- **Actions:**
  - Refactor backend tests to use FastAPI's `TestClient` for in-process API testing.
  - Remove or update any test fixtures that try to start/stop uvicorn as a subprocess.
  - For tests that require a running frontend, mock frontend endpoints or use a headless browser if true E2E is needed.

## 2. **Authentication Handling**
- **Goal:** Allow tests to pass with Discord-only authentication enforced.
- **Actions:**
  - Mock Discord authentication in backend tests (e.g., inject a valid user/token into the test client session).
  - For submission tests, provide a valid Discord token or bypass auth in test mode.
  - Update or skip tests that depend on invite code logic.

## 3. **Test Data and Database Isolation**
- **Goal:** Prevent test data from polluting production or each other.
- **Actions:**
  - Use a temporary SQLite database for each test run (e.g., `sqlite:///:memory:` or a temp file).
  - Ensure all test setup/teardown is robust and cleans up after itself.

## 4. **Frontend/API Contract Tests**
- **Goal:** Ensure frontend API contract tests do not require a running frontend server.
- **Actions:**
  - Mock frontend API calls in tests, or use a test instance of the backend only.
  - For E2E tests, use a tool like Playwright or Cypress, but only if needed.

## 5. **Test Output and Linting**
- **Goal:** Clean up warnings and ensure all tests use proper assertions.
- **Actions:**
  - Replace all `return` statements in tests with `assert`.
  - Add linting for test files to catch common mistakes.

## 6. **Documentation and CI**
- **Goal:** Make it easy for contributors to run tests locally and in CI.
- **Actions:**
  - Update README and test docs with clear instructions.
  - Add a GitHub Actions workflow for automated test runs.

---

## **Next Steps**
1. Review this plan and adjust as needed.
2. Refactor backend tests to use `TestClient` and mock Discord auth.
3. Update or remove frontend tests that require a running dev server.
4. Clean up test data handling and assertions.
5. Rerun all tests and verify a clean pass. 