// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "./IComplianceRule.sol";
import "../../registry/IIdentityRegistry.sol";

/**
 * @title GeographicRule
 * @dev Compliance rule that enforces geographic/jurisdictional restrictions
 * @author Sowad Al-Mughni
 * 
 * This rule is commonly required for Regulation S offerings which exclude
 * US persons, or for offerings that need to exclude specific jurisdictions
 * due to regulatory requirements (e.g., OFAC sanctions).
 */
contract GeographicRule is IComplianceRule, Ownable {
    
    // Token contract this rule applies to
    address public token;
    
    // Identity registry for checking jurisdictions
    IIdentityRegistry public identityRegistry;
    
    // Whether this rule is currently active
    bool public active;
    
    // Mode: true = allowlist (only allowed countries), false = blocklist (excluded countries)
    bool public isAllowlistMode;
    
    // Mapping of jurisdiction codes to their permission status
    // In allowlist mode: true = allowed, false = blocked
    // In blocklist mode: true = blocked, false = allowed
    mapping(string => bool) public jurisdictionStatus;
    
    // Array of all configured jurisdictions for enumeration
    string[] public configuredJurisdictions;
    
    // Events
    event JurisdictionUpdated(string indexed jurisdiction, bool status);
    event ModeChanged(bool isAllowlistMode);
    
    /**
     * @dev Constructor
     * @param token_ Address of the token contract
     * @param identityRegistry_ Address of the identity registry
     * @param isAllowlistMode_ True for allowlist mode, false for blocklist mode
     */
    constructor(
        address token_,
        address identityRegistry_,
        bool isAllowlistMode_
    ) Ownable(msg.sender) {
        require(token_ != address(0), "GeographicRule: Invalid token address");
        require(identityRegistry_ != address(0), "GeographicRule: Invalid registry address");
        
        token = token_;
        identityRegistry = IIdentityRegistry(identityRegistry_);
        isAllowlistMode = isAllowlistMode_;
        active = true;
    }
    
    /**
     * @dev Check if a transfer complies with geographic restrictions
     * @param from Address sending tokens
     * @param to Address receiving tokens
     * @param amount Number of tokens being transferred (unused but required by interface)
     * @return True if transfer complies with geographic restrictions, false otherwise
     */
    function canTransfer(address from, address to, uint256 amount) external view override returns (bool) {
        if (!active) return true;
        
        // Minting - only check recipient
        if (from == address(0)) {
            return _isJurisdictionAllowed(to);
        }
        
        // Burning - only check sender
        if (to == address(0)) {
            return _isJurisdictionAllowed(from);
        }
        
        // Regular transfer - check both parties
        return _isJurisdictionAllowed(from) && _isJurisdictionAllowed(to);
    }
    
    /**
     * @dev Internal function to check if an address's jurisdiction is allowed
     * @param account Address to check
     * @return True if jurisdiction is allowed, false otherwise
     */
    function _isJurisdictionAllowed(address account) internal view returns (bool) {
        IIdentityRegistry.Identity memory identity = identityRegistry.getIdentity(account);
        
        // If not verified, cannot determine jurisdiction - block transfer
        if (!identity.isVerified) {
            return false;
        }
        
        string memory jurisdiction = identity.jurisdiction;
        
        if (isAllowlistMode) {
            // In allowlist mode: jurisdiction must be explicitly allowed
            return jurisdictionStatus[jurisdiction];
        } else {
            // In blocklist mode: jurisdiction must NOT be blocked
            return !jurisdictionStatus[jurisdiction];
        }
    }
    
    /**
     * @dev Get human-readable description of this rule
     * @return Description of what this rule enforces
     */
    function getRuleDescription() external view override returns (string memory) {
        if (isAllowlistMode) {
            return "Geographic restriction: Only allowed jurisdictions can transfer";
        } else {
            return "Geographic restriction: Blocked jurisdictions cannot transfer";
        }
    }
    
    /**
     * @dev Get rule parameters
     * @return names Array of parameter names
     * @return values Array of parameter values
     */
    function getRuleParameters() external view override returns (string[] memory names, string[] memory values) {
        uint256 jurisdictionCount = configuredJurisdictions.length;
        names = new string[](jurisdictionCount + 2);
        values = new string[](jurisdictionCount + 2);
        
        names[0] = "mode";
        values[0] = isAllowlistMode ? "allowlist" : "blocklist";
        
        names[1] = "active";
        values[1] = active ? "true" : "false";
        
        for (uint256 i = 0; i < jurisdictionCount; i++) {
            names[i + 2] = configuredJurisdictions[i];
            values[i + 2] = jurisdictionStatus[configuredJurisdictions[i]] ? "true" : "false";
        }
    }
    
    /**
     * @dev Check if rule is currently active
     * @return True if rule is active, false otherwise
     */
    function isActive() external view override returns (bool) {
        return active;
    }
    
    /**
     * @dev Add or update a jurisdiction's status
     * @param jurisdiction Jurisdiction code (e.g., "US", "EU", "UK")
     * @param status Status to set (meaning depends on mode)
     */
    function setJurisdiction(string memory jurisdiction, bool status) external onlyOwner {
        // Track if this is a new jurisdiction
        bool isNew = true;
        for (uint256 i = 0; i < configuredJurisdictions.length; i++) {
            if (keccak256(bytes(configuredJurisdictions[i])) == keccak256(bytes(jurisdiction))) {
                isNew = false;
                break;
            }
        }
        
        if (isNew) {
            configuredJurisdictions.push(jurisdiction);
        }
        
        jurisdictionStatus[jurisdiction] = status;
        emit JurisdictionUpdated(jurisdiction, status);
    }
    
    /**
     * @dev Batch update multiple jurisdictions
     * @param jurisdictions Array of jurisdiction codes
     * @param statuses Array of statuses
     */
    function batchSetJurisdictions(string[] memory jurisdictions, bool[] memory statuses) external onlyOwner {
        require(jurisdictions.length == statuses.length, "GeographicRule: Array length mismatch");
        
        for (uint256 i = 0; i < jurisdictions.length; i++) {
            // Track if this is a new jurisdiction
            bool isNew = true;
            for (uint256 j = 0; j < configuredJurisdictions.length; j++) {
                if (keccak256(bytes(configuredJurisdictions[j])) == keccak256(bytes(jurisdictions[i]))) {
                    isNew = false;
                    break;
                }
            }
            
            if (isNew) {
                configuredJurisdictions.push(jurisdictions[i]);
            }
            
            jurisdictionStatus[jurisdictions[i]] = statuses[i];
            emit JurisdictionUpdated(jurisdictions[i], statuses[i]);
        }
    }
    
    /**
     * @dev Switch between allowlist and blocklist modes
     * @param isAllowlistMode_ True for allowlist mode, false for blocklist mode
     */
    function setMode(bool isAllowlistMode_) external onlyOwner {
        isAllowlistMode = isAllowlistMode_;
        emit ModeChanged(isAllowlistMode_);
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
        require(identityRegistry_ != address(0), "GeographicRule: Invalid registry address");
        identityRegistry = IIdentityRegistry(identityRegistry_);
    }
    
    /**
     * @dev Get all configured jurisdictions
     * @return Array of jurisdiction codes
     */
    function getConfiguredJurisdictions() external view returns (string[] memory) {
        return configuredJurisdictions;
    }
    
    /**
     * @dev Check if a specific jurisdiction is allowed
     * @param jurisdiction Jurisdiction code to check
     * @return True if allowed, false if blocked
     */
    function isJurisdictionAllowed(string memory jurisdiction) external view returns (bool) {
        if (isAllowlistMode) {
            return jurisdictionStatus[jurisdiction];
        } else {
            return !jurisdictionStatus[jurisdiction];
        }
    }
}
