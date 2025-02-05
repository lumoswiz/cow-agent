// SPDX-License-Identifier: MIT
pragma solidity 0.8.25;

import {Enum} from "./dependencies/@gnosis.pm/safe-contracts/contracts/common/Enum.sol";
import {Module} from "./dependencies/@gnosis-guild/zodiac/contracts/core/Module.sol";
import {IAvatar} from "./dependencies/@gnosis-guild/zodiac/contracts/interfaces/IAvatar.sol";
import {GPv2Order} from "./dependencies/cowprotocol/contracts/src/contracts/libraries/GPv2Order.sol";
import {ITokenAllowlist} from "./interfaces/ITokenAllowlist.sol";

contract AgentTradingModule is Module {
    using GPv2Order for bytes;

    event SetOrderTradeable(
        bytes indexed orderUid,
        address indexed sellToken,
        address indexed buyToken,
        uint256 sellAmount,
        uint256 buyAmount
    );

    ITokenAllowlist internal allowlist;
    bytes32 internal domainSeparator;

    constructor(address _owner, address _avatar, address _target, address _tokenAllowlist, bytes32 _domainSeparator) {
        bytes memory initParams = abi.encode(_owner, _avatar, _target, _tokenAllowlist, _domainSeparator);
        setUp(initParams);
    }

    function setUp(bytes memory initParams) public override initializer {
        (address _owner, address _avatar, address _target, address _tokenAllowlist, bytes32 _domainSeparator) =
            abi.decode(initParams, (address, address, address, address, bytes32));

        require(_avatar != address(0));
        require(_target != address(0));

        __Ownable_init(msg.sender);

        setAvatar(_avatar);
        setTarget(_target);
        allowlist = ITokenAllowlist(_tokenAllowlist);
        domainSeparator = _domainSeparator;

        transferOwnership(_owner);
    }

    function setOrderTradeable(bytes memory orderUid, GPv2Order.Data memory order) external {
        bytes memory uid;
        uid.packOrderUidParams(GPv2Order.hash(order, domainSeparator), owner(), order.validTo);

        // Order UID validation
        require(keccak256(orderUid) == keccak256(uid));

        // Order tokens validation
        require(allowlist.isOrderAllowed(address(order.sellToken), address(order.buyToken)));

        // @todo validation:
        //   - balances
        //   - paused
        //   - trade frequency

        bytes memory data = abi.encodeWithSignature("setPreSignature(bytes,bool)", orderUid, true);
        require(exec(address(allowlist), 0, data, Enum.Operation.Call));

        emit SetOrderTradeable(
            orderUid, address(order.sellToken), address(order.buyToken), order.sellAmount, order.buyAmount
        );
    }
}
