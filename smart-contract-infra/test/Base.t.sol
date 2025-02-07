// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { TokenAllowlist } from "src/TokenAllowlist.sol";
import { Constants } from "test/utils/Constants.sol";
import { Utils } from "test/utils/Utils.sol";

contract BaseTest is Constants, Utils {
    address internal alice;
    address internal dao;

    TokenAllowlist internal allowlist;

    function setUp() public {
        alice = makeAddr("alice");
        dao = makeAddr("dao");

        vm.startPrank(dao);
        allowlist = new TokenAllowlist();

        // Default caller: dao
    }
}
