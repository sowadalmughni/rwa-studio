# RWA-Studio Style Guide

This document establishes coding conventions for the RWA-Studio codebase. All contributors must follow these rules to maintain consistency.

## General Rules

### No Emojis in Source Code

Do not use emojis in:

- Source code (Python, JavaScript, Solidity)
- Code comments
- Commit messages
- Log messages

Emojis are permitted only in user-facing documentation (README.md) for visual emphasis.

### Comment Philosophy

Write comments that explain **why**, not **what**. The code already shows what it does.

**Bad:**

```python
# Increment counter
counter += 1
```

**Good:**

```python
# Rate limit window resets every 60 seconds per RFC 6585
counter += 1
```

**When to comment:**

- Non-obvious business logic or regulatory requirements
- Workarounds for external library bugs
- Security-sensitive decisions
- Performance tradeoffs

**When not to comment:**

- Self-explanatory code
- Restating the function name
- Obvious type information

### Logging Standards

Use structured logging with appropriate levels:

| Level     | Use Case                               |
| --------- | -------------------------------------- |
| `debug`   | Development-only details, verbose data |
| `info`    | Normal operations, startup, shutdown   |
| `warning` | Recoverable issues, deprecations       |
| `error`   | Failures requiring attention           |

**Never log:**

- Passwords, tokens, API keys, private keys
- Full credit card or SSN numbers
- Personal identifying information (PII)
- Request/response bodies containing secrets

**Python example:**

```python
import structlog
logger = structlog.get_logger(__name__)

logger.info("token_deployed", address=token_address, symbol=symbol)
logger.error("transfer_failed", reason=str(e), from_addr=from_addr)
```

**JavaScript example:**

```javascript
console.log(`Token deployed: ${tokenAddress}`);
console.error(`Deployment failed: ${error.message}`);
```

## Python Conventions

### Formatting

- Formatter: **black** (line length: 120)
- Import sorter: **isort** (black profile)
- Linter: **flake8**

### Naming

| Type      | Convention         | Example             |
| --------- | ------------------ | ------------------- |
| Variables | snake_case         | `token_address`     |
| Functions | snake_case         | `verify_investor()` |
| Classes   | PascalCase         | `ComplianceModule`  |
| Constants | UPPER_SNAKE        | `MAX_INVESTORS`     |
| Private   | Leading underscore | `_internal_state`   |

### File Organization

- One class per file for large classes
- Group related utilities in a single module
- Keep files under 500 lines; split if larger

## JavaScript/TypeScript Conventions

### Formatting

- Formatter: **Prettier**
- Linter: **ESLint**

### Naming

| Type             | Convention  | Example            |
| ---------------- | ----------- | ------------------ |
| Variables        | camelCase   | `tokenAddress`     |
| Functions        | camelCase   | `verifyInvestor()` |
| Classes          | PascalCase  | `RWAToken`         |
| Constants        | UPPER_SNAKE | `MAX_SUPPLY`       |
| React Components | PascalCase  | `WalletConnect`    |

### File Organization

- One React component per file
- Colocate tests with source (`Component.test.jsx`)
- Keep files under 400 lines

## Solidity Conventions

### Formatting

- Indentation: 4 spaces
- Line length: 120 characters

### Naming

| Type          | Convention         | Example             |
| ------------- | ------------------ | ------------------- |
| Contracts     | PascalCase         | `RWAToken`          |
| Functions     | camelCase          | `canTransfer()`     |
| Events        | PascalCase         | `TransferCompleted` |
| Constants     | UPPER_SNAKE        | `MAX_SUPPLY`        |
| Private state | Leading underscore | `_totalSupply`      |

### Documentation

- Use NatSpec for all public/external functions
- Document parameters and return values
- Include security considerations

```solidity
/// @notice Transfers tokens with compliance checks
/// @dev Reverts if compliance module rejects the transfer
/// @param to Recipient address (must be verified)
/// @param amount Token amount in wei
/// @return success True if transfer completed
function transfer(address to, uint256 amount) external returns (bool success);
```

## File Size Guidelines

| File Type         | Max Lines | Action if Exceeded           |
| ----------------- | --------- | ---------------------------- |
| Python module     | 500       | Split into submodules        |
| React component   | 400       | Extract child components     |
| Solidity contract | 400       | Use inheritance or libraries |
| Test file         | 600       | Split by feature             |

## Git Conventions

### Commit Messages

Format: `<type>: <description>`

Types:

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code change that neither fixes nor adds
- `docs`: Documentation only
- `test`: Adding or fixing tests
- `chore`: Tooling, dependencies, configs

Examples:

```
feat: add holding period compliance rule
fix: correct investor limit check in RegD mode
refactor: extract compliance validation to service
docs: update deployment instructions
```

### Branch Names

Format: `<type>/<short-description>`

Examples:

- `feat/kyc-integration`
- `fix/transfer-validation`
- `refactor/compliance-module`

## Verification Commands

Run these before committing:

```bash
# Python
cd backend
black --check src/
isort --check-only src/
flake8 src/
pytest tests/

# JavaScript
cd frontend
pnpm lint
pnpm build

# Contracts
cd smart-contracts
npx hardhat compile
npx hardhat test
```
