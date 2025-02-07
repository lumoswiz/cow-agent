// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { BaseTest } from "test/Base.t.sol";

contract Concrete_Unit_TokenAllowlist is BaseTest {
    function test_ShouldRevert_AddToken() external {
        resetPrank(alice);
        vm.expectRevert();
        allowlist.addToken(GNO);
    }

    modifier whenOwner() {
        _;
    }

    function test_AddToken() external whenOwner {
        allowlist.addToken(GNO);
        assertEq(allowlist.isAllowed(GNO), true);
    }
}
