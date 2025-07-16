// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";
import "./IIdentityRegistry.sol";

/**
 * @title IdentityRegistry
 * @dev Implementation of identity registry for ERC-3643 tokens
 * @author Sowad Al-Mughni
 * 
 * This contract manages verified addresses and their compliance status,
 * integrating with KYC/AML providers and maintaining investor eligibility.
 */
contract IdentityRegistry is IIdentityRegistry, Ownable {
    using EnumerableSet for EnumerableSet.AddressSet;
    
    // Mapping from address to identity information
    mapping(address => Identity) private _identities;
    
    // Set of all verified addresses for enumeration
    EnumerableSet.AddressSet private _verifiedAddresses;
    
    // Mapping of authorized agents who can verify addresses
    mapping(address => bool) public authorizedAgents;
    
    // Default verification expiration period (1 year)
    uint256 public defaultExpirationPeriod = 365 days;
    
    modifier onlyAuthorized() {
        require(authorizedAgents[msg.sender] || msg.sender == owner(), "IdentityRegistry: Unauthorized");
        _;
    }
    
    /**
     * @dev Constructor
     */
    constructor() Ownable(msg.sender) {
        // Owner is automatically an authorized agent
        authorizedAgents[msg.sender] = true;
    }
    
    /**
     * @dev Check if an address is verified
     * @param account Address to check
     * @return True if address is verified and not expired, false otherwise
     */
    function isVerified(address account) external view override returns (bool) {
        Identity memory identity = _identities[account];
        return identity.isVerified && !_isExpired(identity.expirationDate);
    }
    
    /**
     * @dev Get verification level for an address
     * @param account Address to check
     * @return Verification level of the address
     */
    function getVerificationLevel(address account) external view override returns (VerificationLevel) {
        Identity memory identity = _identities[account];
        if (!identity.isVerified || _isExpired(identity.expirationDate)) {
            return VerificationLevel.None;
        }
        return identity.level;
    }
    
    /**
     * @dev Get full identity information for an address
     * @param account Address to check
     * @return Identity struct with all verification details
     */
    function getIdentity(address account) external view override returns (Identity memory) {
        return _identities[account];
    }
    
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
    ) external override onlyAuthorized {
        require(account != address(0), "IdentityRegistry: Invalid address");
        require(level != VerificationLevel.None, "IdentityRegistry: Invalid verification level");
        require(expirationDate > block.timestamp, "IdentityRegistry: Expiration date in the past");
        
        // If address was not previously verified, add to set
        if (!_identities[account].isVerified) {
            _verifiedAddresses.add(account);
        }
        
        _identities[account] = Identity({
            isVerified: true,
            level: level,
            jurisdiction: jurisdiction,
            verificationDate: block.timestamp,
            expirationDate: expirationDate,
            identityHash: identityHash
        });
        
        emit AddressVerified(account, level, jurisdiction);
    }
    
    /**
     * @dev Remove verification for an address
     * @param account Address to remove verification
     */
    function removeVerification(address account) external override onlyAuthorized {
        require(_identities[account].isVerified, "IdentityRegistry: Address not verified");
        
        delete _identities[account];
        _verifiedAddresses.remove(account);
        
        emit VerificationRemoved(account);
    }
    
    /**
     * @dev Update verification level for an address
     * @param account Address to update
     * @param level New verification level
     */
    function updateVerificationLevel(address account, VerificationLevel level) external override onlyAuthorized {
        require(_identities[account].isVerified, "IdentityRegistry: Address not verified");
        require(level != VerificationLevel.None, "IdentityRegistry: Invalid verification level");
        
        VerificationLevel oldLevel = _identities[account].level;
        _identities[account].level = level;
        
        emit VerificationLevelUpdated(account, oldLevel, level);
    }
    
    /**
     * @dev Check if verification has expired
     * @param account Address to check
     * @return True if verification has expired, false otherwise
     */
    function isVerificationExpired(address account) external view override returns (bool) {
        Identity memory identity = _identities[account];
        return identity.isVerified && _isExpired(identity.expirationDate);
    }
    
    /**
     * @dev Get all verified addresses (paginated)
     * @param offset Starting index
     * @param limit Maximum number of addresses to return
     * @return Array of verified addresses
     */
    function getVerifiedAddresses(uint256 offset, uint256 limit) external view override returns (address[] memory) {
        uint256 total = _verifiedAddresses.length();
        
        if (offset >= total) {
            return new address[](0);
        }
        
        uint256 end = offset + limit;
        if (end > total) {
            end = total;
        }
        
        address[] memory result = new address[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            result[i - offset] = _verifiedAddresses.at(i);
        }
        
        return result;
    }
    
    /**
     * @dev Get total number of verified addresses
     * @return Total count of verified addresses
     */
    function getVerifiedAddressCount() external view override returns (uint256) {
        return _verifiedAddresses.length();
    }
    
    /**
     * @dev Add an authorized agent who can verify addresses
     * @param agent Address to authorize
     */
    function addAuthorizedAgent(address agent) external onlyOwner {
        require(agent != address(0), "IdentityRegistry: Invalid agent address");
        authorizedAgents[agent] = true;
    }
    
    /**
     * @dev Remove an authorized agent
     * @param agent Address to remove authorization
     */
    function removeAuthorizedAgent(address agent) external onlyOwner {
        authorizedAgents[agent] = false;
    }
    
    /**
     * @dev Set default expiration period for new verifications
     * @param period New expiration period in seconds
     */
    function setDefaultExpirationPeriod(uint256 period) external onlyOwner {
        require(period > 0, "IdentityRegistry: Invalid expiration period");
        defaultExpirationPeriod = period;
    }
    
    /**
     * @dev Batch verify multiple addresses
     * @param accounts Array of addresses to verify
     * @param levels Array of verification levels
     * @param jurisdictions Array of jurisdictions
     * @param identityHashes Array of identity hashes
     */
    function batchVerifyAddresses(
        address[] memory accounts,
        VerificationLevel[] memory levels,
        string[] memory jurisdictions,
        bytes32[] memory identityHashes
    ) external onlyAuthorized {
        require(
            accounts.length == levels.length &&
            accounts.length == jurisdictions.length &&
            accounts.length == identityHashes.length,
            "IdentityRegistry: Array length mismatch"
        );
        
        uint256 expirationDate = block.timestamp + defaultExpirationPeriod;
        
        for (uint256 i = 0; i < accounts.length; i++) {
            require(accounts[i] != address(0), "IdentityRegistry: Invalid address");
            require(levels[i] != VerificationLevel.None, "IdentityRegistry: Invalid verification level");
            
            // If address was not previously verified, add to set
            if (!_identities[accounts[i]].isVerified) {
                _verifiedAddresses.add(accounts[i]);
            }
            
            _identities[accounts[i]] = Identity({
                isVerified: true,
                level: levels[i],
                jurisdiction: jurisdictions[i],
                verificationDate: block.timestamp,
                expirationDate: expirationDate,
                identityHash: identityHashes[i]
            });
            
            emit AddressVerified(accounts[i], levels[i], jurisdictions[i]);
        }
    }
    
    /**
     * @dev Clean up expired verifications
     * @param accounts Array of addresses to check and clean up
     */
    function cleanupExpiredVerifications(address[] memory accounts) external {
        for (uint256 i = 0; i < accounts.length; i++) {
            Identity memory identity = _identities[accounts[i]];
            if (identity.isVerified && _isExpired(identity.expirationDate)) {
                delete _identities[accounts[i]];
                _verifiedAddresses.remove(accounts[i]);
                emit VerificationExpired(accounts[i]);
            }
        }
    }
    
    /**
     * @dev Internal function to check if a timestamp has expired
     * @param expirationDate Timestamp to check
     * @return True if expired, false otherwise
     */
    function _isExpired(uint256 expirationDate) internal view returns (bool) {
        return block.timestamp > expirationDate;
    }
}

