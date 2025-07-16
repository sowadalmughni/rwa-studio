// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";
import "./ICompliance.sol";
import "./rules/IComplianceRule.sol";

/**
 * @title ComplianceModule
 * @dev Implementation of compliance module for ERC-3643 tokens
 * @author Sowad Al-Mughni
 * 
 * This contract manages multiple compliance rules and evaluates whether
 * token transfers are compliant with all applicable regulations.
 */
contract ComplianceModule is ICompliance, Ownable {
    using EnumerableSet for EnumerableSet.AddressSet;
    
    // Set of active compliance rules
    EnumerableSet.AddressSet private _rules;
    
    // Compliance status for addresses
    mapping(address => ComplianceStatus) private _complianceStatus;
    
    struct ComplianceStatus {
        bool isCompliant;
        string status;
        uint256 lastUpdate;
    }
    
    // Token contract that this compliance module serves
    address public token;
    
    modifier onlyToken() {
        require(msg.sender == token, "ComplianceModule: Only token contract");
        _;
    }
    
    modifier onlyTokenOrOwner() {
        require(msg.sender == token || msg.sender == owner(), "ComplianceModule: Unauthorized");
        _;
    }
    
    /**
     * @dev Constructor
     * @param token_ Address of the token contract
     */
    constructor(address token_) Ownable(msg.sender) {
        require(token_ != address(0), "ComplianceModule: Invalid token address");
        token = token_;
    }
    
    /**
     * @dev Check if a transfer is compliant with all rules
     * @param from Address sending tokens
     * @param to Address receiving tokens
     * @param amount Number of tokens being transferred
     * @return True if transfer is compliant, false otherwise
     */
    function canTransfer(address from, address to, uint256 amount) external view override returns (bool) {
        // Check all active compliance rules
        uint256 ruleCount = _rules.length();
        for (uint256 i = 0; i < ruleCount; i++) {
            address ruleAddress = _rules.at(i);
            IComplianceRule rule = IComplianceRule(ruleAddress);
            
            if (!rule.canTransfer(from, to, amount)) {
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * @dev Get compliance status for an address
     * @param account Address to check
     * @return isCompliant Whether the address is compliant
     * @return status Human-readable status description
     * @return lastUpdate Timestamp of last compliance update
     */
    function getComplianceStatus(address account) external view override returns (
        bool isCompliant,
        string memory status,
        uint256 lastUpdate
    ) {
        ComplianceStatus memory accountStatus = _complianceStatus[account];
        
        if (accountStatus.lastUpdate == 0) {
            // Default status for new addresses
            return (true, "No compliance issues", block.timestamp);
        }
        
        return (accountStatus.isCompliant, accountStatus.status, accountStatus.lastUpdate);
    }
    
    /**
     * @dev Add a compliance rule
     * @param rule Address of the compliance rule contract
     */
    function addRule(address rule) external override onlyOwner {
        require(rule != address(0), "ComplianceModule: Invalid rule address");
        require(_rules.add(rule), "ComplianceModule: Rule already exists");
        
        emit RuleAdded(rule);
    }
    
    /**
     * @dev Remove a compliance rule
     * @param rule Address of the compliance rule contract
     */
    function removeRule(address rule) external override onlyOwner {
        require(_rules.remove(rule), "ComplianceModule: Rule does not exist");
        
        emit RuleRemoved(rule);
    }
    
    /**
     * @dev Get all active compliance rules
     * @return Array of compliance rule addresses
     */
    function getRules() external view override returns (address[] memory) {
        return _rules.values();
    }
    
    /**
     * @dev Update compliance status for an address
     * @param account Address to update
     * @param isCompliant New compliance status
     * @param status Status description
     */
    function updateComplianceStatus(
        address account,
        bool isCompliant,
        string memory status
    ) external onlyTokenOrOwner {
        _complianceStatus[account] = ComplianceStatus({
            isCompliant: isCompliant,
            status: status,
            lastUpdate: block.timestamp
        });
        
        emit ComplianceStatusChanged(account, isCompliant, status);
    }
    
    /**
     * @dev Batch update compliance status for multiple addresses
     * @param accounts Array of addresses to update
     * @param isCompliant Array of compliance statuses
     * @param statuses Array of status descriptions
     */
    function batchUpdateComplianceStatus(
        address[] memory accounts,
        bool[] memory isCompliant,
        string[] memory statuses
    ) external onlyTokenOrOwner {
        require(
            accounts.length == isCompliant.length && accounts.length == statuses.length,
            "ComplianceModule: Array length mismatch"
        );
        
        for (uint256 i = 0; i < accounts.length; i++) {
            _complianceStatus[accounts[i]] = ComplianceStatus({
                isCompliant: isCompliant[i],
                status: statuses[i],
                lastUpdate: block.timestamp
            });
            
            emit ComplianceStatusChanged(accounts[i], isCompliant[i], statuses[i]);
        }
    }
    
    /**
     * @dev Check if a specific rule exists
     * @param rule Address of the rule to check
     * @return True if rule exists, false otherwise
     */
    function hasRule(address rule) external view returns (bool) {
        return _rules.contains(rule);
    }
    
    /**
     * @dev Get number of active rules
     * @return Number of active compliance rules
     */
    function getRuleCount() external view returns (uint256) {
        return _rules.length();
    }
    
    /**
     * @dev Emergency function to reset all compliance rules
     */
    function resetRules() external onlyOwner {
        address[] memory rules = _rules.values();
        for (uint256 i = 0; i < rules.length; i++) {
            _rules.remove(rules[i]);
            emit RuleRemoved(rules[i]);
        }
    }
}

