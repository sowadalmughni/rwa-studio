// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title IIdentityRegistry
 * @dev Interface for identity registry that manages verified addresses
 * @author Sowad Al-Mughni
 * 
 * The identity registry maintains a list of verified addresses that are
 * eligible to hold and transfer security tokens. It integrates with
 * KYC/AML providers and maintains compliance status for each address.
 */
interface IIdentityRegistry {
    
    /**
     * @dev Verification levels for different types of investors
     */
    enum VerificationLevel {
        None,           // Not verified
        Basic,          // Basic KYC completed
        Accredited,     // Accredited investor verified
        Institutional   // Institutional investor verified
    }
    
    /**
     * @dev Identity information for verified addresses
     */
    struct Identity {
        bool isVerified;
        VerificationLevel level;
        string jurisdiction;
        uint256 verificationDate;
        uint256 expirationDate;
        bytes32 identityHash;
    }
    
    /**
     * @dev Check if an address is verified
     * @param account Address to check
     * @return True if address is verified, false otherwise
     */
    function isVerified(address account) external view returns (bool);
    
    /**
     * @dev Get verification level for an address
     * @param account Address to check
     * @return Verification level of the address
     */
    function getVerificationLevel(address account) external view returns (VerificationLevel);
    
    /**
     * @dev Get full identity information for an address
     * @param account Address to check
     * @return Identity struct with all verification details
     */
    function getIdentity(address account) external view returns (Identity memory);
    
    /**
     * @dev Add a verified address to the registry
     * @param account Address to verify
     * @param level Verification level to assign
     * @param jurisdiction Jurisdiction of the investor
     * @param expirationDate When verification expires
     * @param identityHash Hash of identity documents
     */
    function addVerifiedAddress(
        address account,
        VerificationLevel level,
        string memory jurisdiction,
        uint256 expirationDate,
        bytes32 identityHash
    ) external;
    
    /**
     * @dev Remove verification for an address
     * @param account Address to remove verification
     */
    function removeVerification(address account) external;
    
    /**
     * @dev Update verification level for an address
     * @param account Address to update
     * @param level New verification level
     */
    function updateVerificationLevel(address account, VerificationLevel level) external;
    
    /**
     * @dev Check if verification has expired
     * @param account Address to check
     * @return True if verification has expired, false otherwise
     */
    function isVerificationExpired(address account) external view returns (bool);
    
    /**
     * @dev Get all verified addresses (paginated)
     * @param offset Starting index
     * @param limit Maximum number of addresses to return
     * @return Array of verified addresses
     */
    function getVerifiedAddresses(uint256 offset, uint256 limit) external view returns (address[] memory);
    
    /**
     * @dev Get total number of verified addresses
     * @return Total count of verified addresses
     */
    function getVerifiedAddressCount() external view returns (uint256);
    
    /**
     * @dev Event emitted when an address is verified
     * @param account Address that was verified
     * @param level Verification level assigned
     * @param jurisdiction Jurisdiction of the investor
     */
    event AddressVerified(address indexed account, VerificationLevel level, string jurisdiction);
    
    /**
     * @dev Event emitted when verification is removed
     * @param account Address whose verification was removed
     */
    event VerificationRemoved(address indexed account);
    
    /**
     * @dev Event emitted when verification level is updated
     * @param account Address whose level was updated
     * @param oldLevel Previous verification level
     * @param newLevel New verification level
     */
    event VerificationLevelUpdated(address indexed account, VerificationLevel oldLevel, VerificationLevel newLevel);
    
    /**
     * @dev Event emitted when verification expires
     * @param account Address whose verification expired
     */
    event VerificationExpired(address indexed account);
}

