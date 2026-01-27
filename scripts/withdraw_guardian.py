"""#!/usr/bin/env python3
"""

"""Withdraw guardian script for ERC-20/721-like contracts with owner withdraw function.

Place this file in scripts/ and run it periodically (cron, systemd timer, GitHub Actions runner, etc.).

Features / improvements over the provided template:
- Loads sensitive data from environment variables (supports .env via python-dotenv).
- Uses on-chain contract balance (w3.eth.get_balance) instead of relying on a custom view.
- Tries both withdraw() and withdraw(address) function signatures to be compatible with different contracts.
- Estimates gas and falls back to a sane default.
- Waits for and prints transaction receipt.
- Configurable threshold, chain id and retry behavior via env or CLI.

REQUIREMENTS:
- pip install web3 python-dotenv

USAGE:
- Create a .env file with RPC_URL, PRIVATE_KEY, CONTRACT_ADDRESS (see .env.example) or set env vars directly.
- Run: python3 scripts/withdraw_guardian.py
"""