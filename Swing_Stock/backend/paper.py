from dataclasses import dataclass, asdict
from datetime import datetime
import math

from .data import MarketData
from .database import Database


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

        self.market = MarketData()
        self.db = Database()

    # =====================================================
    # DATABASE
    # =====================================================

    def conn(self):

        return self.db.get_connection()

    # =====================================================
    # SAFE NUMBER
    # =====================================================

    def safe_number(
        self,
        value,
        default=0.0
    ):

        try:

            value = float(value)

            if not math.isfinite(value):
                return default

            return value

        except Exception:

            return default

    # =====================================================
    # CASH
    # =====================================================

    def get_cash(self):

        conn = self.conn()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT cash
            FROM portfolio
            WHERE id = 1
            """
        )

        row = cur.fetchone()

        conn.close()

        if row:

            return float(row[0])

        return 100000.0

    def update_cash(
        self,
        cash
    ):

        conn = self.conn()

        cur = conn.cursor()

        cur.execute(
            """
            UPDATE portfolio
            SET cash = ?
            WHERE id = 1
            """,
            (cash,)
        )

        conn.commit()
        conn.close()

    # =====================================================
    # POSITIONS
    # =====================================================

    def get_positions(self):

        conn = self.conn()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                symbol,
                quantity,
                avg_price
            FROM positions
            """
        )

        rows = cur.fetchall()

        conn.close()

        positions = {}

        for row in rows:

            positions[row[0]] = {

                "quantity": int(row[1]),

                "avg_price": float(row[2])

            }

        return positions

    # =====================================================
    # TRADES
    # =====================================================

    def get_trades(self):

        conn = self.conn()

        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                symbol,
                side,
                quantity,
                price,
                timestamp,
                pnl
            FROM trades
            ORDER BY id
            """
        )

        rows = cur.fetchall()

        conn.close()

        trades = []

        for row in rows:

            trades.append(

                PaperTrade(
                    id=row[0],
                    symbol=row[1],
                    side=row[2],
                    quantity=row[3],
                    price=row[4],
                    timestamp=row[5],
                    pnl=row[6]
                )

            )

        return trades

    # =====================================================
    # MARKET PRICE
    # =====================================================

    def get_current_price(
        self,
        symbol
    ):

        try:

            df = self.market.get_history(
                symbol + ".NS"
            )

            if df is None or df.empty:
                return None

            closes = (
                df["Close"]
                .dropna()
            )

            if closes.empty:
                return None

            return round(
                float(
                    closes.iloc[-1]
                ),
                2
            )

        except Exception:

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

        price = float(price)

        quantity = int(quantity)

        cost = (
            price *
            quantity
        )

        cash = self.get_cash()

        if cost > cash:

            return {
                "error":
                    "Insufficient cash"
            }

        cash -= cost

        self.update_cash(cash)

        positions = self.get_positions()

        position = positions.get(
            symbol,
            {
                "quantity": 0,
                "avg_price": 0.0
            }
        )

        old_qty = position["quantity"]

        old_price = position[
            "avg_price"
        ]

        new_qty = (
            old_qty +
            quantity
        )

        avg_price = (

            (
                old_qty *
                old_price
            )

            +

            (
                quantity *
                price
            )

        ) / new_qty

        conn = self.conn()

        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR REPLACE
            INTO positions
            (
                symbol,
                quantity,
                avg_price
            )
            VALUES (
                ?, ?, ?
            )
            """,
            (
                symbol,
                new_qty,
                avg_price
            )
        )

        timestamp = (
            datetime.now()
            .isoformat()
        )

        cur.execute(
            """
            INSERT INTO trades
            (
                symbol,
                side,
                quantity,
                price,
                pnl,
                timestamp
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                symbol,
                "BUY",
                quantity,
                price,
                0,
                timestamp
            )
        )

        trade_id = cur.lastrowid

        conn.commit()
        conn.close()

        return asdict(

            PaperTrade(
                id=trade_id,
                symbol=symbol,
                side="BUY",
                quantity=quantity,
                price=price,
                timestamp=timestamp,
                pnl=0
            )

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

        price = float(price)

        quantity = int(quantity)

        positions = self.get_positions()

        position = positions.get(
            symbol
        )

        if not position:

            return {
                "error":
                    f"No position in {symbol}"
            }

        if position["quantity"] < quantity:

            return {
                "error":
                    "Not enough shares"
            }

        avg_price = position[
            "avg_price"
        ]

        pnl = (

            price -
            avg_price

        ) * quantity

        cash = self.get_cash()

        cash += (
            quantity *
            price
        )

        self.update_cash(cash)

        remaining = (

            position["quantity"]

            -

            quantity

        )

        conn = self.conn()

        cur = conn.cursor()

        if remaining <= 0:

            cur.execute(
                """
                DELETE FROM positions
                WHERE symbol = ?
                """,
                (
                    symbol,
                )
            )

        else:

            cur.execute(
                """
                UPDATE positions
                SET quantity = ?
                WHERE symbol = ?
                """,
                (
                    remaining,
                    symbol
                )
            )

        timestamp = (
            datetime.now()
            .isoformat()
        )

        cur.execute(
            """
            INSERT INTO trades
            (
                symbol,
                side,
                quantity,
                price,
                pnl,
                timestamp
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                symbol,
                "SELL",
                quantity,
                price,
                pnl,
                timestamp
            )
        )

        trade_id = cur.lastrowid

        conn.commit()
        conn.close()

        return asdict(

            PaperTrade(
                id=trade_id,
                symbol=symbol,
                side="SELL",
                quantity=quantity,
                price=price,
                timestamp=timestamp,
                pnl=round(
                    pnl,
                    2
                )
            )

        )

    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(self):

        positions = self.get_positions()

        trades = self.get_trades()

        cash = self.get_cash()

        response_positions = {}

        invested = 0.0

        current_value = 0.0

        unrealized_pnl = 0.0

        for symbol, p in positions.items():

            qty = p["quantity"]

            avg_price = p["avg_price"]

            latest = self.get_current_price(
                symbol
            )

            if latest is None:

                latest = avg_price

            inv = qty * avg_price

            val = qty * latest

            pnl = (
                latest -
                avg_price
            ) * qty

            pnl_pct = 0

            if avg_price > 0:

                pnl_pct = (

                    (
                        latest -
                        avg_price
                    )

                    /

                    avg_price

                ) * 100

            invested += inv
            current_value += val
            unrealized_pnl += pnl

            response_positions[
                symbol
            ] = {

                "quantity":
                    qty,

                "avg_price":
                    round(
                        avg_price,
                        2
                    ),

                "current_price":
                    round(
                        latest,
                        2
                    ),

                "current_value":
                    round(
                        val,
                        2
                    ),

                "unrealized_pnl":
                    round(
                        pnl,
                        2
                    ),

                "pnl_percent":
                    round(
                        pnl_pct,
                        2
                    )
            }

        realized_pnl = sum(
            t.pnl
            for t in trades
            if t.side == "SELL"
        )

        return {

            "cash":
                round(
                    cash,
                    2
                ),

            "invested":
                round(
                    invested,
                    2
                ),

            "current_value":
                round(
                    current_value,
                    2
                ),

            "portfolio_value":
                round(
                    cash +
                    current_value,
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
                    realized_pnl +
                    unrealized_pnl,
                    2
                ),

            "positions":
                response_positions,

            "trades":
                [
                    asdict(t)
                    for t in trades
                ]
        }