# ECLIPSEMOON AI Protocol Framework

<div align="center">
  <img src="https://ik.imagekit.io/rzu2i5t1r/Orbit.png?updatedAt=1747026694375" alt="ECLIPSEMOON Logo" width="100%">
</div>

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-alpha-orange)

## Overview

The ECLIPSEMOON AI Protocol Framework is a comprehensive suite of tools designed to interact with various DeFi protocols through AI-enhanced strategies. This framework provides a secure foundation for automated trading, liquidity provision, and yield optimization across multiple blockchain ecosystems.

## Key Features

- **Multi-Protocol Support**: Seamless integration with major DeFi protocols including Jupiter, Raydium, Drift, Meteora, and more
- **AI-Powered Decision Making**: Advanced machine learning models for optimal entry/exit points
- **Risk Management**: Sophisticated stop-loss and take-profit mechanisms
- **Automated Yield Farming**: Intelligent rebalancing and compounding strategies
- **Secure Execution Environment**: Robust safeguards for private key and API management

## Project Structure

```
eclipse-defi-ai/
├── drift/                  # Drift protocol integration
│   ├── perps-close/        # Close perpetual positions
│   ├── perps-open/         # Open new perpetual positions
│   ├── vaults-deposit/     # Deposit into Drift vaults
│   └── vaults-withdraw/    # Withdraw from Drift vaults
├── jupiter/                # Jupiter aggregator integration
│   ├── dao-claim/          # Claim DAO rewards
│   ├── dao-stake/          # Stake in Jupiter DAO
│   ├── dao-unstake/        # Unstake from Jupiter DAO
│   ├── perps-add-collateral/  # Add collateral to perp positions
│   ├── perps-close/        # Close Jupiter perp positions
│   ├── perps-open/         # Open Jupiter perp positions
│   ├── perps-remove-collateral/  # Remove collateral from positions
│   ├── perps-stop-loss/    # Manage stop-loss orders
│   ├── perps-take-profit/  # Manage take-profit orders
│   └── swap/               # Token swap operations
├── kamino/                 # Kamino protocol integration
├── lulo/                   # Lulo protocol integration
│   ├── deposit/            # Deposit into Lulo
│   └── withdraw/           # Withdraw from Lulo
├── marginfi/               # MarginFi protocol integration
│   ├── supply/             # Supply assets to MarginFi
│   └── withdraw/           # Withdraw assets from MarginFi
├── meteora/                # Meteora protocol integration
│   ├── add-liquidity/      # Add liquidity to Meteora pools
│   ├── launch-token/       # Token launch utilities
│   └── remove-liquidity/   # Remove liquidity from Meteora pools
├── raydium/                # Raydium protocol integration
│   ├── add-liquidity/      # Add liquidity to Raydium pools
│   ├── create-position/    # Create new LP positions
│   ├── staking-claim/      # Claim staking rewards
│   ├── staking-stake/      # Stake in Raydium pools
│   ├── staking-unstake/    # Unstake from Raydium pools
│   └── save/               # Save configuration and state
├── core/                   # Core framework components
│   ├── ai/                 # AI models and prediction engines
│   ├── blockchain/         # Blockchain interaction utilities
│   ├── config/             # Configuration management
│   ├── data/               # Data processing and storage
│   ├── security/           # Security and encryption utilities
│   └── utils/              # General utilities
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── simulation/         # Strategy simulation tests
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore file
├── main.py                 # Main entry point
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Installation

1. Clone the repository:
```bash
git clone hhttps://github.com/eclipseresearch/eclipse-defi-ai.git
cd eclipse-defi-ai

# Using venv (Python 3.10+ recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -e .
# Or for development dependencies
pip install -e ".[dev]"

cp .env.example .env
# Edit .env file with your configuration settings

# For Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev

# For macOS
brew install openssl

python setup.py