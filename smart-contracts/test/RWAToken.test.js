const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("RWAToken", function () {
  let RWAToken, rwaToken;
  let ComplianceModule, complianceModule;
  let IdentityRegistry, identityRegistry;
  let owner, addr1, addr2, addr3;

  // Helper to get future expiration timestamp (1 year from blockchain time)
  async function getFutureExpiration() {
    const block = await ethers.provider.getBlock("latest");
    return block.timestamp + 365 * 24 * 60 * 60; // 1 year from now
  }

  beforeEach(async function () {
    // Get signers
    [owner, addr1, addr2, addr3] = await ethers.getSigners();

    // Deploy contracts
    RWAToken = await ethers.getContractFactory("RWAToken");
    ComplianceModule = await ethers.getContractFactory("ComplianceModule");
    IdentityRegistry = await ethers.getContractFactory("IdentityRegistry");

    // Deploy RWA Token
    rwaToken = await RWAToken.deploy(
      "Real Estate Token",
      "RET",
      18,
      ethers.parseEther("1000000"), // 1M max supply
      "real-estate",
      "reg-d",
      "US",
      "Tokenized commercial real estate portfolio"
    );

    // Deploy supporting contracts
    identityRegistry = await IdentityRegistry.deploy();
    complianceModule = await ComplianceModule.deploy(await rwaToken.getAddress());

    // Configure token
    await rwaToken.setIdentityRegistry(await identityRegistry.getAddress());
    await rwaToken.setCompliance(await complianceModule.getAddress());
  });

  describe("Deployment", function () {
    it("Should set the correct token details", async function () {
      expect(await rwaToken.name()).to.equal("Real Estate Token");
      expect(await rwaToken.symbol()).to.equal("RET");
      expect(await rwaToken.decimals()).to.equal(18);
      expect(await rwaToken.maxSupply()).to.equal(ethers.parseEther("1000000"));
    });

    it("Should set the correct asset information", async function () {
      const assetInfo = await rwaToken.assetInfo();
      expect(assetInfo.assetType).to.equal("real-estate");
      expect(assetInfo.regulatoryFramework).to.equal("reg-d");
      expect(assetInfo.jurisdiction).to.equal("US");
      expect(assetInfo.description).to.equal("Tokenized commercial real estate portfolio");
    });

    it("Should set the owner correctly", async function () {
      expect(await rwaToken.owner()).to.equal(owner.address);
    });

    it("Should have transfers disabled by default", async function () {
      expect(await rwaToken.transfersEnabled()).to.equal(false);
    });
  });

  describe("Identity Registry Integration", function () {
    it("Should verify addresses through identity registry", async function () {
      // Initially not verified
      expect(await rwaToken.isVerified(addr1.address)).to.equal(false);

      // Add verified address
      const expiration = await getFutureExpiration();
      await identityRegistry.addVerifiedAddress(
        addr1.address,
        1, // Basic verification
        "US",
        expiration,
        ethers.keccak256(ethers.toUtf8Bytes("identity-hash"))
      );

      // Should now be verified
      expect(await rwaToken.isVerified(addr1.address)).to.equal(true);
    });

    it("Should prevent minting to unverified addresses", async function () {
      await expect(rwaToken.mint(addr1.address, ethers.parseEther("100"))).to.be.revertedWith(
        "RWAToken: Account not verified"
      );
    });

    it("Should allow minting to verified addresses", async function () {
      // Verify address first
      const expiration = await getFutureExpiration();
      await identityRegistry.addVerifiedAddress(
        addr1.address,
        1,
        "US",
        expiration,
        ethers.keccak256(ethers.toUtf8Bytes("identity-hash"))
      );

      // Should be able to mint
      await rwaToken.mint(addr1.address, ethers.parseEther("100"));
      expect(await rwaToken.balanceOf(addr1.address)).to.equal(ethers.parseEther("100"));
    });
  });

  describe("Transfer Controls", function () {
    beforeEach(async function () {
      // Verify addresses
      const expiration = await getFutureExpiration();
      await identityRegistry.addVerifiedAddress(
        addr1.address,
        1,
        "US",
        expiration,
        ethers.keccak256(ethers.toUtf8Bytes("identity-hash-1"))
      );

      await identityRegistry.addVerifiedAddress(
        addr2.address,
        1,
        "US",
        expiration,
        ethers.keccak256(ethers.toUtf8Bytes("identity-hash-2"))
      );

      // Mint tokens
      await rwaToken.mint(addr1.address, ethers.parseEther("100"));
    });

    it("Should prevent transfers when transfers are disabled", async function () {
      await expect(
        rwaToken.connect(addr1).transfer(addr2.address, ethers.parseEther("50"))
      ).to.be.revertedWith("RWAToken: Transfer not compliant");
    });

    it("Should allow transfers when transfers are enabled", async function () {
      // Enable transfers
      await rwaToken.setTransfersEnabled(true);

      // Should be able to transfer
      await rwaToken.connect(addr1).transfer(addr2.address, ethers.parseEther("50"));
      expect(await rwaToken.balanceOf(addr1.address)).to.equal(ethers.parseEther("50"));
      expect(await rwaToken.balanceOf(addr2.address)).to.equal(ethers.parseEther("50"));
    });

    it("Should prevent transfers to unverified addresses", async function () {
      await rwaToken.setTransfersEnabled(true);

      await expect(
        rwaToken.connect(addr1).transfer(addr3.address, ethers.parseEther("50"))
      ).to.be.revertedWith("RWAToken: Transfer not compliant");
    });
  });

  describe("Compliance Integration", function () {
    it("Should check compliance before transfers", async function () {
      // Verify addresses
      const expiration = await getFutureExpiration();
      await identityRegistry.addVerifiedAddress(
        addr1.address,
        1,
        "US",
        expiration,
        ethers.keccak256(ethers.toUtf8Bytes("identity-hash-1"))
      );

      await identityRegistry.addVerifiedAddress(
        addr2.address,
        1,
        "US",
        expiration,
        ethers.keccak256(ethers.toUtf8Bytes("identity-hash-2"))
      );

      // Mint tokens and enable transfers
      await rwaToken.mint(addr1.address, ethers.parseEther("100"));
      await rwaToken.setTransfersEnabled(true);

      // Should be able to check transfer compliance
      expect(
        await rwaToken.canTransfer(addr1.address, addr2.address, ethers.parseEther("50"))
      ).to.equal(true);
    });

    it("Should get compliance status", async function () {
      const [isCompliant, status, _lastUpdate] = await rwaToken.getComplianceStatus(addr1.address);
      expect(isCompliant).to.equal(true);
      expect(status).to.equal("No compliance issues");
    });
  });

  describe("Administrative Functions", function () {
    it("Should allow owner to pause and unpause", async function () {
      await rwaToken.pause();
      expect(await rwaToken.paused()).to.equal(true);

      await rwaToken.unpause();
      expect(await rwaToken.paused()).to.equal(false);
    });

    it("Should allow owner to update asset information", async function () {
      await rwaToken.updateAssetInfo("Updated description", "QmNewDocumentHash");

      const assetInfo = await rwaToken.assetInfo();
      expect(assetInfo.description).to.equal("Updated description");
      expect(assetInfo.documentHash).to.equal("QmNewDocumentHash");
    });

    it("Should prevent non-owners from administrative functions", async function () {
      await expect(rwaToken.connect(addr1).pause()).to.be.revertedWithCustomError(
        rwaToken,
        "OwnableUnauthorizedAccount"
      );

      await expect(rwaToken.connect(addr1).setTransfersEnabled(true)).to.be.revertedWithCustomError(
        rwaToken,
        "OwnableUnauthorizedAccount"
      );
    });
  });

  describe("Supply Management", function () {
    beforeEach(async function () {
      // Verify address for minting
      const expiration = await getFutureExpiration();
      await identityRegistry.addVerifiedAddress(
        addr1.address,
        1,
        "US",
        expiration,
        ethers.keccak256(ethers.toUtf8Bytes("identity-hash"))
      );
    });

    it("Should enforce maximum supply", async function () {
      const maxSupply = await rwaToken.maxSupply();

      await expect(rwaToken.mint(addr1.address, maxSupply + 1n)).to.be.revertedWith(
        "RWAToken: Exceeds max supply"
      );
    });

    it("Should allow burning tokens", async function () {
      await rwaToken.mint(addr1.address, ethers.parseEther("100"));
      expect(await rwaToken.balanceOf(addr1.address)).to.equal(ethers.parseEther("100"));

      await rwaToken.burn(addr1.address, ethers.parseEther("50"));
      expect(await rwaToken.balanceOf(addr1.address)).to.equal(ethers.parseEther("50"));
    });
  });

  describe("Token Information", function () {
    it("Should return complete token information", async function () {
      const tokenInfo = await rwaToken.getTokenInfo();

      expect(tokenInfo.name).to.equal("Real Estate Token");
      expect(tokenInfo.symbol).to.equal("RET");
      expect(tokenInfo.tokenDecimals).to.equal(18);
      expect(tokenInfo.maxTokenSupply).to.equal(ethers.parseEther("1000000"));
      expect(tokenInfo.transfersActive).to.equal(false);
      expect(tokenInfo.asset.assetType).to.equal("real-estate");
      expect(tokenInfo.asset.regulatoryFramework).to.equal("reg-d");
    });
  });
});
