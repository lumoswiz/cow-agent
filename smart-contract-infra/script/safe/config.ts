import { createWalletClient, http, publicActions, type Address, type Chain } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { gnosis, base, arbitrum, mainnet, sepolia, anvil } from "viem/chains";
import Safe from "@safe-global/protocol-kit";
import fs from "fs";
import path from "path";

export const SIGNER_PRIVATE_KEY = process.env.PRIVATE_KEY as `0x${string}`;
if (!SIGNER_PRIVATE_KEY) {
  throw new Error("Please set your PRIVATE_KEY env variable");
}
export const SIGNER_ACCOUNT = privateKeyToAccount(SIGNER_PRIVATE_KEY);

type ChainIds = 42161 | 8453 | 100 | 1 | 11155111 | 31337;

export const RPC_URLS: Record<ChainIds, string> = {
  [arbitrum.id]: "https://rpc.ankr.com/arbitrum",
  [base.id]: "https://rpc.ankr.com/base",
  [gnosis.id]: "https://rpc.ankr.com/gnosis",
  [mainnet.id]: "https://rpc.ankr.com/eth",
  [sepolia.id]: "https://rpc2.sepolia.org",
  [anvil.id]: "http://localhost:8545",
};

export const SUPPORTED_CHAINS: Record<ChainIds, Chain> = {
  [arbitrum.id]: arbitrum,
  [base.id]: base,
  [gnosis.id]: gnosis,
  [mainnet.id]: mainnet,
  [sepolia.id]: sepolia,
  [anvil.id]: anvil,
};
export const CHAIN_ID = Number(process.env.CHAIN_ID) || 31337;
export const CHAIN = SUPPORTED_CHAINS[CHAIN_ID as ChainIds];
if (!CHAIN) throw new Error(`Chain ${CHAIN_ID} not supported`);

export const getWalletClient = (chain: Chain) => {
  return createWalletClient({
    chain,
    transport: http(RPC_URLS[CHAIN_ID as ChainIds]),
  }).extend(publicActions);
};

export const updateContractsJson = (key: string, value: string) => {
  const contractsPath = path.join(__dirname, "../../deployments/contracts.json");
  const contracts = JSON.parse(fs.readFileSync(contractsPath, "utf8"));

  if (!contracts.chains[CHAIN_ID]) {
    contracts.chains[CHAIN_ID] = {};
  }

  contracts.chains[CHAIN_ID][key] = value;
  fs.writeFileSync(contractsPath, JSON.stringify(contracts, null, 2));
};

export const getSafe = async (safeAddress: string) => {
  return await Safe.init({
    provider: RPC_URLS[CHAIN_ID as ChainIds],
    signer: SIGNER_PRIVATE_KEY,
    safeAddress,
  });
};

export const getContractAddress = (contractKey: string): Address => {
  const contractsPath = path.join(__dirname, "../../deployments/contracts.json");
  const contracts = JSON.parse(fs.readFileSync(contractsPath, "utf8"));

  const address = contracts.chains[CHAIN_ID]?.[contractKey];
  if (!address) {
    throw new Error(`No address found for ${contractKey} on chain ${CHAIN_ID}`);
  }

  return address;
};
