/**
 * RWA Token Deployment Script
 * Author: Sowad Al-Mughni
 * 
 * Deploys a complete RWA token with compliance infrastructure
 */

const fs = require("fs");
const path = require("path");

async function deployRWAToken(taskArgs, hre) {
  const [deployer] = await hre.ethers.getSigners();
  
  console.log("🔑 Deploying with account:", deployer.address);
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("💰 Account balance:", hre.ethers.formatEther(balance));
  
  // Validate parameters
  await hre.run("rwa:validate-params", taskArgs);
  
  // Get asset configuration
  const assetConfig = hre.rwaStudio.getAssetConfig(taskArgs.assetType);
  const defaultRules = hre.rwaStudio.getDefaultRules(taskArgs.framework);
  
  // Use asset-specific defaults if not provided
  const decimals = taskArgs.decimals || assetConfig.defaultDecimals;
  const maxSupply = taskArgs.maxSupply || assetConfig.suggestedSupply;
  
  console.log("📋 Deployment Configuration:");
  console.log(`   Decimals: ${decimals}`);
  console.log(`   Max Supply: ${maxSupply}`);
  console.log(`   Default Rules: ${defaultRules.length}`);
  
  try {
    // Step 1: Deploy Identity Registry
    console.log("\n🔍 Deploying Identity Registry...");
    const IdentityRegistry = await hre.ethers.getContractFactory("IdentityRegistry");
    const identityRegistry = await IdentityRegistry.deploy();
    await identityRegistry.waitForDeployment();
    const identityRegistryAddress = await identityRegistry.getAddress();
    console.log("✅ Identity Registry deployed to:", identityRegistryAddress);
    
    // Step 2: Deploy Compliance Module
    console.log("\n⚖️  Deploying Compliance Module...");
    const ComplianceModule = await hre.ethers.getContractFactory("ComplianceModule");
    const complianceModule = await ComplianceModule.deploy(hre.ethers.ZeroAddress); // Will be updated with token address
    await complianceModule.waitForDeployment();
    const complianceModuleAddress = await complianceModule.getAddress();
    console.log("✅ Compliance Module deployed to:", complianceModuleAddress);
    
    // Step 3: Deploy RWA Token
    console.log("\n🪙 Deploying RWA Token...");
    const RWAToken = await hre.ethers.getContractFactory("RWAToken");
    const rwaToken = await RWAToken.deploy(
      taskArgs.name,
      taskArgs.symbol,
      decimals,
      hre.rwaStudio.formatTokenAmount(maxSupply, decimals),
      complianceModuleAddress,
      identityRegistryAddress,
      taskArgs.assetType,
      taskArgs.framework,
      taskArgs.jurisdiction,
      taskArgs.description || `${taskArgs.assetType} token compliant with ${taskArgs.framework}`
    );
    await rwaToken.waitForDeployment();
    const rwaTokenAddress = await rwaToken.getAddress();
    console.log("✅ RWA Token deployed to:", rwaTokenAddress);
    
    // Step 4: Update Compliance Module with token address
    console.log("\n🔗 Linking Compliance Module to Token...");
    await complianceModule.setToken(rwaTokenAddress);
    console.log("✅ Compliance Module linked");
    
    // Step 5: Deploy default compliance rules
    console.log("\n📋 Deploying Default Compliance Rules...");
    const deployedRules = [];
    
    for (const rule of defaultRules) {
      if (rule.type === "investor-limit") {
        const InvestorLimitRule = await hre.ethers.getContractFactory("InvestorLimitRule");
        const investorLimitRule = await InvestorLimitRule.deploy(
          rwaTokenAddress,
          rule.params.maxInvestors
        );
        await investorLimitRule.waitForDeployment();
        const investorLimitRuleAddress = await investorLimitRule.getAddress();
        
        // Add rule to compliance module
        await complianceModule.addRule(investorLimitRuleAddress);
        
        deployedRules.push({
          type: rule.type,
          address: investorLimitRuleAddress,
          params: rule.params
        });
        
        console.log(`   ✅ Investor Limit Rule: ${investorLimitRuleAddress} (max: ${rule.params.maxInvestors})`);
      }
      // Add more rule types as needed
    }
    
    // Step 6: Set up initial permissions
    console.log("\n🔐 Setting up Permissions...");
    
    // Add deployer as authorized agent in identity registry
    await identityRegistry.addAuthorizedAgent(deployer.address);
    console.log("   ✅ Deployer added as authorized agent");
    
    // Step 7: Generate deployment report
    const deployment = {
      network: hre.network.name,
      deployer: deployer.address,
      timestamp: new Date().toISOString(),
      tokenAddress: rwaTokenAddress,
      complianceAddress: complianceModuleAddress,
      identityRegistryAddress: identityRegistryAddress,
      deployedRules: deployedRules,
      tokenInfo: {
        name: taskArgs.name,
        symbol: taskArgs.symbol,
        decimals: decimals,
        maxSupply: maxSupply,
        assetType: taskArgs.assetType,
        framework: taskArgs.framework,
        jurisdiction: taskArgs.jurisdiction,
        description: taskArgs.description
      }
    };
    
    // Save deployment report
    const deploymentsDir = path.join(__dirname, "..", "deployments");
    if (!fs.existsSync(deploymentsDir)) {
      fs.mkdirSync(deploymentsDir, { recursive: true });
    }
    
    const reportPath = path.join(deploymentsDir, `${taskArgs.symbol}-${hre.network.name}-${Date.now()}.json`);
    fs.writeFileSync(reportPath, JSON.stringify(deployment, null, 2));
    console.log(`📄 Deployment report saved to: ${reportPath}`);
    
    // Step 8: Verify contracts (if on supported network)
    if (hre.network.name !== "hardhat" && hre.network.name !== "localhost") {
      console.log("\n🔍 Verifying contracts on Etherscan...");
      try {
        await hre.run("verify:verify", {
          address: identityRegistry.address,
          constructorArguments: []
        });
        
        await hre.run("verify:verify", {
          address: complianceModule.address,
          constructorArguments: [rwaToken.address]
        });
        
        await hre.run("verify:verify", {
          address: rwaToken.address,
          constructorArguments: [
            taskArgs.name,
            taskArgs.symbol,
            decimals,
            hre.rwaStudio.formatTokenAmount(maxSupply, decimals),
            complianceModule.address,
            identityRegistry.address,
            taskArgs.assetType,
            taskArgs.framework,
            taskArgs.jurisdiction,
            taskArgs.description || `${taskArgs.assetType} token compliant with ${taskArgs.framework}`
          ]
        });
        
        console.log("✅ Contracts verified on Etherscan");
      } catch (error) {
        console.log("⚠️  Contract verification failed:", error.message);
      }
    }
    
    // Step 9: Generate asset page URL
    const assetPageUrl = `https://rwa-studio.com/assets/${rwaTokenAddress}?network=${hre.network.name}`;
    deployment.assetPageUrl = assetPageUrl;
    
    console.log("\n🎉 Deployment Complete!");
    console.log("=" .repeat(50));
    console.log(`📄 Token: ${rwaTokenAddress}`);
    console.log(`🔒 Compliance: ${complianceModuleAddress}`);
    console.log(`👤 Identity Registry: ${identityRegistryAddress}`);
    console.log(`🌐 Asset Page: ${assetPageUrl}`);
    console.log(`📊 Rules Deployed: ${deployedRules.length}`);
    console.log("=" .repeat(50));
    
    return deployment;
    
  } catch (error) {
    console.error("❌ Deployment failed:", error);
    throw error;
  }
}

// Helper function to estimate deployment costs
async function estimateDeploymentCost(taskArgs, hre) {
  const [deployer] = await hre.ethers.getSigners();
  
  // Get contract factories
  const IdentityRegistry = await hre.ethers.getContractFactory("IdentityRegistry");
  const ComplianceModule = await hre.ethers.getContractFactory("ComplianceModule");
  const RWAToken = await hre.ethers.getContractFactory("RWAToken");
  
  // Estimate gas for each deployment
  const identityRegistryGas = await deployer.estimateGas(
    IdentityRegistry.getDeployTransaction()
  );
  
  const complianceModuleGas = await deployer.estimateGas(
    ComplianceModule.getDeployTransaction(hre.ethers.ZeroAddress)
  );
  
  const assetConfig = hre.rwaStudio.getAssetConfig(taskArgs.assetType);
  const decimals = taskArgs.decimals || assetConfig.defaultDecimals;
  const maxSupply = taskArgs.maxSupply || assetConfig.suggestedSupply;
  
  const rwaTokenGas = await deployer.estimateGas(
    RWAToken.getDeployTransaction(
      taskArgs.name,
      taskArgs.symbol,
      decimals,
      hre.rwaStudio.formatTokenAmount(maxSupply, decimals),
      hre.ethers.ZeroAddress, // placeholder
      hre.ethers.ZeroAddress, // placeholder
      taskArgs.assetType,
      taskArgs.framework,
      taskArgs.jurisdiction,
      taskArgs.description || ""
    )
  );
  
  const totalGas = identityRegistryGas + complianceModuleGas + rwaTokenGas;
  const feeData = await hre.ethers.provider.getFeeData();
  const gasPrice = feeData.gasPrice || 0n;
  const totalCost = totalGas * gasPrice;
  
  return {
    totalGas: totalGas.toString(),
    gasPrice: gasPrice.toString(),
    totalCostWei: totalCost.toString(),
    totalCostEth: hre.ethers.formatEther(totalCost),
    breakdown: {
      identityRegistry: {
        gas: identityRegistryGas.toString(),
        cost: hre.ethers.formatEther(identityRegistryGas * gasPrice)
      },
      complianceModule: {
        gas: complianceModuleGas.toString(),
        cost: hre.ethers.formatEther(complianceModuleGas * gasPrice)
      },
      rwaToken: {
        gas: rwaTokenGas.toString(),
        cost: hre.ethers.formatEther(rwaTokenGas * gasPrice)
      }
    }
  };
}

module.exports = {
  deployRWAToken,
  estimateDeploymentCost
};

