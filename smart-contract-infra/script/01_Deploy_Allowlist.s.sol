// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { console2 } from "forge-std/Script.sol";
import { ScriptUtils } from "script/ScriptUtils.sol";
import { TokenAllowlist } from "src/TokenAllowlist.sol";

// With verification:
/*
    forge script script/01_Deploy_Allowlist.s.sol \
    --rpc-url gnosis \
    --private-key $PRIVATE_KEY \
    --verify --etherscan-api-key $ETHERSCAN_API_KEY \
    --broadcast -vvvv
*/

contract DeployAllowlist is ScriptUtils {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(pk);

        address allowlist = address(new TokenAllowlist());
        console2.log("Allowlist deployed to:", allowlist);
        _writeDeploymentAddress(allowlist, ".allowlist");

        vm.stopBroadcast();
    }
}
