// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title IComplianceRule
 * @dev Interface for individual compliance rules
 * @author Sowad Al-Mughni
 * 
 * Individual compliance rules implement specific regulatory requirements
 * such as investor limits, geographic restrictions, or holding periods.
 */
interface IComplianceRule {
    
    /**
     * @dev Check if a transfer complies with this specific rule
     * @param from Address sending tokens
     * @param to Address receiving tokens
     * @param amount Number of tokens being transferred
     * @return True if transfer complies with this rule, false otherwise
     */
    function canTransfer(address from, address to, uint256 amount) external view returns (bool);
    
    /**
     * @dev Get human-readable description of this rule
     * @return Description of what this rule enforces
     */
    function getRuleDescription() external view returns (string memory);
    
    /**
     * @dev Get rule parameters
     * @return names Array of parameter names
     * @return values Array of parameter values
     */
    function getRuleParameters() external view returns (string[] memory names, string[] memory values);
    
    /**
     * @dev Check if rule is currently active
     * @return True if rule is active, false otherwise
     */
    function isActive() external view returns (bool);
}

