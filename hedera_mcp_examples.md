# Hedera MCP Query Examples

This collection of Python scripts demonstrates how to interact with the Hedera blockchain network using the Metaprogramming Client Protocol (MCP).

## Scripts Overview

### 1. hedera_query.py
A basic script that demonstrates how to:
- Connect to the Hedera MCP client
- Query HBAR balance for an account
- Query token balances for an account

### 2. hedera_token_operations.py
An interactive script that demonstrates token operations:
- Creating fungible tokens
- Transferring tokens between accounts
- Associating tokens with accounts
- Creating NFT collections
- Minting NFTs

### 3. hedera_transactions.py
An interactive script for querying transaction data:
- Getting transaction details by transaction ID
- Getting recent transactions for an account
- Getting detailed information about tokens
- Querying consensus topic messages
- Submitting custom queries to the MCP

## Prerequisites

1. Hedera account credentials configured in the `config.py` file:
   - `HEDERA_ACCOUNT_ID`: Your Hedera account ID
   - `HEDERA_PRIVATE_KEY`: Your Hedera private key
   - `HEDERA_NETWORK`: The Hedera network to use (e.g., "testnet", "mainnet")

2. Required Python packages:
   - `mcps`: The MCP client library
   - `uagents`: For agent-related functionality (if needed)

## Usage

Run any of the scripts using Python:

```bash
python hedera_query.py
python hedera_token_operations.py
python hedera_transactions.py
```

Follow the interactive prompts to execute different operations on the Hedera network.

## Notes

- These scripts are meant for demonstration purposes to show how to use the MCP architecture to interact with Hedera.
- The actual functionality depends on the capabilities of the Hedera MCP client.
- All operations are performed against the network specified in your configuration.
- For testnet operations, you can get free testnet HBAR from the Hedera Testnet Faucet.