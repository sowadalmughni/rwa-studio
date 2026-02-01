# RWA-Studio E2E Tests

End-to-end tests for RWA-Studio using Playwright.

## Setup

```bash
cd e2e
npm install
npx playwright install
```

## Running Tests

```bash
# Run all tests
npm test

# Run tests with UI mode
npm run test:ui

# Run tests in headed mode (see browser)
npm run test:headed

# Debug tests
npm run test:debug

# Generate test code
npm run codegen

# View test report
npm run report
```

## Test Structure

- `tests/landing.spec.js` - Landing page and navigation tests
- `tests/auth.spec.js` - Authentication flow tests
- `tests/token-creation.spec.js` - Token creation workflow tests

## Environment Variables

- `E2E_BASE_URL` - Base URL for tests (default: http://localhost:5173)
- `E2E_AUTHENTICATED` - Set to enable authenticated route tests
- `CI` - Set when running in CI environment

## Writing Tests

```javascript
import { test, expect } from '@playwright/test';

test('example test', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/RWA/);
});
```

## CI Integration

Tests are configured to:
- Retry failed tests twice on CI
- Run with a single worker on CI
- Capture screenshots and traces on failure
- Auto-start the dev server before tests
