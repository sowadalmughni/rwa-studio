// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./IComplianceRule.sol";

/**
 * @title HoldingPeriodRule
 * @dev Compliance rule that enforces minimum holding periods for token transfers
 * @author Sowad Al-Mughni
 * 
 * This rule is commonly required for Regulation S offerings which have
 * a distribution compliance period (typically 40 days for equity, 1 year for debt),
 * and Regulation D offerings which may have a 6-12 month holding period.
 */
contract HoldingPeriodRule is IComplianceRule, Ownable {
    
    // Token contract this rule applies to
    address public token;
    
    // Whether this rule is currently active
    bool public active;
    
    // Global holding period in seconds (default: 1 year)
    uint256 public holdingPeriod;
    
    // Mapping of address to when they first acquired tokens
    mapping(address => uint256) public acquisitionTimestamp;
    
    // Whitelist of addresses exempt from holding period (e.g., issuer, market makers)
    mapping(address => bool) public exemptAddresses;
    
    // Custom holding periods for specific addresses (overrides global)
    mapping(address => uint256) public customHoldingPeriods;
    mapping(address => bool) public hasCustomHoldingPeriod;
    
    // Events
    event HoldingPeriodUpdated(uint256 oldPeriod, uint256 newPeriod);
    event AcquisitionRecorded(address indexed account, uint256 timestamp);
    event AddressExemptionUpdated(address indexed account, bool exempt);
    event CustomHoldingPeriodSet(address indexed account, uint256 period);
    
    // Common holding periods as constants
    uint256 public constant FORTY_DAYS = 40 days;      // Reg S equity
    uint256 public constant SIX_MONTHS = 180 days;     // Reg D typical
    uint256 public constant ONE_YEAR = 365 days;       // Reg S debt, Reg D Rule 144
    
    /**
     * @dev Constructor
     * @param token_ Address of the token contract
     * @param holdingPeriod_ Default holding period in seconds
     */
    constructor(
        address token_,
        uint256 holdingPeriod_
    ) Ownable(msg.sender) {
        require(token_ != address(0), "HoldingPeriodRule: Invalid token address");
        require(holdingPeriod_ > 0, "HoldingPeriodRule: Invalid holding period");
        
        token = token_;
        holdingPeriod = holdingPeriod_;
        active = true;
    }
    
    /**
     * @dev Check if a transfer complies with holding period requirements
     * @param from Address sending tokens
     * @param to Address receiving tokens
     * @param amount Number of tokens being transferred (unused but required by interface)
     * @return True if transfer complies with holding period, false otherwise
     */
    function canTransfer(address from, address to, uint256 amount) external view override returns (bool) {
        if (!active) return true;
        
        // Minting - always allowed (record acquisition time elsewhere)
        if (from == address(0)) {
            return true;
        }
        
        // Burning - always allowed
        if (to == address(0)) {
            return true;
        }
        
        // Check if sender is exempt
        if (exemptAddresses[from]) {
            return true;
        }
        
        // Check if holding period has passed
        return _hasHoldingPeriodPassed(from);
    }
    
    /**
     * @dev Internal function to check if holding period has passed for an address
     * @param account Address to check
     * @return True if holding period has passed, false otherwise
     */
    function _hasHoldingPeriodPassed(address account) internal view returns (bool) {
        uint256 acquiredAt = acquisitionTimestamp[account];
        
        // If no acquisition timestamp recorded, block transfer (be conservative)
        if (acquiredAt == 0) {
            return false;
        }
        
        // Get applicable holding period
        uint256 applicablePeriod = holdingPeriod;
        if (hasCustomHoldingPeriod[account]) {
            applicablePeriod = customHoldingPeriods[account];
        }
        
        return block.timestamp >= acquiredAt + applicablePeriod;
    }
    
    /**
     * @dev Get human-readable description of this rule
     * @return Description of what this rule enforces
     */
    function getRuleDescription() external view override returns (string memory) {
        return string(abi.encodePacked(
            "Minimum holding period: ",
            _uint256ToString(holdingPeriod / 1 days),
            " days"
        ));
    }
    
    /**
     * @dev Get rule parameters
     * @return names Array of parameter names
     * @return values Array of parameter values
     */
    function getRuleParameters() external view override returns (string[] memory names, string[] memory values) {
        names = new string[](3);
        values = new string[](3);
        
        names[0] = "holdingPeriodDays";
        values[0] = _uint256ToString(holdingPeriod / 1 days);
        
        names[1] = "holdingPeriodSeconds";
        values[1] = _uint256ToString(holdingPeriod);
        
        names[2] = "active";
        values[2] = active ? "true" : "false";
    }
    
    /**
     * @dev Check if rule is currently active
     * @return True if rule is active, false otherwise
     */
    function isActive() external view override returns (bool) {
        return active;
    }
    
    /**
     * @dev Record acquisition timestamp for an address (called after minting/transfer to new holder)
     * @param account Address that acquired tokens
     * @param timestamp Timestamp of acquisition (use 0 for current block)
     */
    function recordAcquisition(address account, uint256 timestamp) external {
        require(
            msg.sender == token || msg.sender == owner(),
            "HoldingPeriodRule: Only token or owner"
        );
        
        uint256 recordedTime = timestamp == 0 ? block.timestamp : timestamp;
        acquisitionTimestamp[account] = recordedTime;
        
        emit AcquisitionRecorded(account, recordedTime);
    }
    
    /**
     * @dev Batch record acquisition timestamps
     * @param accounts Array of addresses
     * @param timestamps Array of timestamps (0 for current block)
     */
    function batchRecordAcquisitions(address[] memory accounts, uint256[] memory timestamps) external onlyOwner {
        require(accounts.length == timestamps.length, "HoldingPeriodRule: Array length mismatch");
        
        for (uint256 i = 0; i < accounts.length; i++) {
            uint256 recordedTime = timestamps[i] == 0 ? block.timestamp : timestamps[i];
            acquisitionTimestamp[accounts[i]] = recordedTime;
            emit AcquisitionRecorded(accounts[i], recordedTime);
        }
    }
    
    /**
     * @dev Set global holding period
     * @param holdingPeriod_ New holding period in seconds
     */
    function setHoldingPeriod(uint256 holdingPeriod_) external onlyOwner {
        require(holdingPeriod_ > 0, "HoldingPeriodRule: Invalid holding period");
        
        uint256 oldPeriod = holdingPeriod;
        holdingPeriod = holdingPeriod_;
        
        emit HoldingPeriodUpdated(oldPeriod, holdingPeriod_);
    }
    
    /**
     * @dev Set a custom holding period for a specific address
     * @param account Address to set custom period for
     * @param period Custom holding period in seconds (0 to remove custom period)
     */
    function setCustomHoldingPeriod(address account, uint256 period) external onlyOwner {
        if (period == 0) {
            hasCustomHoldingPeriod[account] = false;
            delete customHoldingPeriods[account];
        } else {
            hasCustomHoldingPeriod[account] = true;
            customHoldingPeriods[account] = period;
        }
        
        emit CustomHoldingPeriodSet(account, period);
    }
    
    /**
     * @dev Add or remove an address from the exempt list
     * @param account Address to update
     * @param exempt Whether address should be exempt
     */
    function setExemption(address account, bool exempt) external onlyOwner {
        require(account != address(0), "HoldingPeriodRule: Invalid address");
        exemptAddresses[account] = exempt;
        emit AddressExemptionUpdated(account, exempt);
    }
    
    /**
     * @dev Batch update exemptions
     * @param accounts Array of addresses
     * @param exemptions Array of exemption statuses
     */
    function batchSetExemptions(address[] memory accounts, bool[] memory exemptions) external onlyOwner {
        require(accounts.length == exemptions.length, "HoldingPeriodRule: Array length mismatch");
        
        for (uint256 i = 0; i < accounts.length; i++) {
            require(accounts[i] != address(0), "HoldingPeriodRule: Invalid address");
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
     * @dev Get time remaining until an address can transfer
     * @param account Address to check
     * @return Time remaining in seconds (0 if already can transfer)
     */
    function getTimeRemaining(address account) external view returns (uint256) {
        if (exemptAddresses[account]) return 0;
        
        uint256 acquiredAt = acquisitionTimestamp[account];
        if (acquiredAt == 0) return type(uint256).max; // Never acquired
        
        uint256 applicablePeriod = holdingPeriod;
        if (hasCustomHoldingPeriod[account]) {
            applicablePeriod = customHoldingPeriods[account];
        }
        
        uint256 unlockTime = acquiredAt + applicablePeriod;
        if (block.timestamp >= unlockTime) {
            return 0;
        }
        
        return unlockTime - block.timestamp;
    }
    
    /**
     * @dev Get unlock timestamp for an address
     * @param account Address to check
     * @return Timestamp when tokens unlock (0 if never acquired, type(uint256).max if exempt)
     */
    function getUnlockTimestamp(address account) external view returns (uint256) {
        if (exemptAddresses[account]) return 0;
        
        uint256 acquiredAt = acquisitionTimestamp[account];
        if (acquiredAt == 0) return 0;
        
        uint256 applicablePeriod = holdingPeriod;
        if (hasCustomHoldingPeriod[account]) {
            applicablePeriod = customHoldingPeriods[account];
        }
        
        return acquiredAt + applicablePeriod;
    }
    
    /**
     * @dev Convert uint256 to string
     * @param value Number to convert
     * @return String representation of the number
     */
    function _uint256ToString(uint256 value) internal pure returns (string memory) {
        if (value == 0) {
            return "0";
        }
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }
        return string(buffer);
    }
}
