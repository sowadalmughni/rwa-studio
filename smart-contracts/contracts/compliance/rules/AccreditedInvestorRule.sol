// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./IComplianceRule.sol";
import "../../registry/IIdentityRegistry.sol";

/**
 * @title AccreditedInvestorRule
 * @dev Compliance rule that requires accredited investor status for transfers
 * @author Sowad Al-Mughni
 * 
 * This rule is commonly required for Regulation D offerings (Rule 506(c))
 * which can only accept accredited investors. It checks the verification
 * level in the identity registry to ensure investors meet accreditation requirements.
 */
contract AccreditedInvestorRule is IComplianceRule, Ownable {
    
    // Token contract this rule applies to
    address public token;
    
    // Identity registry for checking accreditation status
    IIdentityRegistry public identityRegistry;
    
    // Whether this rule is currently active
    bool public active;
    
    // Minimum verification level required (default: Accredited)
    IIdentityRegistry.VerificationLevel public minimumLevel;
    
    // Whitelist of addresses exempt from accreditation check (e.g., issuer, treasury)
    mapping(address => bool) public exemptAddresses;
    
    // Events
    event MinimumLevelUpdated(IIdentityRegistry.VerificationLevel oldLevel, IIdentityRegistry.VerificationLevel newLevel);
    event AddressExemptionUpdated(address indexed account, bool exempt);
    
    /**
     * @dev Constructor
     * @param token_ Address of the token contract
     * @param identityRegistry_ Address of the identity registry
     */
    constructor(
        address token_,
        address identityRegistry_
    ) Ownable(msg.sender) {
        require(token_ != address(0), "AccreditedInvestorRule: Invalid token address");
        require(identityRegistry_ != address(0), "AccreditedInvestorRule: Invalid registry address");
        
        token = token_;
        identityRegistry = IIdentityRegistry(identityRegistry_);
        minimumLevel = IIdentityRegistry.VerificationLevel.Accredited;
        active = true;
    }
    
    /**
     * @dev Check if a transfer complies with accreditation requirements
     * @param from Address sending tokens
     * @param to Address receiving tokens
     * @param amount Number of tokens being transferred (unused but required by interface)
     * @return True if transfer complies with accreditation requirements, false otherwise
     */
    function canTransfer(address from, address to, uint256 amount) external view override returns (bool) {
        if (!active) return true;
        
        // Minting - only check recipient
        if (from == address(0)) {
            return _isAccredited(to);
        }
        
        // Burning - always allowed (reducing supply)
        if (to == address(0)) {
            return true;
        }
        
        // Regular transfer - check recipient only (sender already holds tokens)
        // This allows accredited investors to transfer to other accredited investors
        return _isAccredited(to);
    }
    
    /**
     * @dev Internal function to check if an address meets accreditation requirements
     * @param account Address to check
     * @return True if account is accredited or exempt, false otherwise
     */
    function _isAccredited(address account) internal view returns (bool) {
        // Check if address is exempt
        if (exemptAddresses[account]) {
            return true;
        }
        
        // Get verification level from identity registry
        IIdentityRegistry.VerificationLevel level = identityRegistry.getVerificationLevel(account);
        
        // Check if level meets minimum requirement
        return uint8(level) >= uint8(minimumLevel);
    }
    
    /**
     * @dev Get human-readable description of this rule
     * @return Description of what this rule enforces
     */
    function getRuleDescription() external view override returns (string memory) {
        if (minimumLevel == IIdentityRegistry.VerificationLevel.Accredited) {
            return "Accredited investor verification required for all transfers";
        } else if (minimumLevel == IIdentityRegistry.VerificationLevel.Institutional) {
            return "Institutional investor verification required for all transfers";
        } else {
            return "Basic verification required for all transfers";
        }
    }
    
    /**
     * @dev Get rule parameters
     * @return names Array of parameter names
     * @return values Array of parameter values
     */
    function getRuleParameters() external view override returns (string[] memory names, string[] memory values) {
        names = new string[](2);
        values = new string[](2);
        
        names[0] = "minimumLevel";
        if (minimumLevel == IIdentityRegistry.VerificationLevel.None) {
            values[0] = "None";
        } else if (minimumLevel == IIdentityRegistry.VerificationLevel.Basic) {
            values[0] = "Basic";
        } else if (minimumLevel == IIdentityRegistry.VerificationLevel.Accredited) {
            values[0] = "Accredited";
        } else {
            values[0] = "Institutional";
        }
        
        names[1] = "active";
        values[1] = active ? "true" : "false";
    }
    
    /**
     * @dev Check if rule is currently active
     * @return True if rule is active, false otherwise
     */
    function isActive() external view override returns (bool) {
        return active;
    }
    
    /**
     * @dev Set minimum verification level required
     * @param level New minimum verification level
     */
    function setMinimumLevel(IIdentityRegistry.VerificationLevel level) external onlyOwner {
        require(level != IIdentityRegistry.VerificationLevel.None, "AccreditedInvestorRule: Invalid level");
        
        IIdentityRegistry.VerificationLevel oldLevel = minimumLevel;
        minimumLevel = level;
        
        emit MinimumLevelUpdated(oldLevel, level);
    }
    
    /**
     * @dev Add or remove an address from the exempt list
     * @param account Address to update
     * @param exempt Whether address should be exempt
     */
    function setExemption(address account, bool exempt) external onlyOwner {
        require(account != address(0), "AccreditedInvestorRule: Invalid address");
        exemptAddresses[account] = exempt;
        emit AddressExemptionUpdated(account, exempt);
    }
    
    /**
     * @dev Batch update exemptions
     * @param accounts Array of addresses
     * @param exemptions Array of exemption statuses
     */
    function batchSetExemptions(address[] memory accounts, bool[] memory exemptions) external onlyOwner {
        require(accounts.length == exemptions.length, "AccreditedInvestorRule: Array length mismatch");
        
        for (uint256 i = 0; i < accounts.length; i++) {
            require(accounts[i] != address(0), "AccreditedInvestorRule: Invalid address");
            exemptAddresses[accounts[i]] = exemptions[i];
            emit AddressExemptionUpdated(accounts[i], exemptions[i]);
        }
    }
    
    /**
     * @dev Activate or deactivate this rule
     * @param active_ Whether rule should be active
     */
    function setActive(bool active_) external onlyOwner {
        active = active_;
    }
    
    /**
     * @dev Update the identity registry address
     * @param identityRegistry_ New identity registry address
     */
    function setIdentityRegistry(address identityRegistry_) external onlyOwner {
        require(identityRegistry_ != address(0), "AccreditedInvestorRule: Invalid registry address");
        identityRegistry = IIdentityRegistry(identityRegistry_);
    }
    
    /**
     * @dev Check if a specific address is accredited
     * @param account Address to check
     * @return True if accredited or exempt, false otherwise
     */
    function checkAccreditation(address account) external view returns (bool) {
        return _isAccredited(account);
    }
    
    /**
     * @dev Get the current verification level of an address
     * @param account Address to check
     * @return Current verification level
     */
    function getAccountLevel(address account) external view returns (IIdentityRegistry.VerificationLevel) {
        return identityRegistry.getVerificationLevel(account);
    }
}
