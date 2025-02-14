import { type Chain, type Address } from "viem";
import { getWalletClient } from "./config";
import { deploySafe } from "./deploy-safe";
import { deployModule } from "./deploy-module";
import { configureModule } from "./module-config";
import { enableModule } from "./enable-module";

interface DeployAllArgs {
  salt?: bigint;
  existingSafeAddress?: Address;
  existingModuleAddress?: Address;
}

interface DeployAllResult {
  safeAddress: Address;
  moduleAddress: Address;
  safeTxHash?: `0x${string}`;
  moduleTxHash?: `0x${string}`;
  configTxHash?: `0x${string}`;
  enableTxHash?: `0x${string}`;
}

export async function deployAll({
  salt = 0n,
  existingSafeAddress,
  existingModuleAddress,
}: DeployAllArgs): Promise<DeployAllResult> {
  const walletClient = getWalletClient(CHAIN);
  console.log(`Starting deployment sequence on ${CHAIN.name}...`);

  const result: DeployAllResult = {
    safeAddress: existingSafeAddress || "0x",
    moduleAddress: existingModuleAddress || "0x",
  };

  // 1. Deploy Safe
  console.log("\n1. Deploying Safe...");
  if (!existingSafeAddress) {
    const { safeAddress, txHash } = await deploySafe();
    result.safeAddress = safeAddress;
    result.safeTxHash = txHash;
    await walletClient.waitForTransactionReceipt({ hash: txHash });
    console.log("Safe deployed at:", result.safeAddress);
  } else {
    console.log(`Using existing Safe at ${existingSafeAddress}`);
  }

  // 2. Deploy Module
  console.log("\n2. Deploying Trading Module...");
  if (!existingModuleAddress) {
    const { moduleAddress, txHash } = await deployModule(result.safeAddress, salt);
    result.moduleAddress = moduleAddress;
    result.moduleTxHash = txHash;
    await walletClient.waitForTransactionReceipt({ hash: txHash });
    console.log("Trading Module deployed at:", result.moduleAddress);
  } else {
    console.log(`Using existing Module at ${existingModuleAddress}`);
  }

  // 3. Configure Module
  console.log("\n3. Configuring Module...");
  const configTxHash = await configureModule(result.safeAddress);
  result.configTxHash = configTxHash.hash as `0x${string}`;
  await walletClient.waitForTransactionReceipt({
    hash: configTxHash.hash as `0x${string}`,
  });
  console.log("Module configured successfully");

  // 4. Enable Module
  console.log("\n4. Enabling Module...");
  const enableTxHash = await enableModule(result.safeAddress);
  result.enableTxHash = enableTxHash as `0x${string}`;
  await walletClient.waitForTransactionReceipt({
    hash: enableTxHash as `0x${string}`,
  });
  console.log("Module enabled successfully");

  return result;
}
