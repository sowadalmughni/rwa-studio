/**
 * RWA-Studio Hardhat Plugin for OpenZeppelin Integration
 * Author: Sowad Al-Mughni
 * 
 * This plugin extends Hardhat with RWA tokenization capabilities,
 * integrating seamlessly with OpenZeppelin's tools and contracts.
 */

const { task, subtask } = require("hardhat/config");
const { TASK_COMPILE } = require("hardhat/builtin-tasks/task-names");

// Plugin configuration
const PLUGIN_NAME = "hardhat-rwa-studio";

// RWA Studio tasks
task("rwa:deploy", "Deploy a new RWA token with compliance")
  .addParam("name", "Token name")
  .addParam("symbol", "Token symbol")
  .addParam("assetType", "Type of real-world asset")
  .addParam("framework", "Regulatory framework (RegD, RegS, RegCF)")
  .addParam("jurisdiction", "Jurisdiction code (US, EU, etc.)")
  .addOptionalParam("maxSupply", "Maximum token supply", "1000000")
  .addOptionalParam("decimals", "Token decimals", "18")
  .addOptionalParam("description", "Asset description")
  .setAction(async (taskArgs, hre) => {
    const { deployRWAToken } = require("./scripts/deploy-rwa-token");
    
    console.log("🚀 Deploying RWA Token with RWA-Studio...");
    console.log(`📋 Name: ${taskArgs.name}`);
    console.log(`🔤 Symbol: ${taskArgs.symbol}`);
    console.log(`🏢 Asset Type: ${taskArgs.assetType}`);
    console.log(`⚖️  Framework: ${taskArgs.framework}`);
    console.log(`🌍 Jurisdiction: ${taskArgs.jurisdiction}`);
    
    const deployment = await deployRWAToken(taskArgs, hre);
    
    console.log("✅ RWA Token deployed successfully!");
    console.log(`📄 Token Address: ${deployment.tokenAddress}`);
    console.log(`🔒 Compliance Module: ${deployment.complianceAddress}`);
    console.log(`👤 Identity Registry: ${deployment.identityRegistryAddress}`);
    console.log(`🌐 Asset Page: https://rwa-studio.com/assets/${deployment.tokenAddress}`);
    
    return deployment;
  });

task("rwa:verify-address", "Verify an address for RWA token compliance")
  .addParam("token", "Token contract address")
  .addParam("address", "Address to verify")
  .addParam("level", "Verification level (basic, accredited, institutional)")
  .addParam("jurisdiction", "Address jurisdiction")
  .addOptionalParam("expiry", "Verification expiry (days from now)", "365")
  .setAction(async (taskArgs, hre) => {
    const { verifyAddress } = require("./scripts/verify-address");
    
    console.log("🔍 Verifying address for RWA token...");
    console.log(`📄 Token: ${taskArgs.token}`);
    console.log(`👤 Address: ${taskArgs.address}`);
    console.log(`📊 Level: ${taskArgs.level}`);
    
    const result = await verifyAddress(taskArgs, hre);
    
    console.log("✅ Address verified successfully!");
    console.log(`🆔 Identity Hash: ${result.identityHash}`);
    console.log(`⏰ Expires: ${result.expirationDate}`);
    
    return result;
  });

task("rwa:compliance-check", "Check compliance status for a transfer")
  .addParam("token", "Token contract address")
  .addParam("from", "From address")
  .addParam("to", "To address")
  .addParam("amount", "Transfer amount")
  .setAction(async (taskArgs, hre) => {
    const { checkCompliance } = require("./scripts/compliance-check");
    
    console.log("🔍 Checking transfer compliance...");
    
    const result = await checkCompliance(taskArgs, hre);
    
    if (result.canTransfer) {
      console.log("✅ Transfer is compliant");
    } else {
      console.log("❌ Transfer blocked:");
      result.violations.forEach(violation => {
        console.log(`   - ${violation}`);
      });
    }
    
    return result;
  });

task("rwa:add-rule", "Add a compliance rule to a token")
  .addParam("token", "Token contract address")
  .addParam("rule", "Rule type (investor-limit, geographic, transfer-restriction)")
  .addVariadicPositionalParam("params", "Rule parameters")
  .setAction(async (taskArgs, hre) => {
    const { addComplianceRule } = require("./scripts/add-compliance-rule");
    
    console.log("📋 Adding compliance rule...");
    console.log(`📄 Token: ${taskArgs.token}`);
    console.log(`⚖️  Rule: ${taskArgs.rule}`);
    
    const result = await addComplianceRule(taskArgs, hre);
    
    console.log("✅ Compliance rule added successfully!");
    console.log(`🆔 Rule Address: ${result.ruleAddress}`);
    
    return result;
  });

task("rwa:generate-report", "Generate compliance report for a token")
  .addParam("token", "Token contract address")
  .addOptionalParam("format", "Report format (json, csv, pdf)", "json")
  .addOptionalParam("period", "Report period in days", "30")
  .setAction(async (taskArgs, hre) => {
    const { generateComplianceReport } = require("./scripts/generate-report");
    
    console.log("📊 Generating compliance report...");
    
    const report = await generateComplianceReport(taskArgs, hre);
    
    console.log("✅ Report generated successfully!");
    console.log(`📁 File: ${report.filename}`);
    console.log(`📈 Total Transfers: ${report.totalTransfers}`);
    console.log(`🚫 Blocked Transfers: ${report.blockedTransfers}`);
    console.log(`📊 Compliance Rate: ${report.complianceRate}%`);
    
    return report;
  });

task("rwa:asset-page", "Generate shareable asset page")
  .addParam("token", "Token contract address")
  .addOptionalParam("template", "Page template (default, premium, custom)", "default")
  .setAction(async (taskArgs, hre) => {
    const { generateAssetPage } = require("./scripts/generate-asset-page");
    
    console.log("🌐 Generating asset page...");
    
    const page = await generateAssetPage(taskArgs, hre);
    
    console.log("✅ Asset page generated!");
    console.log(`🌐 URL: ${page.url}`);
    console.log(`🔗 Share: ${page.shareUrl}`);
    console.log(`🏷️  Badge: ${page.badgeUrl}`);
    
    return page;
  });

// Subtasks for internal use
subtask("rwa:validate-params", "Validate RWA deployment parameters")
  .setAction(async (taskArgs, hre) => {
    const validAssetTypes = ["real-estate", "funds", "debt", "commodities", "equity", "art"];
    const validFrameworks = ["RegD", "RegS", "RegCF", "RegA"];
    const validJurisdictions = ["US", "EU", "UK", "CA", "AU", "SG"];
    
    if (!validAssetTypes.includes(taskArgs.assetType)) {
      throw new Error(`Invalid asset type. Must be one of: ${validAssetTypes.join(", ")}`);
    }
    
    if (!validFrameworks.includes(taskArgs.framework)) {
      throw new Error(`Invalid framework. Must be one of: ${validFrameworks.join(", ")}`);
    }
    
    if (!validJurisdictions.includes(taskArgs.jurisdiction)) {
      throw new Error(`Invalid jurisdiction. Must be one of: ${validJurisdictions.join(", ")}`);
    }
    
    return true;
  });

// Plugin configuration and helpers
const RWAStudioConfig = {
  // Default compliance rules by regulatory framework
  defaultRules: {
    RegD: [
      { type: "investor-limit", params: { maxInvestors: 99 } },
      { type: "accredited-only", params: { requireAccredited: true } }
    ],
    RegS: [
      { type: "geographic", params: { excludedCountries: ["US"] } },
      { type: "holding-period", params: { minimumHoldDays: 40 } }
    ],
    RegCF: [
      { type: "investor-limit", params: { maxInvestors: 1000 } },
      { type: "investment-limit", params: { maxPerInvestor: "107000" } }
    ],
    RegA: [
      { type: "investor-limit", params: { maxInvestors: 2000 } },
      { type: "qualified-only", params: { requireQualified: true } }
    ]
  },
  
  // Asset type configurations
  assetConfigs: {
    "real-estate": {
      defaultDecimals: 0,
      suggestedSupply: "1000",
      requiredDocs: ["property-deed", "appraisal", "insurance"]
    },
    "funds": {
      defaultDecimals: 18,
      suggestedSupply: "1000000",
      requiredDocs: ["fund-prospectus", "audited-financials", "management-agreement"]
    },
    "debt": {
      defaultDecimals: 6,
      suggestedSupply: "1000000",
      requiredDocs: ["loan-agreement", "credit-rating", "collateral-valuation"]
    },
    "commodities": {
      defaultDecimals: 8,
      suggestedSupply: "100000",
      requiredDocs: ["storage-receipt", "quality-certificate", "insurance"]
    }
  },
  
  // Network configurations
  networks: {
    mainnet: {
      factoryAddress: "0x...", // To be deployed
      gasPrice: "20000000000", // 20 gwei
      confirmations: 2
    },
    polygon: {
      factoryAddress: "0x...", // To be deployed
      gasPrice: "30000000000", // 30 gwei
      confirmations: 3
    },
    arbitrum: {
      factoryAddress: "0x...", // To be deployed
      gasPrice: "100000000", // 0.1 gwei
      confirmations: 1
    }
  }
};

// Plugin initialization
function initializeRWAStudioPlugin(hre) {
  // Add RWA Studio configuration to Hardhat Runtime Environment
  hre.rwaStudio = {
    config: RWAStudioConfig,
    
    // Helper functions
    getAssetConfig: (assetType) => RWAStudioConfig.assetConfigs[assetType],
    getDefaultRules: (framework) => RWAStudioConfig.defaultRules[framework],
    getNetworkConfig: (network) => RWAStudioConfig.networks[network],
    
    // Validation helpers
    validateAssetType: (assetType) => Object.keys(RWAStudioConfig.assetConfigs).includes(assetType),
    validateFramework: (framework) => Object.keys(RWAStudioConfig.defaultRules).includes(framework),
    
    // Utility functions
    formatTokenAmount: (amount, decimals = 18) => {
      return hre.ethers.utils.parseUnits(amount.toString(), decimals);
    },
    
    parseTokenAmount: (amount, decimals = 18) => {
      return hre.ethers.utils.formatUnits(amount, decimals);
    }
  };
  
  console.log("🏗️  RWA-Studio plugin initialized");
}

// Export plugin
module.exports = {
  initializeRWAStudioPlugin,
  RWAStudioConfig,
  PLUGIN_NAME
};

// Auto-initialize when plugin is loaded
if (typeof hre !== 'undefined') {
  initializeRWAStudioPlugin(hre);
}

