# Moozilla x Kong [![Open in Gitpod][gitpod-badge]][gitpod] [![CI Status][ci-badge]][ci] [![Built with Silverback][silverback-badge]][silverback] [![License: MIT][license-badge]][license]

[gitpod]: https://gitpod.io/#https://github.com/lumoswiz/cow-agent
[gitpod-badge]: https://img.shields.io/badge/Gitpod-Open%20in%20Gitpod-FFB45B?logo=gitpod
[ci]: https://github.com/lumoswiz/cow-agent/actions
[ci-badge]: https://github.com/lumoswiz/cow-agent/actions/workflows/ci.yml/badge.svg
[silverback]: https://github.com/ApeWorX/silverback
[silverback-badge]: https://img.shields.io/badge/Built%20with-Silverback-blue?style=flat-square
[license]: https://opensource.org/licenses/MIT
[license-badge]: https://img.shields.io/badge/License-MIT-yellow.svg

## Development Prerequisites

- **[Bun](https://bun.sh)** `v1.1.31`
- **[uv](https://docs.astral.sh/uv/getting-started/)** `v0.5.26`
- **[Foundry](https://book.getfoundry.sh/)** `v0.3.0`

## Monorepo Contents

This repository is organized as a **monorepo** and contains multiple related projects:

- **CoW Trader:** A Silverback CoW Swap trading bot that uses PydanticAI as the agent framework.
- **Smart Contract Infra:** Provides the smart contract development,deployment and configuration scripts for:
  - The token allowlist governance mechanism.
  - Setting up a new Safe or bringing your own.
  - Deploying a trading module proxy enabled on the Safe.
  - Configuring the module on the Safe with the guard and enable the agent to trade via the module.

Each project is maintained in its own subdirectory and may have additional project-specific configuration and dependencies. However, they all share a centralized `.env` file located at the repository root.

## Project Specific Configuration

While a centralized `.env` file is used for common environment variables, each project in this monorepo may have additional settings and build steps:

- **CoW Trader:**  
  This project might require extra, project-specific configuration. Please refer to the [CoW Trader README](./path/to/cow-trader/README.md) for full setup instructions.

- **Smart Contract Infra:**  
  Building and deploying the contract components is handled separately. Detailed instructions are available in the [Smart Contract Infra README](./path/to/smart-contract-infra/README.md).

### Environment Variables

Each variable is explained in the `.env.example` file. Be sure to copy `.env.example` to `.env` and fill in the required values:

- **PydanticAI Variables:**

  - `ANTHROPIC_API_KEY`
  - `ENCOURAGE_TRADE`

- **Bot Variables:**

  - `START_BLOCK`

- **Web3 Variables:**
  - `PRIVATE_KEY`
  - `WEB3_ALCHEMY_PROJECT_ID`
  - `ETHERSCAN_API_KEY`
  - `CHAIN_ID`
  - `SAFE_ADDRESS` (optional)
  - `TRADING_MODULE_ADDRESS` (optional)

This setup allows you to configure both individual projects while sharing common environment variables.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
