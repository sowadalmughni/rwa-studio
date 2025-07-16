// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title IERC3643
 * @dev Interface for ERC-3643 compliant security tokens
 * @author Sowad Al-Mughni
 * 
 * ERC-3643 is a standard for permissioned tokens, also known as security tokens.
 * It provides a framework for issuing tokens that are compliant with regulatory
 * requirements and can enforce transfer restrictions based on identity verification
 * and compliance rules.
 */
interface IERC3643 is IERC20 {
    
    /**
     * @dev Returns true if the transfer is compliant with all applicable rules
     * @param from Address sending tokens
     * @param to Address receiving tokens  
     * @param amount Number of tokens being transferred
     * @return True if transfer is allowed, false otherwise
     */
    function canTransfer(address from, address to, uint256 amount) external view returns (bool);
    
    /**
     * @dev Returns true if the address has been verified and can hold tokens
     * @param account Address to check verification status
     * @return True if address is verified, false otherwise
     */
    function isVerified(address account) external view returns (bool);
    
    /**
     * @dev Event emitted when a transfer is blocked due to compliance violation
     * @param from Address that attempted to send tokens
     * @param to Address that would have received tokens
     * @param amount Number of tokens in the blocked transfer
     * @param reason Human-readable reason for the block
     */
    event TransferBlocked(address indexed from, address indexed to, uint256 amount, string reason);
    
    /**
     * @dev Event emitted when compliance rules are updated
     * @param compliance Address of the new compliance contract
     */
    event ComplianceUpdated(address indexed compliance);
    
    /**
     * @dev Event emitted when identity registry is updated
     * @param identityRegistry Address of the new identity registry contract
     */
    event IdentityRegistryUpdated(address indexed identityRegistry);
}

