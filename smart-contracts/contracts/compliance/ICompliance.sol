// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ICompliance
 * @dev Interface for compliance modules that enforce transfer restrictions
 * @author Sowad Al-Mughni
 * 
 * Compliance modules implement specific regulatory requirements such as
 * investor limits, geographic restrictions, holding periods, and other
 * rules required for compliant security token transfers.
 */
interface ICompliance {
    
    /**
     * @dev Check if a transfer is compliant with all rules
     * @param from Address sending tokens
     * @param to Address receiving tokens
     * @param amount Number of tokens being transferred
     * @return True if transfer is compliant, false otherwise
     */
    function canTransfer(address from, address to, uint256 amount) external view returns (bool);
    
    /**
     * @dev Get compliance status for an address
     * @param account Address to check
     * @return isCompliant Whether the address is compliant
     * @return status Human-readable status description
     * @return lastUpdate Timestamp of last compliance update
     */
    function getComplianceStatus(address account) external view returns (
        bool isCompliant,
        string memory status,
        uint256 lastUpdate
    );
    
    /**
     * @dev Add a compliance rule
     * @param rule Address of the compliance rule contract
     */
    function addRule(address rule) external;
    
    /**
     * @dev Remove a compliance rule
     * @param rule Address of the compliance rule contract
     */
    function removeRule(address rule) external;
    
    /**
     * @dev Get all active compliance rules
     * @return Array of compliance rule addresses
     */
    function getRules() external view returns (address[] memory);
    
    /**
     * @dev Event emitted when a compliance rule is added
     * @param rule Address of the added rule
     */
    event RuleAdded(address indexed rule);
    
    /**
     * @dev Event emitted when a compliance rule is removed
     * @param rule Address of the removed rule
     */
    event RuleRemoved(address indexed rule);
    
    /**
     * @dev Event emitted when compliance status changes
     * @param account Address whose status changed
     * @param isCompliant New compliance status
     * @param reason Reason for status change
     */
    event ComplianceStatusChanged(address indexed account, bool isCompliant, string reason);
}

