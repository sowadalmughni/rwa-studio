/**
 * Verify Address Script for RWA-Studio
 * Author: Sowad Al-Mughni
 *
 * Adds a verified address to the identity registry with specified verification level
 */

// Verification level enum mapping
const VerificationLevel = {
  none: 0,
  basic: 1,
  accredited: 2,
  institutional: 3,
};

async function verifyAddress(taskArgs, hre) {
  const [deployer] = await hre.ethers.getSigners();

  console.log("Verifying address with RWA-Studio...");
  console.log(`Using account: ${deployer.address}`);

  // Parse parameters
  const tokenAddress = taskArgs.token;
  const addressToVerify = taskArgs.address;
  const level = taskArgs.level.toLowerCase();
  const jurisdiction = taskArgs.jurisdiction;
  const expiryDays = parseInt(taskArgs.expiry) || 365;

  // Validate verification level
  if (!(level in VerificationLevel)) {
    throw new Error(
      `Invalid verification level: ${level}. Valid options: basic, accredited, institutional`
    );
  }

  const verificationLevel = VerificationLevel[level];

  console.log(`\nVerification Details:`);
  console.log(`   Token: ${tokenAddress}`);
  console.log(`   Address: ${addressToVerify}`);
  console.log(`   Level: ${level} (${verificationLevel})`);
  console.log(`   Jurisdiction: ${jurisdiction}`);
  console.log(`   Expires: ${expiryDays} days`);

  try {
    // Get token contract to find identity registry
    const RWAToken = await hre.ethers.getContractFactory("RWAToken");
    const token = RWAToken.attach(tokenAddress);

    // Get identity registry address from token
    const identityRegistryAddress = await token.identityRegistry();
    console.log(`\nIdentity Registry: ${identityRegistryAddress}`);

    if (identityRegistryAddress === hre.ethers.ZeroAddress) {
      throw new Error("Token has no identity registry configured");
    }

    // Get identity registry contract
    const IdentityRegistry = await hre.ethers.getContractFactory("IdentityRegistry");
    const identityRegistry = IdentityRegistry.attach(identityRegistryAddress);

    // Calculate expiration timestamp
    const currentTime = Math.floor(Date.now() / 1000);
    const expirationDate = currentTime + expiryDays * 24 * 60 * 60;

    // Generate identity hash (in production, this would be from KYC provider)
    const identityHash = hre.ethers.keccak256(
      hre.ethers.toUtf8Bytes(`${addressToVerify}-${jurisdiction}-${Date.now()}`)
    );

    console.log(`\nAdding verified address...`);

    // Add verified address
    const tx = await identityRegistry.addVerifiedAddress(
      addressToVerify,
      verificationLevel,
      jurisdiction,
      expirationDate,
      identityHash
    );

    console.log(`Transaction submitted: ${tx.hash}`);

    // Wait for confirmation
    const receipt = await tx.wait();
    console.log(`Transaction confirmed in block: ${receipt.blockNumber}`);

    // Verify the address was added
    const isVerified = await identityRegistry.isVerified(addressToVerify);
    const storedLevel = await identityRegistry.getVerificationLevel(addressToVerify);

    console.log(`\nAddress Verified Successfully!`);
    console.log(`   Is Verified: ${isVerified}`);
    console.log(`   Verification Level: ${storedLevel}`);
    console.log(`   Expiration: ${new Date(expirationDate * 1000).toISOString()}`);

    return {
      success: true,
      address: addressToVerify,
      verificationLevel: level,
      jurisdiction: jurisdiction,
      identityHash: identityHash,
      expirationDate: new Date(expirationDate * 1000).toISOString(),
      transactionHash: tx.hash,
    };
  } catch (error) {
    console.error(`\nError verifying address:`, error.message);
    throw error;
  }
}

module.exports = { verifyAddress };
