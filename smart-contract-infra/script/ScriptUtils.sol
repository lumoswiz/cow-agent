// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { Script } from "forge-std/Script.sol";
import { stdJson } from "forge-std/StdJson.sol";

contract ScriptUtils is Script {
    using stdJson for string;

    error AddressNotFound(string key);

    function _writeDeploymentAddress(address addr, string memory key) internal {
        string memory root = vm.projectRoot();
        string memory path = string.concat(root, "/deployments/contracts.json");
        string memory ds = vm.toString(addr);
        vm.writeJson(ds, path, string.concat(".chains.", vm.toString(block.chainid), key));
    }

    function _getDeploymentAddress(string memory key) internal view returns (address) {
        string memory root = vm.projectRoot();
        string memory path = string.concat(root, "/deployments/contracts.json");
        string memory json = vm.readFile(path);
        string memory addressPath = string.concat(".chains.", vm.toString(block.chainid), key);
        address addr = json.readAddress(addressPath);
        if (addr == address(0)) revert AddressNotFound(key);
        return addr;
    }
}
