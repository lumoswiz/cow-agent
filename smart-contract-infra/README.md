# Smart Contract Infrastructure

This repository provides the deployment scripts and tooling for smart contracts and governance processes. It covers
one-off deploys (via Foundry) for core contracts—such as the token allowlist, CoWSwapGuard, and TradingModule
mastercopy—as well as day-to-day operations for users and agents.

## Getting Started

1. **Install dependencies:**

   ```bash
   bun i
   ```

2. **Compile Smart Contracts:**

   ```bash
   bun run build
   ```

## Smart Contracts Overview

- **TokenAllowlist ([TokenAllowlist.sol](./src/TokenAllowlist.sol)):**  
  Enables the contract owner to manage a list of approved tokens. It provides functions to add or remove tokens and
  check if a token is allowed, ensuring that trading is confined to community-vetted assets.

- **TradingModule ([TradingModule.sol](./src/TradingModule.sol)):**  
  A Zodiac Guardable Module that allows an AI trading agent to transact on behalf of a Safe. It enforces trading rules
  by verifying that only tokens on the allowlist are used and that trades execute exclusively on CoWSwap. Additionally,
  it sets a pre-signature on orders to make them tradeable and includes a pause mechanism—letting the owner disable
  trading when needed.

- **CoWSwapGuard ([CoWSwapGuard.sol](./src/CoWSwapGuard.sol)):**  
  Implements guard checks to ensure that trades adhere to community-defined rules. It restricts trading to approved
  token pairs and parameters, acting as an additional security layer to prevent unauthorized or unsafe trading actions.

## Deployment Overview

### Foundry Deploy Scripts (One-Off Deploys)

These scripts deploy core contracts per chain. For example, on Gnosis Chain, the following addresses have been deployed:

- **Allowlist:** `0xE0CBa604f8be035a80D21b49C67BdcE59Bba9d76`
- **Guard:** `0xF67966246d72fC124d19B7F2d03DD690B756De88`
- **TradingModule MasterCopy:** `0xDdd11DC80A25563Cb416647821f3BC5Ad75fF1BA`

Foundry deploy scripts include:

- `script/01_Deploy_Allowlist.s.sol`
- `script/02_Deploy_CoWSwapGuard.s.sol`
- `script/03_Deploy_MasterCopy.s.sol`

**Token Configuration Script:**

- `script/01A_AddTokens_Allowlist.s.sol`  
  This script configures the allowlist with the GNO, WXDAI, and COW tokens.

### Bun Deploy Scripts for Users/Agents

These scripts provide two deployment options:

- **Bring Your Own (BYO) Safe and TradingModule Proxy:** If you already have a Safe and proxy deployed, set the required
  environment variables and run:

  ```bash
  bun run script/safe/module-config.ts
  bun run script/safe/enable-module.ts
  ```

  These commands will:

  - Enable the module on your existing Safe.
  - Configure the module by setting the required guard.
  - Register your account (private key) as an allowed trader.

- **Deploy a New Safe and TradingModule Proxy:** If you don't have a Safe and TradingModule already deployed, run:
  ```bash
  bun run script/safe/deploy-all.ts
  ```
  This deploys a new Safe, a new TradingModule proxy, and then automatically configures them as above.

## Additional Information

- **Configuration Files:**  
  This repo includes configuration files for Prettier, Solhint, Foundry, and others to streamline development and
  deployment.

- **Contract Address Resolution:**  
  Contract addresses can be configured through environment variables. If not set, the scripts will default to values
  from the deployments (Foundry) configuration.

## Safety

This software is experimental and provided on an "as-is" and "as available" basis. The team makes no warranties, express
or implied, and will not be liable for any losses or damages incurred through its use. It is crucial that you perform
your own thorough tests to ensure compatibility and correct behavior with your code.

## Future Work

- Develop a helper script to build Tenderly transactions for the CoW DAO Governance mechanism.
- Implement a comprehensive test suite based on the Branching Tree Technique
  ([BTT](https://github.com/paulber19/branching-tree-testing)).
