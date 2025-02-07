// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { Enum } from "@gnosis.pm/safe-contracts/contracts/common/Enum.sol";
import { BaseGuard } from "@gnosis-guild/zodiac/contracts/guard/BaseGuard.sol";

contract CoWSwapGuard is BaseGuard {
    /// @notice Thrown when the target address is not GPv2Settlement contract address
    error InvalidAddress();

    /// @notice Thrown when the function selector is not `setPreSignature(bytes,bool)`
    error InvalidSelector();

    /// @notice GPv2Settlement address
    /// @dev Deterministically deployed
    address internal constant GPV2_SETTLEMENT_ADDRESS = 0x9008D19f58AAbD9eD0D60971565AA8510560ab41;

    /// @notice Function selector for GPv2Settlement.setPreSignature
    bytes4 internal constant SET_PRE_SIGNATURE_SELECTOR = 0xec6cb13f;

    /// @dev Module transactions only use the first four parameters: to, value, data, and operation.
    function checkTransaction(
        address to,
        uint256,
        bytes memory data,
        Enum.Operation,
        uint256,
        uint256,
        uint256,
        address,
        address payable,
        bytes memory,
        address
    )
        external
        pure
        override
    {
        require(to == GPV2_SETTLEMENT_ADDRESS, InvalidAddress());

        (bytes4 selector,,) = abi.decode(data, (bytes4, bytes, bool));
        require(selector == SET_PRE_SIGNATURE_SELECTOR, InvalidSelector());
    }

    function checkAfterExecution(bytes32 txHash, bool success) external override { }
}
