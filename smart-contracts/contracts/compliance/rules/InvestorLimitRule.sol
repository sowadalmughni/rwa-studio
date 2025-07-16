// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./IComplianceRule.sol";

/**
 * @title InvestorLimitRule
 * @dev Compliance rule that enforces maximum number of token holders
 * @author Sowad Al-Mughni
 * 
 * This rule is commonly required for Regulation D offerings which have
 * limits on the number of investors (e.g., 35 non-accredited investors).
 */
contract InvestorLimitRule is IComplianceRule, Ownable {
    
    // Maximum number of investors allowed
    uint256 public maxInvestors;
    
    // Token contract this rule applies to
    address public token;
    
    // Current number of investors (addresses with non-zero balance)
    uint256 public currentInvestorCount;
    
    // Mapping to track if address is counted as investor
    mapping(address => bool) public isInvestor;
    
    // Whether this rule is currently active
    bool public active;
    
    /**
     * @dev Constructor
     * @param token_ Address of the token contract
     * @param maxInvestors_ Maximum number of investors allowed
     */
    constructor(address token_, uint256 maxInvestors_) Ownable(msg.sender) {
        require(token_ != address(0), "InvestorLimitRule: Invalid token address");
        require(maxInvestors_ > 0, "InvestorLimitRule: Invalid max investors");
        
        token = token_;
        maxInvestors = maxInvestors_;
        active = true;
    }
    
    /**
     * @dev Check if a transfer complies with investor limit rule
     * @param from Address sending tokens
     * @param to Address receiving tokens
     * @param amount Number of tokens being transferred
     * @return True if transfer complies with investor limit, false otherwise
     */
    function canTransfer(address from, address to, uint256 amount) external view override returns (bool) {
        if (!active) return true;
        
        // Minting (from == address(0))
        if (from == address(0)) {
            // If recipient is not already an investor and would become one
            if (!isInvestor[to] && amount > 0) {
                return currentInvestorCount < maxInvestors;
            }
            return true;
        }
        
        // Burning (to == address(0))
        if (to == address(0)) {
            return true; // Burning doesn't increase investor count
        }
        
        // Regular transfer
        IERC20 tokenContract = IERC20(token);
        uint256 senderBalance = tokenContract.balanceOf(from);
        uint256 recipientBalance = tokenContract.balanceOf(to);
        
        // Check if this transfer would create a new investor
        if (recipientBalance == 0 && amount > 0 && !isInvestor[to]) {
            return currentInvestorCount < maxInvestors;
        }
        
        return true;
    }
    
    /**
     * @dev Get human-readable description of this rule
     * @return Description of what this rule enforces
     */
    function getRuleDescription() external view override returns (string memory) {
        return string(abi.encodePacked(
            "Maximum investor limit: ",
            _uint256ToString(maxInvestors),
            " investors"
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
        
        names[0] = "maxInvestors";
        values[0] = _uint256ToString(maxInvestors);
        
        names[1] = "currentInvestorCount";
        values[1] = _uint256ToString(currentInvestorCount);
        
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
     * @dev Update investor count after a transfer
     * @param from Address sending tokens
     * @param to Address receiving tokens
     * @param amount Number of tokens transferred
     */
    function updateInvestorCount(address from, address to, uint256 amount) external {
        require(msg.sender == token, "InvestorLimitRule: Only token contract");
        
        if (!active) return;
        
        IERC20 tokenContract = IERC20(token);
        
        // Handle minting
        if (from == address(0) && amount > 0) {
            if (!isInvestor[to]) {
                isInvestor[to] = true;
                currentInvestorCount++;
            }
            return;
        }
        
        // Handle burning
        if (to == address(0)) {
            uint256 senderBalance = tokenContract.balanceOf(from);
            if (senderBalance == amount && isInvestor[from]) {
                isInvestor[from] = false;
                currentInvestorCount--;
            }
            return;
        }
        
        // Handle regular transfers
        if (amount > 0) {
            uint256 senderBalance = tokenContract.balanceOf(from);
            uint256 recipientBalance = tokenContract.balanceOf(to);
            
            // Check if sender will have zero balance after transfer
            if (senderBalance == amount && isInvestor[from]) {
                isInvestor[from] = false;
                currentInvestorCount--;
            }
            
            // Check if recipient will have non-zero balance after transfer
            if (recipientBalance == 0 && !isInvestor[to]) {
                isInvestor[to] = true;
                currentInvestorCount++;
            }
        }
    }
    
    /**
     * @dev Set maximum number of investors
     * @param maxInvestors_ New maximum number of investors
     */
    function setMaxInvestors(uint256 maxInvestors_) external onlyOwner {
        require(maxInvestors_ > 0, "InvestorLimitRule: Invalid max investors");
        maxInvestors = maxInvestors_;
    }
    
    /**
     * @dev Activate or deactivate this rule
     * @param active_ Whether rule should be active
     */
    function setActive(bool active_) external onlyOwner {
        active = active_;
    }
    
    /**
     * @dev Initialize investor count by scanning existing balances
     * @param investors Array of addresses to check and count
     */
    function initializeInvestorCount(address[] memory investors) external onlyOwner {
        IERC20 tokenContract = IERC20(token);
        currentInvestorCount = 0;
        
        for (uint256 i = 0; i < investors.length; i++) {
            if (tokenContract.balanceOf(investors[i]) > 0) {
                if (!isInvestor[investors[i]]) {
                    isInvestor[investors[i]] = true;
                    currentInvestorCount++;
                }
            } else {
                if (isInvestor[investors[i]]) {
                    isInvestor[investors[i]] = false;
                }
            }
        }
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

