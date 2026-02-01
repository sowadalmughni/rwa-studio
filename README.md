# RWA-Studio

**Tokenize Real-World Assets in 5 Clicks**

Ever tried to tokenize a real estate fund or private equity offering? If you have, you know the pain: enterprise platforms that cost $50K+ upfront, take months to implement, and require a team of blockchain developers. That's exactly what RWA-Studio fixes.

Whether you're a fund manager launching a Reg D offering, a lawyer structuring a real estate syndication, or a compliance officer managing investor restrictions, RWA-Studio lets you deploy fully compliant security tokens in under 5 minutes - no blockchain experience required.

## What's the Big Idea?

Imagine you're launching a $10M real estate fund. Traditional tokenization means:

- 💸 **$50,000+** for enterprise platform licenses
- ⏰ **3-6 months** of implementation and customization
- 👥 **A team** of Solidity developers, compliance experts, and integrators

RWA-Studio flips this entirely:

- 🆓 **Open source** - no licensing fees, ever
- ⚡ **5 minutes** - from concept to deployed token
- 🎯 **5 clicks** - asset type, regulation, economics, restrictions, deploy

Built on the **ERC-3643** security token standard (the same one used by BlackRock, Franklin Templeton, and major institutions), RWA-Studio makes institutional-grade compliance accessible to everyone.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/sowadalmughni/rwa-studio.git
cd rwa-studio

# Install all dependencies (frontend, backend, contracts)
npm run install:all

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development servers (frontend + backend)
npm run dev
```

### Deploy Your First Token

```bash
# Using the Hardhat CLI
npx hardhat rwa:deploy \
  --name "Manhattan Real Estate Fund I" \
  --symbol "MREF" \
  --asset-type "real-estate" \
  --framework "RegD" \
  --supply 1000000 \
  --jurisdiction "US"

# Output: ✅ Token deployed at 0x1234...
#         ✅ Compliance module attached
#         ✅ Identity registry initialized
#         ✅ Asset page generated
```

That's it! You've just deployed an ERC-3643 compliant security token with Reg D restrictions.

### Using Docker (Recommended for Production)

```bash
# Standard deployment
docker-compose up -d

# Enterprise stack with PostgreSQL and monitoring
docker-compose --profile production up -d

# View running services
docker-compose ps
```

## Real-World Use Cases

### Fund Managers

- Launch Reg D/Reg S offerings without enterprise platform fees
- Automate investor verification and transfer restrictions
- Generate compliant asset pages for investor relations
- Track cap table and manage distributions

### Real Estate Syndicators

- Tokenize commercial properties for fractional ownership
- Enforce holding periods and accreditation requirements
- Manage 99-investor limits for 506(b) offerings
- Generate audit-ready compliance reports

### Private Equity Firms

- Create liquid secondary markets for LP interests
- Automate transfer agent functions
- Enforce geographic and jurisdictional restrictions
- Maintain real-time investor registries

### Compliance Officers

- Monitor all token transfers in real-time
- Verify investor accreditation status
- Generate regulatory reports on demand
- Manage KYC/AML verification workflows

## How It Works

RWA-Studio combines three powerful components:

1. **ERC-3643 Smart Contracts**: Institutional-grade security tokens with built-in compliance
2. **Transfer Agent Console**: Web-based management for post-deployment operations
3. **Hardhat Plugin**: Developer tools for automation and CI/CD integration

The 5-click flow:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  1. Asset   │───▶│ 2. Regulation│───▶│ 3. Economics │───▶│ 4. Restrict │───▶│  5. Deploy  │
│    Type     │    │  Framework   │    │   & Supply   │    │   Investors │    │   & Share   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
  Real Estate       Reg D 506(b)       1M tokens          US only            Live on-chain
  Funds             Reg D 506(c)       Vesting schedule   Accredited only    Asset page
  Debt              Reg S              Distribution       99 investor max    Compliance active
  Commodities       Reg CF             Pricing            Holding period
  Private Equity    Reg A+
```

## Features

### 🔐 Compliance-by-Default

Built on ERC-3643, every token comes with institutional-grade compliance:

- **5 Modular Compliance Rules**:
  - `InvestorLimitRule` - Enforce Reg D 99-investor cap or Reg CF 1000-investor limit
  - `GeographicRule` - Restrict transfers by jurisdiction (US, EU, UK, etc.)
  - `AccreditedInvestorRule` - Require investor accreditation verification
  - `HoldingPeriodRule` - Enforce lock-up periods (6mo, 12mo, custom)
  - `TransferLimitRule` - Cap maximum transfer amounts

- **Multi-Regulatory Support**: Reg D 506(b), Reg D 506(c), Reg S, Reg CF, Reg A+

### 💼 Transfer Agent Console

Full-featured backend API for token management:

- **Identity Registry** - Manage verified investor addresses
- **Compliance Monitoring** - Real-time transfer validation
- **Event Logging** - Complete audit trail
- **JWT + Wallet Auth** - Secure dual authentication
- **Rate Limiting** - Protection against abuse

### 🔗 Network Support

RWA-Studio uses ERC-3643 compliant smart contracts that can be deployed to any EVM-compatible network:

| Network          | Status    | Notes                           |
| ---------------- | --------- | ------------------------------- |
| Ethereum Sepolia | ✅ Tested | Primary testnet for development |
| Ethereum Mainnet | 🟡 Ready  | Requires mainnet RPC and gas    |
| Polygon          | 🟡 Ready  | Lower gas costs, L2 deployment  |
| Arbitrum         | 🟡 Ready  | L2 optimistic rollup            |
| Base             | 🟡 Ready  | Coinbase L2                     |

**Status Key:**

- ✅ **Tested** - Verified working with automated tests
- 🟡 **Ready** - Contracts compatible, requires network config

**Current Limitation:** The default configuration targets a single network at a time. Multi-chain deployment (deploying the same token across multiple networks) is on the roadmap but not yet implemented. To deploy on a different network, update your Hardhat config with the appropriate RPC URL and deploy separately.

### 🛠 Developer Friendly

**6 Hardhat Tasks** for automation:

```bash
# Verify an investor address
npx hardhat verify-address --token 0x... --address 0x... --level accredited --jurisdiction US

# Check if a transfer would be compliant
npx hardhat compliance-check --token 0x... --from 0x... --to 0x... --amount 1000

# Add a compliance rule
npx hardhat add-compliance-rule --token 0x... --rule investor-limit --params '{"maxInvestors": 99}'

# Generate compliance report
npx hardhat generate-report --token 0x... --format markdown --period 30

# Create shareable asset page
npx hardhat generate-asset-page --token 0x... --template professional
```

### 🌐 Modern Web3 Stack

- **Wallet Integration**: MetaMask, WalletConnect, Coinbase Wallet, Rainbow
- **React 19 + Vite**: Lightning-fast frontend
- **wagmi + RainbowKit**: Best-in-class Web3 UX
- **shadcn/ui**: Beautiful, accessible components

### 📊 Enterprise Observability

- **Structured Logging** - JSON-formatted logs for analysis
- **Health Checks** - Built-in monitoring endpoints
- **Docker Compose** - One-command deployment
- **PostgreSQL** - Production-ready database

## Deployment

### Development

```bash
# Start all services in development mode
npm run dev

# Or individually:
npm run dev:frontend    # React app on :5173
npm run dev:backend     # Flask API on :5000
npm run dev:contracts   # Hardhat node on :8545
```

### Production with Docker

```bash
# Standard deployment (frontend, backend, redis)
docker-compose up -d

# Full enterprise stack (adds PostgreSQL, monitoring)
docker-compose --profile production up -d

# Scale backend for high availability
docker-compose up -d --scale backend=3
```

### Environment Configuration

```env
# .env.example
# Blockchain
PRIVATE_KEY=your-deployer-private-key
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/...
MAINNET_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/...

# Backend
JWT_SECRET_KEY=your-super-secret-jwt-key
DATABASE_URL=postgresql://user:pass@localhost:5432/rwa_studio
REDIS_URL=redis://localhost:6379

# Frontend
VITE_API_URL=http://localhost:5000
VITE_WALLETCONNECT_PROJECT_ID=your-project-id
```

## Project Structure

```
rwa-studio/
├── frontend/                   # React 19 + Vite + shadcn/ui
│   ├── src/
│   │   ├── components/         # UI components + wallet integration
│   │   │   ├── ui/             # shadcn/ui component library
│   │   │   └── wallet/         # RainbowKit wallet components
│   │   ├── hooks/              # useWallet, useMobile
│   │   ├── providers/          # WalletProvider context
│   │   └── lib/                # Utilities
│   └── Dockerfile
│
├── backend/                    # Flask REST API
│   ├── src/
│   │   ├── routes/             # auth, transfer_agent, user
│   │   ├── middleware/         # auth, rate_limit, security, validation
│   │   ├── models/             # SQLAlchemy models (User, Token)
│   │   └── database/           # DB configuration
│   ├── tests/                  # pytest test suite (40 tests)
│   └── Dockerfile
│
├── smart-contracts/            # Hardhat + Solidity 0.8.28
│   ├── contracts/
│   │   ├── RWAToken.sol        # Core ERC-3643 token
│   │   ├── RWATokenFactory.sol # Factory for token deployment
│   │   ├── compliance/         # ComplianceModule + 5 rules
│   │   ├── registry/           # IdentityRegistry for KYC
│   │   └── interfaces/         # IERC3643 standard interface
│   ├── scripts/                # 6 Hardhat tasks
│   └── test/                   # Contract tests (27 tests)
│
├── docs/                       # Documentation
│   ├── DEVELOPER_GUIDE.md
│   └── SECURITY_AUDIT_BRIEF.md
│
├── docker-compose.yml          # Full-stack orchestration
└── .github/workflows/          # CI/CD pipelines
```

## Roadmap

### Phase 1: Foundation ✅

- [x] ERC-3643 token implementation
- [x] 5-click tokenization wizard
- [x] Wallet integration (RainbowKit)
- [x] Backend authentication (JWT + wallet)
- [x] Basic compliance rules

### Phase 2: Security & Quality ✅

- [x] 5 modular compliance rules
- [x] Rate limiting & input validation
- [x] Docker containerization
- [x] CI/CD pipeline (GitHub Actions)
- [x] 67 tests (40 backend + 27 contracts)
- [x] Security audit documentation

### Phase 3: Integration Services (Q1 2026)

- [ ] KYC provider integration (Onfido, Jumio)
- [ ] Payment gateway (Stripe, crypto rails)
- [ ] Email notification service
- [ ] IPFS document storage
- [ ] Advanced analytics dashboard

### Phase 4: Scale & Ecosystem (Q2 2026)

- [ ] Multi-chain deployment automation
- [ ] Secondary market support
- [ ] Governance token integration
- [ ] ONCHAINID identity standard
- [ ] Mobile application

### Phase 5: Enterprise (Q3-Q4 2026)

- [ ] White-label solutions
- [ ] Enterprise SSO/LDAP
- [ ] Custom compliance rule builder
- [ ] Professional services & support
- [ ] Regulatory reporting automation

## Contributing

This is an open-source project and contributions are welcome!

### Getting Started

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/rwa-studio.git
cd rwa-studio

# Install dependencies
npm run install:all

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes, add tests
npm test

# Submit pull request
```

### Development Setup

```bash
# Backend development
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pytest  # Run tests

# Frontend development
cd frontend
pnpm install
pnpm dev

# Smart contract development
cd smart-contracts
npm install
npx hardhat compile
npx hardhat test
```

### Areas Where We Need Help

- 🔗 Additional blockchain integrations (Solana, Cosmos)
- 📱 Mobile app development (React Native)
- 🌍 Internationalization (i18n)
- 📚 Documentation improvements
- 🧪 Additional test coverage
- ♿ Accessibility improvements

## Security

Security is critical for financial infrastructure. Here's our approach:

- **ERC-3643 Standard** - Battle-tested security token standard
- **OpenZeppelin Contracts** - Industry-standard Solidity libraries
- **Comprehensive Testing** - 67 automated tests
- **Audit Documentation** - Prepared for OpenZeppelin security audit
- **Rate Limiting** - Protection against API abuse
- **Input Validation** - All endpoints validated

### Security Checklist

- [x] Secrets in environment variables
- [x] Rate limiting on all endpoints
- [x] Input validation middleware
- [x] SQL injection prevention
- [x] XSS prevention
- [x] CORS configuration
- [x] Content Security Policy headers
- [ ] Smart contract audit (scheduled)
- [ ] Penetration testing
- [ ] Multi-sig for contract ownership

Found a security issue? Please email **sowad@kitalonlabs.com** instead of opening a public issue.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

This project builds on the incredible work of:

- [OpenZeppelin](https://openzeppelin.com/) - Security standards and Solidity libraries
- [Tokeny](https://tokeny.com/) - ERC-3643 security token standard
- [Hardhat](https://hardhat.org/) - Ethereum development framework
- [RainbowKit](https://www.rainbowkit.com/) - Beautiful wallet connection
- [shadcn/ui](https://ui.shadcn.com/) - Stunning React components
- The broader DeFi and RWA tokenization community

## Support

- **Primary Contact**: Md. Sowad Al-Mughni (sowad@kitalonlabs.com)
- **Company**: [Kitalon Labs](https://kitalonlabs.com)
- **Documentation**: [Developer Guide](docs/DEVELOPER_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/sowadalmughni/rwa-studio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sowadalmughni/rwa-studio/discussions)

---

**Maintained by [Kitalon Labs](https://kitalonlabs.com)** | Md. Sowad Al-Mughni (sowad@kitalonlabs.com)

Made with ❤️ for the future of finance
