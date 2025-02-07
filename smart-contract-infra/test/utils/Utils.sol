// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { Test } from "forge-std/Test.sol";

contract Utils is Test {
    /// @notice Stops the active prank and starts a new one with `_msgSender`
    function resetPrank(address _msgSender) internal {
        vm.stopPrank();
        vm.startPrank(_msgSender);
    }
}
