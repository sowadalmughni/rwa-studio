# RWA-Studio Production Security Checklist

This checklist ensures your RWA-Studio deployment is properly secured before going to production.

## Pre-Deployment Checklist

### 1. Environment Variables

#### Backend (.env)

- [ ] **SECRET_KEY**: Generated with `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] **JWT_SECRET_KEY**: Different from SECRET_KEY, same generation method
- [ ] **FLASK_ENV**: Set to `production`
- [ ] **FLASK_DEBUG**: Set to `False`
- [ ] **DATABASE_URL**: PostgreSQL connection string (not SQLite)
- [ ] **RATELIMIT_STORAGE_URL**: Redis URL (e.g., `redis://localhost:6379/0`)

#### Frontend (.env)

- [ ] **VITE_WALLETCONNECT_PROJECT_ID**: Valid project ID from [WalletConnect Cloud](https://cloud.walletconnect.com)
- [ ] **VITE_API_URL**: Production API URL (HTTPS)
- [ ] **VITE_ENABLE_DEBUG_MODE**: Set to `false`

### 2. Database

- [ ] PostgreSQL configured and running
- [ ] Database user has minimal required permissions
- [ ] Connection uses SSL in production
- [ ] Database backups configured

### 3. Redis

- [ ] Redis server running for rate limiting
- [ ] Redis password configured
- [ ] Separate Redis databases for different purposes:
  - `/0` - Rate limiting
  - `/1` - Celery broker
  - `/2` - Celery results

### 4. HTTPS/TLS

- [ ] SSL certificate installed
- [ ] All HTTP traffic redirects to HTTPS
- [ ] HSTS header enabled (automatic with our security middleware)

### 5. Third-Party Services

#### Required

- [ ] **Onfido** (KYC): API token and webhook secret configured
- [ ] **Stripe** (Payments): Secret key, publishable key, and webhook secret configured
- [ ] **SendGrid** (Email): API key configured
- [ ] **Pinata** (IPFS): API key and secret configured

#### Blockchain

- [ ] **RPC URLs**: Production RPC endpoints (Infura/Alchemy) configured
- [ ] **Network**: Set to `mainnet` or appropriate production network

### 6. CORS Configuration

- [ ] **CORS_ORIGINS**: Only production domain(s) listed
- [ ] Remove localhost origins

### 7. Firewall & Network

- [ ] Only ports 80 and 443 exposed publicly
- [ ] Database port (5432) not publicly accessible
- [ ] Redis port (6379) not publicly accessible
- [ ] Admin endpoints protected by VPN/IP whitelist

## Security Features Enabled

Our security hardening implementation provides:

### Rate Limiting (OWASP A05:2021)

| Endpoint Type | Limit | Purpose |
|--------------|-------|---------|
| Auth | 20/min | Prevent brute force |
| Sensitive | 5/min | Protect critical operations |
| Write | 30/min | Prevent abuse |
| Read | 200/min | Allow normal usage |
| Public | 60/min | Protect unauthenticated endpoints |

### Account Lockout

- 5 failed login attempts = 15 minute lockout
- Lockout tracked per email/username

### Input Validation (OWASP A03:2021)

- Schema-based validation on all endpoints
- Strict mode rejects unexpected fields
- HTML/XSS sanitization
- Path traversal prevention
- Ethereum address validation

### Password Policy

- Minimum 8 characters
- Uppercase + lowercase required
- At least 1 digit
- At least 1 special character
- Common password rejection

### Security Headers (OWASP A05:2021)

- Content Security Policy (CSP) - no `unsafe-eval` in production
- Strict-Transport-Security (HSTS) with preload
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block

### Token Security

- JWT access tokens: 1 hour expiry
- Refresh tokens: 30 days expiry
- Redis-backed token blocklist
- Wallet signature verification (EIP-191)

## Monitoring Recommendations

### Logging

- [ ] Structured JSON logging enabled (`LOG_FORMAT=json`)
- [ ] Log aggregation service configured (e.g., Datadog, ELK)
- [ ] Security events logged:
  - Failed login attempts
  - Rate limit hits
  - Account lockouts
  - Token blocklist additions

### Alerting

Set up alerts for:

- [ ] High rate of 429 (Too Many Requests) responses
- [ ] Spike in failed login attempts
- [ ] Account lockout events
- [ ] 500 errors

### Health Checks

- [ ] `/health` endpoint monitored
- [ ] Database connectivity check
- [ ] Redis connectivity check

## Post-Deployment Verification

Run these checks after deployment:

```bash
# 1. Verify rate limiting works
for i in {1..25}; do curl -s -o /dev/null -w "%{http_code}\n" https://api.yoursite.com/api/auth/login; done
# Should see 429 after ~20 requests

# 2. Verify security headers
curl -I https://api.yoursite.com/api/health

# 3. Verify HTTPS redirect
curl -I http://yoursite.com
# Should see 301/302 redirect to https://

# 4. Test wallet signature verification
# Use your frontend to test wallet login flow
```

## Emergency Procedures

### If a secret is compromised:

1. Immediately rotate the affected key in production
2. Invalidate all existing tokens (clear Redis token blocklist DB)
3. Force all users to re-authenticate
4. Review logs for unauthorized access
5. Update key in all environments

### Commands for key rotation:

```bash
# Generate new secrets
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"

# Clear Redis (invalidate all sessions)
redis-cli FLUSHDB
```

## Compliance Notes

This implementation follows:

- **OWASP Top 10 2021** guidelines
- **OWASP API Security Top 10** recommendations
- **EIP-191** for wallet signature verification
- **ERC-3643** compliance for security token operations
