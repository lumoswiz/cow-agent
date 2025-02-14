import { type Address, encodeFunctionData } from "viem";
import { getSafe, getContractAddress } from "./config";
import { SAFE_ABI } from "../../deployments/abis";
import { OperationType, type MetaTransactionData } from "@safe-global/types-kit";

async function enableModule(safeAddress: Address) {
  try {
    console.log("Starting enable module process using Safe:", safeAddress);

    // Create a Safe instance using the env-provided configuration
    const safe = await getSafe(safeAddress);
    console.log("Safe instance created");

    // Retrieve the trading module proxy address from our deployed contracts store
    const tradingModuleProxy = getContractAddress("tradingModuleProxy");
    console.log("Trading module proxy:", tradingModuleProxy);

    // Build the call data for enabling the module
    const enableModuleData = encodeFunctionData({
      abi: SAFE_ABI,
      functionName: "enableModule",
      args: [tradingModuleProxy],
    });
    console.log("Enable module data created:", enableModuleData);

    // Prepare the meta-transaction data object
    const enableModuleTx: MetaTransactionData = {
      to: safeAddress,
      value: "0",
      data: enableModuleData,
      operation: OperationType.Call,
    };
    console.log("Transaction data prepared:", enableModuleTx);

    // Build the Safe transaction
    const safeModuleTx = await safe.createTransaction({
      transactions: [enableModuleTx],
    });
    console.log("Safe transaction built");

    // Sign the transaction using the locally configured signer (PRIVATE_KEY)
    const signedEnableModuleTx = await safe.signTransaction(safeModuleTx);
    console.log("Transaction signed");

    // Execute the transaction and obtain the transaction hash
    const enableModuleTxHash = await safe.executeTransaction(signedEnableModuleTx);
    console.log("Transaction executed successfully:", enableModuleTxHash);

    return enableModuleTxHash.hash;
  } catch (error) {
    console.error("Error in enableModule:", error);
    throw error;
  }
}

export { enableModule };

if (require.main === module) {
  console.log("Running enable-module script...");
  const safeAddress = process.env.SAFE_ADDRESS as Address;
  console.log("Safe address from env:", safeAddress);

  if (!safeAddress) {
    throw new Error("SAFE_ADDRESS env variable not set");
  }

  enableModule(safeAddress)
    .then(() => process.exit(0))
    .catch((error) => {
      console.error("Execution error:", error);
      process.exit(1);
    });
}
