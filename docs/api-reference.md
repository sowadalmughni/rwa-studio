# RWA-Studio API Reference

**Version:** 1.0.0  
**Base URL:** `http://localhost:5000/api`

This document provides detailed documentation for all REST API endpoints in RWA-Studio.

## Table of Contents

1. [Authentication](#authentication)
2. [Users](#users)
3. [Transfer Agent](#transfer-agent)
4. [KYC Verification](#kyc-verification)
5. [Billing & Subscriptions](#billing--subscriptions)
6. [Assets](#assets)
7. [Documents](#documents)
8. [Analytics](#analytics)
9. [Badges](#badges)
10. [Error Handling](#error-handling)

---

## Authentication

All protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Register User

Create a new user account.

```http
POST /auth/register
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username |
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | Min 8 characters |
| `wallet_address` | string | No | Ethereum address (0x...) |
| `role` | string | No | User role (default: "user") |

**Example Request:**

```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securePassword123",
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678"
}
```

**Example Response (201):**

```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
    "role": "user"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Error Responses:**

| Code | Description |
|------|-------------|
| 400 | Invalid input (missing field, invalid format) |
| 409 | Username, email, or wallet already exists |

---

### Login

Authenticate and receive JWT tokens.

```http
POST /auth/login
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | Registered email |
| `password` | string | Yes | User password |

**Example Request:**

```json
{
  "email": "john@example.com",
  "password": "securePassword123"
}
```

**Example Response (200):**

```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "user"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### Wallet Login

Authenticate using Ethereum wallet signature.

```http
POST /auth/wallet-login
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `wallet_address` | string | Yes | Ethereum address |
| `signature` | string | Yes | Signed message |
| `message` | string | Yes | Original message that was signed |

**Example Request:**

```json
{
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "signature": "0x...",
  "message": "Sign in to RWA-Studio: nonce123456"
}
```

---

### Refresh Token

Get a new access token using refresh token.

```http
POST /auth/refresh
```

**Headers:**

```
Authorization: Bearer <refresh_token>
```

**Example Response (200):**

```json
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### Logout

Revoke current tokens.

```http
POST /auth/logout
```

**Headers:**

```
Authorization: Bearer <access_token>
```

**Example Response (200):**

```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

---

## Users

### List Users

Get all users (admin only).

```http
GET /users
```

**Example Response (200):**

```json
[
  {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "wallet_address": "0x1234...",
    "role": "user",
    "created_at": "2025-01-15T10:30:00Z"
  }
]
```

---

### Get User

Get user by ID.

```http
GET /users/:user_id
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | integer | User ID |

**Example Response (200):**

```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "wallet_address": "0x1234...",
  "role": "user",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### Update User

Update user information.

```http
PUT /users/:user_id
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | No | New username |
| `email` | string | No | New email |

---

### Delete User

Delete a user (admin only).

```http
DELETE /users/:user_id
```

**Response:** `204 No Content`

---

## Transfer Agent

The Transfer Agent API provides endpoints for managing tokenized assets and compliance.

### List Tokens

Get all token deployments with pagination and filtering.

```http
GET /transfer-agent/tokens
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `per_page` | integer | 20 | Items per page |
| `asset_type` | string | - | Filter by asset type |
| `regulatory_framework` | string | - | Filter by framework (RegD, RegS, etc.) |
| `is_active` | boolean | - | Filter by active status |

**Example Response (200):**

```json
{
  "success": true,
  "data": {
    "tokens": [
      {
        "id": 1,
        "token_address": "0xabc...",
        "token_name": "Manhattan Real Estate Fund I",
        "token_symbol": "MREF",
        "asset_type": "real-estate",
        "regulatory_framework": "RegD",
        "jurisdiction": "US",
        "max_supply": "1000000",
        "is_active": true,
        "deployment_date": "2025-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 45,
      "pages": 3,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

### Get Token Details

Get detailed information about a specific token.

```http
GET /transfer-agent/tokens/:token_address
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `token_address` | string | Token contract address |

**Example Response (200):**

```json
{
  "success": true,
  "data": {
    "token": {
      "id": 1,
      "token_address": "0xabc...",
      "token_name": "Manhattan Real Estate Fund I",
      "token_symbol": "MREF",
      "asset_type": "real-estate",
      "regulatory_framework": "RegD",
      "jurisdiction": "US",
      "max_supply": "1000000",
      "compliance_address": "0xdef...",
      "identity_registry_address": "0x123...",
      "deployer_address": "0x456...",
      "is_active": true
    },
    "recent_events": [
      {
        "id": 1,
        "event_type": "transfer_blocked",
        "from_address": "0x...",
        "to_address": "0x...",
        "reason": "Recipient not verified",
        "timestamp": "2025-01-15T11:00:00Z"
      }
    ],
    "verification_stats": [
      {"level": 1, "count": 50},
      {"level": 2, "count": 30},
      {"level": 3, "count": 10}
    ],
    "latest_metrics": {
      "total_holders": 90,
      "total_supply": "500000",
      "transfer_count": 150
    }
  }
}
```

---

### Register Token

Register a new token deployment.

```http
POST /transfer-agent/tokens
```

**Authorization:** Requires `transfer_agent` role

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token_address` | string | Yes | Deployed token address |
| `token_name` | string | Yes | Token name |
| `token_symbol` | string | Yes | Token symbol |
| `asset_type` | string | Yes | Asset type |
| `regulatory_framework` | string | Yes | Regulatory framework |
| `jurisdiction` | string | Yes | Primary jurisdiction |
| `max_supply` | string | Yes | Maximum token supply |
| `deployer_address` | string | Yes | Deployer wallet |
| `compliance_address` | string | Yes | Compliance module address |
| `identity_registry_address` | string | Yes | Identity registry address |
| `deployment_tx_hash` | string | No | Deployment transaction hash |

**Example Request:**

```json
{
  "token_address": "0xabc123...",
  "token_name": "Manhattan Real Estate Fund I",
  "token_symbol": "MREF",
  "asset_type": "real-estate",
  "regulatory_framework": "RegD",
  "jurisdiction": "US",
  "max_supply": "1000000",
  "deployer_address": "0x456...",
  "compliance_address": "0xdef...",
  "identity_registry_address": "0x789..."
}
```

---

### Verify Address

Verify an investor address for a token.

```http
POST /transfer-agent/tokens/:token_address/verify
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `investor_address` | string | Yes | Wallet to verify |
| `verification_level` | integer | Yes | KYC level (1-3) |
| `country` | string | Yes | Investor country (2-letter code) |
| `is_accredited` | boolean | No | Accreditation status |
| `expiry_date` | string | No | Verification expiry (ISO date) |

---

### Get Verified Addresses

List all verified addresses for a token.

```http
GET /transfer-agent/tokens/:token_address/verified
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `per_page` | integer | Items per page |
| `verification_level` | integer | Filter by level |
| `is_active` | boolean | Filter by active status |

---

### Get Compliance Events

Get compliance events for a token.

```http
GET /transfer-agent/tokens/:token_address/events
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `per_page` | integer | Items per page |
| `event_type` | string | Filter by event type |
| `start_date` | string | Filter from date |
| `end_date` | string | Filter to date |

---

## KYC Verification

### Start Verification

Initiate KYC verification process.

```http
POST /api/kyc/start
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `wallet_address` | string | Yes | Wallet to verify |
| `first_name` | string | Yes | Legal first name |
| `last_name` | string | Yes | Legal last name |
| `email` | string | Yes | Contact email |
| `country` | string | No | Country code |
| `date_of_birth` | string | No | DOB (YYYY-MM-DD) |

**Example Request:**

```json
{
  "wallet_address": "0x1234...",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "country": "US",
  "date_of_birth": "1990-01-15"
}
```

**Example Response (200):**

```json
{
  "success": true,
  "verification_id": "kyc_123456",
  "status": "pending",
  "verification_url": "https://kyc-provider.com/verify/abc123"
}
```

---

### Get Verification Status

Check status of a KYC verification.

```http
GET /api/kyc/status/:wallet_address
```

**Example Response (200):**

```json
{
  "wallet_address": "0x1234...",
  "status": "approved",
  "verification_level": 2,
  "verified_at": "2025-01-15T10:30:00Z",
  "expires_at": "2026-01-15T10:30:00Z",
  "checks_passed": ["identity", "address", "sanctions"]
}
```

---

### KYC Webhook

Webhook endpoint for KYC provider callbacks.

```http
POST /api/kyc/webhook
```

**Headers:**

```
X-Webhook-Signature: <signature>
```

---

## Billing & Subscriptions

### Get Plans

List available subscription plans.

```http
GET /api/billing/plans
```

**Example Response (200):**

```json
{
  "plans": [
    {
      "id": "starter",
      "name": "Starter",
      "price": 99,
      "currency": "usd",
      "interval": "month",
      "tokens_limit": 3,
      "features": [
        "Up to 3 tokenized assets",
        "Basic compliance rules",
        "Email support",
        "Standard analytics"
      ]
    },
    {
      "id": "professional",
      "name": "Professional",
      "price": 299,
      "currency": "usd",
      "interval": "month",
      "tokens_limit": 10,
      "features": [
        "Up to 10 tokenized assets",
        "All compliance rules",
        "Priority support",
        "Advanced analytics",
        "Custom branding",
        "API access"
      ],
      "recommended": true
    },
    {
      "id": "enterprise",
      "name": "Enterprise",
      "price": null,
      "tokens_limit": 100,
      "contact_sales": true
    }
  ]
}
```

---

### Get Subscription

Get current user's subscription.

```http
GET /api/billing/subscription
```

**Example Response (200):**

```json
{
  "has_subscription": true,
  "subscription": {
    "id": 1,
    "plan_id": "professional",
    "status": "active",
    "current_period_start": "2025-01-01T00:00:00Z",
    "current_period_end": "2025-02-01T00:00:00Z",
    "tokens_used": 5,
    "tokens_limit": 10
  }
}
```

---

### Create Checkout Session

Create a Stripe checkout session.

```http
POST /api/billing/checkout
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plan_id` | string | Yes | Plan to subscribe to |
| `success_url` | string | Yes | Redirect URL on success |
| `cancel_url` | string | Yes | Redirect URL on cancel |

**Example Response (200):**

```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_live_...",
  "session_id": "cs_live_..."
}
```

---

### Cancel Subscription

Cancel current subscription.

```http
POST /api/billing/cancel
```

**Example Response (200):**

```json
{
  "success": true,
  "message": "Subscription will be cancelled at end of billing period",
  "cancellation_date": "2025-02-01T00:00:00Z"
}
```

---

### Billing Webhook

Webhook endpoint for Stripe events.

```http
POST /api/billing/webhook
```

---

## Assets

### Get Asset Page

Get public asset page data for a token.

```http
GET /assets/:token_address
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ref` | string | Referral code |
| `utm_source` | string | UTM source tracking |
| `utm_medium` | string | UTM medium tracking |
| `utm_campaign` | string | UTM campaign tracking |

**Example Response (200):**

```json
{
  "success": true,
  "data": {
    "token": {
      "token_name": "Manhattan Real Estate Fund I",
      "token_symbol": "MREF",
      "asset_type": "real-estate",
      "regulatory_framework": "RegD"
    },
    "stats": {
      "verified_investors": 90,
      "compliance_events": 150
    },
    "badges": [
      {
        "type": "regulatory",
        "label": "Reg D 506(c)",
        "color": "blue"
      },
      {
        "type": "kyc",
        "label": "KYC Required",
        "color": "green"
      }
    ],
    "share_urls": {
      "twitter": "https://twitter.com/intent/tweet?...",
      "linkedin": "https://linkedin.com/share?..."
    },
    "embed_codes": {
      "badge": "<iframe src='...' />",
      "widget": "<script src='...' />"
    }
  }
}
```

---

### Get Asset Page HTML

Get rendered HTML asset page (for embedding).

```http
GET /assets/:token_address/html
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `template` | string | default | Template name |

**Response:** HTML content with `Content-Type: text/html`

---

### Get Templates

List available asset page templates.

```http
GET /assets/templates
```

**Example Response (200):**

```json
{
  "templates": [
    {
      "name": "real-estate",
      "display_name": "Real Estate",
      "description": "Template for real estate assets",
      "is_premium": false
    },
    {
      "name": "art-collectibles",
      "display_name": "Art & Collectibles",
      "description": "Premium template for art assets",
      "is_premium": true
    }
  ]
}
```

---

## Documents

### Upload Document

Upload a document for a token.

```http
POST /documents/upload
```

**Content-Type:** `multipart/form-data`

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Document file |
| `token_address` | string | Yes | Associated token |
| `document_type` | string | Yes | Type (ppm, subscription, etc.) |
| `title` | string | No | Document title |

---

### Get Documents

List documents for a token.

```http
GET /documents/:token_address
```

---

## Analytics

### Export Analytics

Export analytics data.

```http
GET /analytics/export
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `token_address` | string | Filter by token |
| `start_date` | string | Start date |
| `end_date` | string | End date |
| `format` | string | Export format (csv, json) |

---

## Badges

### Get Badge

Get embeddable compliance badge.

```http
GET /badge/:token_address
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `style` | string | default | Badge style |
| `size` | string | medium | Badge size (small, medium, large) |

**Response:** SVG image with `Content-Type: image/svg+xml`

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

### Rate Limiting

API requests are rate limited:

| Endpoint Type | Limit |
|---------------|-------|
| Authentication | 5 requests/minute |
| General API | 100 requests/minute |
| Webhook | 1000 requests/minute |

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:5000/api"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "user@example.com",
    "password": "password123"
})
tokens = response.json()
access_token = tokens["access_token"]

# Get tokens
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/transfer-agent/tokens", headers=headers)
tokens = response.json()
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:5000/api';

// Login
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});
const { access_token } = await loginResponse.json();

// Get tokens
const tokensResponse = await fetch(`${BASE_URL}/transfer-agent/tokens`, {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const tokens = await tokensResponse.json();
```

---

**Last Updated:** February 2026  
**Author:** Sowad Al-Mughni
