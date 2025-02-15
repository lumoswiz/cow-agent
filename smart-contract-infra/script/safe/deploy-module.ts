import { type Chain, type Address, encodeAbiParameters, encodeFunctionData, parseAbiParameters } from "viem";
import { SIGNER_ACCOUNT, getWalletClient, updateContractsJson, getContractAddress, CHAIN } from "./config";
import { TRADING_MODULE_ABI, MODULE_PROXY_FACTORY_ABI } from "../../deployments/abis";

const MODULE_PROXY_FACTORY = "0x000000000000aDdB49795b0f9bA5BC298cDda236" as Address;
const ZERO_ADDRESS = "0x0000000000000000000000000000000000000000" as Address;

async function deployModule(
  safeAddress: Address,
  salt: bigint = 110647465789069657756111682142268192901188952877020749627246931254533522453n,
): Promise<{ moduleAddress: Address; txHash: `0x${string}` }> {
  if (safeAddress === ZERO_ADDRESS) {
    throw new Error(`Safe address not set for chain ${CHAIN.name}. Deploy a Safe first.`);
  }

  const walletClient = getWalletClient(CHAIN);
  const tradingModuleMastercopy = getContractAddress("tradingModuleMasterCopy");

  const initParams = encodeAbiParameters(parseAbiParameters("address x, address y, address z"), [
    safeAddress,
    safeAddress,
    safeAddress,
  ]);

  const initData = encodeFunctionData({
    abi: TRADING_MODULE_ABI,
    functionName: "setUp",
    args: [initParams],
  });

  const { result, request } = await walletClient.simulateContract({
    address: MODULE_PROXY_FACTORY,
    abi: MODULE_PROXY_FACTORY_ABI,
    functionName: "deployModule",
    args: [tradingModuleMastercopy, initData, salt],
    account: SIGNER_ACCOUNT,
  });

  const moduleAddress = result as Address;
  const txHash = await walletClient.writeContract(request);

  console.log(`Trading Module deployed on ${CHAIN.name} at:`, moduleAddress);
  console.log("Transaction hash:", txHash);

  updateContractsJson("tradingModuleProxy", moduleAddress);

  return { moduleAddress, txHash };
}

export { deployModule };
