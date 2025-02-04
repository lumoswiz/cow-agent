import json
import os
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from ape import Contract, accounts, chain
from ape.types import LogFilter
from silverback import SilverbackBot

# Initialize bot
bot = SilverbackBot()

# File path configuration
TRADE_FILEPATH = os.environ.get("TRADE_FILEPATH", ".db/trades.csv")
GPV2_ABI_FILEPATH = os.environ.get("GPV2_ABI_FILEPATH", "./abi/GPv2Settlement.json")

# Load GPv2Settlement ABI
abi_path = Path(GPV2_ABI_FILEPATH)
with open(abi_path) as f:
    gpv2_settlement_abi = json.load(f)

# Gnosis Chain Addresses
GPV2_SETTLEMENT_ADDRESS = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
GNO_ADDRESS = "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb"

# Contracts
GPV2_SETTLEMENT_CONTRACT = Contract(GPV2_SETTLEMENT_ADDRESS, abi=gpv2_settlement_abi)

# Variables
START_BLOCK = int(os.environ.get("START_BLOCK", chain.blocks.head.number))


# Local storage helper functions
def _load_trades_db() -> Dict:
    """
    Load trades database from CSV file or create new if doesn't exist.
    Returns dict with trade data indexed by transaction hash.
    """
    dtype = {
        "block_number": np.int64,
        "owner": str,
        "sellToken": str,
        "buyToken": str,
        "sellAmount": object,
        "buyAmount": object,
        "timestamp": np.int64,
    }

    df = (
        pd.read_csv(TRADE_FILEPATH, dtype=dtype)
        if os.path.exists(TRADE_FILEPATH)
        else pd.DataFrame(columns=dtype.keys()).astype(dtype)
    )
    return df.set_index("block_number").to_dict("index")


def _save_trades_db(trades_dict: Dict) -> None:
    """
    Save trades dictionary back to CSV file.
    """
    df = pd.DataFrame.from_dict(trades_dict, orient="index")
    df.index.name = "transaction_hash"
    df.to_csv(TRADE_FILEPATH)


# Historical log helper functions
def _process_trade_log(log) -> Dict:
    """Process trade log and return formatted dictionary entry"""
    return {
        "block_number": log.block_number,
        "owner": log.owner,
        "sellToken": log.sellToken,
        "buyToken": log.buyToken,
        "sellAmount": str(log.sellAmount),
        "buyAmount": str(log.buyAmount),
        "timestamp": log.timestamp,
    }


def _get_historical_gno_trades(
    settlement_contract,
    gno_address: str,
    start_block: int,
    stop_block: int = chain.blocks.head.number,
):
    """Get historical GNO trades from start_block to stop_block"""
    log_filter = LogFilter(
        addresses=[settlement_contract.address],
        events=[settlement_contract.Trade.abi],
        start_block=start_block,
        stop_block=stop_block,
    )

    for log in accounts.provider.get_contract_logs(log_filter):
        if log.sellToken == gno_address or log.buyToken == gno_address:
            yield log


def _process_historical_gno_trades(
    settlement_contract, gno_address: str, start_block: int, stop_block: int
) -> Dict:
    """Process historical GNO trades and store in database"""
    trades_db = _load_trades_db()

    for log in _get_historical_gno_trades(
        settlement_contract, gno_address, start_block, stop_block
    ):
        trades_db[log.transaction_hash] = _process_trade_log(log)

    _save_trades_db(trades_db)
    return trades_db
