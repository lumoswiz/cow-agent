import { type Address, encodeFunctionData } from "viem";
import { getSafe, getContractAddress, SIGNER_ACCOUNT, CHAIN } from "./config";
import { TRADING_MODULE_ABI } from "../../deployments/abis";
import { OperationType, type MetaTransactionData } from "@safe-global/types-kit";

async function configureModule(safeAddress?: Address, tradingModuleAddress?: Address) {
  // Determine addresses either from arguments, env vars, or stored JSON
  const finalSafeAddress = safeAddress ?? process.env.SAFE_ADDRESS;
  const finalTradingModule =
    tradingModuleAddress ?? process.env.TRADING_MODULE_ADDRESS ?? getContractAddress("tradingModuleProxy");

  if (!finalSafeAddress) {
    throw new Error("Safe address must be provided via argument or SAFE_ADDRESS env variable");
  }

  console.log(`Using Safe: ${finalSafeAddress} on ${CHAIN.name}`);

  const safe = await getSafe(finalSafeAddress);
  const guard = getContractAddress("guard");

  // Prepare the call data for setting the guard
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

  // Prepare the call data for setting allowed traders
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

  console.log("Built transaction, now signing...");

  const signedModuleTxs = await safe.signTransaction(moduleTxs);
  console.log("Transaction signed, executing...");

  const moduleTxsHash = await safe.executeTransaction(signedModuleTxs);

  console.log(`Module configured on ${CHAIN.name} Safe at: ${finalSafeAddress}`);
  console.log("Transaction hash:", moduleTxsHash);

  return moduleTxsHash;
}

export { configureModule };

if (require.main === module) {
  console.log("Running module-config script...");
  configureModule()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error("Error configuring module:", error);
      process.exit(1);
    });
}
