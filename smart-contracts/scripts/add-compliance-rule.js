/**
 * Add Compliance Rule Script for RWA-Studio
 * Author: Sowad Al-Mughni
 *
 * Deploys and adds compliance rules to a token's compliance module
 */

// Rule type configurations
const RuleConfigs = {
  "investor-limit": {
    contract: "InvestorLimitRule",
    description: "Limits the maximum number of token holders",
    defaultParams: { maxInvestors: 99 },
  },
  geographic: {
    contract: "GeographicRule",
    description: "Restricts transfers based on jurisdiction",
    defaultParams: { isAllowlistMode: false },
  },
  accredited: {
    contract: "AccreditedInvestorRule",
    description: "Requires accredited investor status for transfers",
    defaultParams: {},
  },
  "holding-period": {
    contract: "HoldingPeriodRule",
    description: "Enforces minimum token holding periods",
    defaultParams: { holdingPeriodDays: 365 },
  },
  "transfer-limit": {
    contract: "TransferLimitRule",
    description: "Limits maximum investment per investor",
    defaultParams: {
      maxTokensPerInvestor: 0,
      maxInvestmentAmount: 0,
      tokenPriceUSDCents: 0,
    },
  },
};

async function addComplianceRule(taskArgs, hre) {
  const [deployer] = await hre.ethers.getSigners();

  console.log("Adding compliance rule with RWA-Studio...");
  console.log(`Using account: ${deployer.address}`);

  const tokenAddress = taskArgs.token;
  const ruleType = taskArgs.rule.toLowerCase();
  const params = taskArgs.params || [];

  // Validate rule type
  if (!(ruleType in RuleConfigs)) {
    const validRules = Object.keys(RuleConfigs).join(", ");
    throw new Error(`Invalid rule type: ${ruleType}. Valid options: ${validRules}`);
  }

  const ruleConfig = RuleConfigs[ruleType];

  console.log(`\nRule Configuration:`);
  console.log(`   Token: ${tokenAddress}`);
  console.log(`   Rule Type: ${ruleType}`);
  console.log(`   Description: ${ruleConfig.description}`);
  console.log(`   Parameters: ${params.length > 0 ? params.join(", ") : "Using defaults"}`);

  try {
    // Get token contract
    const RWAToken = await hre.ethers.getContractFactory("RWAToken");
    const token = RWAToken.attach(tokenAddress);

    // Get compliance and identity registry addresses
    const complianceAddress = await token.compliance();
    const identityRegistryAddress = await token.identityRegistry();

    console.log(`\nContract Addresses:`);
    console.log(`   Compliance Module: ${complianceAddress}`);
    console.log(`   Identity Registry: ${identityRegistryAddress}`);

    if (complianceAddress === hre.ethers.ZeroAddress) {
      throw new Error("Token has no compliance module configured");
    }

    // Get compliance module
    const ComplianceModule = await hre.ethers.getContractFactory("ComplianceModule");
    const compliance = ComplianceModule.attach(complianceAddress);

    // Deploy the specific rule contract
    let ruleContract;
    let ruleAddress;

    console.log(`\nDeploying ${ruleConfig.contract}...`);

    switch (ruleType) {
      case "investor-limit": {
        const maxInvestors = params[0]
          ? parseInt(params[0])
          : ruleConfig.defaultParams.maxInvestors;
        console.log(`   Max Investors: ${maxInvestors}`);

        const InvestorLimitRule = await hre.ethers.getContractFactory("InvestorLimitRule");
        ruleContract = await InvestorLimitRule.deploy(tokenAddress, maxInvestors);
        break;
      }

      case "geographic": {
        const isAllowlistMode = params[0] === "true" || params[0] === "allowlist";
        console.log(`   Mode: ${isAllowlistMode ? "Allowlist" : "Blocklist"}`);

        if (identityRegistryAddress === hre.ethers.ZeroAddress) {
          throw new Error("Geographic rule requires an identity registry");
        }

        const GeographicRule = await hre.ethers.getContractFactory("GeographicRule");
        ruleContract = await GeographicRule.deploy(
          tokenAddress,
          identityRegistryAddress,
          isAllowlistMode
        );
        break;
      }

      case "accredited": {
        if (identityRegistryAddress === hre.ethers.ZeroAddress) {
          throw new Error("Accredited investor rule requires an identity registry");
        }

        const AccreditedInvestorRule =
          await hre.ethers.getContractFactory("AccreditedInvestorRule");
        ruleContract = await AccreditedInvestorRule.deploy(tokenAddress, identityRegistryAddress);
        break;
      }

      case "holding-period": {
        const holdingPeriodDays = params[0]
          ? parseInt(params[0])
          : ruleConfig.defaultParams.holdingPeriodDays;
        const holdingPeriodSeconds = holdingPeriodDays * 24 * 60 * 60;
        console.log(
          `   Holding Period: ${holdingPeriodDays} days (${holdingPeriodSeconds} seconds)`
        );

        const HoldingPeriodRule = await hre.ethers.getContractFactory("HoldingPeriodRule");
        ruleContract = await HoldingPeriodRule.deploy(tokenAddress, holdingPeriodSeconds);
        break;
      }

      case "transfer-limit": {
        const maxTokens = params[0] ? hre.ethers.parseEther(params[0]) : 0n;
        const maxInvestmentUSD = params[1] ? parseInt(params[1]) * 100 : 0; // Convert to cents
        const tokenPriceCents = params[2] ? parseInt(params[2]) * 100 : 0; // Convert to cents

        console.log(`   Max Tokens: ${maxTokens.toString()}`);
        console.log(`   Max Investment USD: $${maxInvestmentUSD / 100}`);
        console.log(`   Token Price: $${tokenPriceCents / 100}`);

        if (maxTokens === 0n && maxInvestmentUSD === 0) {
          throw new Error("At least one limit (maxTokens or maxInvestmentUSD) must be specified");
        }

        const TransferLimitRule = await hre.ethers.getContractFactory("TransferLimitRule");
        ruleContract = await TransferLimitRule.deploy(
          tokenAddress,
          maxTokens,
          maxInvestmentUSD,
          tokenPriceCents
        );
        break;
      }

      default:
        throw new Error(`Rule type ${ruleType} not yet implemented`);
    }

    await ruleContract.waitForDeployment();
    ruleAddress = await ruleContract.getAddress();

    console.log(`Rule deployed to: ${ruleAddress}`);

    // Add rule to compliance module
    console.log(`\nAdding rule to compliance module...`);
    const addTx = await compliance.addRule(ruleAddress);
    console.log(`Transaction submitted: ${addTx.hash}`);

    const receipt = await addTx.wait();
    console.log(`Rule added in block: ${receipt.blockNumber}`);

    // Verify the rule was added
    const hasRule = await compliance.hasRule(ruleAddress);
    const ruleCount = await compliance.getRuleCount();

    console.log(`\nCompliance Rule Added Successfully!`);
    console.log(`   Rule Address: ${ruleAddress}`);
    console.log(`   Rule Type: ${ruleType}`);
    console.log(`   Is Registered: ${hasRule}`);
    console.log(`   Total Rules: ${ruleCount.toString()}`);

    // Transfer ownership of the rule to the token owner
    const tokenOwner = await token.owner();
    if (tokenOwner !== deployer.address) {
      console.log(`\nTransferring rule ownership to token owner...`);
      const transferTx = await ruleContract.transferOwnership(tokenOwner);
      await transferTx.wait();
      console.log(`Ownership transferred to: ${tokenOwner}`);
    }

    return {
      success: true,
      ruleAddress: ruleAddress,
      ruleType: ruleType,
      tokenAddress: tokenAddress,
      complianceAddress: complianceAddress,
      transactionHash: addTx.hash,
    };
  } catch (error) {
    console.error(`\nError adding compliance rule:`, error.message);
    throw error;
  }
}

module.exports = { addComplianceRule };
