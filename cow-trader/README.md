# Cow Swap Agent

Automated CoW Swap trading agent built with Silverback SDK

## Getting Started

This project utilises uv, see [docs](https://docs.astral.sh/uv/getting-started/) for installation.

Create venv and install dependencies:

```bash
uv sync --all-extras --dev
```

Venv:

```bash
source .venv/bin/activate
```

Install all Ape framework plugins:

```bash
ape plugins install .
```

## Run Silverback Bot

Before running the bot, ensure you've set up an account alias as outlined in the [Ape Accounts documentation](https://docs.apeworx.io/ape/stable/userguides/accounts.html).

Once your account alias is ready (e.g. `cow-agent`), you can run the bot:

```bash
silverback run --network gnosis:mainnet:alchemy --account cow-agent
```

This command uses the alias you configured as the signer. There will be a prompt asking if you want to enable auto-signing.

### Bot Overview

The bot continuously monitors new blocks and manages trading through two primary block handlers:

- **update_state:**

  - Processes each new block to fetch and update CoW Swap trade data.
  - Tracks key events (e.g. recent trades, block numbers) and updates local storage (e.g. `trades.csv`, `block.csv`, `orders.csv`, `reasoning.csv`, `decisions.csv`).
  - Controls whether trading is enabled based on a cooldown and past decisions.

- **make_trading_decision:**
  - When permitted, it builds a **TradeContext** from recent trade events and past decisions.
  - Provides this context to an AI agent (with tools like token naming, token type, and eligible buy tokens) along with a system prompt (stored in `system_prompt.txt`).
  - The agent returns a decision on whether to trade and which token to buy.
  - If a trade is executed, the bot builds a CoW Swap order (via a quote → order payload → submit → pre-sign sequence using the TradingModule).
  - A trading cooldown is applied after executing a trade.

Other key components include:

- **Agent Architecture:**

  - The agent receives an aggregated **TradeContext** via **AgentDependencies** and produces an **AgentResponse** that's converted to an **AgentDecision**.
  - Past decisions (and their outcomes) are fed back to refine future trading decisions.

  - **Contract Address Configuration:**
    - The `TOKEN_ALLOWLIST_ADDRESS` is loaded from [deployments](../smart-contract-infra/deployments/contracts.json) (for chain ID 100).
    - The `SAFE_ADDRESS` and `TRADING_MODULE_ADDRESS` are taken from environment variables if set; otherwise, they default to the values in deployments.

- **Local Storage Helpers:**

  - Utility functions load and persist state data (trades, orders, decisions, and processed blocks) in CSV files.

- **CoW Swap Trading Functions:**

  - Dedicated functions handle constructing, submitting, and signing orders through the CoW Swap orderbook API and TradingModule.

- **Initialization:**
  - On startup (`bot_startup`), the bot loads persistent state, catches up on historical trades, and optionally enables auto-signing.
  - During worker initialization (`worker_startup`), each worker (both block handlers) gets access to shared state—including the trading agent instance, historical trades, and past decisions.

This design ensures the bot continuously tracks market activity, leverages an AI agent for dynamic decision-making, and safely executes trades on CoW Swap.
