import inspect
import sys
import statistics
import numpy as np
import pandas as pd
from scipy import stats
from typing import Protocol, Type, runtime_checkable, Any, Dict, List
from pyHaasAPI.logger import log

# Define TimeSeries as a pandas DataFrame for clarity
TimeSeries = pd.DataFrame

@runtime_checkable
class WorkforceOptimizationHeuristic(Protocol):
    @staticmethod
    def calculate(data: TimeSeries) -> dict:
        """
        Calculates actual scalar value based on input
        """
        ...


class EquityCurveStability(WorkforceOptimizationHeuristic):
    """
    Simple heoristics for the equity curve analysis.
    """

    @staticmethod
    def calculate(data: TimeSeries) -> dict:
        """
        :param data: Sequence of the equity curve values
        :raises ValueError: If equity curve does not contain at least 2 values more then 0
        :returns: Variance of the given equity curve
        """
        log.info(
            f"Starting calculation of equity curve of {len(data)} samples ({data=})"
        )
        rates_of_return = []
        pnls = data["pnl"]

        for i in range(1, len(pnls)):
            if pnls[i - 1] == 0.0:
                continue

            diff = (pnls[i] - pnls[i - 1]) / pnls[i - 1]
            rates_of_return.append(diff)

        if len(rates_of_return) <= 2:
            raise ValueError(
                "Not enough data. Most of the values of equity curve are zeros"
            )

        return {"variance": statistics.variance(rates_of_return)}


class PerformanceMetrics(WorkforceOptimizationHeuristic):
    """
    Simple heoristics for the performance metrics analysis.
    """

    @staticmethod
    def calculate(data: TimeSeries, risk_free_rate=0.02, market_returns=None) -> dict:
        daily_returns = data.groupby("exit_date")["pnl"].sum().pct_change()

        total_return = data["pnl"].sum() / data["position_size"].iloc[0] * 100
        cagr = (1 + total_return) ** (252 / len(daily_returns)) - 1

        sharpe_ratio = (
            (daily_returns.mean() - risk_free_rate / 252)
            / daily_returns.std()
            * np.sqrt(252)
        )

        sortino_ratio = (
            (daily_returns.mean() - risk_free_rate / 252)
            / daily_returns[daily_returns < 0].std()
            * np.sqrt(252)
        )

        max_drawdown = (daily_returns.cumsum() - daily_returns.cumsum().cummax()).min()

        calmar_ratio = cagr / abs(max_drawdown)

        if market_returns is not None:
            market_returns = market_returns.reindex(daily_returns.index)
            beta = np.cov(daily_returns, market_returns)[0][1] / np.var(market_returns)
            alpha = daily_returns.mean() - beta * market_returns.mean()
        else:
            beta = alpha = np.nan

        return {
            "Total Return (%)": total_return,
            "CAGR (%)": cagr * 100,
            "Sharpe Ratio": sharpe_ratio,
            "Sortino Ratio": sortino_ratio,
            "Max Drawdown (%)": max_drawdown * 100,
            "Calmar Ratio": calmar_ratio,
            "Alpha": alpha,
            "Beta": beta,
        }


class TradesAnalysis(WorkforceOptimizationHeuristic):

    @staticmethod
    def calculate(data: TimeSeries) -> dict:
        total_trades = len(data)
        winning_trades = data[data["pnl"] > 0]
        losing_trades = data[data["pnl"] <= 0]

        win_rate = len(winning_trades) / total_trades
        profit_factor = winning_trades["pnl"].sum() / abs(losing_trades["pnl"].sum())

        avg_win = winning_trades["pnl"].mean()
        avg_loss = losing_trades["pnl"].mean()

        largest_win = winning_trades["pnl"].max()
        largest_loss = losing_trades["pnl"].min()

        avg_hold_time_win = (
            winning_trades["exit_date"] - winning_trades["entry_date"]
        ).mean().total_seconds() / 86400
        avg_hold_time_loss = (
            losing_trades["exit_date"] - losing_trades["entry_date"]
        ).mean().total_seconds() / 86400

        return {
            "Total Trades": total_trades,
            "Win Rate": win_rate,
            "Profit Factor": profit_factor,
            "Average Win": avg_win,
            "Average Loss": avg_loss,
            "Largest Win": largest_win,
            "Largest Loss": largest_loss,
            "Avg Hold Time (Win)": avg_hold_time_win,
            "Avg Hold Time (Loss)": avg_hold_time_loss,
        }


class RiskAnalysis(WorkforceOptimizationHeuristic):

    @staticmethod
    def calculate(data: TimeSeries, confidence_level=0.95) -> dict:
        daily_returns = data.groupby("exit_date")["pnl"].sum().pct_change()

        var = np.percentile(daily_returns, 100 * (1 - confidence_level))
        cvar = daily_returns[daily_returns <= var].mean()

        risk_return_ratio = daily_returns.mean() / daily_returns.std()

        return {
            f"Value at Risk ({confidence_level*100}%)": var,
            f"Conditional VaR ({confidence_level*100}%)": cvar,
            "Risk-Return Ratio": risk_return_ratio,
        }


class TradesDistribution(WorkforceOptimizationHeuristic):

    @staticmethod
    def calculate(data: TimeSeries) -> dict:
        return {
            "skewness": stats.skew(data["pnl"]),
            "kurtosis": stats.kurtosis(data["pnl"]),
        }


class RealizedVsOpenProfit(WorkforceOptimizationHeuristic):

    @staticmethod
    def calculate(data: TimeSeries, confidence_level=0.95) -> dict:
        realized_profit = data["pnl"].sum()

        # Simulate open trades (last 10% of trades)
        open_trades = data.iloc[-int(len(data) * 0.1) :]
        open_profit = (
            (open_trades["exit_price"] - open_trades["entry_price"])
            * open_trades["position_size"]
        ).sum()

        total_profit = realized_profit + open_profit

        return {
            "realized": realized_profit,
            "open": open_profit,
            "total": total_profit,
            "realized ratio": realized_profit / total_profit,
        }

def list_heuristics() -> list[Type[WorkforceOptimizationHeuristic]]:
    is_class_member = (
        lambda member: inspect.isclass(member) and member.__module__ == __name__
    )
    clsmembers = [
        cls
        for _, cls in inspect.getmembers(sys.modules[__name__], is_class_member)
        if issubclass(cls, WorkforceOptimizationHeuristic)
        and cls != WorkforceOptimizationHeuristic
    ]
    return clsmembers
