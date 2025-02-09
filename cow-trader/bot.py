import json
import os
from pathlib import Path
from typing import Annotated, Dict, List

import click
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
ORDERS_FILEPATH = os.environ.get("ORDERS_FILEPATH", ".db/orders.csv")

# Addresses
SAFE_ADDRESS = "0x5aFE3855358E112B5647B952709E6165e1c1eEEe"  # PLACEHOLDER
TOKEN_ALLOWLIST_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
GPV2_SETTLEMENT_ADDRESS = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
GNO = "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb"
COW = "0x177127622c4A00F3d409B75571e12cB3c8973d3c"
WETH = "0x6A023CCd1ff6F2045C3309768eAd9E68F978f6e1"
SAFE = "0x4d18815D14fe5c3304e87B3FA18318baa5c23820"
WXDAI = "0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d"

MONITORED_TOKENS = [GNO, COW, WETH, SAFE, WXDAI]


# ABI
def _load_abi(abi_name: str) -> Dict:
    """Load ABI from json file"""
    abi_path = Path(os.environ.get(f"{abi_name}_ABI_FILEPATH", f"./abi/{abi_name}.json"))
    with open(abi_path) as f:
        return json.load(f)


# Contracts
GPV2_SETTLEMENT_CONTRACT = Contract(GPV2_SETTLEMENT_ADDRESS, abi=_load_abi("GPv2Settlement"))
TOKEN_ALLOWLIST_CONTRACt = Contract(TOKEN_ALLOWLIST_ADDRESS, abi=_load_abi("TokenAllowlist"))

# ABI
GPV2_ORDER_ABI = _load_abi("GPv2Order")

# API
API_BASE_URL = "https://api.cow.fi/xdai/api/v1"
API_HEADERS = {"accept": "application/json", "Content-Type": "application/json"}

# Variables
START_BLOCK = int(os.environ.get("START_BLOCK", chain.blocks.head.number))
HISTORICAL_BLOCK_STEP = int(os.environ.get("HISTORICAL_BLOCK_STEP", 720))
EXTENSION_INTERVAL = int(os.environ.get("EXTENSION_INTERVAL", 6))


# Local storage helper functions
def _load_trades_db() -> pd.DataFrame:
    """Load trades database from CSV file or create new if doesn't exist"""
    dtype = {
        "block_number": int,
        "owner": str,
        "sellToken": str,
        "buyToken": str,
        "sellAmount": str,
        "buyAmount": str,
    }

    df = (
        pd.read_csv(TRADE_FILEPATH, dtype=dtype)
        if os.path.exists(TRADE_FILEPATH)
        else pd.DataFrame(columns=dtype.keys()).astype(dtype)
    )
    return df


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


def _load_orders_db() -> pd.DataFrame:
    """
    Load orders database from CSV file or create new if doesn't exist
    """
    dtype = {
        "orderUid": str,
        "signed": bool,
        "sellToken": str,
        "buyToken": str,
        "receiver": str,
        "sellAmount": str,
        "buyAmount": str,
        "validTo": int,
    }

    df = (
        pd.read_csv(ORDERS_FILEPATH, dtype=dtype)
        if os.path.exists(ORDERS_FILEPATH)
        else pd.DataFrame(columns=dtype.keys()).astype(dtype)
    )
    return df


def _save_orders_db(df: pd.DataFrame) -> None:
    """Save orders to CSV file"""
    os.makedirs(os.path.dirname(ORDERS_FILEPATH), exist_ok=True)
    df.to_csv(ORDERS_FILEPATH, index=False)


# Historical log helper functions
def get_canonical_pair(token_a: str, token_b: str) -> tuple[str, str]:
    """Return tokens in canonical order (alphabetically by address)"""
    return (token_a, token_b) if token_a.lower() < token_b.lower() else (token_b, token_a)


def calculate_price(sell_amount: str, buy_amount: str) -> float:
    """Calculate price from amounts"""
    return int(sell_amount) / int(buy_amount)


def _process_trade_log(log) -> Dict:
    """Process trade log with price calculation"""
    token_a, token_b = get_canonical_pair(log.sellToken, log.buyToken)
    price = calculate_price(log.sellAmount, log.buyAmount)

    if token_a != log.sellToken:
        price = 1 / price

    return {
        "block_number": log.block_number,
        "owner": log.owner,
        "sellToken": log.sellToken,
        "buyToken": log.buyToken,
        "sellAmount": str(log.sellAmount),
        "buyAmount": str(log.buyAmount),
        "token_a": token_a,
        "token_b": token_b,
        "price": price,
    }


def _get_historical_trades(
    settlement_contract,
    start_block: int,
    stop_block: int = chain.blocks.head.number,
):
    """Get historical trades for monitored token pairs"""
    log_filter = LogFilter(
        addresses=[settlement_contract.address],
        events=[settlement_contract.Trade.abi],
        start_block=start_block,
        stop_block=stop_block,
    )

    for log in accounts.provider.get_contract_logs(log_filter):
        if log.sellToken in MONITORED_TOKENS and log.buyToken in MONITORED_TOKENS:
            yield log


def _process_historical_trades(
    settlement_contract, start_block: int, stop_block: int
) -> List[Dict]:
    """Process historical trades and store in database"""
    trades = []

    for log in _get_historical_trades(settlement_contract, start_block, stop_block):
        trades.append(_process_trade_log(log))

    if trades:
        existing_trades = _load_trades_db()
        all_trades = pd.concat([existing_trades, pd.DataFrame(trades)], ignore_index=True)

        _save_trades_db(all_trades)

    return trades


def extend_historical_trades() -> None:
    """Extend trades.csv data further back in history"""
    trades_df = _load_trades_db()

    if len(trades_df) == 0:
        oldest_block = chain.blocks.head.number
    else:
        oldest_block = trades_df["block_number"].min()

    new_trades = _process_historical_trades(
        GPV2_SETTLEMENT_CONTRACT,
        start_block=oldest_block - HISTORICAL_BLOCK_STEP,
        stop_block=oldest_block - 1,
    )

    new_trades_df = pd.DataFrame(new_trades)
    all_trades = pd.concat([new_trades_df, trades_df])
    all_trades = all_trades.sort_values("block_number", ascending=True)

    _save_trades_db(all_trades)


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
        "feeAmount": "0",
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


def _submit_order(order_payload: Dict) -> str:
    """
    Submit order to CoW API
    Returns order UID string or raises exception
    """
    try:
        response = requests.post(
            url=f"{API_BASE_URL}/orders", headers=API_HEADERS, json=order_payload
        )
        response.raise_for_status()
        return response.text.strip('"')
    except requests.RequestException as e:
        if e.response is not None:
            error_data = e.response.json()
            error_type = error_data.get("errorType", "Unknown")
            error_description = error_data.get("description", str(e))
            raise Exception(f"{error_type} - {error_description}")
        raise Exception(f"Order request failed: {e}")


def _save_order(order_uid: str, order_payload: Dict, signed: bool) -> None:
    """Save order to database with individual fields"""
    df = _load_orders_db()

    new_order = {
        "orderUid": order_uid,
        "signed": signed,
        "sellToken": order_payload["sellToken"],
        "buyToken": order_payload["buyToken"],
        "receiver": order_payload["receiver"],
        "sellAmount": order_payload["sellAmount"],
        "buyAmount": order_payload["buyAmount"],
        "validTo": order_payload["validTo"],
    }

    df = pd.concat([df, pd.DataFrame([new_order])], ignore_index=True)
    _save_orders_db(df)


def create_and_submit_order(
    sell_token: str,
    buy_token: str,
    sell_amount: str,
) -> tuple[str | None, str | None]:
    """
    Create and submit order to CoW API
    Returns (order_uid, error_message)
    """
    try:
        quote_payload = _construct_quote_payload(
            sell_token=sell_token, buy_token=buy_token, sell_amount=sell_amount
        )
        quote = _get_quote(quote_payload)
        click.echo(f"Quote received: {quote}")

        order_payload = _construct_order_payload(quote)
        click.echo(f"Submitting order payload: {order_payload}")

        order_uid = _submit_order(order_payload)
        click.echo(f"Order response: {order_uid}")

        _save_order(order_uid, order_payload, False)

        return order_uid, None

    except Exception as e:
        return None, str(e)


# Silverback bot
@bot.on_startup()
def bot_startup(startup_state: StateSnapshot):
    """Initialize bot state and historical data"""
    block_db = _load_block_db()
    last_processed_block = block_db["last_processed_block"]

    _process_historical_trades(
        GPV2_SETTLEMENT_CONTRACT,
        start_block=last_processed_block,
        stop_block=chain.blocks.head.number,
    )

    _save_block_db({"last_processed_block": chain.blocks.head.number})
    bot.state.last_extension_block = chain.blocks.head.number
    return {"message": "Starting...", "block_number": startup_state.last_block_seen}


@bot.on_(chain.blocks)
def exec_block(block: BlockAPI, context: Annotated[Context, TaskiqDepends()]):
    _save_block_db({"last_processed_block": block.number})

    if block.number - bot.state.last_extension_block >= EXTENSION_INTERVAL:
        extend_historical_trades()
        bot.state.last_extension_block = block.number


#    """Execute block handler"""
#    order_uid, error = create_and_submit_order(
#        sell_token=GNO, buy_token=COW, sell_amount="20000000000000000000"
#    )
#
#    if error:
#        click.echo(f"Order failed: {error}")
#    else:
#        click.echo(f"Order submitted successfully. UID: {order_uid}")
