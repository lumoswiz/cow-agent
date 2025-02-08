import json
import os
from pathlib import Path
from typing import Annotated, Dict

import click
import numpy as np
import pandas as pd
import requests
from ape import Contract, accounts, chain
from ape.api import BlockAPI
from ape.types import LogFilter
from silverback import SilverbackBot, StateSnapshot
from taskiq import Context, TaskiqDepends

# Initialize bot
bot = SilverbackBot()

# File path configuration
TRADE_FILEPATH = os.environ.get("TRADE_FILEPATH", ".db/trades.csv")
BLOCK_FILEPATH = os.environ.get("BLOCK_FILEPATH", ".db/block.csv")
GPV2_ABI_FILEPATH = os.environ.get("GPV2_ABI_FILEPATH", "./abi/GPv2Settlement.json")
TOKEN_ALLOWLIST_FILEPATH = os.environ.get("TOKEN_ALLOWLIST_FILEPATH", "./abi/TokenAllowlist.json")

# Addresses
SAFE_ADDRESS = "0x5aFE3855358E112B5647B952709E6165e1c1eEEe"  # PLACEHOLDER
TOKEN_ALLOWLIST_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
GPV2_SETTLEMENT_ADDRESS = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
GNO_ADDRESS = "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb"
COW_ADDRESS = "0x177127622c4A00F3d409B75571e12cB3c8973d3c"


# Load ABI helper function
def _load_abi(abi_name: str) -> Dict:
    """Load ABI from json file"""
    abi_path = Path(os.environ.get(f"{abi_name}_ABI_FILEPATH", f"./abi/{abi_name}.json"))
    with open(abi_path) as f:
        return json.load(f)


# Contracts
GPV2_SETTLEMENT_CONTRACT = Contract(GPV2_SETTLEMENT_ADDRESS, abi=_load_abi("GPv2Settlement"))
TOKEN_ALLOWLIST_CONTRACt = Contract(TOKEN_ALLOWLIST_ADDRESS, abi=_load_abi("TokenAllowlist"))

# API
API_BASE_URL = "https://api.cow.fi/xdai/api/v1"
API_HEADERS = {"accept": "application/json", "Content-Type": "application/json"}

# Variables
START_BLOCK = int(os.environ.get("START_BLOCK", chain.blocks.head.number))


# Local storage helper functions
def _load_trades_db() -> Dict:
    """
    Load trades database from CSV file or create new if doesn't exist.
    Returns dict with trade data indexed by block number.
    """
    dtype = {
        "owner": str,
        "sellToken": str,
        "buyToken": str,
        "sellAmount": object,
        "buyAmount": object,
        "block_number": np.int64,
    }

    df = (
        pd.read_csv(TRADE_FILEPATH, dtype=dtype)
        if os.path.exists(TRADE_FILEPATH)
        else pd.DataFrame(columns=dtype.keys()).astype(dtype)
    )
    return df.to_dict("records")


def _save_trades_db(trades_dict: Dict) -> None:
    """
    Save trades dictionary back to CSV file.
    """
    df = pd.DataFrame(trades_dict)
    df.to_csv(TRADE_FILEPATH, index=False)


def _load_block_db() -> Dict:
    """Load the last processed block from CSV file or create new if doesn't exist"""
    df = (
        pd.read_csv(BLOCK_FILEPATH)
        if os.path.exists(BLOCK_FILEPATH)
        else pd.DataFrame({"last_processed_block": [START_BLOCK]})
    )
    return {"last_processed_block": df["last_processed_block"].iloc[0]}


def _save_block_db(data: Dict):
    """Save the last processed block to CSV file"""
    os.makedirs(os.path.dirname(BLOCK_FILEPATH), exist_ok=True)
    df = pd.DataFrame([data])
    df.to_csv(BLOCK_FILEPATH, index=False)


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
        trades_db.append(_process_trade_log(log))

    _save_trades_db(trades_db)
    return trades_db


# CoW Swap trading helper functions
def _construct_quote_payload(
    sell_token: str,
    buy_token: str,
    sell_amount: str,
) -> Dict:
    """
    Construct payload for CoW Protocol quote request using PreSign method.
    Returns dict with required quote parameters.
    """
    return {
        "sellToken": sell_token,
        "buyToken": buy_token,
        "sellAmountBeforeFee": sell_amount,
        "from": SAFE_ADDRESS,
        "receiver": SAFE_ADDRESS,
        "appData": "{}",
        "appDataHash": "0xb48d38f93eaa084033fc5970bf96e559c33c4cdc07d889ab00b4d63f9590739d",
        "sellTokenBalance": "erc20",
        "buyTokenBalance": "erc20",
        "priceQuality": "verified",
        "signingScheme": "presign",
        "onchainOrder": False,
        "kind": "sell",
    }


def _get_quote(payload: Dict) -> Dict:
    """
    Get quote from CoW API
    Returns quote response or raises exception
    """
    response = requests.post(url=f"{API_BASE_URL}/quote", headers=API_HEADERS, json=payload)
    response.raise_for_status()
    return response.json()


def _construct_order_payload(quote_response: Dict) -> Dict:
    """
    Transform quote response into order request payload
    """
    quote = quote_response["quote"]

    return {
        "sellToken": quote["sellToken"],
        "buyToken": quote["buyToken"],
        "receiver": quote["receiver"],
        "sellAmount": quote["sellAmount"],
        "buyAmount": quote["buyAmount"],
        "validTo": quote["validTo"],
        "feeAmount": quote["feeAmount"],
        "kind": quote["kind"],
        "partiallyFillable": quote["partiallyFillable"],
        "sellTokenBalance": quote["sellTokenBalance"],
        "buyTokenBalance": quote["buyTokenBalance"],
        "signingScheme": "presign",
        "signature": "0x",
        "from": quote_response["from"],
        "quoteId": quote_response["id"],
        "appData": quote["appData"],
        "appDataHash": quote["appDataHash"],
    }


def _submit_order(order_payload: Dict) -> Dict:
    """
    Submit order to CoW API
    Returns order response or raises exception
    """
    response = requests.post(url=f"{API_BASE_URL}/orders", headers=API_HEADERS, json=order_payload)
    response.raise_for_status()
    return response.json()


# Silverback bot
@bot.on_startup()
def app_startup(startup_state: StateSnapshot):
    block_db = _load_block_db()
    last_processed_block = block_db["last_processed_block"]

    _process_historical_gno_trades(
        GPV2_SETTLEMENT_CONTRACT,
        GNO_ADDRESS,
        start_block=last_processed_block,
        stop_block=chain.blocks.head.number,
    )

    _save_block_db({"last_processed_block": chain.blocks.head.number})

    return {"message": "Starting...", "block_number": startup_state.last_block_seen}


@bot.on_(chain.blocks)
def exec_block(block: BlockAPI, context: Annotated[Context, TaskiqDepends()]):
    """Execute block handler"""
    quote_payload = _construct_quote_payload(
        sell_token=GNO_ADDRESS, buy_token=COW_ADDRESS, sell_amount="1000000000000000000"
    )

    try:
        quote = _get_quote(quote_payload)
        click.echo(f"Quote received: {quote}")
    except requests.RequestException as e:
        click.echo(f"Quote request failed: {e}")
