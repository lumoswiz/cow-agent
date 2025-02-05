// SPDX-License-Identifier: MIT
pragma solidity 0.8.25;

import {Ownable} from "solady/src/auth/Ownable.sol";
import {EnumerableSetLib} from "solady/src/utils/EnumerableSetLib.sol";

contract TokenAllowlist is Ownable {
    using EnumerableSetLib for EnumerableSetLib.AddressSet;

    EnumerableSetLib.AddressSet internal allowlist;

    constructor() {
        _initializeOwner(msg.sender);
    }

    function addToken(address token) external onlyOwner {
        allowlist.add(token);
    }

    function addTokensBatch(address[] memory tokens) external onlyOwner {
        for (uint256 i; i < tokens.length; ++i) {
            allowlist.add(tokens[i]);
        }
    }

    function removeToken(address token) external onlyOwner {
        allowlist.remove(token);
    }

    function removeTokensBatch(address[] memory tokens) external onlyOwner {
        for (uint256 i; i < tokens.length; ++i) {
            allowlist.remove(tokens[i]);
        }
    }

    function allowedTokens() external view returns (address[] memory) {
        return allowlist.values();
    }

    function isAllowed(address token) public view returns (bool) {
        return allowlist.contains(token);
    }

    function isOrderAllowed(address sellToken, address buyToken) external view returns (bool) {
        return isAllowed(sellToken) && isAllowed(buyToken);
    }
}
