// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { console2 } from "forge-std/Script.sol";
import { ScriptUtils } from "script/ScriptUtils.sol";
import { TradingModule } from "src/TradingModule.sol";

interface IModuleProxyFactory {
    function deployModule(address, bytes memory, uint256) external returns (address);
}

// With verification:
/*
    forge script script/04_Deploy_TradingModuleProxy.s.sol \
    --rpc-url gnosis \
    --private-key $PRIVATE_KEY \
    --verify --etherscan-api-key $ETHERSCAN_API_KEY \
    --broadcast -vvvv
*/

// Without verification:
/*
    forge script script/04_Deploy_TradingModuleProxy.s.sol \
    --rpc-url gnosis \
    --private-key $PRIVATE_KEY \
    --broadcast -vvvv
*/
contract DeployTradingModuleProxy is ScriptUtils {
    address internal constant MODULE_PROXY_FACTORY = 0x000000000000aDdB49795b0f9bA5BC298cDda236;
    address internal constant SAFE = 0x5aFE3855358E112B5647B952709E6165e1c1eEEe;

    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");

        address masterCopy = _getDeploymentAddress(".tradingModuleMasterCopy");

        bytes memory initData = abi.encodeCall(TradingModule.setUp, (abi.encode(SAFE, SAFE, SAFE)));
        bytes32 salt = keccak256(abi.encodePacked("TradingModuleProxyV1"));

        vm.startBroadcast(pk);

        address proxy = IModuleProxyFactory(MODULE_PROXY_FACTORY).deployModule(masterCopy, initData, uint256(salt));
        console2.log("TradingModule Proxy deployed to:", proxy);
        _writeDeploymentAddress(proxy, ".tradingModuleProxy");

        vm.stopBroadcast();
    }
}
