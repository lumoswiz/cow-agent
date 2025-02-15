import {
  createWalletClient,
  encodeAbiParameters,
  encodeFunctionData,
  http,
  parseAbiParameters,
  parseEther,
  parseGwei,
  publicActions,
} from "viem";
import { privateKeyToAccount, type Address } from "viem/accounts";
import Safe, { type PredictedSafeProps, type SafeAccountConfig } from "@safe-global/protocol-kit";
import { TRADING_MODULE_ABI, MODULE_PROXY_FACTORY_ABI, SAFE_ABI } from "./deployments/abis";
import { OperationType, type MetaTransactionData } from "@safe-global/types-kit";
import { gnosis } from "viem/chains";

const SIGNER_PRIVATE_KEY = process.env.PRIVATE_KEY as `0x${string}`;
if (!SIGNER_PRIVATE_KEY) {
  throw new Error("Please set your PRIVATE_KEY env variable");
}
const SIGNER_ACCOUNT = privateKeyToAccount(SIGNER_PRIVATE_KEY);
const RPC_URL = "https://rpc.ankr.com/gnosis";

export const walletClient = createWalletClient({
  chain: gnosis,
  transport: http("https://rpc.ankr.com/gnosis"),
}).extend(publicActions);

const safeAccountConfig: SafeAccountConfig = {
  owners: [SIGNER_ACCOUNT.address],
  threshold: 1,
};

const predictedSafe: PredictedSafeProps = {
  safeAccountConfig,
};

const protocolKit = await Safe.init({
  provider: RPC_URL,
  signer: SIGNER_PRIVATE_KEY,
  predictedSafe,
});

// PREDICTED SAFE ADDRESS
const safeAddress = await protocolKit.getAddress();
//
// // TRADING MODULE DEPLOYMENT
const MODULE_PROXY_FACTORY = "0x000000000000aDdB49795b0f9bA5BC298cDda236" as Address;
const TRADING_MODULE_MASTERCOPY = "0xDdd11DC80A25563Cb416647821f3BC5Ad75fF1BA" as Address;
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
const salt = 110647465789069657756111682142268192901188952877020749627246931254533522453n;
const { result, request } = await walletClient.simulateContract({
  address: MODULE_PROXY_FACTORY,
  abi: MODULE_PROXY_FACTORY_ABI,
  functionName: "deployModule",
  args: [TRADING_MODULE_MASTERCOPY, initData, salt],
  account: SIGNER_ACCOUNT,
});
const TRADING_MODULE_PROXY_ADDRESS = "0x56be50C311E9B8f805285Bc205e877b5De2dd69B" as Address;

// BUILD SAFE DEPLOYMENT TRANSACTION
const safeDeployTransaction = await protocolKit.createSafeDeploymentTransaction();

// TRANSACTION 1. Enable module transaction
const enableModuleData = encodeFunctionData({
  abi: SAFE_ABI,
  functionName: "enableModule",
  args: [TRADING_MODULE_PROXY_ADDRESS],
});
const enableModuleTx: MetaTransactionData = {
  to: safeAddress,
  value: "0",
  data: enableModuleData,
  operation: OperationType.Call,
};

// TRANSACTION 2. Set guard transaction
const COWSWAP_GUARD = "0xcab68170145d593F15BF398670876CcCBFe173e2" as Address;
const setGuardData = encodeFunctionData({
  abi: TRADING_MODULE_ABI,
  functionName: "setGuard",
  args: [COWSWAP_GUARD],
});
const setGuardTx: MetaTransactionData = {
  to: TRADING_MODULE_PROXY_ADDRESS,
  value: "0",
  data: setGuardData,
  operation: OperationType.Call,
};

// TRANSACTION 3. Enable agent as allowed trader on TradingModule
const setAllowedTradersData = encodeFunctionData({
  abi: TRADING_MODULE_ABI,
  functionName: "setAllowedTraders",
  args: [SIGNER_ACCOUNT.address, true],
});
const setAllowedTradersTx: MetaTransactionData = {
  to: TRADING_MODULE_PROXY_ADDRESS,
  value: "0",
  data: setAllowedTradersData,
  operation: OperationType.Call,
};

// EXECUTE TRANSACTIONS
//  Deploy trading module
const deployTradingModuleHash = await walletClient.writeContract(request);
console.log("Transaction hash for TradingModule deployment:", deployTradingModuleHash);
console.log("TradingModule deployed address:", result);

//deploy safe
const safeClient = await protocolKit.getSafeProvider().getExternalSigner();
if (!safeClient) throw "No safeClient";
const transactionHash = await safeClient.sendTransaction({
  to: safeDeployTransaction.to,
  value: BigInt(safeDeployTransaction.value),
  data: safeDeployTransaction.data as `0x${string}`,
  chain: gnosis,
});
console.log("Transaction hash for Safe deployment:", transactionHash);

const safe = await Safe.init({
  provider: RPC_URL,
  signer: SIGNER_PRIVATE_KEY,
  safeAddress: "0xbDa7d1A5E0F86f7a17654c092DE407f5fF7Dc619",
});

const safeModuleTx = await safe.createTransaction({
  transactions: [enableModuleTx],
});
const signedEnableModuleTx = await safe.signTransaction(safeModuleTx);
const enableModuleTxHash = await safe.executeTransaction(signedEnableModuleTx);
console.log("Module enabled:", enableModuleTxHash);

// Then configure the module
const moduleTxs = await safe.createTransaction({
  transactions: [setGuardTx, setAllowedTradersTx],
});
const signedModuleTxs = await safe.signTransaction(moduleTxs);
const moduleTxsHash = await safe.executeTransaction(signedModuleTxs);
console.log("Module configured:", moduleTxsHash);
