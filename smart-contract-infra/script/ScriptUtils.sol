// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { Script } from "forge-std/Script.sol";
import { stdJson } from "forge-std/StdJson.sol";

contract ScriptUtils is Script {
    using stdJson for string;

    error AddressNotFound(string key);

    address internal constant SAFE = 0xbc3c7818177dA740292659b574D48B699Fdf0816;

    address internal constant SINGLETON_FACTORY = 0xce0042B868300000d44A59004Da54A005ffdcf9f;
    address internal constant MODULE_PROXY_FACTORY = 0x000000000000aDdB49795b0f9bA5BC298cDda236;
    address internal constant ZERO_ADDRESS = address(0);

    address internal constant GNO = 0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb;
    address internal constant COW = 0x177127622c4A00F3d409B75571e12cB3c8973d3c;
    address internal constant WXDAI = 0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d;

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
