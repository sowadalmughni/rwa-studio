/**
 * Compliance Check Script for RWA-Studio
 * Author: Sowad Al-Mughni
 * 
 * Checks if a proposed transfer would pass all compliance rules
 */

async function checkCompliance(taskArgs, hre) {
  console.log("🔍 Checking transfer compliance with RWA-Studio...");
  
  const tokenAddress = taskArgs.token;
  const fromAddress = taskArgs.from;
  const toAddress = taskArgs.to;
  const amount = taskArgs.amount;
  
  console.log(`\n📋 Transfer Details:`);
  console.log(`   Token: ${tokenAddress}`);
  console.log(`   From: ${fromAddress}`);
  console.log(`   To: ${toAddress}`);
  console.log(`   Amount: ${amount}`);
  
  try {
    // Get token contract
    const RWAToken = await hre.ethers.getContractFactory("RWAToken");
    const token = RWAToken.attach(tokenAddress);
    
    // Parse amount based on token decimals
    const decimals = await token.decimals();
    const parsedAmount = hre.ethers.parseUnits(amount, decimals);
    
    console.log(`\n📊 Token Info:`);
    console.log(`   Name: ${await token.name()}`);
    console.log(`   Symbol: ${await token.symbol()}`);
    console.log(`   Decimals: ${decimals}`);
    console.log(`   Parsed Amount: ${parsedAmount.toString()}`);
    
    // Check if transfers are enabled
    const transfersEnabled = await token.transfersEnabled();
    console.log(`   Transfers Enabled: ${transfersEnabled}`);
    
    if (!transfersEnabled) {
      console.log(`\n⚠️ Warning: Transfers are currently disabled for this token`);
    }
    
    // Get compliance and identity registry addresses
    const complianceAddress = await token.compliance();
    const identityRegistryAddress = await token.identityRegistry();
    
    console.log(`\n🔗 Contract Addresses:`);
    console.log(`   Compliance Module: ${complianceAddress}`);
    console.log(`   Identity Registry: ${identityRegistryAddress}`);
    
    const violations = [];
    
    // Check identity registry verification
    if (identityRegistryAddress !== hre.ethers.ZeroAddress) {
      const IdentityRegistry = await hre.ethers.getContractFactory("IdentityRegistry");
      const identityRegistry = IdentityRegistry.attach(identityRegistryAddress);
      
      const fromVerified = await identityRegistry.isVerified(fromAddress);
      const toVerified = await identityRegistry.isVerified(toAddress);
      
      console.log(`\n👤 Identity Verification:`);
      console.log(`   From Address Verified: ${fromVerified}`);
      console.log(`   To Address Verified: ${toVerified}`);
      
      if (!fromVerified) {
        violations.push(`Sender address (${fromAddress}) is not verified in identity registry`);
      }
      if (!toVerified) {
        violations.push(`Recipient address (${toAddress}) is not verified in identity registry`);
      }
      
      // Get verification details
      if (fromVerified) {
        const fromLevel = await identityRegistry.getVerificationLevel(fromAddress);
        const fromIdentity = await identityRegistry.getIdentity(fromAddress);
        console.log(`   From Level: ${fromLevel} | Jurisdiction: ${fromIdentity.jurisdiction}`);
      }
      if (toVerified) {
        const toLevel = await identityRegistry.getVerificationLevel(toAddress);
        const toIdentity = await identityRegistry.getIdentity(toAddress);
        console.log(`   To Level: ${toLevel} | Jurisdiction: ${toIdentity.jurisdiction}`);
      }
    }
    
    // Check compliance module
    if (complianceAddress !== hre.ethers.ZeroAddress) {
      const ComplianceModule = await hre.ethers.getContractFactory("ComplianceModule");
      const compliance = ComplianceModule.attach(complianceAddress);
      
      // Get all active rules
      const rules = await compliance.getRules();
      console.log(`\n📋 Active Compliance Rules: ${rules.length}`);
      
      // Check each rule individually
      for (let i = 0; i < rules.length; i++) {
        const ruleAddress = rules[i];
        
        // Try to get rule description
        try {
          const IComplianceRule = await hre.ethers.getContractAt("IComplianceRule", ruleAddress);
          const description = await IComplianceRule.getRuleDescription();
          const isActive = await IComplianceRule.isActive();
          const canTransfer = await IComplianceRule.canTransfer(fromAddress, toAddress, parsedAmount);
          
          console.log(`\n   Rule ${i + 1}: ${ruleAddress}`);
          console.log(`   Description: ${description}`);
          console.log(`   Active: ${isActive}`);
          console.log(`   Can Transfer: ${canTransfer}`);
          
          if (!canTransfer && isActive) {
            violations.push(`Rule violation: ${description}`);
          }
        } catch (e) {
          console.log(`   Rule ${i + 1}: ${ruleAddress} (Unable to query: ${e.message})`);
        }
      }
      
      // Check overall compliance
      const overallCanTransfer = await compliance.canTransfer(fromAddress, toAddress, parsedAmount);
      console.log(`\n🔒 Overall Compliance Check: ${overallCanTransfer ? 'PASS' : 'FAIL'}`);
    }
    
    // Final check using token's canTransfer
    const tokenCanTransfer = await token.canTransfer(fromAddress, toAddress, parsedAmount);
    
    console.log(`\n${'='.repeat(50)}`);
    console.log(`📊 FINAL RESULT`);
    console.log(`${'='.repeat(50)}`);
    
    if (tokenCanTransfer && violations.length === 0) {
      console.log(`✅ Transfer is COMPLIANT`);
      console.log(`   This transfer would succeed if executed.`);
    } else {
      console.log(`❌ Transfer is NOT COMPLIANT`);
      if (violations.length > 0) {
        console.log(`\n🚫 Violations Found:`);
        violations.forEach((v, i) => console.log(`   ${i + 1}. ${v}`));
      }
    }
    
    return {
      canTransfer: tokenCanTransfer,
      violations: violations,
      token: tokenAddress,
      from: fromAddress,
      to: toAddress,
      amount: amount
    };
    
  } catch (error) {
    console.error(`\n❌ Error checking compliance:`, error.message);
    throw error;
  }
}

module.exports = { checkCompliance };
