// SPDX-License-Identifier: MIT
pragma solidity 0.8.25;

import {Enum} from "./dependencies/@gnosis.pm/safe-contracts/contracts/common/Enum.sol";
import {Module} from "./dependencies/@gnosis-guild/zodiac/contracts/core/Module.sol";
import {IAvatar} from "./dependencies/@gnosis-guild/zodiac/contracts/interfaces/IAvatar.sol";

abstract contract AgentTradingModule is Module {
    function exec(address to, uint256 value, bytes memory data, Enum.Operation operation)
        internal
        override
        returns (bool success)
    {
        success = IAvatar(target).execTransactionFromModule(to, value, data, operation);
    }

    function execAndReturnData(address to, uint256 value, bytes memory data, Enum.Operation operation)
        internal
        virtual
        override
        returns (bool success, bytes memory returnData)
    {
        (success, returnData) = IAvatar(target).execTransactionFromModuleReturnData(to, value, data, operation);
    }
}
