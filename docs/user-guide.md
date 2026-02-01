# RWA-Studio User Guide

**Tokenize Real-World Assets in 5 Clicks**

Welcome to RWA-Studio! This guide will walk you through everything you need to know to tokenize your real-world assets with full regulatory compliance.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [The 5-Click Tokenization Workflow](#the-5-click-tokenization-workflow)
4. [Managing Your Tokens](#managing-your-tokens)
5. [Transfer Agent Console](#transfer-agent-console)
6. [Compliance Management](#compliance-management)
7. [Investor Management](#investor-management)
8. [Asset Pages](#asset-pages)
9. [Billing & Subscriptions](#billing--subscriptions)
10. [FAQ](#faq)

---

## Introduction

### What is RWA-Studio?

RWA-Studio is an open-source platform that enables you to create regulatory-compliant security tokens for real-world assets. Whether you're tokenizing real estate, private equity, debt instruments, or art, RWA-Studio handles the complexity of compliance so you can focus on your business.

### Who is RWA-Studio For?

- **Fund Managers**: Launch Reg D/Reg S offerings without enterprise platform fees
- **Real Estate Syndicators**: Tokenize properties for fractional ownership
- **Private Equity Firms**: Create liquid secondary markets for LP interests
- **Compliance Officers**: Monitor transfers and manage investor verification
- **Lawyers**: Structure compliant token offerings for clients

### Key Benefits

| Traditional Approach | RWA-Studio |
|---------------------|------------|
| $50,000+ platform fees | Free & open source |
| 3-6 months implementation | 5 minutes to deploy |
| Team of blockchain developers | No coding required |
| Complex compliance setup | Compliance-by-default |

---

## Getting Started

### System Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- MetaMask or compatible Web3 wallet
- ETH for gas fees (testnet ETH for testing)

### Creating Your Account

1. Navigate to your RWA-Studio instance
2. Click **Sign Up** in the top right corner
3. Enter your email address and create a password
4. Verify your email address
5. Complete your profile information

### Connecting Your Wallet

1. Click **Connect Wallet** in the dashboard
2. Select MetaMask (or your preferred wallet)
3. Approve the connection request
4. Your wallet address will appear in the header

### Choosing Your Network

RWA-Studio supports multiple networks:

| Network | Use Case | Gas Costs |
|---------|----------|-----------|
| **Sepolia** (Default) | Testing & development | Free (testnet) |
| **Polygon Amoy** | Testing on Polygon | Free (testnet) |
| **Ethereum Mainnet** | Production deployments | Variable |

To switch networks:
1. Open MetaMask
2. Click the network dropdown
3. Select your desired network
4. RWA-Studio will automatically detect the change

---

## The 5-Click Tokenization Workflow

### Overview

RWA-Studio's signature feature is the 5-click workflow that guides you through creating a fully compliant security token:

```
Click 1: Select Asset Type
        ↓
Click 2: Choose Regulatory Framework
        ↓
Click 3: Configure Token Economics
        ↓
Click 4: Set Transfer Restrictions
        ↓
Click 5: Deploy Token
```

### Click 1: Select Asset Type

Choose the type of asset you're tokenizing:

| Asset Type | Description | Common Use Cases |
|------------|-------------|------------------|
| **Real Estate** | Commercial or residential property | REITs, syndications, fractional ownership |
| **Private Equity** | Ownership in private companies | LP interests, venture funds |
| **Debt Instruments** | Loans, bonds, notes | Revenue-based financing, fixed income |
| **Commodities** | Physical goods | Gold, silver, agricultural products |
| **Equity** | Company shares | Startup equity, employee tokens |
| **Art & Collectibles** | Fine art, collectibles | Fractional art ownership |

### Click 2: Choose Regulatory Framework

Select the regulatory exemption for your offering:

| Framework | Description | Investor Types | Geographic Limits |
|-----------|-------------|----------------|-------------------|
| **Reg D 506(b)** | Private placement | Accredited + up to 35 non-accredited | US only |
| **Reg D 506(c)** | Private placement (verified) | Accredited only | US only |
| **Reg S** | Offshore offering | Non-US investors | Non-US only |
| **Reg CF** | Crowdfunding | Anyone | US only, $5M limit |
| **Reg A** | Mini-IPO | Anyone | US only, $75M limit |

**Need help choosing?** Consider:
- Who are your investors? (Accredited vs. general public)
- Where are they located? (US, international, or both)
- How much are you raising? (Affects Reg CF/Reg A eligibility)

### Click 3: Configure Token Economics

Set up your token's financial structure:

**Basic Settings:**
- **Token Name**: Full name (e.g., "Manhattan Real Estate Fund I")
- **Token Symbol**: 3-5 character ticker (e.g., "MREF")
- **Total Supply**: Maximum number of tokens
- **Initial Price**: Price per token in USD

**Optional Settings:**
- **Minimum Investment**: Smallest purchase allowed
- **Maximum per Investor**: Cap per investor (for concentration limits)
- **Dividend Schedule**: Quarterly, annual, or none

### Click 4: Set Transfer Restrictions

Configure compliance rules for secondary trading:

| Restriction | Description | Common Settings |
|-------------|-------------|-----------------|
| **Holding Period** | Minimum time before transfer | 12 months (Reg D) |
| **Investor Limit** | Maximum number of investors | 99 (506(b)), 2000 (506(c)) |
| **Geographic** | Allowed/blocked countries | Based on regulatory framework |
| **Accreditation** | Require verified accreditation | Required for 506(c) |
| **KYC Level** | Required verification level | Level 1, 2, or 3 |

### Click 5: Deploy Token

Review your configuration and deploy:

1. **Review Summary**: Check all settings
2. **Estimate Gas**: See deployment cost
3. **Confirm in Wallet**: Approve the transaction
4. **Wait for Confirmation**: ~15-30 seconds on testnets
5. **Success!** Your token is live

After deployment, you'll receive:
- Token contract address
- Compliance module address
- Identity registry address
- Shareable asset page URL

---

## Managing Your Tokens

### Dashboard Overview

The dashboard shows all your deployed tokens with key metrics:

- **Total Value Locked (TVL)**
- **Number of Holders**
- **24h Transfer Volume**
- **Compliance Status**

### Token Actions

For each token, you can:

| Action | Description |
|--------|-------------|
| **View Details** | See full token configuration |
| **Manage Holders** | View and manage investor list |
| **Mint Tokens** | Create new tokens (if allowed) |
| **Burn Tokens** | Destroy tokens |
| **Pause/Unpause** | Emergency transfer freeze |
| **Update Compliance** | Modify compliance rules |

### Viewing Token Details

Click any token to see:
- Contract addresses
- Current supply and distribution
- Holder breakdown by jurisdiction
- Recent transfer history
- Compliance rule status

---

## Transfer Agent Console

The Transfer Agent Console provides professional tools for managing your tokens' compliance.

### Accessing the Console

1. Click **Transfer Agent** in the navigation
2. Select the token you want to manage

### Key Features

#### Holder Registry

View all token holders with:
- Wallet addresses
- Token balance
- KYC status
- Accreditation status
- Jurisdiction
- Acquisition date

#### Transfer History

Monitor all token transfers:
- Sender and recipient
- Amount transferred
- Timestamp
- Compliance check results
- Block confirmation

#### Pending Transfers

For tokens requiring manual approval:
- Review pending transfer requests
- Approve or reject with comments
- Bulk approval for multiple transfers

---

## Compliance Management

### Understanding Compliance Modules

Each token has a compliance module that enforces your rules:

```
Transfer Request
       ↓
┌─────────────────────┐
│ Compliance Module   │
│  • Check sender     │
│  • Check recipient  │
│  • Check amount     │
│  • Apply rules      │
└─────────────────────┘
       ↓
    Allow / Deny
```

### Managing Compliance Rules

#### Adding New Rules

1. Go to **Compliance** → **Rules**
2. Click **Add Rule**
3. Select rule type:
   - Investor limit
   - Geographic restriction
   - Holding period
   - Accreditation requirement
   - Custom rule
4. Configure parameters
5. Deploy the rule

#### Modifying Existing Rules

1. Select the rule to modify
2. Click **Edit**
3. Update parameters
4. Confirm the transaction

#### Removing Rules

⚠️ **Warning**: Removing compliance rules may affect your regulatory status.

1. Select the rule to remove
2. Click **Remove**
3. Acknowledge the warning
4. Confirm the transaction

### Compliance Reports

Generate reports for:
- Regulatory filings
- Audit purposes
- Investor communications

**Available Reports:**
- Holder composition report
- Transfer activity report
- Compliance violation log
- KYC status summary

---

## Investor Management

### Identity Registry

The Identity Registry tracks verified investors:

| Field | Description |
|-------|-------------|
| **Address** | Ethereum wallet address |
| **Country** | Jurisdiction of residence |
| **KYC Level** | Verification level (1-3) |
| **Accredited** | Accreditation status |
| **Verified Date** | When verification was completed |
| **Expiry Date** | When re-verification is needed |

### Verifying Investors

#### Manual Verification

1. Go to **Investors** → **Pending**
2. Review investor documents
3. Click **Verify** or **Reject**
4. Add notes if needed

#### Automated Verification (Onfido Integration)

If configured, investors can self-verify:
1. Investor submits ID documents
2. Onfido performs verification
3. Results automatically update registry
4. You receive notification of new verifications

### KYC Levels

| Level | Requirements | Use Case |
|-------|--------------|----------|
| **Level 1** | Basic identity | Low-value transactions |
| **Level 2** | ID verification + address | Standard investments |
| **Level 3** | Enhanced due diligence | High-value or high-risk |

### Managing Accreditation

For Reg D 506(c) offerings, you must verify accreditation:

**Accepted Methods:**
- CPA/Attorney letter
- Broker-dealer verification
- Third-party verification service
- Recent tax returns (income method)
- Recent financial statements (net worth method)

---

## Asset Pages

### What are Asset Pages?

Shareable public pages for your token offering with:
- Asset description and images
- Token economics
- Compliance badge
- Investor resources
- Contact information

### Creating an Asset Page

1. Go to **Assets** → **Pages**
2. Click **Create New Page**
3. Select a template:
   - Real Estate
   - Private Equity
   - Debt Instrument
   - Art & Collectibles
   - Revenue Share
   - Minimal
   - Default
4. Fill in your content
5. Upload images and documents
6. Publish

### Customizing Your Page

**Available Sections:**
- Hero banner with title and description
- Asset gallery (images/videos)
- Key metrics and terms
- Investment thesis
- Team/Sponsor information
- Documents (PPM, subscription docs)
- FAQ
- Contact form

### Sharing Your Page

Each asset page gets a unique URL:
```
https://your-domain.com/assets/your-token-symbol
```

Share this with potential investors. Each page includes:
- 🔒 Compliance badge showing regulatory framework
- "Powered by RWA-Studio" branding

---

## Billing & Subscriptions

### Subscription Plans

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0/mo | 1 token, basic features |
| **Pro** | $299/mo | Unlimited tokens, API access, priority support |
| **Enterprise** | Custom | White-label, custom compliance, dedicated support |

### Managing Your Subscription

1. Go to **Settings** → **Billing**
2. View current plan and usage
3. Upgrade or downgrade as needed
4. Update payment method
5. Download invoices

### Transaction Fees

Some operations incur platform fees:
- Token deployment: Included in subscription
- Transfer agent API calls: $0.10 per call (Pro plan)
- Asset page hosting: Included

---

## FAQ

### General

**Q: Do I need to know how to code?**
A: No! RWA-Studio provides a user-friendly interface for all operations.

**Q: What blockchain networks are supported?**
A: Currently Ethereum (Sepolia testnet, Mainnet) and Polygon (Amoy testnet). More networks coming soon.

**Q: Is my data secure?**
A: Yes. We use encryption at rest and in transit, and all smart contracts are based on audited OpenZeppelin code.

### Compliance

**Q: Does RWA-Studio replace legal counsel?**
A: No. RWA-Studio automates compliance enforcement but you should work with qualified securities attorneys for your offering.

**Q: Can I change compliance rules after deployment?**
A: Yes, but some changes may require governance approval or have time delays for security.

**Q: What if an investor's status changes?**
A: You can update the identity registry at any time. Transfers will be blocked if a holder no longer meets requirements.

### Technical

**Q: What if a transaction fails?**
A: Check the compliance status of both sender and recipient. Most failures are due to compliance restrictions.

**Q: Can I recover tokens sent to the wrong address?**
A: If you have admin rights, you can use the forced transfer function. Otherwise, standard ERC-20 rules apply.

**Q: What happens if I lose access to my admin wallet?**
A: If you have multiple admins configured, another admin can remove the lost wallet. Otherwise, you may need to deploy a new token.

---

## Getting Help

### Documentation

- [Developer Guide](DEVELOPER_GUIDE.md) - Technical documentation
- [API Reference](api-reference.md) - API endpoints
- [Security Audit Brief](SECURITY_AUDIT_BRIEF.md) - Security information

### Support

- **Email**: sowadalmughni@gmail.com
- **GitHub Issues**: [Report bugs or request features](https://github.com/sowadalmughni/rwa-studio/issues)
- **Discussions**: [Ask questions](https://github.com/sowadalmughni/rwa-studio/discussions)

---

**Built with ❤️ by Sowad Al-Mughni**

*"Tokenize Real-World Assets in 5 Clicks"*
