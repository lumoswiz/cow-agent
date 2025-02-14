import { type Chain, type Address, encodeFunctionData } from "viem";
import { getSafe, getContractAddress, SUPPORTED_CHAINS, CHAIN_ID } from "./config";
import { SAFE_ABI } from "../../deployments/abis";
import { OperationType, type MetaTransactionData } from "@safe-global/types-kit";

async function enableModule(safeAddress: Address) {
  try {
    const safe = await getSafe(safeAddress);
    console.log("Safe instance created");

    const tradingModuleProxy = getContractAddress("tradingModuleProxy");
    console.log("Trading module proxy:", tradingModuleProxy);

    const enableModuleData = encodeFunctionData({
      abi: SAFE_ABI,
      functionName: "enableModule",
      args: [tradingModuleProxy],
    });
    console.log("Enable module data created");

    const enableModuleTx: MetaTransactionData = {
      to: safeAddress,
      value: "0",
      data: enableModuleData,
      operation: OperationType.Call,
    };
    console.log("Transaction data prepared:", enableModuleTx);

    const safeModuleTx = await safe.createTransaction({
      transactions: [enableModuleTx],
    });
    console.log("Safe transaction created");

    const signedEnableModuleTx = await safe.signTransaction(safeModuleTx);
    console.log("Transaction signed");

    const enableModuleTxHash = await safe.executeTransaction(signedEnableModuleTx);
    console.log("Transaction executed:", enableModuleTxHash);

    return enableModuleTxHash.hash;
  } catch (error) {
    console.error("Error in enableModule:", error);
    throw error;
  }
}

export { enableModule };

if (require.main === module) {
  console.log("Script starting...");

  const args = process.argv.slice(2);
  console.log("Command args:", args);

  // Fix argument parsing
  const chainId = args[args.indexOf("--chain") + 1];
  console.log("Parsed chain ID:", chainId);

  if (!chainId) {
    throw new Error("Please provide --chain parameter");
  }

  const safeAddress = process.env.SAFE_ADDRESS as Address;
  console.log("Safe address from env:", safeAddress);

  if (!safeAddress) {
    throw new Error("SAFE_ADDRESS env variable not set");
  }

  enableModule(safeAddress)
    .then(() => process.exit(0))
    .catch((error) => {
      console.error("Error:", error);
      process.exit(1);
    });
}
