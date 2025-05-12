#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ECLIPSEMOON AI Protocol Framework
Performance Evaluation Tests
Author: ECLIPSEMOON
"""

import os
import sys
import unittest
import asyncio
import tempfile
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from decimal import Decimal
from datetime import datetime, timedelta

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import core modules
from core.utils import setup_logging, Timer


class PerformanceMetrics:
    """Class for calculating performance metrics."""
    
    @staticmethod
    def calculate_returns(values):
        """Calculate returns from a series of values."""
        returns = []
        for i in range(1, len(values)):
            returns.append((values[i] - values[i-1]) / values[i-1])
        return returns
    
    @staticmethod
    def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
        """Calculate Sharpe ratio."""
        if not returns:
            return 0.0
        
        excess_returns = [r - risk_free_rate for r in returns]
        return np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0.0
    
    @staticmethod
    def calculate_sortino_ratio(returns, risk_free_rate=0.0):
        """Calculate Sortino ratio."""
        if not returns:
            return 0.0
        
        excess_returns = [r - risk_free_rate for r in returns]
        downside_returns = [r for r in excess_returns if r < 0]
        downside_deviation = np.std(downside_returns) if downside_returns else 0.0
        
        return np.mean(excess_returns) / downside_deviation if downside_deviation > 0 else 0.0
    
    @staticmethod
    def calculate_max_drawdown(values):
        """Calculate maximum drawdown."""
        if not values:
            return 0.0
        
        max_drawdown = 0.0
        peak = values[0]
        
        for value in values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    @staticmethod
    def calculate_win_rate(trades):
        """Calculate win rate from a list of trades."""
        if not trades:
            return 0.0
        
        winning_trades = sum(1 for trade in trades if trade > 0)
        return winning_trades / len(trades)
    
    @staticmethod
    def calculate_profit_factor(trades):
        """Calculate profit factor from a list of trades."""
        if not trades:
            return 0.0
        
        gross_profit = sum(trade for trade in trades if trade > 0)
        gross_loss = sum(abs(trade) for trade in trades if trade < 0)
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    @staticmethod
    def calculate_average_trade(trades):
        """Calculate average trade from a list of trades."""
        if not trades:
            return 0.0
        
        return sum(trades) / len(trades)
    
    @staticmethod
    def calculate_expectancy(trades):
        """Calculate expectancy from a list of trades."""
        if not trades:
            return 0.0
        
        win_rate = PerformanceMetrics.calculate_win_rate(trades)
        
        winning_trades = [trade for trade in trades if trade > 0]
        losing_trades = [trade for trade in trades if trade < 0]
        
        average_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0.0
        average_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 0.0
        
        return (win_rate * average_win) - ((1 - win_rate) * abs(average_loss))


class StrategyBacktest:
    """Class for backtesting a trading strategy."""
    
    def __init__(self, initial_capital=10000.0):
        """Initialize the backtest."""
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = [initial_capital]
        self.timestamps = []
    
    def buy(self, symbol, price, size, timestamp):
        """Buy a position."""
        cost = price * size
        
        if cost > self.capital:
            return False
        
        self.capital -= cost
        
        if symbol in self.positions:
            # Average down
            current_size = self.positions[symbol]["size"]
            current_price = self.positions[symbol]["price"]
            
            # Calculate new average price
            total_cost = (current_size * current_price) + cost
            total_size = current_size + size
            average_price = total_cost / total_size
            
            self.positions[symbol] = {
                "size": total_size,
                "price": average_price,
                "timestamp": timestamp
            }
        else:
            # New position
            self.positions[symbol] = {
                "size": size,
                "price": price,
                "timestamp": timestamp
            }
        
        return True
    
    def sell(self, symbol, price, size, timestamp):
        """Sell a position."""
        if symbol not in self.positions:
            return False
        
        if size > self.positions[symbol]["size"]:
            return False
        
        # Calculate profit/loss
        entry_price = self.positions[symbol]["price"]
        profit_loss = (price - entry_price) * size
        
        # Update capital
        self.capital += (price * size)
        
        # Record trade
        self.trades.append({
            "symbol": symbol,
            "entry_price": entry_price,
            "exit_price": price,
            "size": size,
            "profit_loss": profit_loss,
            "entry_timestamp": self.positions[symbol]["timestamp"],
            "exit_timestamp": timestamp
        })
        
        # Update position
        if size == self.positions[symbol]["size"]:
            del self.positions[symbol]
        else:
            self.positions[symbol]["size"] -= size
        
        return True
    
    def update_equity(self, prices, timestamp):
        """Update equity curve with current prices."""
        # Calculate current equity
        equity = self.capital
        
        for symbol, position in self.positions.items():
            if symbol in prices:
                equity += position["size"] * prices[symbol]
        
        self.equity_curve.append(equity)
        self.timestamps.append(timestamp)
    
    def get_equity_curve(self):
        """Get the equity curve."""
        return self.equity_curve
    
    def get_trades(self):
        """Get the list of trades."""
        return self.trades
    
    def get_trade_pnls(self):
        """Get the list of trade profit/losses."""
        return [trade["profit_loss"] for trade in self.trades]
    
    def get_performance_metrics(self):
        """Calculate performance metrics."""
        equity_curve = self.equity_curve
        trades = self.get_trade_pnls()
        
        # Calculate returns
        returns = PerformanceMetrics.calculate_returns(equity_curve)
        
        # Calculate metrics
        sharpe_ratio = PerformanceMetrics.calculate_sharpe_ratio(returns)
        sortino_ratio = PerformanceMetrics.calculate_sortino_ratio(returns)
        max_drawdown = PerformanceMetrics.calculate_max_drawdown(equity_curve)
        win_rate = PerformanceMetrics.calculate_win_rate(trades)
        profit_factor = PerformanceMetrics.calculate_profit_factor(trades)
        average_trade = PerformanceMetrics.calculate_average_trade(trades)
        expectancy = PerformanceMetrics.calculate_expectancy(trades)
        
        # Calculate total return
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        
        return {
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "average_trade": average_trade,
            "expectancy": expectancy,
            "total_trades": len(trades)
        }
    
    def plot_equity_curve(self, filename=None):
        """Plot the equity curve."""
        plt.figure(figsize=(12, 6))
        plt.plot(self.equity_curve)
        plt.title("Equity Curve")
        plt.xlabel("Time")
        plt.ylabel("Equity")
        plt.grid(True)
        
        if filename:
            plt.savefig(filename)
        else:
            plt.show()
    
    def plot_drawdown(self, filename=None):
        """Plot the drawdown curve."""
        equity_curve = self.equity_curve
        drawdowns = []
        peak = equity_curve[0]
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
                drawdowns.append(0.0)
            else:
                drawdown = (peak - equity) / peak
                drawdowns.append(drawdown)
        
        plt.figure(figsize=(12, 6))
        plt.plot(drawdowns)
        plt.title("Drawdown Curve")
        plt.xlabel("Time")
        plt.ylabel("Drawdown")
        plt.grid(True)
        
        if filename:
            plt.savefig(filename)
        else:
            plt.show()


class TestPerformanceEvaluation(unittest.TestCase):
    """Tests for performance evaluation."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        
        # Set up logging
        setup_logging(log_level="INFO")
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove test directory
        shutil.rmtree(self.test_dir)
    
    def test_performance_metrics(self):
        """Test performance metrics calculations."""
        # Test data
        values = [100.0, 105.0, 103.0, 110.0, 108.0, 115.0]
        trades = [5.0, -2.0, 7.0, -2.0, 7.0]
        
        # Calculate returns
        returns = PerformanceMetrics.calculate_returns(values)
        self.assertEqual(len(returns), len(values) - 1)
        self.assertAlmostEqual(returns[0], 0.05)
        
        # Calculate Sharpe ratio
        sharpe_ratio = PerformanceMetrics.calculate_sharpe_ratio(returns)
        self.assertGreater(sharpe_ratio, 0)
        
        # Calculate Sortino ratio
        sortino_ratio = PerformanceMetrics.calculate_sortino_ratio(returns)
        self.assertGreater(sortino_ratio, 0)
        
        # Calculate max drawdown
        max_drawdown = PerformanceMetrics.calculate_max_drawdown(values)
        self.assertGreater(max_drawdown, 0)
        
        # Calculate win rate
        win_rate = PerformanceMetrics.calculate_win_rate(trades)
        self.assertEqual(win_rate, 0.6)
        
        # Calculate profit factor
        profit_factor = PerformanceMetrics.calculate_profit_factor(trades)
        self.assertGreater(profit_factor, 1)
        
        # Calculate average trade
        average_trade = PerformanceMetrics.calculate_average_trade(trades)
        self.assertGreater(average_trade, 0)
        
        # Calculate expectancy
        expectancy = PerformanceMetrics.calculate_expectancy(trades)
        self.assertGreater(expectancy, 0)
    
    def test_strategy_backtest(self):
        """Test strategy backtest."""
        # Create backtest
        backtest = StrategyBacktest(initial_capital=10000.0)
        
        # Generate price data
        start_price = 100.0
        prices = {}
        timestamps = []
        
        start_time = datetime.now() - timedelta(days=30)
        for i in range(31):
            timestamp = start_time + timedelta(days=i)
            timestamps.append(timestamp)
            
            # Simple price model with some randomness
            price = start_price * (1 + 0.001 * i + 0.01 * np.random.randn())
            prices[timestamp] = {"BTC": price}
        
        # Simulate a simple strategy
        for i in range(len(timestamps)):
            timestamp = timestamps[i]
            price = prices[timestamp]["BTC"]
            
            # Simple strategy: buy on even days, sell on odd days
            if i > 0:
                if i % 2 == 0:
                    backtest.buy("BTC", price, 0.1, timestamp)
                else:
                    if "BTC" in backtest.positions:
                        backtest.sell("BTC", price, backtest.positions["BTC"]["size"], timestamp)
            
            # Update equity curve
            backtest.update_equity({"BTC": price}, timestamp)
        
        # Close any remaining positions
        for symbol, position in list(backtest.positions.items()):
            backtest.sell(symbol, prices[timestamps[-1]][symbol], position["size"], timestamps[-1])
        
        # Get performance metrics
        metrics = backtest.get_performance_metrics()
        
        # Verify metrics
        self.assertIn("total_return", metrics)
        self.assertIn("sharpe_ratio", metrics)
        self.assertIn("sortino_ratio", metrics)
        self.assertIn("max_drawdown", metrics)
        self.assertIn("win_rate", metrics)
        self.assertIn("profit_factor", metrics)
        self.assertIn("average_trade", metrics)
        self.assertIn("expectancy", metrics)
        self.assertIn("total_trades", metrics)
        
        # Print metrics
        print("Performance Metrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        # Plot equity curve
        equity_curve_file = os.path.join(self.test_dir, "equity_curve.png")
        backtest.plot_equity_curve(equity_curve_file)
        self.assertTrue(os.path.exists(equity_curve_file))
        
        # Plot drawdown curve
        drawdown_file = os.path.join(self.test_dir, "drawdown.png")
        backtest.plot_drawdown(drawdown_file)
        self.assertTrue(os.path.exists(drawdown_file))


if __name__ == '__main__':
    unittest.main()