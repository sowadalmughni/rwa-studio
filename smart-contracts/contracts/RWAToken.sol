// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./interfaces/IERC3643.sol";
import "./compliance/ICompliance.sol";
import "./registry/IIdentityRegistry.sol";

/**
 * @title RWAToken
 * @dev ERC-3643 compliant security token for real-world asset tokenization
 * @author Sowad Al-Mughni
 * 
 * This contract implements the ERC-3643 standard for compliant security tokens,
 * providing built-in compliance checks, identity verification, and transfer restrictions
 * suitable for tokenizing real-world assets under various regulatory frameworks.
 */
contract RWAToken is ERC20, Ownable, Pausable, ReentrancyGuard, IERC3643 {
    
    // Token metadata
    string private _tokenName;
    string private _tokenSymbol;
    uint8 private _tokenDecimals;
    
    // Compliance and registry contracts
    ICompliance public compliance;
    IIdentityRegistry public identityRegistry;
    
    // Token configuration
    uint256 public maxSupply;
    bool public transfersEnabled;
    
    // Asset information
    struct AssetInfo {
        string assetType;           // real-estate, private-equity, debt, etc.
        string regulatoryFramework; // reg-d, reg-s, reg-cf, etc.
        string jurisdiction;        // US, EU, etc.
        string description;         // Asset description
        string documentHash;        // IPFS hash of legal documents
    }
    
    AssetInfo public assetInfo;
    
    // Events
    event ComplianceSet(address indexed compliance);
    event IdentityRegistrySet(address indexed identityRegistry);
    event TransfersEnabled(bool enabled);
    event AssetInfoUpdated(string assetType, string regulatoryFramework);
    event ComplianceViolation(address indexed from, address indexed to, uint256 amount, string reason);
    
    // Modifiers
    modifier onlyCompliant(address from, address to, uint256 amount) {
        require(canTransfer(from, to, amount), "RWAToken: Transfer not compliant");
        _;
    }
    
    modifier onlyVerified(address account) {
        require(isVerified(account), "RWAToken: Account not verified");
        _;
    }
    
    /**
     * @dev Constructor
     * @param name_ Token name
     * @param symbol_ Token symbol
     * @param decimals_ Token decimals
     * @param maxSupply_ Maximum token supply
     * @param assetType_ Type of underlying asset
     * @param regulatoryFramework_ Applicable regulatory framework
     */
    constructor(
        string memory name_,
        string memory symbol_,
        uint8 decimals_,
        uint256 maxSupply_,
        string memory assetType_,
        string memory regulatoryFramework_,
        string memory jurisdiction_,
        string memory description_
    ) ERC20(name_, symbol_) Ownable(msg.sender) {
        _tokenName = name_;
        _tokenSymbol = symbol_;
        _tokenDecimals = decimals_;
        maxSupply = maxSupply_;
        transfersEnabled = false;
        
        assetInfo = AssetInfo({
            assetType: assetType_,
            regulatoryFramework: regulatoryFramework_,
            jurisdiction: jurisdiction_,
            description: description_,
            documentHash: ""
        });
        
        emit AssetInfoUpdated(assetType_, regulatoryFramework_);
    }
    
    /**
     * @dev Returns token decimals
     */
    function decimals() public view override returns (uint8) {
        return _tokenDecimals;
    }
    
    /**
     * @dev Set compliance contract
     * @param compliance_ Address of compliance contract
     */
    function setCompliance(address compliance_) external onlyOwner {
        require(compliance_ != address(0), "RWAToken: Invalid compliance address");
        compliance = ICompliance(compliance_);
        emit ComplianceSet(compliance_);
    }
    
    /**
     * @dev Set identity registry contract
     * @param identityRegistry_ Address of identity registry contract
     */
    function setIdentityRegistry(address identityRegistry_) external onlyOwner {
        require(identityRegistry_ != address(0), "RWAToken: Invalid registry address");
        identityRegistry = IIdentityRegistry(identityRegistry_);
        emit IdentityRegistrySet(identityRegistry_);
    }
    
    /**
     * @dev Enable or disable transfers
     * @param enabled Whether transfers should be enabled
     */
    function setTransfersEnabled(bool enabled) external onlyOwner {
        transfersEnabled = enabled;
        emit TransfersEnabled(enabled);
    }
    
    /**
     * @dev Update asset information
     * @param description_ New asset description
     * @param documentHash_ IPFS hash of updated documents
     */
    function updateAssetInfo(string memory description_, string memory documentHash_) external onlyOwner {
        assetInfo.description = description_;
        assetInfo.documentHash = documentHash_;
    }
    
    /**
     * @dev Mint tokens to verified address
     * @param to Address to mint tokens to
     * @param amount Amount of tokens to mint
     */
    function mint(address to, uint256 amount) external onlyOwner onlyVerified(to) {
        require(totalSupply() + amount <= maxSupply, "RWAToken: Exceeds max supply");
        _mint(to, amount);
    }
    
    /**
     * @dev Burn tokens from address
     * @param from Address to burn tokens from
     * @param amount Amount of tokens to burn
     */
    function burn(address from, uint256 amount) external onlyOwner {
        _burn(from, amount);
    }
    
    /**
     * @dev Pause all token transfers
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause token transfers
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Check if transfer is compliant
     * @param from Sender address
     * @param to Recipient address
     * @param amount Transfer amount
     * @return Whether transfer is compliant
     */
    function canTransfer(address from, address to, uint256 amount) public view override returns (bool) {
        // Basic checks
        if (!transfersEnabled) return false;
        if (paused()) return false;
        if (from == address(0) || to == address(0)) return false;
        if (amount == 0) return false;
        
        // Identity verification checks
        if (address(identityRegistry) != address(0)) {
            if (!identityRegistry.isVerified(from) || !identityRegistry.isVerified(to)) {
                return false;
            }
        }
        
        // Compliance checks
        if (address(compliance) != address(0)) {
            return compliance.canTransfer(from, to, amount);
        }
        
        return true;
    }
    
    /**
     * @dev Check if address is verified
     * @param account Address to check
     * @return Whether address is verified
     */
    function isVerified(address account) public view override returns (bool) {
        if (address(identityRegistry) == address(0)) return true;
        return identityRegistry.isVerified(account);
    }
    
    /**
     * @dev Get compliance status for address
     * @param account Address to check
     * @return isCompliant Whether the address is compliant
     * @return status Human-readable status description
     * @return lastUpdate Timestamp of last update
     */
    function getComplianceStatus(address account) external view returns (
        bool isCompliant,
        string memory status,
        uint256 lastUpdate
    ) {
        if (address(compliance) == address(0)) {
            return (true, "No compliance module", block.timestamp);
        }
        return compliance.getComplianceStatus(account);
    }
    
    /**
     * @dev Override transfer to include compliance checks
     */
    function transfer(address to, uint256 amount) public override(ERC20, IERC20) onlyCompliant(msg.sender, to, amount) returns (bool) {
        return super.transfer(to, amount);
    }
    
    /**
     * @dev Override transferFrom to include compliance checks
     */
    function transferFrom(address from, address to, uint256 amount) public override(ERC20, IERC20) onlyCompliant(from, to, amount) returns (bool) {
        return super.transferFrom(from, to, amount);
    }
    
    /**
     * @dev Override _update to add additional checks
     */
    function _update(address from, address to, uint256 amount) internal override whenNotPaused {
        // Additional compliance logging
        if (from != address(0) && to != address(0)) {
            if (!canTransfer(from, to, amount)) {
                emit ComplianceViolation(from, to, amount, "Transfer blocked by compliance");
                revert("RWAToken: Transfer blocked by compliance");
            }
        }
        
        super._update(from, to, amount);
    }
    
    /**
     * @dev Emergency function to recover stuck tokens
     * @param token Address of token to recover
     * @param amount Amount to recover
     */
    function emergencyRecovery(address token, uint256 amount) external onlyOwner {
        require(token != address(this), "RWAToken: Cannot recover own tokens");
        IERC20(token).transfer(owner(), amount);
    }
    
    /**
     * @dev Get detailed token information
     */
    function getTokenInfo() external view returns (
        string memory name,
        string memory symbol,
        uint8 tokenDecimals,
        uint256 currentSupply,
        uint256 maxTokenSupply,
        bool transfersActive,
        AssetInfo memory asset
    ) {
        return (
            _tokenName,
            _tokenSymbol,
            _tokenDecimals,
            totalSupply(),
            maxSupply,
            transfersEnabled,
            assetInfo
        );
    }
}

