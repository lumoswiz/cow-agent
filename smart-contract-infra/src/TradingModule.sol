// SPDX-License-Identifier: MIT
pragma solidity 0.8.28;

import { Enum } from "@gnosis.pm/safe-contracts/contracts/common/Enum.sol";
import { Module } from "@gnosis-guild/zodiac/contracts/core/Module.sol";
import { GPv2Order } from "cowprotocol/contracts/src/contracts/libraries/GPv2Order.sol";
import { GPv2Signing } from "cowprotocol/contracts/src/contracts/mixins/GPv2Signing.sol";
import { ITokenAllowlist } from "./interfaces/ITokenAllowlist.sol";

abstract contract TradingModule is Module {
    using GPv2Order for bytes;

    event SetOrderTradeable(
        bytes indexed orderUid,
        address indexed sellToken,
        address indexed buyToken,
        uint256 sellAmount,
        uint256 buyAmount
    );

    error InvalidOrderUID();
    error OrderNotAllowed();

    address public constant GPV2_SETTLEMENT_ADDRESS = 0x9008D19f58AAbD9eD0D60971565AA8510560ab41;

    ITokenAllowlist internal allowlist;
    bytes32 internal domainSeparator;

    constructor(address _owner, address _avatar, address _target, address _tokenAllowlist) {
        bytes memory initParams = abi.encode(_owner, _avatar, _target, _tokenAllowlist);
        setUp(initParams);
    }

    function setUp(bytes memory initParams) public override initializer {
        (address _owner, address _avatar, address _target, address _tokenAllowlist) =
            abi.decode(initParams, (address, address, address, address));

        require(_avatar != address(0));
        require(_target != address(0));

        __Ownable_init(msg.sender);

        setAvatar(_avatar);
        setTarget(_target);
        allowlist = ITokenAllowlist(_tokenAllowlist);
        domainSeparator = GPv2Signing(GPV2_SETTLEMENT_ADDRESS).domainSeparator();

        transferOwnership(_owner);
    }

    function setOrderTradeable(bytes memory orderUid, GPv2Order.Data memory order) external {
        bytes memory uid;
        uid.packOrderUidParams(GPv2Order.hash(order, domainSeparator), owner(), order.validTo);

        require(keccak256(orderUid) == keccak256(uid), InvalidOrderUID());

        require(allowlist.isOrderAllowed(address(order.sellToken), address(order.buyToken)), OrderNotAllowed());

        bytes memory data = abi.encodeWithSignature("setPreSignature(bytes,bool)", orderUid, true);
        require(exec(GPV2_SETTLEMENT_ADDRESS, 0, data, Enum.Operation.Call));

        emit SetOrderTradeable(
            orderUid, address(order.sellToken), address(order.buyToken), order.sellAmount, order.buyAmount
        );
    }
}
