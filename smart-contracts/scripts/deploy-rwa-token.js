/**
 * RWA Token Deployment Script
 * Author: Sowad Al-Mughni
 * 
 * Deploys a complete RWA token with compliance infrastructure
 */

const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function deployRWAToken(taskArgs, hre) {
  const [deployer] = await ethers.getSigners();
  
  console.log("🔑 Deploying with account:", deployer.address);
  console.log("💰 Account balance:", ethers.utils.formatEther(await deployer.getBalance()));
  
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
    const IdentityRegistry = await ethers.getContractFactory("IdentityRegistry");
    const identityRegistry = await IdentityRegistry.deploy();
    await identityRegistry.deployed();
    console.log("✅ Identity Registry deployed to:", identityRegistry.address);
    
    // Step 2: Deploy Compliance Module
    console.log("\n⚖️  Deploying Compliance Module...");
    const ComplianceModule = await ethers.getContractFactory("ComplianceModule");
    const complianceModule = await ComplianceModule.deploy(ethers.constants.AddressZero); // Will be updated with token address
    await complianceModule.deployed();
    console.log("✅ Compliance Module deployed to:", complianceModule.address);
    
    // Step 3: Deploy RWA Token
    console.log("\n🪙 Deploying RWA Token...");
    const RWAToken = await ethers.getContractFactory("RWAToken");
    const rwaToken = await RWAToken.deploy(
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
    );
    await rwaToken.deployed();
    console.log("✅ RWA Token deployed to:", rwaToken.address);
    
    // Step 4: Update Compliance Module with token address
    console.log("\n🔗 Linking Compliance Module to Token...");
    await complianceModule.setToken(rwaToken.address);
    console.log("✅ Compliance Module linked");
    
    // Step 5: Deploy default compliance rules
    console.log("\n📋 Deploying Default Compliance Rules...");
    const deployedRules = [];
    
    for (const rule of defaultRules) {
      if (rule.type === "investor-limit") {
        const InvestorLimitRule = await ethers.getContractFactory("InvestorLimitRule");
        const investorLimitRule = await InvestorLimitRule.deploy(
          rwaToken.address,
          rule.params.maxInvestors
        );
        await investorLimitRule.deployed();
        
        // Add rule to compliance module
        await complianceModule.addRule(investorLimitRule.address);
        
        deployedRules.push({
          type: rule.type,
          address: investorLimitRule.address,
          params: rule.params
        });
        
        console.log(`   ✅ Investor Limit Rule: ${investorLimitRule.address} (max: ${rule.params.maxInvestors})`);
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
      tokenAddress: rwaToken.address,
      complianceAddress: complianceModule.address,
      identityRegistryAddress: identityRegistry.address,
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
      },
      transactionHashes: {
        identityRegistry: identityRegistry.deployTransaction.hash,
        complianceModule: complianceModule.deployTransaction.hash,
        token: rwaToken.deployTransaction.hash
      },
      gasUsed: {
        identityRegistry: (await identityRegistry.deployTransaction.wait()).gasUsed.toString(),
        complianceModule: (await complianceModule.deployTransaction.wait()).gasUsed.toString(),
        token: (await rwaToken.deployTransaction.wait()).gasUsed.toString()
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
    const assetPageUrl = `https://rwa-studio.com/assets/${rwaToken.address}?network=${hre.network.name}`;
    deployment.assetPageUrl = assetPageUrl;
    
    console.log("\n🎉 Deployment Complete!");
    console.log("=" .repeat(50));
    console.log(`📄 Token: ${rwaToken.address}`);
    console.log(`🔒 Compliance: ${complianceModule.address}`);
    console.log(`👤 Identity Registry: ${identityRegistry.address}`);
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
  const [deployer] = await ethers.getSigners();
  
  // Get contract factories
  const IdentityRegistry = await ethers.getContractFactory("IdentityRegistry");
  const ComplianceModule = await ethers.getContractFactory("ComplianceModule");
  const RWAToken = await ethers.getContractFactory("RWAToken");
  
  // Estimate gas for each deployment
  const identityRegistryGas = await IdentityRegistry.signer.estimateGas(
    IdentityRegistry.getDeployTransaction()
  );
  
  const complianceModuleGas = await ComplianceModule.signer.estimateGas(
    ComplianceModule.getDeployTransaction(ethers.constants.AddressZero)
  );
  
  const assetConfig = hre.rwaStudio.getAssetConfig(taskArgs.assetType);
  const decimals = taskArgs.decimals || assetConfig.defaultDecimals;
  const maxSupply = taskArgs.maxSupply || assetConfig.suggestedSupply;
  
  const rwaTokenGas = await RWAToken.signer.estimateGas(
    RWAToken.getDeployTransaction(
      taskArgs.name,
      taskArgs.symbol,
      decimals,
      hre.rwaStudio.formatTokenAmount(maxSupply, decimals),
      ethers.constants.AddressZero, // placeholder
      ethers.constants.AddressZero, // placeholder
      taskArgs.assetType,
      taskArgs.framework,
      taskArgs.jurisdiction,
      taskArgs.description || ""
    )
  );
  
  const totalGas = identityRegistryGas.add(complianceModuleGas).add(rwaTokenGas);
  const gasPrice = await deployer.getGasPrice();
  const totalCost = totalGas.mul(gasPrice);
  
  return {
    totalGas: totalGas.toString(),
    gasPrice: gasPrice.toString(),
    totalCostWei: totalCost.toString(),
    totalCostEth: ethers.utils.formatEther(totalCost),
    breakdown: {
      identityRegistry: {
        gas: identityRegistryGas.toString(),
        cost: ethers.utils.formatEther(identityRegistryGas.mul(gasPrice))
      },
      complianceModule: {
        gas: complianceModuleGas.toString(),
        cost: ethers.utils.formatEther(complianceModuleGas.mul(gasPrice))
      },
      rwaToken: {
        gas: rwaTokenGas.toString(),
        cost: ethers.utils.formatEther(rwaTokenGas.mul(gasPrice))
      }
    }
  };
}

module.exports = {
  deployRWAToken,
  estimateDeploymentCost
};

