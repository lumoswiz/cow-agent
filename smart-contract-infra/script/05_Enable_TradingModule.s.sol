// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { console2 } from "forge-std/Script.sol";
import { ScriptUtils } from "script/ScriptUtils.sol";

interface ISafe {
    function enableModule(address module) external;
}

// With verification:
/*
    forge script script/05_Enable_TradingModule.s.sol \
    --rpc-url gnosis \
    --private-key $PRIVATE_KEY \
    --broadcast -vvvv
*/

// Without verification:
/*
    forge script script/05_Enable_TradingModule.s.sol \
    --rpc-url gnosis \
    --private-key $PRIVATE_KEY \
    --broadcast -vvvv
*/
contract EnableTradingModule is ScriptUtils {
    address internal constant SAFE = 0x5aFE3855358E112B5647B952709E6165e1c1eEEe;

    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");

        address tradingModuleProxy = _getDeploymentAddress(".tradingModuleProxy");

        vm.startBroadcast(pk);

        ISafe(SAFE).enableModule(tradingModuleProxy);
        console2.log("Enabled TradingModule:", tradingModuleProxy);

        vm.stopBroadcast();
    }
}
