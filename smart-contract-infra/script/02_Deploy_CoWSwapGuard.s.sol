// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { console2 } from "forge-std/Script.sol";
import { ScriptUtils } from "script/ScriptUtils.sol";
import { CoWSwapGuard } from "src/CoWSwapGuard.sol";

// With verification:
/*
    forge script script/02_Deploy_CoWSwapGuard.s.sol \
    --rpc-url gnosis \
    --private-key $PRIVATE_KEY \
    --verify --etherscan-api-key $ETHERSCAN_API_KEY \
    --broadcast -vvvv
*/

// Without verification:
/*
    forge script script/02_Deploy_CoWSwapGuard.s.sol \
    --rpc-url gnosis \
    --private-key $PRIVATE_KEY \
    --broadcast -vvvv
*/

contract DeployGuard is ScriptUtils {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(pk);

        address allowlist = _getDeploymentAddress(".allowlist");
        address guard = address(new CoWSwapGuard(allowlist));
        console2.log("CoWSwapGuard deployed to:", guard);
        _writeDeploymentAddress(guard, ".guard");

        vm.stopBroadcast();
    }
}
