// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { console2 } from "forge-std/Script.sol";
import { ScriptUtils } from "script/ScriptUtils.sol";
import { TradingModule } from "src/TradingModule.sol";

interface ISingletonFactory {
    function deploy(bytes memory, bytes32) external returns (address payable createdContract);
}

// With verification:
/*
    forge script script/03_Deploy_MasterCopy.s.sol \
    --rpc-url gnosis \
    --private-key $PRIVATE_KEY \
    --verify --etherscan-api-key $ETHERSCAN_API_KEY \
    --broadcast -vvvv
*/

// Without verification:
/*
    forge script script/03_Deploy_MasterCopy.s.sol \
    --rpc-url gnosis \
    --private-key $PRIVATE_KEY \
    --broadcast -vvvv
*/

contract DeployMasterCopy is ScriptUtils {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");

        bytes memory creationCode = type(TradingModule).creationCode;
        bytes memory constructorArgs = abi.encode(vm.addr(pk), ZERO_ADDRESS, ZERO_ADDRESS);
        bytes memory initCode = abi.encodePacked(creationCode, constructorArgs);

        bytes32 salt = keccak256(abi.encodePacked("TradingModuleV1"));

        vm.startBroadcast(pk);

        ISingletonFactory factory = ISingletonFactory(SINGLETON_FACTORY);
        address tradingModuleMasterCopy = factory.deploy(initCode, salt);

        console2.log("TradingModule MasterCopy deployed to:", tradingModuleMasterCopy);
        _writeDeploymentAddress(tradingModuleMasterCopy, ".tradingModuleMasterCopy");

        vm.stopBroadcast();
    }
}
