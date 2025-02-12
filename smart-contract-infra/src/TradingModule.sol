// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { Enum } from "@gnosis.pm/safe-contracts/contracts/common/Enum.sol";
import { Module } from "@gnosis-guild/zodiac/contracts/core/Module.sol";
import { Guardable } from "@gnosis-guild/zodiac/contracts/guard/Guardable.sol";
import { GPv2Order } from "cowprotocol/contracts/src/contracts/libraries/GPv2Order.sol";
import { GPv2Signing } from "cowprotocol/contracts/src/contracts/mixins/GPv2Signing.sol";

import { IAvatar } from "@gnosis-guild/zodiac/contracts/interfaces/IAvatar.sol";
import { IGuard } from "@gnosis-guild/zodiac/contracts/interfaces/IGuard.sol";

contract TradingModule is Module, Guardable {
    using GPv2Order for bytes;

    /// @notice Emitted when an order was successfully set
    event SetOrder(bytes indexed orderUid, bool indexed signed);

    /// @notice Thrown when the supplied order UID and order is mismatched
    error InvalidOrderUID();

    /// @notice Thrown when the transaction cannot execute
    error CannotExec();

    /// @notice GPv2Settlement address
    /// @dev Deterministically deployed
    address public constant GPV2_SETTLEMENT_ADDRESS = 0x9008D19f58AAbD9eD0D60971565AA8510560ab41;

    /// @notice CoW Swap Guard contract address
    address public constant COW_SWAP_GUARD = 0x9008D19f58AAbD9eD0D60971565AA8510560ab41; // placeholder

    /// @notice GPv2Settlement domain separator
    bytes32 internal domainSeparator;

    constructor(address _owner, address _avatar, address _target) {
        bytes memory initParams = abi.encode(_owner, _avatar, _target);
        setUp(initParams);
    }

    function setUp(bytes memory initParams) public override initializer {
        (address _owner, address _avatar, address _target) = abi.decode(initParams, (address, address, address));

        __Ownable_init(msg.sender);

        setAvatar(_avatar);
        setTarget(_target);

        domainSeparator = GPv2Signing(GPV2_SETTLEMENT_ADDRESS).domainSeparator();

        transferOwnership(_owner);
    }

    function setOrder(bytes memory orderUid, GPv2Order.Data memory order, bool signed) external {
        bytes memory uid = new bytes(GPv2Order.UID_LENGTH);
        uid.packOrderUidParams(GPv2Order.hash(order, domainSeparator), owner(), order.validTo);
        require(keccak256(orderUid) == keccak256(uid), InvalidOrderUID());

        bytes memory txData = abi.encodeCall(GPv2Signing.setPreSignature, (orderUid, signed));
        bytes memory data = abi.encode(txData, address(order.sellToken), address(order.buyToken));

        require(exec(GPV2_SETTLEMENT_ADDRESS, 0, data, Enum.Operation.Call), CannotExec());

        emit SetOrder(orderUid, signed);
    }

    function exec(
        address to,
        uint256 value,
        bytes memory data,
        Enum.Operation operation
    )
        internal
        override
        returns (bool)
    {
        IGuard(COW_SWAP_GUARD).checkTransaction(
            to, value, data, operation, 0, 0, 0, address(0), payable(0), "", msg.sender
        );

        (bytes memory txData,,) = abi.decode(data, (bytes, address, address));

        return IAvatar(target).execTransactionFromModule(to, value, txData, operation);
    }
}
