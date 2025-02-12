// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { console2 } from "forge-std/Script.sol";
import { ScriptUtils } from "script/ScriptUtils.sol";
import { TokenAllowlist } from "src/TokenAllowlist.sol";

// Without verification:
/*
    forge script script/06_AddTokens_Allowlist.s.sol \
    --rpc-url gnosis \
    --private-key $PRIVATE_KEY \
    --broadcast -vvvv
*/

contract AddTokensScript is ScriptUtils {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(pk);

        TokenAllowlist allowlist = TokenAllowlist(_getDeploymentAddress(".allowlist"));

        address[] memory tokens = new address[](3);
        tokens[0] = GNO;
        tokens[1] = COW;
        tokens[2] = WXDAI;

        allowlist.addTokensBatch(tokens);

        vm.stopBroadcast();
    }
}
