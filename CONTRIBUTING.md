# Contributing to RWA-Studio

Thank you for your interest in contributing to RWA-Studio! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Branch Strategy](#branch-strategy)
- [Making Changes](#making-changes)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Be kind, constructive, and professional in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/rwa-studio.git
   cd rwa-studio
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/sowadalmughni/rwa-studio.git
   ```

## Development Setup

### Prerequisites

- **Node.js** 18+ and npm/pnpm
- **Python** 3.8+
- **Git**
- **Docker** (optional, for containerized development)

### Installation

```bash
# Install all dependencies
cd frontend && pnpm install && cd ..
cd backend && pip install -r requirements.txt && cd ..
cd smart-contracts && npm install && cd ..
```

### Running Locally

**Frontend:**

```bash
cd frontend
pnpm dev
# Runs on http://localhost:5173
```

**Backend:**

```bash
cd backend
python src/main.py
# Runs on http://localhost:5000
```

**Smart Contracts:**

```bash
cd smart-contracts
npx hardhat node
# In another terminal:
npx hardhat test --network localhost
```

### Using Docker

```bash
docker-compose up -d
```

## Branch Strategy

We follow a simplified GitFlow model:

| Branch      | Purpose                         | Base      |
| ----------- | ------------------------------- | --------- |
| `main`      | Production-ready code           | -         |
| `develop`   | Integration branch for features | `main`    |
| `feature/*` | New features                    | `develop` |
| `bugfix/*`  | Bug fixes                       | `develop` |
| `hotfix/*`  | Urgent production fixes         | `main`    |
| `release/*` | Release preparation             | `develop` |

### Branch Naming

```
feature/add-polygon-support
bugfix/fix-jwt-expiration
hotfix/critical-security-patch
release/v1.2.0
```

## Making Changes

### 1. Create a Feature Branch

```bash
git checkout develop
git pull upstream develop
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write clean, readable code
- Follow existing code style and patterns
- Add comments for complex logic
- Update documentation if needed

### 3. Commit Your Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
git commit -m "feat(contracts): add dividend distribution function"
git commit -m "fix(backend): resolve JWT token expiration issue"
git commit -m "docs: update API reference with new endpoints"
git commit -m "test(frontend): add component tests for TokenWizard"
```

## Testing Requirements

All contributions must include appropriate tests.

### Backend (Python/pytest)

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

**Coverage Requirement:** Maintain or improve the current ~54% coverage. New code should have >80% coverage.

### Smart Contracts (Hardhat)

```bash
cd smart-contracts

# Run all tests
npm test

# Run with coverage
npm run coverage

# Run specific test
npx hardhat test test/RWAToken.test.js
```

**Requirements:**

- All contract functions must have test coverage
- Test edge cases and failure scenarios
- Include gas consumption tests for critical functions

### Frontend (Vitest + React Testing Library)

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

**Requirements:**

- Test user interactions, not implementation details
- Mock API calls and external dependencies
- Test error states and loading states

### E2E Tests (Playwright)

```bash
# From project root
npx playwright test

# Run specific test
npx playwright test e2e/tokenization-flow.spec.ts

# Debug mode
npx playwright test --debug
```

## Pull Request Process

### 1. Before Submitting

- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] No merge conflicts with `develop`
- [ ] Commits follow conventional commit format

### 2. Create Pull Request

1. Push your branch to your fork
2. Open a PR against `develop` (or `main` for hotfixes)
3. Fill out the PR template completely

### 3. PR Template

```markdown
## Description

[Describe what this PR does]

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## How Has This Been Tested?

[Describe the tests you ran]

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

## Screenshots (if applicable)

[Add screenshots for UI changes]

## Related Issues

Closes #[issue number]
```

### 4. Review Process

- At least one maintainer must approve the PR
- All CI checks must pass
- Address all review comments
- Squash commits if requested

## Style Guidelines

### Python (Backend)

- Follow [PEP 8](https://pep8.org/)
- Use type hints where possible
- Maximum line length: 100 characters
- Use docstrings for all public functions

```python
def verify_investor(
    address: str,
    kyc_level: int,
    jurisdiction: str
) -> bool:
    """
    Verify an investor's eligibility for token transfers.

    Args:
        address: Ethereum wallet address
        kyc_level: KYC verification level (1-3)
        jurisdiction: Two-letter country code

    Returns:
        True if investor is verified, False otherwise
    """
    ...
```

### JavaScript/TypeScript (Frontend & Contracts)

- Use ESLint configuration provided
- Prefer `const` over `let`
- Use async/await over raw promises
- Use meaningful variable and function names

```javascript
// Good
const fetchUserTokens = async (userId) => {
  const response = await api.get(`/users/${userId}/tokens`);
  return response.data;
};

// Avoid
const f = async (id) => {
  return api.get(`/users/${id}/tokens`).then((r) => r.data);
};
```

### Solidity (Smart Contracts)

- Follow [Solidity Style Guide](https://docs.soliditylang.org/en/latest/style-guide.html)
- Use NatSpec comments for all public functions
- Order: receive/fallback, external, public, internal, private
- Use explicit visibility modifiers

```solidity
/// @notice Transfer tokens with compliance check
/// @param to Recipient address
/// @param amount Number of tokens to transfer
/// @return success Whether the transfer succeeded
function transfer(
    address to,
    uint256 amount
) external override returns (bool success) {
    require(_checkCompliance(msg.sender, to, amount), "Compliance check failed");
    return super.transfer(to, amount);
}
```

## Reporting Issues

### Bug Reports

Use the bug report template and include:

1. **Environment** (OS, Node version, Python version)
2. **Steps to reproduce**
3. **Expected behavior**
4. **Actual behavior**
5. **Screenshots/logs** (if applicable)

### Feature Requests

1. **Is it related to a problem?** Describe the problem.
2. **Describe the solution** you'd like
3. **Describe alternatives** you've considered
4. **Additional context**

## Questions?

- Open a [Discussion](https://github.com/sowadalmughni/rwa-studio/discussions)
- Email: sowadalmughni@gmail.com

---

Thank you for contributing to RWA-Studio! 🚀
