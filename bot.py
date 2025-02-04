import json

import Path
from ape import Contract
from silverback import SilverbackBot

# Initialize bot
bot = SilverbackBot()

# Load GPv2Settlement ABI
abi_path = Path("./abi/GPv2Settlement.json")
with open(abi_path) as f:
    gpv2_settlement_abi = json.load(f)

# Gnosis Chain Addresses
GPV2_SETTLEMENT_ADDRESS = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
GNO_ADDRESS = "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb"

# Contracts
GPV2_SETTLEMENT_CONTRACT = Contract(GPV2_SETTLEMENT_ADDRESS, abi=gpv2_settlement_abi)
