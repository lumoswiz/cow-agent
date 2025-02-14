import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Dict, List

import click
import numpy as np
import pandas as pd
import requests
from ape import Contract, accounts, chain
from ape.api import BlockAPI
from ape.types import LogFilter
from ape_ethereum import multicall
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from silverback import SilverbackBot, StateSnapshot
from taskiq import Context, TaskiqDepends, TaskiqState

# Initialize bot
bot = SilverbackBot()

# Config
PROMPT_AUTOSIGN = bot.signer
ENCOURAGE_TRADE = os.environ.get("ENCOURAGE_TRADE", False)

# File path configuration
TRADE_FILEPATH = os.environ.get("TRADE_FILEPATH", ".db/trades.csv")
BLOCK_FILEPATH = os.environ.get("BLOCK_FILEPATH", ".db/block.csv")
ORDERS_FILEPATH = os.environ.get("ORDERS_FILEPATH", ".db/orders.csv")
DECISIONS_FILEPATH = os.environ.get("DECISIONS_FILEPATH", ".db/decisions.csv")
REASONING_FILEPATH = os.environ.get("REASONING_FILEPATH", ".db/reasoning.csv")

# Addresses
SAFE_ADDRESS = "0xbc3c7818177dA740292659b574D48B699Fdf0816"
TOKEN_ALLOWLIST_ADDRESS = "0x98a4351d926e6274829c3807f39D9a7037462589"
GPV2_SETTLEMENT_ADDRESS = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
TRADING_MODULE_ADDRESS = "0xF11bC1ff8Ab8Cc297e5a1f1A51B8d1792E99D648"

GNO = "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb"
COW = "0x177127622c4A00F3d409B75571e12cB3c8973d3c"
WXDAI = "0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d"
MONITORED_TOKENS = [GNO, COW, WXDAI]

MINIMUM_TOKEN_BALANCES = {
    GNO: 116,
    COW: 10e18,
    WXDAI: 5e18,
}


# ABI
def _load_abi(abi_name: str) -> Dict:
    """Load ABI from json file"""
    abi_path = Path(os.environ.get(f"{abi_name}_ABI_FILEPATH", f"./abi/{abi_name}.json"))
    with open(abi_path) as f:
        return json.load(f)


# Contracts
GPV2_SETTLEMENT_CONTRACT = Contract(GPV2_SETTLEMENT_ADDRESS, abi=_load_abi("GPv2Settlement"))
TOKEN_ALLOWLIST_CONTRACT = Contract(TOKEN_ALLOWLIST_ADDRESS, abi=_load_abi("TokenAllowlist"))
TRADING_MODULE_CONTRACT = Contract(TRADING_MODULE_ADDRESS, abi=_load_abi("TradingModule"))


# API
API_BASE_URL = "https://api.cow.fi/xdai/api/v1"
API_HEADERS = {"accept": "application/json", "Content-Type": "application/json"}

# Variables
START_BLOCK = int(os.environ.get("START_BLOCK", chain.blocks.head.number))
HISTORICAL_BLOCK_STEP = int(os.environ.get("HISTORICAL_BLOCK_STEP", 720))
EXTENSION_INTERVAL = int(os.environ.get("EXTENSION_INTERVAL", 6))
TRADING_BLOCK_COOLDOWN = int(os.environ.get("TRADING_BLOCK_COOLDOWN", 360))
SYSTEM_PROMPT = Path("./system_prompt.txt").read_text().strip()


# Agents
class TradeMetrics(BaseModel):
    token_a: str
    token_b: str
    last_price: float
    min_price: float
    max_price: float
    volume_buy: float
    volume_sell: float
    up_moves_ratio: float
    max_up_streak: int
    max_down_streak: int
    trade_count: int


def _compute_metrics(df: pd.DataFrame, lookback_blocks: int = 15000) -> List[TradeMetrics]:
    """Compute trading metrics for all token pairs in filtered DataFrame"""
    if df.empty:
        return []

    latest_block = df.block_number.max()
    filtered_df = df[df.block_number >= (latest_block - lookback_blocks)]

    if filtered_df.empty:
        return []

    pairs_df = filtered_df[["token_a", "token_b"]].drop_duplicates()
    metrics_list = []

    for _, pair in pairs_df.iterrows():
        try:
            pair_df = filtered_df[
                (filtered_df.token_a == pair.token_a) & (filtered_df.token_b == pair.token_b)
            ].sort_values("block_number")

            pair_df = pair_df[pair_df.price.notna()]

            if pair_df.empty:
                continue

            try:
                volume_buy = pair_df.buyAmount.astype(float).sum()
                volume_sell = pair_df.sellAmount.astype(float).sum()
            except (ValueError, TypeError):
                volume_buy = volume_sell = 0.0

            prices = pair_df.price.values

            up_moves_ratio = 0.5
            max_up_streak = 0
            max_down_streak = 0

            if len(prices) >= 2:
                price_changes = np.sign(np.diff(prices))
                non_zero_moves = price_changes[price_changes != 0]

                if len(non_zero_moves) > 0:
                    up_moves_ratio = np.mean(non_zero_moves > 0)

                if len(price_changes) > 1:
                    try:
                        change_points = np.where(price_changes[1:] != price_changes[:-1])[0] + 1
                        if len(change_points) > 0:
                            streaks = np.split(price_changes, change_points)
                            max_up_streak = max(
                                (len(s) for s in streaks if len(s) > 0 and s[0] > 0), default=0
                            )
                            max_down_streak = max(
                                (len(s) for s in streaks if len(s) > 0 and s[0] < 0), default=0
                            )
                    except Exception:
                        pass

            metrics = TradeMetrics(
                token_a=pair.token_a,
                token_b=pair.token_b,
                last_price=float(prices[-1]),
                min_price=float(np.min(prices)),
                max_price=float(np.max(prices)),
                volume_buy=float(volume_buy),
                volume_sell=float(volume_sell),
                up_moves_ratio=float(up_moves_ratio),
                max_up_streak=int(max_up_streak),
                max_down_streak=int(max_down_streak),
                trade_count=len(pair_df),
            )
            metrics_list.append(metrics)
        except Exception as e:
            click.echo(f"Error processing pair {pair.token_a}-{pair.token_b}: {str(e)}")
            continue

    return metrics_list


class TradeContext(BaseModel):
    """Context for agent analysis"""

    token_balances: Dict[str, int]
    metrics: List[TradeMetrics]
    prior_decisions: List[Dict]
    lookback_blocks: int = 15000


@dataclass
class AgentDependencies:
    """Dependencies for trading agent"""

    trade_ctx: TradeContext
    sell_token: str | None


class AgentResponse(BaseModel):
    """Structured response from agent"""

    should_trade: bool
    buy_token: str | None = None
    reasoning: str


class AgentDecision(BaseModel):
    """Trading decision with metrics snapshot"""

    block_number: int
    should_trade: bool
    sell_token: str | None = None
    buy_token: str | None = None
    metrics_snapshot: List[TradeMetrics]
    profitable: int = 2
    valid: bool = False


trading_agent = Agent(
    "anthropic:claude-3-sonnet-20240229",
    deps_type=AgentDependencies,
    result_type=AgentResponse,
    system_prompt=SYSTEM_PROMPT,
)

TOKEN_NAMES = {
    GNO: "GNO",
    COW: "COW",
    WXDAI: "WXDAI",
}


@trading_agent.tool_plain(retries=3)
def get_token_name(address: str) -> str:
    """Return a human-readable token name for the provided address."""
    try:
        return TOKEN_NAMES.get(address, address)
    except Exception as e:
        print(f"[get_token_name] failed with error: {e}")
        raise


@trading_agent.tool(retries=3)
def get_eligible_buy_tokens(ctx: RunContext[AgentDependencies]) -> List[str]:
    """Return a list of tokens eligible for purchase (excluding the sell token)."""
    try:
        sell_token = ctx.deps.sell_token
        return [token for token in MONITORED_TOKENS if token != sell_token]
    except Exception as e:
        print(f"[get_eligible_buy_tokens] failed with error: {e}")
        raise


@trading_agent.tool_plain(retries=3)
def get_token_type(token: str) -> Dict:
    """Determine if the token is stable or volatile."""
    try:
        is_stable = token == WXDAI
        return {
            "token": get_token_name(token),
            "is_stable": is_stable,
            "expected_behavior": "USD value stable, good for preserving value"
            if is_stable
            else "USD value can fluctuate",
        }
    except Exception as e:
        print(f"[get_token_type] failed with error: {e}")
        raise


@trading_agent.tool(retries=3)
def get_trading_context(ctx: RunContext[AgentDependencies]) -> TradeContext:
    """Return the trading context from the agent's dependencies."""
    try:
        return ctx.deps.trade_ctx
    except Exception as e:
        print(f"[get_trading_context] failed with error: {e}")
        raise


@trading_agent.tool(retries=3)
def get_sell_token(ctx: RunContext[AgentDependencies]) -> str | None:
    """Return the sell token from the agent's dependencies."""
    try:
        return ctx.deps.sell_token
    except Exception as e:
        print(f"[get_sell_token] failed with error: {e}")
        raise


@trading_agent.system_prompt
def encourage_trade(ctx: RunContext[AgentDependencies]) -> str:
    if ENCOURAGE_TRADE:
        return (
            f"I encourage you to sell {ctx.deps.sell_token}. Use the tool "
            "'get_eligible_buy_tokens' to get a list of eligible buy tokens, and from that "
            "list, pick the one that is most promising despite current market conditions. "
            "Remember, we're experimenting and learning—consider unconventional choices."
        )
    else:
        return ""


def _get_token_balances() -> Dict[str, int]:
    """Get balances of monitored tokens using multicall"""
    token_contracts = [Contract(token_address) for token_address in MONITORED_TOKENS]

    call = multicall.Call()
    for contract in token_contracts:
        call.add(contract.balanceOf, SAFE_ADDRESS)

    results = list(call())

    return {token_address: balance for token_address, balance in zip(MONITORED_TOKENS, results)}


def _create_trade_context(
    trades_df: pd.DataFrame, decisions_df: pd.DataFrame, lookback_blocks: int = 15000
) -> TradeContext:
    """Create TradeContext with all required data"""
    prior_decisions = decisions_df.tail(3).copy()
    prior_decisions["metrics_snapshot"] = prior_decisions["metrics_snapshot"].apply(json.loads)

    return TradeContext(
        token_balances=_get_token_balances(),
        metrics=_compute_metrics(trades_df, lookback_blocks),
        prior_decisions=prior_decisions.to_dict("records"),
        lookback_blocks=lookback_blocks,
    )


def _select_sell_token() -> str | None:
    """
    Select token to sell based on current balances and minimum thresholds.
    Returns the token address that has a balance above threshold, or None if no token qualifies.
    """
    balances = _get_token_balances()
    valid_tokens = [
        token for token in MONITORED_TOKENS if balances[token] > MINIMUM_TOKEN_BALANCES[token]
    ]
    return valid_tokens[0] if valid_tokens else None


def _build_decision(
    block_number: int,
    response: AgentResponse,
    metrics: List[TradeMetrics],
    sell_token: str,
) -> AgentDecision:
    """Build decision dict from agent response"""
    return AgentDecision(
        block_number=block_number,
        should_trade=response.should_trade,
        sell_token=sell_token if response.should_trade else None,
        buy_token=response.buy_token if response.should_trade else None,
        metrics_snapshot=metrics,
        reasoning=response.reasoning,
        valid=False,
    )


def _validate_decision(decision: AgentDecision) -> bool:
    """
    Validate decision structure and buy token validity
    """
    if not decision.should_trade or decision.sell_token is None or decision.buy_token is None:
        return False

    if decision.buy_token not in MONITORED_TOKENS or decision.buy_token == decision.sell_token:
        click.echo(f"Invalid buy token: buy={decision.buy_token}")
        return False

    return True


def _save_decision(decision: AgentDecision) -> pd.DataFrame:
    """Save validated decision to database"""
    decisions_df = _load_decisions_db()

    new_decision = {
        "block_number": decision.block_number,
        "should_trade": decision.should_trade,
        "sell_token": decision.sell_token,
        "buy_token": decision.buy_token,
        "metrics_snapshot": json.dumps([m.dict() for m in decision.metrics_snapshot]),
        "profitable": decision.profitable,
        "valid": decision.valid,
    }

    decisions_df = pd.concat([decisions_df, pd.DataFrame([new_decision])], ignore_index=True)
    _save_decisions_db(decisions_df)
    return decisions_df


def _update_latest_decision_outcome(
    decisions_df: pd.DataFrame, final_price: float | None = None
) -> pd.DataFrame:
    """Update most recent decision with outcome data"""
    if decisions_df.empty:
        return decisions_df

    latest_idx = decisions_df.index[-1]
    latest_decision = decisions_df.iloc[-1]

    if latest_decision.should_trade:
        if final_price is None:
            return decisions_df
        else:
            metrics = json.loads(latest_decision.metrics_snapshot)
            initial_price = next(
                m["last_price"]
                for m in metrics
                if m["token_a"] == latest_decision.sell_token
                and m["token_b"] == latest_decision.buy_token
            )

            profitable = (
                final_price > initial_price
                if latest_decision.sell_token == metrics[0]["token_a"]
                else final_price < initial_price
            )

            decisions_df.loc[latest_idx, "profitable"] = int(profitable)

        _save_decisions_db(decisions_df)

    return decisions_df


def _save_reasoning(block_number: int, reasoning: str) -> None:
    """Save agent reasoning to JSON file"""
    os.makedirs(os.path.dirname(REASONING_FILEPATH), exist_ok=True)

    entry = {"block_number": block_number, "reasoning": reasoning}

    with open(REASONING_FILEPATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


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


def _load_block_db() -> int:
    """Load the last processed block from CSV file or create new if doesn't exist"""
    df = (
        pd.read_csv(BLOCK_FILEPATH)
        if os.path.exists(BLOCK_FILEPATH)
        else pd.DataFrame({"last_processed_block": [START_BLOCK]})
    )
    return df["last_processed_block"].iloc[0]


def _save_block_db(block_number: int) -> None:
    """Save the last processed block to CSV file"""
    os.makedirs(os.path.dirname(BLOCK_FILEPATH), exist_ok=True)
    df = pd.DataFrame({"last_processed_block": [block_number]})
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


def _load_decisions_db() -> pd.DataFrame:
    """Load decisions database from CSV file"""
    dtype = {
        "block_number": int,
        "should_trade": bool,
        "sell_token": str,
        "buy_token": str,
        "metrics_snapshot": str,
        "profitable": int,
        "valid": bool,
    }

    df = (
        pd.read_csv(DECISIONS_FILEPATH, dtype=dtype)
        if os.path.exists(DECISIONS_FILEPATH)
        else pd.DataFrame(columns=dtype.keys()).astype(dtype)
    )
    return df


def _save_decisions_db(df: pd.DataFrame) -> None:
    """Save decisions to CSV file"""
    df = df.copy()
    os.makedirs(os.path.dirname(DECISIONS_FILEPATH), exist_ok=True)
    df.to_csv(DECISIONS_FILEPATH, index=False)


# Historical log helper functions
def _get_canonical_pair(token_a: str, token_b: str) -> tuple[str, str]:
    """Return tokens in canonical order (alphabetically by address)"""
    return (token_a, token_b) if token_a.lower() < token_b.lower() else (token_b, token_a)


def _calculate_price(sell_amount: str, buy_amount: str) -> float:
    """Calculate price from amounts"""
    return int(sell_amount) / int(buy_amount)


def _process_trade_log(log) -> Dict:
    """
    Process trade log and compute canonical price as:
       canonical price = (quote token amount) / (base token amount)
    where (token_a, token_b) is the canonical pair sorted lexicographically.
    """
    token_a, token_b = _get_canonical_pair(log.sellToken, log.buyToken)

    if log.sellToken == token_a:
        price = int(log.buyAmount) / int(log.sellAmount)
    else:
        price = int(log.sellAmount) / int(log.buyAmount)

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


def _catch_up_trades(current_block: int, next_decision_block: int, buffer_blocks: int = 5) -> None:
    """
    Catch up on trade events from last processed block until shortly before next decision
    """
    trades_df = _load_trades_db()
    last_processed_block = trades_df["block_number"].max() if not trades_df.empty else START_BLOCK

    target_block = min(current_block, next_decision_block - buffer_blocks)

    if target_block <= last_processed_block:
        return

    _process_historical_trades(
        GPV2_SETTLEMENT_CONTRACT, start_block=last_processed_block + 1, stop_block=target_block
    )


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
        "sellAmountBeforeFee": str(sell_amount),
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


def sign_order(order_uid: str, order_payload: dict) -> None:
    """Sign order via TradingModule contract"""

    BALANCE_ERC20 = "0x5a28e9363bb942b639270062aa6bb295f434bcdfc42c97267bf003f272060dc9"
    KIND_SELL = "0xf3b277728b3fee749481eb3e0b3b48980dbbab78658fc419025cb16eee346775"

    TRADING_MODULE_CONTRACT.setOrder(
        order_uid,
        (
            order_payload["sellToken"],
            order_payload["buyToken"],
            order_payload["receiver"],
            order_payload["sellAmount"],
            order_payload["buyAmount"],
            order_payload["validTo"],
            order_payload["appDataHash"],
            order_payload["feeAmount"],
            KIND_SELL,
            order_payload["partiallyFillable"],
            BALANCE_ERC20,
            BALANCE_ERC20,
        ),
        True,
        sender=bot.signer,
    )


def create_submit_and_sign_order(
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
        order_uid = _submit_order(order_payload)
        click.echo(f"Order submitted: {order_uid}")

        _save_order(order_uid, order_payload, False)

        click.echo("Signing order...")
        sign_order(order_uid, order_payload)

        return order_uid, None

    except Exception as e:
        return None, str(e)


# Silverback bot
@bot.on_startup()
def bot_startup(startup_state: StateSnapshot):
    """Initialize bot state and historical data"""
    if PROMPT_AUTOSIGN and click.confirm("Enable autosign?"):
        bot.signer.set_autosign(enabled=True)

    # Process historical trades
    block_db = _load_block_db()
    last_processed_block = block_db
    _save_block_db(chain.blocks.head.number)
    _process_historical_trades(
        GPV2_SETTLEMENT_CONTRACT,
        start_block=last_processed_block,
        stop_block=chain.blocks.head.number,
    )

    # Initialize bot state

    decisions_df = _load_decisions_db()
    if decisions_df.empty:
        bot.state.next_decision_block = chain.blocks.head.number
    else:
        bot.state.next_decision_block = decisions_df.iloc[-1].block_number + TRADING_BLOCK_COOLDOWN

    bot.state.can_trade = False
    bot.state.sell_token = None

    return {"message": "Starting...", "block_number": startup_state.last_block_seen}


@bot.on_worker_startup()
def worker_startup(state: TaskiqState):
    """Initialize worker state"""
    state.agent = trading_agent
    state.trades_df = _load_trades_db()
    state.decisions_df = _load_decisions_db()


@bot.on_(chain.blocks)
def update_state(block: BlockAPI, context: Annotated[Context, TaskiqDepends()]):
    """Update trade history and decision outcomes"""
    click.echo(f"\n[{block.number}] Starting state update...")
    _save_block_db(block.number)
    bot.state.can_trade = False
    click.echo(f"[{block.number}] State: trade={bot.state.can_trade}, sell={bot.state.sell_token}")

    if block.number < bot.state.next_decision_block:
        click.echo(f"[{block.number}] Skip - next decision at {bot.state.next_decision_block}")
        return {"message": "Skipped - before cooldown", "block": block.number}

    click.echo(f"[{block.number}] Past cooldown, catching up trades...")
    _catch_up_trades(current_block=block.number, next_decision_block=bot.state.next_decision_block)

    bot.state.sell_token = _select_sell_token()
    click.echo(f"[{block.number}] Sell token: {bot.state.sell_token}")

    if not bot.state.sell_token:
        click.echo(f"[{block.number}] No eligible sell tokens found")
        return {"message": "No eligible sell tokens", "block": block.number}

    if context.state.decisions_df.empty:
        click.echo(f"[{block.number}] No previous decisions, enabling trading")
        bot.state.can_trade = True
        return {"message": "No previous decisions", "can_trade": True}

    latest_decision = context.state.decisions_df.iloc[-1]
    msg = (
        f"[{block.number}] Latest: "
        f"trade={latest_decision.should_trade}, "
        f"block={latest_decision.block_number}"
    )
    click.echo(msg)

    if not latest_decision.should_trade:
        click.echo(f"[{block.number}] Last decision wasn't a trade, enabling trading")
        bot.state.can_trade = True
        return {
            "message": "Last decision was not a trade",
            "can_trade": True,
            "last_decision_block": latest_decision.block_number,
        }

    click.echo(f"[{block.number}] Creating trade context for outcome update...")
    trade_ctx = _create_trade_context(
        trades_df=context.state.trades_df, decisions_df=context.state.decisions_df
    )

    matching_metrics = [
        m.last_price
        for m in trade_ctx.metrics
        if m.token_a == latest_decision.sell_token and m.token_b == latest_decision.buy_token
    ]

    if not matching_metrics:
        click.echo(
            f"[{block.number}] No metrics {latest_decision.sell_token}-{latest_decision.buy_token}"
        )
        context.state.decisions_df = _update_latest_decision_outcome(
            decisions_df=context.state.decisions_df,
            final_price=None,
        )
        bot.state.can_trade = True
        return {
            "message": "Marked as unknown outcome",
            "block": block.number,
            "can_trade": True,
        }

    click.echo(f"[{block.number}] Updating previous decision outcome...")
    context.state.decisions_df = _update_latest_decision_outcome(
        decisions_df=context.state.decisions_df, final_price=matching_metrics[0]
    )

    bot.state.can_trade = True
    click.echo(f"[{block.number}] State: trade={bot.state.can_trade}, sell={bot.state.sell_token}")
    return {
        "message": "Updated previous decision outcome",
        "can_trade": True,
        "last_decision_block": latest_decision.block_number,
    }


@bot.on_(chain.blocks)
def make_trading_decision(block: BlockAPI, context: Annotated[Context, TaskiqDepends()]):
    """Make and execute trading decisions"""
    click.echo(f"\n[{block.number}] Starting trading decision...")
    click.echo(f"[{block.number}] State: trade={bot.state.can_trade}, sell={bot.state.sell_token}")

    if not bot.state.can_trade:
        click.echo(f"[{block.number}] Trading not enabled, skipping")
        return {"message": "Trading not enabled", "block": block.number}

    click.echo(f"[{block.number}] Creating trade context...")
    trade_ctx = _create_trade_context(
        trades_df=context.state.trades_df, decisions_df=context.state.decisions_df
    )

    click.echo(f"[{block.number}] Running agent with sell_token={bot.state.sell_token}...")
    deps = AgentDependencies(trade_ctx=trade_ctx, sell_token=bot.state.sell_token)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    result = context.state.agent.run_sync(
        "Analyze current market conditions and make a trading decision", deps=deps
    )

    click.echo(
        f"[{block.number}] Agent: trade={result.data.should_trade}, buy={result.data.buy_token}"
    )
    _save_reasoning(block.number, result.data.reasoning)

    decision = _build_decision(
        block_number=block.number,
        response=result.data,
        metrics=trade_ctx.metrics,
        sell_token=bot.state.sell_token,
    )

    decision.valid = _validate_decision(decision)
    click.echo(f"[{block.number}] Decision valid={decision.valid}")
    _save_decision(decision)

    if decision.valid and decision.should_trade:
        click.echo(f"[{block.number}] Order: {decision.sell_token} -> {decision.buy_token}")
        order_uid, error = create_submit_and_sign_order(
            sell_token=decision.sell_token,
            buy_token=decision.buy_token,
            sell_amount=trade_ctx.token_balances[decision.sell_token],
        )
        if error:
            click.echo(f"[{block.number}] Order failed: {error}")
        else:
            click.echo(f"[{block.number}] Order: {order_uid}")

    bot.state.next_decision_block = block.number + TRADING_BLOCK_COOLDOWN
    click.echo(f"[{block.number}] Next decision: {bot.state.next_decision_block}")

    return {
        "message": "Trading decision made",
        "block": block.number,
        "should_trade": decision.should_trade,
        "sell_token": decision.sell_token,
        "buy_token": decision.buy_token,
        "next_decision_block": bot.state.next_decision_block,
    }
