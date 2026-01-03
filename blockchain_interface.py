"""
Blockchain Interface - Abstraction layer for multi-chain support
Defines base classes for transaction fetchers and trade parsers
Supports both EVM and non-EVM chains (Solana, Sui, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any


class BlockchainTransactionFetcher(ABC):
    """Abstract base class for fetching transactions from any blockchain"""
    
    @abstractmethod
    def fetch_all_data(self) -> Dict:
        """
        Fetch all transaction data for the configured address
        
        Returns:
            Dictionary with transaction data in a standardized format:
            {
                "address": str,
                "normal_transactions": List[Dict],
                "token_transfers": List[Dict],  # ERC-20 for EVM, SPL for Solana, etc.
                "internal_transactions": List[Dict],  # Optional, for EVM chains
                "metadata": {
                    "total_normal": int,
                    "total_token": int,
                    "total_internal": int,
                    "fetched_at": str
                }
            }
        """
        pass
    
    @abstractmethod
    def validate_address(self, address: str) -> bool:
        """Validate that the address format is correct for this blockchain"""
        pass


class BlockchainTradeParser(ABC):
    """Abstract base class for parsing trades from any blockchain"""
    
    @abstractmethod
    def parse_all_trades(self) -> List[Dict]:
        """
        Parse all DEX trades from transaction data
        
        Returns:
            List of trade dictionaries with standardized format:
            {
                'tx_hash': str,
                'block_number': int,  # or slot/sequence number for non-EVM
                'timestamp': int,  # Unix timestamp
                'dex': str,  # DEX name
                'token_in': str,  # Token address/identifier
                'token_out': str,  # Token address/identifier
                'amount_in': str,  # Raw amount (wei, lamports, etc.)
                'amount_out': str,  # Raw amount
                'type': 'swap'
            }
        """
        pass


def get_fetcher_class(chain_name: str) -> type:
    """
    Factory function to get the appropriate fetcher class for a chain
    
    Args:
        chain_name: Lowercase chain name (e.g., 'ethereum', 'solana', 'sui')
    
    Returns:
        Fetcher class for the chain
    """
    chain_name = chain_name.lower()
    
    # EVM chains use EthereumTransactionFetcher
    evm_chains = ['ethereum', 'monad', 'arbitrum', 'linea', 'optimism', 
                  'polygon', 'katana', 'binance', 'base', 'avax']
    
    if chain_name in evm_chains:
        from fetch_ethereum_transactions import EthereumTransactionFetcher
        return EthereumTransactionFetcher
    
    elif chain_name == 'solana':
        from fetch_solana_transactions import SolanaTransactionFetcher
        return SolanaTransactionFetcher
    
    elif chain_name == 'sui':
        from fetch_sui_transactions import SuiTransactionFetcher
        return SuiTransactionFetcher
    
    else:
        raise ValueError(f"Unsupported chain: {chain_name}")


def get_parser_class(chain_name: str) -> type:
    """
    Factory function to get the appropriate parser class for a chain
    
    Args:
        chain_name: Lowercase chain name (e.g., 'ethereum', 'solana', 'sui')
    
    Returns:
        Parser class for the chain
    """
    chain_name = chain_name.lower()
    
    # EVM chains use EthereumTradeParser
    evm_chains = ['ethereum', 'monad', 'arbitrum', 'linea', 'optimism', 
                  'polygon', 'katana', 'binance', 'base', 'avax']
    
    if chain_name in evm_chains:
        from parse_ethereum_trades import EthereumTradeParser
        return EthereumTradeParser
    
    elif chain_name == 'solana':
        from parse_solana_trades import SolanaTradeParser
        return SolanaTradeParser
    
    elif chain_name == 'sui':
        from parse_sui_trades import SuiTradeParser
        return SuiTradeParser
    
    else:
        raise ValueError(f"Unsupported chain: {chain_name}")

