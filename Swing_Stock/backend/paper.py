from dataclasses import dataclass, asdict
from datetime import datetime
import math

from .data import MarketData


@dataclass
class PaperTrade:

    id: int
    symbol: str
    side: str
    quantity: int
    price: float
    timestamp: str
    pnl: float = 0.0


class PaperBroker:

    def __init__(self):

        self.cash = 100000.0

        self.positions = {}

        self.trades = []

        self.next_id = 1

        self.market = MarketData()


    # =====================================================
    # SAFE NUMBER
    # =====================================================

    def safe_number(self, value, default=0.0):

        try:

            value = float(value)

            if not math.isfinite(value):
                return default

            return value

        except Exception:

            return default


    # =====================================================
    # GET CURRENT MARKET PRICE
    # =====================================================

    def get_current_price(self, symbol):

        try:

            df = self.market.get_history(
                symbol + ".NS"
            )

            if df is None or df.empty:

                return None


            # Find latest valid Close value
            closes = df["Close"].dropna()


            if closes.empty:

                return None


            price = float(
                closes.iloc[-1]
            )


            if not math.isfinite(price):

                return None


            return round(
                price,
                2
            )


        except Exception as e:

            print(
                f"Price fetch failed for {symbol}: {e}"
            )

            return None


    # =====================================================
    # BUY
    # =====================================================

    def buy(
        self,
        symbol,
        price,
        quantity
    ):

        symbol = symbol.upper()

        price = self.safe_number(
            price
        )

        quantity = int(
            quantity
        )


        if price <= 0:

            return {
                "error":
                    "Invalid price"
            }


        if quantity <= 0:

            return {
                "error":
                    "Invalid quantity"
            }


        cost = (
            price *
            quantity
        )


        if cost > self.cash:

            return {
                "error":
                    "Insufficient cash"
            }


        self.cash -= cost


        position = self.positions.setdefault(

            symbol,

            {
                "quantity": 0,
                "avg_price": 0.0
            }

        )


        old_quantity = position[
            "quantity"
        ]


        old_avg_price = position[
            "avg_price"
        ]


        new_quantity = (
            old_quantity +
            quantity
        )


        # Weighted average entry price

        if new_quantity > 0:

            new_avg_price = (

                (
                    old_avg_price *
                    old_quantity
                )

                +

                (
                    price *
                    quantity
                )

            ) / new_quantity

        else:

            new_avg_price = price


        position[
            "quantity"
        ] = new_quantity


        position[
            "avg_price"
        ] = round(
            new_avg_price,
            2
        )


        trade = PaperTrade(

            id=self.next_id,

            symbol=symbol,

            side="BUY",

            quantity=quantity,

            price=round(
                price,
                2
            ),

            timestamp=datetime.now().isoformat(),

            pnl=0.0

        )


        self.next_id += 1


        self.trades.append(
            trade
        )


        return asdict(
            trade
        )


    # =====================================================
    # SELL
    # =====================================================

    def sell(
        self,
        symbol,
        price,
        quantity
    ):

        symbol = symbol.upper()

        price = self.safe_number(
            price
        )

        quantity = int(
            quantity
        )


        if price <= 0:

            return {
                "error":
                    "Invalid price"
            }


        if quantity <= 0:

            return {
                "error":
                    "Invalid quantity"
            }


        position = self.positions.get(
            symbol
        )


        if not position:

            return {
                "error":
                    f"No open position for {symbol}"
            }


        available_quantity = int(
            position[
                "quantity"
            ]
        )


        if available_quantity < quantity:

            return {
                "error":
                    "Insufficient position quantity"
            }


        avg_price = self.safe_number(

            position[
                "avg_price"
            ]

        )


        # Realized P&L

        realized_pnl = (

            price -
            avg_price

        ) * quantity


        realized_pnl = self.safe_number(
            realized_pnl
        )


        # Add sale proceeds to cash

        self.cash += (

            price *
            quantity

        )


        # Reduce position

        position[
            "quantity"
        ] -= quantity


        # Remove position completely

        if position[
            "quantity"
        ] <= 0:

            del self.positions[
                symbol
            ]


        trade = PaperTrade(

            id=self.next_id,

            symbol=symbol,

            side="SELL",

            quantity=quantity,

            price=round(
                price,
                2
            ),

            timestamp=datetime.now().isoformat(),

            pnl=round(
                realized_pnl,
                2
            )

        )


        self.next_id += 1


        self.trades.append(
            trade
        )


        return asdict(
            trade
        )


    # =====================================================
    # PORTFOLIO SUMMARY
    # =====================================================

    def summary(self):

        positions = {}


        total_invested = 0.0

        current_value = 0.0

        unrealized_pnl = 0.0


        # -------------------------------------------------
        # OPEN POSITIONS
        # -------------------------------------------------

        for symbol, position in list(
            self.positions.items()
        ):

            quantity = int(
                position.get(
                    "quantity",
                    0
                )
            )


            avg_price = self.safe_number(

                position.get(
                    "avg_price",
                    0
                )

            )


            if quantity <= 0:

                continue


            # Get latest market price

            latest_price = (
                self.get_current_price(
                    symbol
                )
            )


            # If market data unavailable,
            # use average buy price.

            if (
                latest_price is None
                or not math.isfinite(
                    latest_price
                )
            ):

                latest_price = avg_price


            # ---------------------------------------------
            # INVESTED VALUE
            # ---------------------------------------------

            invested = (

                avg_price *
                quantity

            )


            invested = self.safe_number(
                invested
            )


            # ---------------------------------------------
            # CURRENT VALUE
            # ---------------------------------------------

            value = (

                latest_price *
                quantity

            )


            value = self.safe_number(
                value
            )


            # ---------------------------------------------
            # UNREALIZED P&L
            # ---------------------------------------------

            pnl = (

                latest_price -
                avg_price

            ) * quantity


            pnl = self.safe_number(
                pnl
            )


            # ---------------------------------------------
            # P&L %
            # ---------------------------------------------

            if avg_price > 0:

                pnl_percent = (

                    (
                        latest_price -
                        avg_price
                    )

                    /

                    avg_price

                ) * 100

            else:

                pnl_percent = 0.0


            pnl_percent = self.safe_number(
                pnl_percent
            )


            # ---------------------------------------------
            # ADD TO TOTALS
            # ---------------------------------------------

            total_invested += invested

            current_value += value

            unrealized_pnl += pnl


            # ---------------------------------------------
            # POSITION RESPONSE
            # ---------------------------------------------

            positions[symbol] = {

                "quantity":
                    quantity,

                "avg_price":
                    round(
                        avg_price,
                        2
                    ),

                "current_price":
                    round(
                        latest_price,
                        2
                    ),

                "invested":
                    round(
                        invested,
                        2
                    ),

                "current_value":
                    round(
                        value,
                        2
                    ),

                "unrealized_pnl":
                    round(
                        pnl,
                        2
                    ),

                "pnl_percent":
                    round(
                        pnl_percent,
                        2
                    )

            }


        # -------------------------------------------------
        # REALIZED P&L
        # -------------------------------------------------

        realized_pnl = 0.0


        for trade in self.trades:

            if trade.side == "SELL":

                realized_pnl += self.safe_number(
                    trade.pnl
                )


        realized_pnl = self.safe_number(
            realized_pnl
        )


        # -------------------------------------------------
        # TOTAL PORTFOLIO VALUE
        # -------------------------------------------------

        cash = self.safe_number(
            self.cash
        )


        total_invested = self.safe_number(
            total_invested
        )


        current_value = self.safe_number(
            current_value
        )


        unrealized_pnl = self.safe_number(
            unrealized_pnl
        )


        portfolio_value = (

            cash +
            current_value

        )


        portfolio_value = self.safe_number(
            portfolio_value
        )


        # -------------------------------------------------
        # TOTAL P&L
        # -------------------------------------------------

        total_pnl = (

            realized_pnl +
            unrealized_pnl

        )


        total_pnl = self.safe_number(
            total_pnl
        )


        # -------------------------------------------------
        # FINAL RESPONSE
        # -------------------------------------------------

        return {

            "cash":
                round(
                    cash,
                    2
                ),

            "invested":
                round(
                    total_invested,
                    2
                ),

            "current_value":
                round(
                    current_value,
                    2
                ),

            "portfolio_value":
                round(
                    portfolio_value,
                    2
                ),

            "realized_pnl":
                round(
                    realized_pnl,
                    2
                ),

            "unrealized_pnl":
                round(
                    unrealized_pnl,
                    2
                ),

            "total_pnl":
                round(
                    total_pnl,
                    2
                ),

            "positions":
                positions,

            "trades":
                [
                    asdict(trade)
                    for trade in self.trades
                ]

        }