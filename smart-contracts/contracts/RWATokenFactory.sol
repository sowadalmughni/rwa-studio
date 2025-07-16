// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";
import "./RWAToken.sol";
import "./compliance/ComplianceModule.sol";
import "./registry/IdentityRegistry.sol";
import "./compliance/rules/InvestorLimitRule.sol";

/**
 * @title RWATokenFactory
 * @dev Factory contract for deploying RWA tokens with compliance modules
 * @author Sowad Al-Mughni
 * 
 * This factory contract implements the 5-click tokenization workflow,
 * deploying compliant security tokens with pre-configured compliance
 * modules and identity registries based on regulatory requirements.
 */
contract RWATokenFactory is Ownable, ReentrancyGuard {
    using EnumerableSet for EnumerableSet.AddressSet;
    
    // Deployed tokens registry
    EnumerableSet.AddressSet private _deployedTokens;
    
    // Mapping from token address to deployment info
    mapping(address => TokenDeployment) public tokenDeployments;
    
    // Deployment fee in wei
    uint256 public deploymentFee;
    
    // Treasury address for collecting fees
    address public treasury;
    
    struct TokenDeployment {
        address token;
        address compliance;
        address identityRegistry;
        address deployer;
        uint256 deploymentTime;
        string assetType;
        string regulatoryFramework;
        bool isActive;
    }
    
    struct DeploymentParams {
        string name;
        string symbol;
        uint8 decimals;
        uint256 maxSupply;
        string assetType;
        string regulatoryFramework;
        string jurisdiction;
        string description;
        uint256 maxInvestors;
        bool enableInvestorLimit;
    }
    
    // Events
    event TokenDeployed(
        address indexed token,
        address indexed compliance,
        address indexed identityRegistry,
        address deployer,
        string assetType,
        string regulatoryFramework
    );
    
    event DeploymentFeeUpdated(uint256 oldFee, uint256 newFee);
    event TreasuryUpdated(address oldTreasury, address newTreasury);
    
    /**
     * @dev Constructor
     * @param deploymentFee_ Initial deployment fee
     * @param treasury_ Treasury address for collecting fees
     */
    constructor(uint256 deploymentFee_, address treasury_) Ownable(msg.sender) {
        deploymentFee = deploymentFee_;
        treasury = treasury_;
    }
    
    /**
     * @dev Deploy a new RWA token with compliance modules
     * @param params Deployment parameters
     * @return token Address of deployed token
     * @return compliance Address of deployed compliance module
     * @return identityRegistry Address of deployed identity registry
     */
    function deployRWAToken(DeploymentParams memory params) 
        external 
        payable 
        nonReentrant 
        returns (
            address token,
            address compliance,
            address identityRegistry
        ) 
    {
        require(msg.value >= deploymentFee, "RWATokenFactory: Insufficient deployment fee");
        require(bytes(params.name).length > 0, "RWATokenFactory: Invalid token name");
        require(bytes(params.symbol).length > 0, "RWATokenFactory: Invalid token symbol");
        require(params.maxSupply > 0, "RWATokenFactory: Invalid max supply");
        
        // Deploy identity registry
        identityRegistry = address(new IdentityRegistry());
        
        // Deploy token
        token = address(new RWAToken(
            params.name,
            params.symbol,
            params.decimals,
            params.maxSupply,
            params.assetType,
            params.regulatoryFramework,
            params.jurisdiction,
            params.description
        ));
        
        // Deploy compliance module
        compliance = address(new ComplianceModule(token));
        
        // Configure token with compliance and registry
        RWAToken(token).setCompliance(compliance);
        RWAToken(token).setIdentityRegistry(identityRegistry);
        
        // Transfer ownership of contracts to deployer
        RWAToken(token).transferOwnership(msg.sender);
        ComplianceModule(compliance).transferOwnership(msg.sender);
        IdentityRegistry(identityRegistry).transferOwnership(msg.sender);
        
        // Add compliance rules based on regulatory framework
        _addComplianceRules(compliance, params);
        
        // Register deployment
        _deployedTokens.add(token);
        tokenDeployments[token] = TokenDeployment({
            token: token,
            compliance: compliance,
            identityRegistry: identityRegistry,
            deployer: msg.sender,
            deploymentTime: block.timestamp,
            assetType: params.assetType,
            regulatoryFramework: params.regulatoryFramework,
            isActive: true
        });
        
        // Transfer deployment fee to treasury
        if (msg.value > 0) {
            payable(treasury).transfer(msg.value);
        }
        
        emit TokenDeployed(
            token,
            compliance,
            identityRegistry,
            msg.sender,
            params.assetType,
            params.regulatoryFramework
        );
        
        return (token, compliance, identityRegistry);
    }
    
    /**
     * @dev Get deployment information for a token
     * @param token Address of the token
     * @return Deployment information
     */
    function getTokenDeployment(address token) external view returns (TokenDeployment memory) {
        return tokenDeployments[token];
    }
    
    /**
     * @dev Get all deployed tokens (paginated)
     * @param offset Starting index
     * @param limit Maximum number of tokens to return
     * @return Array of token addresses
     */
    function getDeployedTokens(uint256 offset, uint256 limit) external view returns (address[] memory) {
        uint256 total = _deployedTokens.length();
        
        if (offset >= total) {
            return new address[](0);
        }
        
        uint256 end = offset + limit;
        if (end > total) {
            end = total;
        }
        
        address[] memory result = new address[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            result[i - offset] = _deployedTokens.at(i);
        }
        
        return result;
    }
    
    /**
     * @dev Get total number of deployed tokens
     * @return Total count of deployed tokens
     */
    function getDeployedTokenCount() external view returns (uint256) {
        return _deployedTokens.length();
    }
    
    /**
     * @dev Get tokens deployed by a specific address
     * @param deployer Address of the deployer
     * @return Array of token addresses deployed by the address
     */
    function getTokensByDeployer(address deployer) external view returns (address[] memory) {
        uint256 total = _deployedTokens.length();
        uint256 count = 0;
        
        // First pass: count tokens by deployer
        for (uint256 i = 0; i < total; i++) {
            address token = _deployedTokens.at(i);
            if (tokenDeployments[token].deployer == deployer) {
                count++;
            }
        }
        
        // Second pass: collect tokens by deployer
        address[] memory result = new address[](count);
        uint256 index = 0;
        for (uint256 i = 0; i < total; i++) {
            address token = _deployedTokens.at(i);
            if (tokenDeployments[token].deployer == deployer) {
                result[index] = token;
                index++;
            }
        }
        
        return result;
    }
    
    /**
     * @dev Set deployment fee
     * @param fee New deployment fee in wei
     */
    function setDeploymentFee(uint256 fee) external onlyOwner {
        uint256 oldFee = deploymentFee;
        deploymentFee = fee;
        emit DeploymentFeeUpdated(oldFee, fee);
    }
    
    /**
     * @dev Set treasury address
     * @param treasury_ New treasury address
     */
    function setTreasury(address treasury_) external onlyOwner {
        require(treasury_ != address(0), "RWATokenFactory: Invalid treasury address");
        address oldTreasury = treasury;
        treasury = treasury_;
        emit TreasuryUpdated(oldTreasury, treasury_);
    }
    
    /**
     * @dev Mark a token deployment as inactive
     * @param token Address of the token to deactivate
     */
    function deactivateToken(address token) external onlyOwner {
        require(_deployedTokens.contains(token), "RWATokenFactory: Token not found");
        tokenDeployments[token].isActive = false;
    }
    
    /**
     * @dev Emergency withdrawal of contract balance
     */
    function emergencyWithdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "RWATokenFactory: No balance to withdraw");
        payable(owner()).transfer(balance);
    }
    
    /**
     * @dev Add compliance rules based on regulatory framework
     * @param compliance Address of compliance module
     * @param params Deployment parameters
     */
    function _addComplianceRules(address compliance, DeploymentParams memory params) internal {
        // Add investor limit rule for Regulation D
        if (keccak256(bytes(params.regulatoryFramework)) == keccak256(bytes("reg-d")) && params.enableInvestorLimit) {
            address investorLimitRule = address(new InvestorLimitRule(
                tokenDeployments[msg.sender].token,
                params.maxInvestors
            ));
            ComplianceModule(compliance).addRule(investorLimitRule);
        }
        
        // Additional rules can be added here for other regulatory frameworks
        // For example:
        // - Geographic restrictions for Regulation S
        // - Investment limits for Regulation CF
        // - Holding period restrictions
        // - Accredited investor requirements
    }
    
    /**
     * @dev Calculate deployment cost including gas estimates
     * @return Estimated total cost for deployment
     */
    function getDeploymentCost() external view returns (uint256) {
        // Base deployment fee plus estimated gas costs
        // This is a simplified calculation - in production, you might want
        // to use a more sophisticated gas estimation
        return deploymentFee;
    }
    
    /**
     * @dev Check if factory supports a specific regulatory framework
     * @param framework Regulatory framework to check
     * @return True if supported, false otherwise
     */
    function supportsRegulatoryFramework(string memory framework) external pure returns (bool) {
        bytes32 frameworkHash = keccak256(bytes(framework));
        
        return (
            frameworkHash == keccak256(bytes("reg-d")) ||
            frameworkHash == keccak256(bytes("reg-s")) ||
            frameworkHash == keccak256(bytes("reg-cf")) ||
            frameworkHash == keccak256(bytes("custom"))
        );
    }
}

