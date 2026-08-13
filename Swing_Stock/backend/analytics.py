class AnalyticsAgent:

    def generate(self, trades):

        total_trades = 0

        wins = 0

        losses = 0

        total_profit = 0.0

        for trade in trades:

            if trade.side != "SELL":
                continue

            total_trades += 1

            total_profit += trade.pnl

            if trade.pnl > 0:
                wins += 1
            elif trade.pnl < 0:
                losses += 1

        win_rate = 0

        if total_trades > 0:

            win_rate = round(
                (
                    wins /
                    total_trades
                ) * 100,
                2
            )

        avg_profit = 0

        if total_trades > 0:

            avg_profit = round(
                total_profit /
                total_trades,
                2
            )

        return {

            "total_trades":
                total_trades,

            "wins":
                wins,

            "losses":
                losses,

            "win_rate":
                win_rate,

            "net_profit":
                round(
                    total_profit,
                    2
                ),

            "average_profit":
                avg_profit

        }