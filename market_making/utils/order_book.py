#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Order Book Utility
Author: ECLIPSEMOON
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple

# Setup logger
logger = logging.getLogger("market_making.utils.order_book")


class OrderBook:
    """Class for managing and analyzing order books."""

    def __init__(self, market: str):
        """
        Initialize the order book.
        
        Args:
            market: Market symbol
        """
        self.market = market
        self.bids = []  # List of (price, size) tuples
        self.asks = []  # List of (price, size) tuples
        self.last_update_time = None
        
        logger.info(f"Order book initialized for {market}")

    def update(self, bids: List[Dict], asks: List[Dict]) -> None:
        """
        Update the order book.
        
        Args:
            bids: List of bid orders
            asks: List of ask orders
        """
        # Convert to internal format
        self.bids = [(Decimal(str(bid["price"])), Decimal(str(bid["size"]))) for bid in bids]
        self.asks = [(Decimal(str(ask["price"])), Decimal(str(ask["size"]))) for ask in asks]
        
        # Sort bids in descending order (highest price first)
        self.bids.sort(key=lambda x: x[0], reverse=True)
        
        # Sort asks in ascending order (lowest price first)
        self.asks.sort(key=lambda x: x[0])
        
        # Update timestamp
        import time
        self.last_update_time = time.time()
        
        logger.debug(f"Order book updated for {self.market}: {len(self.bids)} bids, {len(self.asks)} asks")

    def get_mid_price(self) -> Optional[Decimal]:
        """
        Get the mid price.
        
        Returns:
            Optional[Decimal]: Mid price or None if order book is empty
        """
        if not self.bids or not self.asks:
            return None
        
        best_bid = self.bids[0][0]
        best_ask = self.asks[0][0]
        
        return (best_bid + best_ask) / Decimal("2")

    def get_spread(self) -> Optional[Decimal]:
        """
        Get the bid-ask spread.
        
        Returns:
            Optional[Decimal]: Spread or None if order book is empty
        """
        if not self.bids or not self.asks:
            return None
        
        best_bid = self.bids[0][0]
        best_ask = self.asks[0][0]
        
        return (best_ask - best_bid) / best_bid

    def get_depth(self, price_levels: int = 10) -> Tuple[Decimal, Decimal]:
        """
        Get the order book depth.
        
        Args:
            price_levels: Number of price levels to consider
            
        Returns:
            Tuple[Decimal, Decimal]: Bid depth and ask depth
        """
        bid_depth = sum(size for _, size in self.bids[:price_levels])
        ask_depth = sum(size for _, size in self.asks[:price_levels])
        
        return bid_depth, ask_depth

    def get_imbalance(self, price_levels: int = 10) -> float:
        """
        Get the order book imbalance.
        
        Args:
            price_levels: Number of price levels to consider
            
        Returns:
            float: Imbalance (-1.0 to 1.0)
        """
        bid_depth, ask_depth = self.get_depth(price_levels)
        
        total_depth = bid_depth + ask_depth
        if total_depth == 0:
            return 0.0
        
        return float((bid_depth - ask_depth) / total_depth)

    def get_vwap(self, size: Decimal, side: str) -> Optional[Decimal]:
        """
        Get the volume-weighted average price for a given size.
        
        Args:
            size: Size to calculate VWAP for
            side: 'bid' or 'ask'
            
        Returns:
            Optional[Decimal]: VWAP or None if not enough liquidity
        """
        if side.lower() == 'bid':
            orders = self.bids
        elif side.lower() == 'ask':
            orders = self.asks
        else:
            raise ValueError(f"Invalid side: {side}")
        
        remaining_size = size
        total_value = Decimal("0")
        
        for price, order_size in orders:
            if remaining_size <= 0:
                break
            
            executed_size = min(remaining_size, order_size)
            total_value += executed_size * price
            remaining_size -= executed_size
        
        if remaining_size > 0:
            # Not enough liquidity
            return None
        
        return total_value / size

    def get_price_impact(self, size: Decimal, side: str) -> Optional[Decimal]:
        """
        Get the price impact for a given size.
        
        Args:
            size: Size to calculate price impact for
            side: 'bid' or 'ask'
            
        Returns:
            Optional[Decimal]: Price impact as a percentage or None if not enough liquidity
        """
        if not self.bids or not self.asks:
            return None
        
        mid_price = self.get_mid_price()
        if mid_price is None:
            return None
        
        vwap = self.get_vwap(size, side)
        if vwap is None:
            return None
        
        if side.lower() == 'bid':
            return (mid_price - vwap) / mid_price
        else:
            return (vwap - mid_price) / mid_price

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert order book to dictionary.
        
        Returns:
            Dict[str, Any]: Order book as dictionary
        """
        return {
            "market": self.market,
            "bids": [{"price": float(price), "size": float(size)} for price, size in self.bids],
            "asks": [{"price": float(price), "size": float(size)} for price, size in self.asks],
            "last_update_time": self.last_update_time
        }