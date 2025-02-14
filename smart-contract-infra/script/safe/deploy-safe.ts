import Safe, { type SafeAccountConfig } from "@safe-global/protocol-kit";
import { type Address } from "viem";
import { SIGNER_ACCOUNT, SIGNER_PRIVATE_KEY, RPC_URLS, updateContractsJson, CHAIN_ID, CHAIN } from "./config";

async function deploySafe(): Promise<{ safeAddress: Address; txHash: `0x${string}` }> {
  const safeAccountConfig: SafeAccountConfig = {
    owners: [SIGNER_ACCOUNT.address],
    threshold: 1,
  };

  const predictedSafe = {
    safeAccountConfig,
  };

  const protocolKit = await Safe.init({
    provider: RPC_URLS[CHAIN_ID as keyof typeof RPC_URLS],
    signer: SIGNER_PRIVATE_KEY,
    predictedSafe,
  });

  const safeAddress = await protocolKit.getAddress();
  const safeDeployTransaction = await protocolKit.createSafeDeploymentTransaction();

  const safeClient = await protocolKit.getSafeProvider().getExternalSigner();
  if (!safeClient) throw "No safeClient";

  const txHash = await safeClient.sendTransaction({
    to: safeDeployTransaction.to,
    value: BigInt(safeDeployTransaction.value),
    data: safeDeployTransaction.data as `0x${string}`,
    chain: CHAIN,
  });

  console.log(`Safe deployed on ${CHAIN.name} at:`, safeAddress);
  console.log("Transaction hash:", txHash);

  updateContractsJson("safe", safeAddress);

  return { safeAddress, txHash };
}

export { deploySafe };
