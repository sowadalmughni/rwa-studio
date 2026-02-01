// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./IComplianceRule.sol";

/**
 * @title TransferLimitRule
 * @dev Compliance rule that enforces investment limits per investor
 * @author Sowad Al-Mughni
 * 
 * This rule is commonly required for Regulation CF (crowdfunding) offerings
 * which have investor investment limits based on income/net worth, and
 * for other offerings that need to cap individual investor participation.
 */
contract TransferLimitRule is IComplianceRule, Ownable {
    
    // Token contract this rule applies to
    address public token;
    
    // Whether this rule is currently active
    bool public active;
    
    // Maximum tokens any single investor can hold (default limit)
    uint256 public maxTokensPerInvestor;
    
    // Maximum total investment amount in USD cents (for value-based limits)
    uint256 public maxInvestmentAmount;
    
    // Token price in USD cents (for calculating investment value)
    uint256 public tokenPriceUSDCents;
    
    // Custom limits per investor (overrides global limit)
    mapping(address => uint256) public customMaxTokens;
    mapping(address => bool) public hasCustomLimit;
    
    // Track total investment per investor (in USD cents, for Reg CF tracking)
    mapping(address => uint256) public totalInvestmentUSD;
    
    // Whitelist of addresses exempt from limits (e.g., issuer, treasury)
    mapping(address => bool) public exemptAddresses;
    
    // Events
    event MaxTokensUpdated(uint256 oldLimit, uint256 newLimit);
    event MaxInvestmentUpdated(uint256 oldLimit, uint256 newLimit);
    event TokenPriceUpdated(uint256 oldPrice, uint256 newPrice);
    event CustomLimitSet(address indexed account, uint256 limit);
    event InvestmentRecorded(address indexed account, uint256 amountUSD, uint256 totalUSD);
    event AddressExemptionUpdated(address indexed account, bool exempt);
    
    /**
     * @dev Constructor
     * @param token_ Address of the token contract
     * @param maxTokensPerInvestor_ Maximum tokens per investor (0 to disable token-based limit)
     * @param maxInvestmentAmount_ Maximum investment in USD cents (0 to disable USD-based limit)
     * @param tokenPriceUSDCents_ Token price in USD cents (for USD calculations)
     */
    constructor(
        address token_,
        uint256 maxTokensPerInvestor_,
        uint256 maxInvestmentAmount_,
        uint256 tokenPriceUSDCents_
    ) Ownable(msg.sender) {
        require(token_ != address(0), "TransferLimitRule: Invalid token address");
        require(
            maxTokensPerInvestor_ > 0 || maxInvestmentAmount_ > 0,
            "TransferLimitRule: At least one limit required"
        );
        
        token = token_;
        maxTokensPerInvestor = maxTokensPerInvestor_;
        maxInvestmentAmount = maxInvestmentAmount_;
        tokenPriceUSDCents = tokenPriceUSDCents_;
        active = true;
    }
    
    /**
     * @dev Check if a transfer complies with investment limits
     * @param from Address sending tokens
     * @param to Address receiving tokens
     * @param amount Number of tokens being transferred
     * @return True if transfer complies with limits, false otherwise
     */
    function canTransfer(address from, address to, uint256 amount) external view override returns (bool) {
        if (!active) return true;
        
        // Minting - check recipient limits
        if (from == address(0)) {
            return _checkLimits(to, amount);
        }
        
        // Burning - always allowed
        if (to == address(0)) {
            return true;
        }
        
        // Regular transfer - check recipient limits
        return _checkLimits(to, amount);
    }
    
    /**
     * @dev Internal function to check if an address can receive more tokens
     * @param account Address to check
     * @param amount Amount of tokens to receive
     * @return True if within limits, false otherwise
     */
    function _checkLimits(address account, uint256 amount) internal view returns (bool) {
        // Check if address is exempt
        if (exemptAddresses[account]) {
            return true;
        }
        
        IERC20 tokenContract = IERC20(token);
        uint256 currentBalance = tokenContract.balanceOf(account);
        uint256 newBalance = currentBalance + amount;
        
        // Check token-based limit
        if (maxTokensPerInvestor > 0) {
            uint256 applicableLimit = maxTokensPerInvestor;
            if (hasCustomLimit[account]) {
                applicableLimit = customMaxTokens[account];
            }
            
            if (newBalance > applicableLimit) {
                return false;
            }
        }
        
        // Check USD-based limit (if price is set)
        if (maxInvestmentAmount > 0 && tokenPriceUSDCents > 0) {
            uint256 additionalInvestmentUSD = (amount * tokenPriceUSDCents) / (10 ** 18); // Assuming 18 decimals
            uint256 newTotalInvestmentUSD = totalInvestmentUSD[account] + additionalInvestmentUSD;
            
            if (newTotalInvestmentUSD > maxInvestmentAmount) {
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * @dev Get human-readable description of this rule
     * @return Description of what this rule enforces
     */
    function getRuleDescription() external view override returns (string memory) {
        if (maxTokensPerInvestor > 0 && maxInvestmentAmount > 0) {
            return "Maximum investment limit: per-investor token and USD caps enforced";
        } else if (maxTokensPerInvestor > 0) {
            return string(abi.encodePacked(
                "Maximum tokens per investor: ",
                _uint256ToString(maxTokensPerInvestor)
            ));
        } else {
            return string(abi.encodePacked(
                "Maximum investment per investor: $",
                _uint256ToString(maxInvestmentAmount / 100),
                " USD"
            ));
        }
    }
    
    /**
     * @dev Get rule parameters
     * @return names Array of parameter names
     * @return values Array of parameter values
     */
    function getRuleParameters() external view override returns (string[] memory names, string[] memory values) {
        names = new string[](4);
        values = new string[](4);
        
        names[0] = "maxTokensPerInvestor";
        values[0] = _uint256ToString(maxTokensPerInvestor);
        
        names[1] = "maxInvestmentAmountUSDCents";
        values[1] = _uint256ToString(maxInvestmentAmount);
        
        names[2] = "tokenPriceUSDCents";
        values[2] = _uint256ToString(tokenPriceUSDCents);
        
        names[3] = "active";
        values[3] = active ? "true" : "false";
    }
    
    /**
     * @dev Check if rule is currently active
     * @return True if rule is active, false otherwise
     */
    function isActive() external view override returns (bool) {
        return active;
    }
    
    /**
     * @dev Record investment amount for USD-based tracking (called after successful transfer)
     * @param account Address that made investment
     * @param tokenAmount Amount of tokens purchased
     */
    function recordInvestment(address account, uint256 tokenAmount) external {
        require(
            msg.sender == token || msg.sender == owner(),
            "TransferLimitRule: Only token or owner"
        );
        
        if (tokenPriceUSDCents > 0) {
            uint256 investmentUSD = (tokenAmount * tokenPriceUSDCents) / (10 ** 18);
            totalInvestmentUSD[account] += investmentUSD;
            
            emit InvestmentRecorded(account, investmentUSD, totalInvestmentUSD[account]);
        }
    }
    
    /**
     * @dev Set maximum tokens per investor
     * @param limit New maximum tokens per investor
     */
    function setMaxTokensPerInvestor(uint256 limit) external onlyOwner {
        uint256 oldLimit = maxTokensPerInvestor;
        maxTokensPerInvestor = limit;
        emit MaxTokensUpdated(oldLimit, limit);
    }
    
    /**
     * @dev Set maximum investment amount in USD cents
     * @param limit New maximum investment in USD cents
     */
    function setMaxInvestmentAmount(uint256 limit) external onlyOwner {
        uint256 oldLimit = maxInvestmentAmount;
        maxInvestmentAmount = limit;
        emit MaxInvestmentUpdated(oldLimit, limit);
    }
    
    /**
     * @dev Update token price for USD calculations
     * @param priceUSDCents New token price in USD cents
     */
    function setTokenPrice(uint256 priceUSDCents) external onlyOwner {
        uint256 oldPrice = tokenPriceUSDCents;
        tokenPriceUSDCents = priceUSDCents;
        emit TokenPriceUpdated(oldPrice, priceUSDCents);
    }
    
    /**
     * @dev Set a custom token limit for a specific address
     * @param account Address to set custom limit for
     * @param limit Custom token limit (0 to remove custom limit)
     */
    function setCustomLimit(address account, uint256 limit) external onlyOwner {
        if (limit == 0) {
            hasCustomLimit[account] = false;
            delete customMaxTokens[account];
        } else {
            hasCustomLimit[account] = true;
            customMaxTokens[account] = limit;
        }
        
        emit CustomLimitSet(account, limit);
    }
    
    /**
     * @dev Add or remove an address from the exempt list
     * @param account Address to update
     * @param exempt Whether address should be exempt
     */
    function setExemption(address account, bool exempt) external onlyOwner {
        require(account != address(0), "TransferLimitRule: Invalid address");
        exemptAddresses[account] = exempt;
        emit AddressExemptionUpdated(account, exempt);
    }
    
    /**
     * @dev Batch update exemptions
     * @param accounts Array of addresses
     * @param exemptions Array of exemption statuses
     */
    function batchSetExemptions(address[] memory accounts, bool[] memory exemptions) external onlyOwner {
        require(accounts.length == exemptions.length, "TransferLimitRule: Array length mismatch");
        
        for (uint256 i = 0; i < accounts.length; i++) {
            require(accounts[i] != address(0), "TransferLimitRule: Invalid address");
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
     * @dev Get remaining investment capacity for an address
     * @param account Address to check
     * @return remainingTokens Remaining tokens that can be acquired
     * @return remainingUSD Remaining USD that can be invested (in cents)
     */
    function getRemainingCapacity(address account) external view returns (
        uint256 remainingTokens,
        uint256 remainingUSD
    ) {
        if (exemptAddresses[account]) {
            return (type(uint256).max, type(uint256).max);
        }
        
        IERC20 tokenContract = IERC20(token);
        uint256 currentBalance = tokenContract.balanceOf(account);
        
        // Calculate remaining tokens
        if (maxTokensPerInvestor > 0) {
            uint256 applicableLimit = maxTokensPerInvestor;
            if (hasCustomLimit[account]) {
                applicableLimit = customMaxTokens[account];
            }
            
            if (currentBalance >= applicableLimit) {
                remainingTokens = 0;
            } else {
                remainingTokens = applicableLimit - currentBalance;
            }
        } else {
            remainingTokens = type(uint256).max;
        }
        
        // Calculate remaining USD
        if (maxInvestmentAmount > 0) {
            uint256 currentInvestment = totalInvestmentUSD[account];
            if (currentInvestment >= maxInvestmentAmount) {
                remainingUSD = 0;
            } else {
                remainingUSD = maxInvestmentAmount - currentInvestment;
            }
        } else {
            remainingUSD = type(uint256).max;
        }
    }
    
    /**
     * @dev Reset investment tracking for an address (use with caution)
     * @param account Address to reset
     */
    function resetInvestmentTracking(address account) external onlyOwner {
        totalInvestmentUSD[account] = 0;
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
