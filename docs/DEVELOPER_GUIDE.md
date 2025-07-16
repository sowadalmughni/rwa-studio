# RWA-Studio Developer Guide

**Tokenize Real-World Assets in 5 Clicks**

Author: Sowad Al-Mughni  
Email: sowadalmughni@gmail.com

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Smart Contracts](#smart-contracts)
5. [Frontend Application](#frontend-application)
6. [Transfer Agent Console](#transfer-agent-console)
7. [OpenZeppelin Plugin](#openzeppelin-plugin)
8. [API Reference](#api-reference)
9. [Deployment Guide](#deployment-guide)
10. [Contributing](#contributing)

## Overview

RWA-Studio is a comprehensive platform for tokenizing real-world assets with built-in regulatory compliance. It provides:

- **5-Click Tokenization**: Simplified workflow for creating compliant security tokens
- **ERC-3643 Compliance**: Built-in support for the T-REX standard
- **Regulatory Frameworks**: Support for Reg D, Reg S, Reg CF, and Reg A
- **Transfer Agent Console**: Professional tools for compliance management
- **OpenZeppelin Integration**: Seamless integration with OpenZeppelin tools

### Key Features

- ✅ **Compliance-by-Default**: Automatic compliance rule deployment
- ✅ **Multi-Jurisdiction Support**: US, EU, UK, CA, AU, SG
- ✅ **Asset Type Flexibility**: Real estate, funds, debt, commodities, equity, art
- ✅ **Professional UX**: Enterprise-grade interface for lawyers and fund managers
- ✅ **Shareable Asset Pages**: Dynamic pages with compliance badges
- ✅ **Transfer Agent APIs**: Complete backend for compliance operations

## Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.8+ (for backend)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/rwa-studio.git
cd rwa-studio

# Install dependencies
npm install

# Install frontend dependencies
cd frontend && npm install && cd ..

# Install backend dependencies
cd backend && pip install -r requirements.txt && cd ..

# Install smart contract dependencies
cd smart-contracts && yarn install && cd ..
```

### Development Setup

1. **Start the Frontend**:
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:5173
```

2. **Start the Backend**:
```bash
cd backend
python src/main.py
# Backend runs on http://localhost:5000
```

3. **Compile Smart Contracts**:
```bash
cd smart-contracts
npx hardhat compile
```

### Deploy Your First RWA Token

```bash
cd smart-contracts

# Deploy a real estate token with Reg D compliance
npx hardhat rwa:deploy \
  --name "Luxury Condo Token" \
  --symbol "LCT" \
  --asset-type "real-estate" \
  --framework "RegD" \
  --jurisdiction "US" \
  --max-supply "1000" \
  --network localhost
```

## Architecture

RWA-Studio follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │ Smart Contracts │
│   (React)       │◄──►│   (Flask)       │◄──►│   (Solidity)    │
│                 │    │                 │    │                 │
│ • 5-Click UI    │    │ • Transfer      │    │ • ERC-3643      │
│ • Asset Pages   │    │   Agent Console │    │ • Compliance    │
│ • Compliance    │    │ • API Endpoints │    │ • Identity      │
│   Dashboard     │    │ • Database      │    │   Registry      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Overview

- **Frontend**: React application with 5-click tokenization workflow
- **Backend**: Flask API with transfer agent console and compliance tracking
- **Smart Contracts**: ERC-3643 compliant tokens with modular compliance rules
- **Database**: SQLite for development, PostgreSQL for production
- **Blockchain**: Ethereum, Polygon, Arbitrum support

## Smart Contracts

### Core Contracts

#### RWAToken.sol
The main token contract implementing ERC-3643 standard:

```solidity
contract RWAToken is ERC20, Ownable, Pausable, ReentrancyGuard, IERC3643 {
    // ERC-3643 compliance implementation
    // Asset information storage
    // Transfer restrictions
    // Compliance integration
}
```

**Key Features**:
- ERC-20 compatible with compliance overlay
- Pausable transfers for emergency situations
- Asset metadata storage (IPFS integration)
- Compliance module integration
- Identity registry integration

#### ComplianceModule.sol
Manages compliance rules and transfer validation:

```solidity
contract ComplianceModule is ICompliance, Ownable {
    // Rule management
    // Transfer validation
    // Compliance reporting
}
```

#### IdentityRegistry.sol
Manages verified addresses and KYC/AML data:

```solidity
contract IdentityRegistry is IIdentityRegistry, Ownable {
    // Address verification
    // KYC/AML integration
    // Jurisdiction tracking
}
```

### Compliance Rules

RWA-Studio supports modular compliance rules:

- **InvestorLimitRule**: Limits number of token holders (Reg D: 99, Reg CF: 1000)
- **GeographicRule**: Restricts transfers by jurisdiction
- **AccreditedInvestorRule**: Requires accredited investor status
- **HoldingPeriodRule**: Enforces minimum holding periods
- **TransferLimitRule**: Limits transfer amounts and frequency

### Deployment

Deploy contracts using the Hardhat plugin:

```bash
# Deploy with default configuration
npx hardhat rwa:deploy --name "My Token" --symbol "MTK" --asset-type "funds" --framework "RegD" --jurisdiction "US"

# Deploy with custom parameters
npx hardhat rwa:deploy \
  --name "Real Estate Fund" \
  --symbol "REF" \
  --asset-type "real-estate" \
  --framework "RegS" \
  --jurisdiction "EU" \
  --max-supply "10000" \
  --decimals "0" \
  --description "Tokenized commercial real estate portfolio"
```

## Frontend Application

### 5-Click Workflow

The frontend implements an intuitive 5-step process:

1. **Asset Type Selection**: Choose from real estate, funds, debt, commodities, equity, art
2. **Regulatory Framework**: Select Reg D, Reg S, Reg CF, or Reg A
3. **Token Economics**: Configure supply, distribution, vesting
4. **Investor Restrictions**: Set KYC/AML, geographic, transfer limits
5. **Deployment & Asset Page**: Deploy contracts and generate shareable page

### Key Components

```jsx
// Main tokenization workflow
<TokenizationWizard />

// Asset type selection
<AssetTypeSelector />

// Regulatory framework configuration
<RegulatoryFrameworkSelector />

// Token economics configuration
<TokenEconomicsForm />

// Investor restrictions setup
<InvestorRestrictionsForm />

// Deployment and asset page generation
<DeploymentSummary />
```

### State Management

The application uses React hooks for state management:

```jsx
const [currentStep, setCurrentStep] = useState(1);
const [tokenConfig, setTokenConfig] = useState({
  assetType: '',
  framework: '',
  tokenomics: {},
  restrictions: {},
  deployment: {}
});
```

## Transfer Agent Console

### Features

The transfer agent console provides professional tools for compliance management:

- **Token Management**: View and manage all deployed tokens
- **Identity Verification**: Add and manage verified addresses
- **Compliance Monitoring**: Track compliance events and violations
- **Reporting**: Generate compliance reports and analytics
- **User Management**: Manage transfer agent users and permissions

### API Endpoints

#### Token Management
```http
GET /api/transfer-agent/tokens
POST /api/transfer-agent/tokens
GET /api/transfer-agent/tokens/{address}
```

#### Identity Verification
```http
GET /api/transfer-agent/tokens/{address}/verified-addresses
POST /api/transfer-agent/tokens/{address}/verified-addresses
PUT /api/transfer-agent/verified-addresses/{id}
```

#### Compliance Monitoring
```http
GET /api/transfer-agent/tokens/{address}/compliance-events
POST /api/transfer-agent/compliance-events
PUT /api/transfer-agent/compliance-events/{id}/resolve
```

#### Analytics
```http
GET /api/transfer-agent/tokens/{address}/metrics
GET /api/transfer-agent/dashboard/overview
```

### Database Schema

The backend uses SQLAlchemy models:

- **TokenDeployment**: Stores token deployment information
- **VerifiedAddress**: Tracks verified addresses per token
- **ComplianceEvent**: Logs compliance events and violations
- **TransferAgentUser**: Manages console users
- **TokenMetrics**: Stores analytics data

## OpenZeppelin Plugin

### Installation

```bash
npm install hardhat-rwa-studio
```

### Configuration

Add to your `hardhat.config.js`:

```javascript
require("hardhat-rwa-studio");

module.exports = {
  solidity: "0.8.19",
  rwaStudio: {
    defaultNetwork: "polygon",
    apiKey: "your-api-key",
    factoryAddress: "0x..." // Optional: custom factory
  }
};
```

### Available Tasks

```bash
# Deploy RWA token
npx hardhat rwa:deploy --name "Token" --symbol "TKN" --asset-type "funds" --framework "RegD" --jurisdiction "US"

# Verify address for compliance
npx hardhat rwa:verify-address --token 0x... --address 0x... --level "accredited" --jurisdiction "US"

# Check transfer compliance
npx hardhat rwa:compliance-check --token 0x... --from 0x... --to 0x... --amount "1000"

# Add compliance rule
npx hardhat rwa:add-rule --token 0x... --rule "investor-limit" 99

# Generate compliance report
npx hardhat rwa:generate-report --token 0x... --format "pdf" --period "30"

# Generate asset page
npx hardhat rwa:asset-page --token 0x... --template "premium"
```

## API Reference

### Authentication

The API uses wallet-based authentication:

```javascript
// Connect wallet and sign message
const signature = await signer.signMessage("RWA-Studio Authentication");

// Include in requests
headers: {
  'Authorization': `Bearer ${signature}`,
  'X-Wallet-Address': walletAddress
}
```

### Response Format

All API responses follow this format:

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "pagination": {
    // Pagination info (for paginated endpoints)
  }
}
```

Error responses:

```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

## Deployment Guide

### Development Deployment

1. **Local Blockchain**:
```bash
cd smart-contracts
npx hardhat node
```

2. **Deploy Contracts**:
```bash
npx hardhat rwa:deploy --network localhost --name "Test Token" --symbol "TEST" --asset-type "funds" --framework "RegD" --jurisdiction "US"
```

3. **Start Services**:
```bash
# Terminal 1: Frontend
cd frontend && npm run dev

# Terminal 2: Backend
cd backend && python src/main.py
```

### Production Deployment

1. **Smart Contracts**:
```bash
# Deploy to mainnet
npx hardhat rwa:deploy --network mainnet --name "Production Token" --symbol "PROD" --asset-type "real-estate" --framework "RegS" --jurisdiction "EU"

# Verify contracts
npx hardhat verify --network mainnet 0x...
```

2. **Frontend**:
```bash
cd frontend
npm run build
# Deploy to your hosting provider
```

3. **Backend**:
```bash
cd backend
# Configure production database
# Deploy to your server (AWS, GCP, etc.)
```

### Environment Variables

Create `.env` files for each environment:

```bash
# Smart Contracts (.env)
PRIVATE_KEY=your_private_key
ETHERSCAN_API_KEY=your_etherscan_key
INFURA_PROJECT_ID=your_infura_id

# Backend (.env)
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your_secret_key
CORS_ORIGINS=https://your-frontend-domain.com

# Frontend (.env)
VITE_API_URL=https://your-backend-domain.com/api
VITE_CHAIN_ID=1
VITE_RPC_URL=https://mainnet.infura.io/v3/your-project-id
```

## Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `npm test`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Standards

- **Solidity**: Follow OpenZeppelin standards and use NatSpec documentation
- **JavaScript**: Use ESLint and Prettier for formatting
- **Python**: Follow PEP 8 and use type hints
- **React**: Use functional components with hooks

### Testing

```bash
# Smart contract tests
cd smart-contracts && npx hardhat test

# Frontend tests
cd frontend && npm test

# Backend tests
cd backend && python -m pytest
```

### Security

- All smart contracts are audited before mainnet deployment
- Follow security best practices for key management
- Use multi-signature wallets for production deployments
- Regular security updates and dependency audits

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Support

For support and questions:

- Email: sowadalmughni@gmail.com
- GitHub Issues: [Create an issue](https://github.com/your-username/rwa-studio/issues)
- Documentation: [Full documentation](https://docs.rwa-studio.com)

---

**Built with ❤️ by Sowad Al-Mughni**

