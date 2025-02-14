# Cow Swap Agent

Automated CoW Swap trading agent built with Silverback SDK

## Getting Started

This project utilises uv, see [docs](https://docs.astral.sh/uv/getting-started/) for installation.

Create venv and install dependencies:

```bash
uv sync --all-extras --dev
```

Install all Ape framework plugins:

```bash
ape plugins install .
```

## Run Silverback Bot

```bash
silverback run --network gnosis:mainnet:alchemy --account cow-agent
```
