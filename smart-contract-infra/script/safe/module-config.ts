import { type Chain, type Address, encodeFunctionData } from "viem";
import { getSafe, getContractAddress, SIGNER_ACCOUNT, CHAIN_ID, CHAIN } from "./config";
import { TRADING_MODULE_ABI } from "../../deployments/abis";
import { OperationType, type MetaTransactionData } from "@safe-global/types-kit";

async function configureModule(safeAddress?: Address, tradingModuleAddress?: Address) {
  const finalSafeAddress = safeAddress ?? process.env.SAFE_ADDRESS;
  const finalTradingModule =
    tradingModuleAddress ?? process.env.TRADING_MODULE_ADDRESS ?? getContractAddress("tradingModuleProxy");

  if (!finalSafeAddress) {
    throw new Error("Safe address must be provided via argument or SAFE_ADDRESS env variable");
  }

  const safe = await getSafe(finalSafeAddress);
  const guard = getContractAddress("guard");

  // Set guard transaction
  const setGuardData = encodeFunctionData({
    abi: TRADING_MODULE_ABI,
    functionName: "setGuard",
    args: [guard],
  });

  const setGuardTx: MetaTransactionData = {
    to: finalTradingModule,
    value: "0",
    data: setGuardData,
    operation: OperationType.Call,
  };

  // Set allowed traders transaction
  const setAllowedTradersData = encodeFunctionData({
    abi: TRADING_MODULE_ABI,
    functionName: "setAllowedTraders",
    args: [SIGNER_ACCOUNT.address, true],
  });

  const setAllowedTradersTx: MetaTransactionData = {
    to: finalTradingModule,
    value: "0",
    data: setAllowedTradersData,
    operation: OperationType.Call,
  };

  // Create and execute batch transaction
  const moduleTxs = await safe.createTransaction({
    transactions: [setGuardTx, setAllowedTradersTx],
  });

  const signedModuleTxs = await safe.signTransaction(moduleTxs);
  const moduleTxsHash = await safe.executeTransaction(signedModuleTxs);

  console.log(`Module configured on ${CHAIN.name} Safe at:`, finalSafeAddress);
  console.log("Transaction hash:", moduleTxsHash);

  return moduleTxsHash;
}

export { configureModule };
