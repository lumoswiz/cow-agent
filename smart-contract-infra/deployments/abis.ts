export const TRADING_MODULE_ABI = [
  {
    type: "constructor",
    inputs: [
      {
        name: "_owner",
        type: "address",
        internalType: "address",
      },
      {
        name: "_avatar",
        type: "address",
        internalType: "address",
      },
      {
        name: "_target",
        type: "address",
        internalType: "address",
      },
    ],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "GPV2_SETTLEMENT_ADDRESS",
    inputs: [],
    outputs: [
      {
        name: "",
        type: "address",
        internalType: "address",
      },
    ],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "avatar",
    inputs: [],
    outputs: [
      {
        name: "",
        type: "address",
        internalType: "address",
      },
    ],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "getGuard",
    inputs: [],
    outputs: [
      {
        name: "_guard",
        type: "address",
        internalType: "address",
      },
    ],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "guard",
    inputs: [],
    outputs: [
      {
        name: "",
        type: "address",
        internalType: "address",
      },
    ],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "owner",
    inputs: [],
    outputs: [
      {
        name: "",
        type: "address",
        internalType: "address",
      },
    ],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "renounceOwnership",
    inputs: [],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "setAllowedTraders",
    inputs: [
      {
        name: "trader",
        type: "address",
        internalType: "address",
      },
      {
        name: "allowed",
        type: "bool",
        internalType: "bool",
      },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "setAvatar",
    inputs: [
      {
        name: "_avatar",
        type: "address",
        internalType: "address",
      },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "setGuard",
    inputs: [
      {
        name: "_guard",
        type: "address",
        internalType: "address",
      },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "setOrder",
    inputs: [
      {
        name: "orderUid",
        type: "bytes",
        internalType: "bytes",
      },
      {
        name: "order",
        type: "tuple",
        internalType: "struct GPv2Order.Data",
        components: [
          {
            name: "sellToken",
            type: "address",
            internalType: "contract IERC20",
          },
          {
            name: "buyToken",
            type: "address",
            internalType: "contract IERC20",
          },
          {
            name: "receiver",
            type: "address",
            internalType: "address",
          },
          {
            name: "sellAmount",
            type: "uint256",
            internalType: "uint256",
          },
          {
            name: "buyAmount",
            type: "uint256",
            internalType: "uint256",
          },
          {
            name: "validTo",
            type: "uint32",
            internalType: "uint32",
          },
          {
            name: "appData",
            type: "bytes32",
            internalType: "bytes32",
          },
          {
            name: "feeAmount",
            type: "uint256",
            internalType: "uint256",
          },
          {
            name: "kind",
            type: "bytes32",
            internalType: "bytes32",
          },
          {
            name: "partiallyFillable",
            type: "bool",
            internalType: "bool",
          },
          {
            name: "sellTokenBalance",
            type: "bytes32",
            internalType: "bytes32",
          },
          {
            name: "buyTokenBalance",
            type: "bytes32",
            internalType: "bytes32",
          },
        ],
      },
      {
        name: "signed",
        type: "bool",
        internalType: "bool",
      },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "setTarget",
    inputs: [
      {
        name: "_target",
        type: "address",
        internalType: "address",
      },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "setUp",
    inputs: [
      {
        name: "initParams",
        type: "bytes",
        internalType: "bytes",
      },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "target",
    inputs: [],
    outputs: [
      {
        name: "",
        type: "address",
        internalType: "address",
      },
    ],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "transferOwnership",
    inputs: [
      {
        name: "newOwner",
        type: "address",
        internalType: "address",
      },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "event",
    name: "AvatarSet",
    inputs: [
      {
        name: "previousAvatar",
        type: "address",
        indexed: true,
        internalType: "address",
      },
      {
        name: "newAvatar",
        type: "address",
        indexed: true,
        internalType: "address",
      },
    ],
    anonymous: false,
  },
  {
    type: "event",
    name: "ChangedGuard",
    inputs: [
      {
        name: "guard",
        type: "address",
        indexed: false,
        internalType: "address",
      },
    ],
    anonymous: false,
  },
  {
    type: "event",
    name: "Initialized",
    inputs: [
      {
        name: "version",
        type: "uint64",
        indexed: false,
        internalType: "uint64",
      },
    ],
    anonymous: false,
  },
  {
    type: "event",
    name: "OwnershipTransferred",
    inputs: [
      {
        name: "previousOwner",
        type: "address",
        indexed: true,
        internalType: "address",
      },
      {
        name: "newOwner",
        type: "address",
        indexed: true,
        internalType: "address",
      },
    ],
    anonymous: false,
  },
  {
    type: "event",
    name: "SetOrder",
    inputs: [
      {
        name: "orderUid",
        type: "bytes",
        indexed: true,
        internalType: "bytes",
      },
      {
        name: "signed",
        type: "bool",
        indexed: true,
        internalType: "bool",
      },
    ],
    anonymous: false,
  },
  {
    type: "event",
    name: "TargetSet",
    inputs: [
      {
        name: "previousTarget",
        type: "address",
        indexed: true,
        internalType: "address",
      },
      {
        name: "newTarget",
        type: "address",
        indexed: true,
        internalType: "address",
      },
    ],
    anonymous: false,
  },
  {
    type: "error",
    name: "CannotExec",
    inputs: [],
  },
  {
    type: "error",
    name: "InvalidInitialization",
    inputs: [],
  },
  {
    type: "error",
    name: "InvalidOrderUID",
    inputs: [],
  },
  {
    type: "error",
    name: "InvalidTrader",
    inputs: [],
  },
  {
    type: "error",
    name: "NotIERC165Compliant",
    inputs: [
      {
        name: "guard_",
        type: "address",
        internalType: "address",
      },
    ],
  },
  {
    type: "error",
    name: "NotInitializing",
    inputs: [],
  },
  {
    type: "error",
    name: "OwnableInvalidOwner",
    inputs: [
      {
        name: "owner",
        type: "address",
        internalType: "address",
      },
    ],
  },
  {
    type: "error",
    name: "OwnableUnauthorizedAccount",
    inputs: [
      {
        name: "account",
        type: "address",
        internalType: "address",
      },
    ],
  },
  {
    type: "error",
    name: "ZeroAddress",
    inputs: [],
  },
] as const;

export const MODULE_PROXY_FACTORY_ABI = [
  {
    type: "function",
    name: "deployModule",
    inputs: [
      {
        name: "",
        type: "address",
        internalType: "address",
      },
      {
        name: "",
        type: "bytes",
        internalType: "bytes",
      },
      {
        name: "",
        type: "uint256",
        internalType: "uint256",
      },
    ],
    outputs: [
      {
        name: "",
        type: "address",
        internalType: "address",
      },
    ],
    stateMutability: "nonpayable",
  },
] as const;

export const SAFE_ABI = [
  {
    inputs: [
      {
        internalType: "address",
        name: "module",
        type: "address",
      },
    ],
    name: "enableModule",
    outputs: [],
    stateMutability: "nonpayable",
    type: "function",
  },
] as const;
