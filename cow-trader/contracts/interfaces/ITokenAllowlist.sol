// SPDX-License-Identifier: MIT
pragma solidity 0.8.25;

interface ITokenAllowlist {
    function isOrderAllowed(address sellToken, address buyToken) external view returns (bool);
}
