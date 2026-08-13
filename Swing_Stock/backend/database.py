import sqlite3


DB_NAME = "swing_stock.db"


class Database:

    def __init__(self):
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(DB_NAME)

    def init_db(self):

        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY,
            cash REAL NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            symbol TEXT PRIMARY KEY,
            quantity INTEGER NOT NULL,
            avg_price REAL NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            pnl REAL DEFAULT 0,
            timestamp TEXT NOT NULL
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            added_at TEXT NOT NULL
        )
        """)

        cur.execute("""
        INSERT OR IGNORE INTO portfolio (
            id,
            cash
        )
        VALUES (
            1,
            100000
        )
        """)

        conn.commit()
        conn.close()