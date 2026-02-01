require("@nomicfoundation/hardhat-toolbox");

// ========== HARDHAT TASKS ==========

/**
 * Verify Address Task
 * Adds a verified address to the identity registry
 * 
 * Usage: npx hardhat verify-address --token <address> --address <address> --level <level> --jurisdiction <code>
 */
task("verify-address", "Add a verified address to the identity registry")
  .addParam("token", "The RWA token contract address")
  .addParam("address", "The address to verify")
  .addParam("level", "Verification level: basic, accredited, or institutional")
  .addParam("jurisdiction", "Two-letter jurisdiction code (e.g., US, DE, SG)")
  .addOptionalParam("expiry", "Expiry in days (default: 365)", "365")
  .setAction(async (taskArgs, hre) => {
    const { verifyAddress } = require("./scripts/verify-address");
    return verifyAddress(taskArgs, hre);
  });

/**
 * Compliance Check Task
 * Checks if a proposed transfer would pass all compliance rules
 * 
 * Usage: npx hardhat compliance-check --token <address> --from <address> --to <address> --amount <amount>
 */
task("compliance-check", "Check if a transfer would pass compliance")
  .addParam("token", "The RWA token contract address")
  .addParam("from", "Sender address")
  .addParam("to", "Recipient address")
  .addParam("amount", "Token amount to transfer")
  .setAction(async (taskArgs, hre) => {
    const { checkCompliance } = require("./scripts/compliance-check");
    return checkCompliance(taskArgs, hre);
  });

/**
 * Add Compliance Rule Task
 * Deploys and adds a compliance rule to a token
 * 
 * Usage: npx hardhat add-compliance-rule --token <address> --rule <type> [--params <params>]
 */
task("add-compliance-rule", "Deploy and add a compliance rule to a token")
  .addParam("token", "The RWA token contract address")
  .addParam("rule", "Rule type: investor-limit, geographic, accredited, holding-period, transfer-limit")
  .addOptionalVariadicPositionalParam("params", "Rule-specific parameters")
  .setAction(async (taskArgs, hre) => {
    const { addComplianceRule } = require("./scripts/add-compliance-rule");
    return addComplianceRule(taskArgs, hre);
  });

/**
 * Generate Report Task
 * Generates compliance reports for RWA tokens
 * 
 * Usage: npx hardhat generate-report --token <address> [--format json|csv|pdf] [--period 30]
 */
task("generate-report", "Generate a compliance report for a token")
  .addParam("token", "The RWA token contract address")
  .addOptionalParam("format", "Output format: json, csv, or pdf (markdown)", "json")
  .addOptionalParam("period", "Report period in days", "30")
  .setAction(async (taskArgs, hre) => {
    const { generateComplianceReport } = require("./scripts/generate-report");
    return generateComplianceReport(taskArgs, hre);
  });

/**
 * Generate Asset Page Task
 * Generates shareable asset pages with compliance badges
 * 
 * Usage: npx hardhat generate-asset-page --token <address> [--template default|premium|minimal]
 */
task("generate-asset-page", "Generate a shareable asset page for a token")
  .addParam("token", "The RWA token contract address")
  .addOptionalParam("template", "Page template: default, premium, or minimal", "default")
  .setAction(async (taskArgs, hre) => {
    const { generateAssetPage } = require("./scripts/generate-asset-page");
    return generateAssetPage(taskArgs, hre);
  });

// ========== HARDHAT CONFIG ==========

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.28",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
  networks: {
    hardhat: {
      chainId: 31337
    },
    // Localhost for testing
    localhost: {
      url: "http://127.0.0.1:8545"
    },
    // Sepolia testnet (configure with env vars in production)
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    },
    // Polygon Amoy testnet
    amoy: {
      url: process.env.AMOY_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    },
    // Mainnet (use with caution)
    mainnet: {
      url: process.env.MAINNET_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : []
    }
  },
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  }
};
