// SPDX-License-Identifier: MIT
pragma solidity 0.8.25;

import {Ownable} from "solady/src/auth/Ownable.sol";
import {EnumerableSetLib} from "solady/src/utils/EnumerableSetLib.sol";

contract TokenAllowlist is Ownable {
    using EnumerableSetLib for EnumerableSetLib.AddressSet;

    EnumerableSetLib.AddressSet internal allowList;

    constructor() {
        _initializeOwner(msg.sender);
    }

    function addToken(address token) external onlyOwner {
        allowList.add(token);
    }

    function addTokensBatch(address[] memory tokens) external onlyOwner {
        for (uint256 i; i < tokens.length; ++i) {
            allowList.add(tokens[i]);
        }
    }

    function removeToken(address token) external onlyOwner {
        allowList.remove(token);
    }

    function removeTokensBatch(address[] memory tokens) external onlyOwner {
        for (uint256 i; i < tokens.length; ++i) {
            allowList.remove(tokens[i]);
        }
    }

    function allowedTokens() external view returns (address[] memory) {
        return allowList.values();
    }

    function isAllowed(address token) external view returns (bool) {
        return allowList.contains(token);
    }
}
