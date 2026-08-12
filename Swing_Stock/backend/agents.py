import os
import math
import json
import time
import requests
import pandas as pd
import numpy as np

from datetime import datetime
from urllib.parse import quote_plus
from xml.etree import ElementTree as ET

from dotenv import load_dotenv

from .data import MarketData


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY",
    ""
)

NASDAQ_API_KEY = os.getenv(
    "NASDAQ_API_KEY",
    ""
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-4o-mini"
)


# =========================================================
# TOP 50 INDIAN SWING STOCKS
# =========================================================

UNIVERSE = [

    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "ICICIBANK",
    "INFY",
    "BHARTIARTL",
    "ITC",
    "SBIN",
    "LICI",
    "HINDUNILVR",

    "LT",
    "BAJFINANCE",
    "HCLTECH",
    "MARUTI",
    "SUNPHARMA",
    "KOTAKBANK",
    "AXISBANK",
    "M&M",
    "TITAN",
    "ADANIENT",

    "ADANIPORTS",
    "NTPC",
    "POWERGRID",
    "TATASTEEL",
    "ONGC",
    "COALINDIA",
    "JSWSTEEL",
    "TECHM",
    "WIPRO",
    "ULTRACEMCO",

    "NESTLEIND",
    "ASIANPAINT",
    "HINDALCO",
    "EICHERMOT",
    "GRASIM",
    "CIPLA",
    "DRREDDY",
    "DIVISLAB",
    "APOLLOHOSP",

    "BAJAJFINSV",
    "SBILIFE",
    "HDFCLIFE",
    "BRITANNIA",
    "HEROMOTOCO",
    "BAJAJ-AUTO",
    "INDUSINDBK",
    "TATAELXSI",
    "TRENT",
    "ADANIENSOL"
]


# =========================================================
# SAFE HELPERS
# =========================================================

def safe_float(value, default=0.0):

    try:

        if value is None:
            return default

        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except Exception:

        return default


def optional_float(value):

    try:

        if value is None:
            return None

        value = float(value)

        if not math.isfinite(value):
            return None

        return value

    except Exception:

        return None


def clean_for_json(value):

    if isinstance(value, float):

        if not math.isfinite(value):
            return None

        return value


    if isinstance(value, np.floating):

        value = float(value)

        if not math.isfinite(value):
            return None

        return value


    if isinstance(value, np.integer):

        return int(value)


    if isinstance(value, dict):

        return {
            str(k): clean_for_json(v)
            for k, v in value.items()
        }


    if isinstance(value, list):

        return [
            clean_for_json(v)
            for v in value
        ]


    return value


def round_or_none(value, digits=2):

    value = optional_float(value)

    if value is None:
        return None

    return round(
        value,
        digits
    )


# =========================================================
# TECHNICAL AGENT
# =========================================================

class TechnicalAgent:

    def analyze(self, df):

        if df is None or df.empty:

            return {
                "direction": "NEUTRAL",
                "bullish_score": 0,
                "bearish_score": 0
            }


        data = df.copy()


        close = pd.to_numeric(
            data["Close"],
            errors="coerce"
        ).dropna()


        if len(close) < 10:

            return {
                "direction": "NEUTRAL",
                "bullish_score": 0,
                "bearish_score": 0
            }


        # -------------------------------------------------
        # EMA
        # -------------------------------------------------

        ema20 = (
            close
            .ewm(
                span=20,
                adjust=False
            )
            .mean()
        )

        ema50 = (
            close
            .ewm(
                span=50,
                adjust=False
            )
            .mean()
        )


        # -------------------------------------------------
        # RSI
        # -------------------------------------------------

        delta = close.diff()

        gain = (
            delta
            .clip(lower=0)
            .rolling(14)
            .mean()
        )

        loss = (
            -delta
            .clip(upper=0)
            .rolling(14)
            .mean()
        )


        rs = gain / loss.replace(
            0,
            np.nan
        )


        rsi = (
            100 -
            (
                100 /
                (1 + rs)
            )
        )


        # -------------------------------------------------
        # MACD
        # -------------------------------------------------

        ema12 = (
            close
            .ewm(
                span=12,
                adjust=False
            )
            .mean()
        )

        ema26 = (
            close
            .ewm(
                span=26,
                adjust=False
            )
            .mean()
        )

        macd = ema12 - ema26

        signal = (
            macd
            .ewm(
                span=9,
                adjust=False
            )
            .mean()
        )


        # -------------------------------------------------
        # RETURNS
        # -------------------------------------------------

        ret5 = 0.0
        ret20 = 0.0


        if len(close) >= 6:

            ret5 = (
                (
                    close.iloc[-1]
                    /
                    close.iloc[-6]
                )
                - 1
            ) * 100


        if len(close) >= 21:

            ret20 = (
                (
                    close.iloc[-1]
                    /
                    close.iloc[-21]
                )
                - 1
            ) * 100


        current = safe_float(
            close.iloc[-1]
        )

        current_ema20 = safe_float(
            ema20.iloc[-1]
        )

        current_ema50 = safe_float(
            ema50.iloc[-1]
        )

        current_rsi = safe_float(
            rsi.iloc[-1],
            50
        )

        current_macd = safe_float(
            macd.iloc[-1]
        )

        current_signal = safe_float(
            signal.iloc[-1]
        )


        bullish = 0
        bearish = 0


        # EMA trend

        if current > current_ema20:

            bullish += 1

        else:

            bearish += 1


        if current_ema20 > current_ema50:

            bullish += 2

        else:

            bearish += 2


        # RSI

        if 50 <= current_rsi <= 70:

            bullish += 1

        elif current_rsi < 35:

            bullish += 1

        elif current_rsi > 75:

            bearish += 1


        # MACD

        if current_macd > current_signal:

            bullish += 2

        else:

            bearish += 2


        # Momentum

        if ret5 > 0:

            bullish += 1

        else:

            bearish += 1


        if ret20 > 0:

            bullish += 1

        else:

            bearish += 1


        if bullish > bearish:

            direction = "BULLISH"

        elif bearish > bullish:

            direction = "BEARISH"

        else:

            direction = "NEUTRAL"


        return clean_for_json({

            "direction":
                direction,

            "bullish_score":
                bullish,

            "bearish_score":
                bearish,

            "rsi":
                round_or_none(
                    current_rsi
                ),

            "ema20":
                round_or_none(
                    current_ema20
                ),

            "ema50":
                round_or_none(
                    current_ema50
                ),

            "macd":
                round_or_none(
                    current_macd
                ),

            "macd_signal":
                round_or_none(
                    current_signal
                ),

            "five_day_return":
                round_or_none(
                    ret5
                ),

            "twenty_day_return":
                round_or_none(
                    ret20
                )

        })


# =========================================================
# PATTERN AGENT
# =========================================================

class PatternAgent:

    def analyze(self, df):

        if df is None or df.empty:

            return {
                "direction": "NEUTRAL",
                "bullish_score": 0,
                "bearish_score": 0
            }


        close = pd.to_numeric(
            df["Close"],
            errors="coerce"
        ).dropna()


        if len(close) < 30:

            return {
                "direction": "NEUTRAL",
                "bullish_score": 0,
                "bearish_score": 0
            }


        bullish = 0
        bearish = 0


        # -------------------------------------------------
        # 20 DAY TREND
        # -------------------------------------------------

        current = safe_float(
            close.iloc[-1]
        )

        price20 = safe_float(
            close.iloc[-21]
        )


        trend20 = 0.0


        if price20 > 0:

            trend20 = (
                (
                    current /
                    price20
                ) - 1
            ) * 100


        if trend20 > 2:

            bullish += 2

        elif trend20 < -2:

            bearish += 2


        # -------------------------------------------------
        # 5 DAY MOMENTUM
        # -------------------------------------------------

        price5 = safe_float(
            close.iloc[-6]
        )


        trend5 = 0.0


        if price5 > 0:

            trend5 = (
                (
                    current /
                    price5
                ) - 1
            ) * 100


        if trend5 > 1:

            bullish += 1

        elif trend5 < -1:

            bearish += 1


        # -------------------------------------------------
        # HIGH / LOW BREAKOUT
        # -------------------------------------------------

        previous20 = close.iloc[-21:-1]


        if len(previous20) > 0:

            high20 = safe_float(
                previous20.max()
            )

            low20 = safe_float(
                previous20.min()
            )


            if current > high20:

                bullish += 2


            elif current < low20:

                bearish += 2


        # -------------------------------------------------
        # VOLATILITY
        # -------------------------------------------------

        returns = (
            close
            .pct_change()
            .dropna()
        )


        volatility = safe_float(
            returns.tail(20).std()
            * 100
        )


        if bullish > bearish:

            direction = "BULLISH"

        elif bearish > bullish:

            direction = "BEARISH"

        else:

            direction = "NEUTRAL"


        return clean_for_json({

            "direction":
                direction,

            "bullish_score":
                bullish,

            "bearish_score":
                bearish,

            "trend_20d_pct":
                round_or_none(
                    trend20
                ),

            "trend_5d_pct":
                round_or_none(
                    trend5
                ),

            "volatility_pct":
                round_or_none(
                    volatility
                )

        })


# =========================================================
# RISK AGENT
# =========================================================

class RiskAgent:

    def analyze(self, df):

        if df is None or df.empty:

            return {
                "risk": "UNKNOWN",
                "atr": None,
                "atr_pct": None,
                "stop_loss_pct": 0,
                "target_pct": 0
            }


        data = df.copy()


        close = pd.to_numeric(
            data["Close"],
            errors="coerce"
        )


        if "High" in data.columns:

            high = pd.to_numeric(
                data["High"],
                errors="coerce"
            )

        else:

            high = close


        if "Low" in data.columns:

            low = pd.to_numeric(
                data["Low"],
                errors="coerce"
            )

        else:

            low = close


        previous_close = (
            close.shift(1)
        )


        tr1 = (
            high - low
        )


        tr2 = (
            high -
            previous_close
        ).abs()


        tr3 = (
            low -
            previous_close
        ).abs()


        true_range = pd.concat(
            [
                tr1,
                tr2,
                tr3
            ],
            axis=1
        ).max(
            axis=1
        )


        atr = safe_float(
            true_range
            .rolling(14)
            .mean()
            .iloc[-1]
        )


        current = safe_float(
            close.dropna().iloc[-1]
        )


        atr_pct = 0.0


        if current > 0:

            atr_pct = (
                atr /
                current
            ) * 100


        if atr_pct <= 2:

            risk = "LOW"

        elif atr_pct <= 4:

            risk = "MEDIUM"

        else:

            risk = "HIGH"


        stop_loss_pct = max(
            2.0,
            atr_pct * 1.5
        )


        target_pct = max(
            4.0,
            atr_pct * 3
        )


        return clean_for_json({

            "risk":
                risk,

            "atr":
                round_or_none(
                    atr
                ),

            "atr_pct":
                round_or_none(
                    atr_pct
                ),

            "stop_loss_pct":
                round_or_none(
                    stop_loss_pct
                ),

            "target_pct":
                round_or_none(
                    target_pct
                )

        })


# =========================================================
# NEWS AGENT
# =========================================================

class NewsAgent:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({

            "User-Agent":
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "Chrome/120 Safari/537.36"

        })


    def analyze(self, symbol):

        headlines = []


        try:

            query = quote_plus(
                f"{symbol} India stock"
            )


            url = (
                "https://news.google.com/rss/search"
                f"?q={query}"
                "&hl=en-IN"
                "&gl=IN"
                "&ceid=IN:en"
            )


            response = self.session.get(
                url,
                timeout=10
            )


            response.raise_for_status()


            root = ET.fromstring(
                response.text
            )


            for item in root.findall(
                ".//item"
            )[:10]:

                title_node = (
                    item.find("title")
                )

                link_node = (
                    item.find("link")
                )

                pub_node = (
                    item.find("pubDate")
                )


                title = (
                    title_node.text
                    if title_node is not None
                    else ""
                )


                link = (
                    link_node.text
                    if link_node is not None
                    else ""
                )


                pub_date = (
                    pub_node.text
                    if pub_node is not None
                    else ""
                )


                if title:

                    headlines.append({

                        "title":
                            title,

                        "url":
                            link,

                        "published":
                            pub_date

                    })


        except Exception as e:

            print(
                f"News search failed "
                f"for {symbol}: {e}"
            )


        bullish_words = [

            "profit",
            "profits",
            "growth",
            "surge",
            "rises",
            "rally",
            "strong",
            "upgrade",
            "buy",
            "order",
            "contract",
            "deal",
            "approval",
            "expansion",
            "record",
            "positive"

        ]


        bearish_words = [

            "loss",
            "losses",
            "fall",
            "falls",
            "drop",
            "decline",
            "weak",
            "downgrade",
            "sell",
            "fraud",
            "probe",
            "investigation",
            "debt",
            "warning",
            "negative",
            "lawsuit"

        ]


        bullish = 0
        bearish = 0


        for item in headlines:

            text = (
                item["title"]
                .lower()
            )


            for word in bullish_words:

                if word in text:

                    bullish += 1


            for word in bearish_words:

                if word in text:

                    bearish += 1


        if bullish > bearish:

            direction = "BULLISH"


        elif bearish > bullish:

            direction = "BEARISH"


        else:

            direction = "NEUTRAL"


        return {

            "direction":
                direction,

            "bullish_score":
                bullish,

            "bearish_score":
                bearish,

            "bullish_count":
                bullish,

            "bearish_count":
                bearish,

            "headlines":
                headlines

        }


# =========================================================
# OPENROUTER AI AGENT
# =========================================================

class AIAnalyst:

    def __init__(self):

        self.api_key = (
            OPENROUTER_API_KEY
        )

        self.model = (
            OPENROUTER_MODEL
        )


    def run(self, analysis):

        if not self.api_key:

            return {

                "summary":
                    "OpenRouter API key not configured.",

                "available":
                    False

            }


        symbol = analysis.get(
            "symbol",
            ""
        )


        prompt = f"""
You are an Indian stock swing-trading analyst.

Analyze this stock using ONLY the supplied
technical, pattern, risk and news information.

Stock:
{symbol}

Current Price:
{analysis.get("price")}

Technical:
{json.dumps(
    analysis.get("technical", {}),
    default=str
)}

Pattern:
{json.dumps(
    analysis.get("pattern", {}),
    default=str
)}

Risk:
{json.dumps(
    analysis.get("risk", {}),
    default=str
)}

News:
{json.dumps(
    analysis.get("news", {}),
    default=str
)}

Bullish Score:
{analysis.get("bullish_score")}

Bearish Score:
{analysis.get("bearish_score")}

Return concise JSON with:

{{
  "summary": "...",
  "direction": "BUY/SELL/HOLD",
  "confidence": 0-100,
  "key_reason": "...",
  "risk_reason": "...",
  "next_day_bias": "BULLISH/BEARISH/NEUTRAL"
}}

Do not invent financial data.
"""


        headers = {

            "Authorization":
                f"Bearer {self.api_key}",

            "Content-Type":
                "application/json",

            "HTTP-Referer":
                "http://localhost:8000",

            "X-Title":
                "Indian Stock Analytics AI"

        }


        payload = {

            "model":
                self.model,

            "messages": [

                {

                    "role":
                        "system",

                    "content":
                        "You are a disciplined stock analyst."

                },

                {

                    "role":
                        "user",

                    "content":
                        prompt

                }

            ],

            "temperature":
                0.1,

            "max_tokens":
                500

        }


        try:

            response = requests.post(

                "https://openrouter.ai/api/v1/chat/completions",

                headers=headers,

                json=payload,

                timeout=30

            )


            # -------------------------------------------------
            # RATE LIMIT
            # -------------------------------------------------

            if response.status_code == 429:

                print(
                    "OpenRouter rate limit "
                    "reached. Continuing "
                    "without AI."
                )


                return {

                    "summary":
                        "AI temporarily unavailable "
                        "because OpenRouter rate limit "
                        "was reached.",

                    "available":
                        False,

                    "rate_limited":
                        True

                }


            response.raise_for_status()


            data = response.json()


            content = (
                data
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )


            if not content:

                return {

                    "summary":
                        "AI returned no analysis.",

                    "available":
                        False

                }


            # -------------------------------------------------
            # TRY JSON
            # -------------------------------------------------

            try:

                cleaned = (
                    content
                    .replace(
                        "```json",
                        ""
                    )
                    .replace(
                        "```",
                        ""
                    )
                    .strip()
                )


                parsed = json.loads(
                    cleaned
                )


                return clean_for_json(
                    parsed
                )


            except Exception:

                return {

                    "summary":
                        content,

                    "available":
                        True

                }


        except Exception as e:

            print(
                f"OpenRouter failed "
                f"for {symbol}: {e}"
            )


            return {

                "summary":
                    "AI analyst unavailable.",

                "error":
                    str(e),

                "available":
                    False

            }


# =========================================================
# ORCHESTRATOR
# =========================================================

class Orchestrator:

    def __init__(self):

        self.market = (
            MarketData()
        )

        self.technical = (
            TechnicalAgent()
        )

        self.pattern = (
            PatternAgent()
        )

        self.risk = (
            RiskAgent()
        )

        self.news = (
            NewsAgent()
        )

        self.ai = (
            AIAnalyst()
        )


    # =====================================================
    # GET VALID DATA
    # =====================================================

    def get_data(self, symbol):

        symbol = (
            symbol
            .strip()
            .upper()
        )


        ticker = (
            symbol + ".NS"
        )


        try:

            df = (
                self.market
                .get_history(
                    ticker
                )
            )


        except Exception as e:

            raise ValueError(
                f"Could not fetch "
                f"{ticker}: {e}"
            )


        if df is None:

            raise ValueError(
                f"No data found "
                f"for {ticker}"
            )


        if df.empty:

            raise ValueError(
                f"No data found "
                f"for {ticker}"
            )


        if "Close" not in df.columns:

            raise ValueError(
                f"Close price unavailable "
                f"for {ticker}"
            )


        close = (
            pd.to_numeric(
                df["Close"],
                errors="coerce"
            )
            .dropna()
        )


        if close.empty:

            raise ValueError(
                f"No valid price "
                f"for {ticker}"
            )


        price = optional_float(
            close.iloc[-1]
        )


        if (
            price is None
            or price <= 0
        ):

            raise ValueError(
                f"Invalid price "
                f"for {ticker}"
            )


        return df, price


    # =====================================================
    # ANALYZE ONE STOCK
    # =====================================================

    def analyze(self, symbol):

        symbol = (
            symbol
            .strip()
            .upper()
        )


        df, price = (
            self.get_data(
                symbol
            )
        )


        # -------------------------------------------------
        # RUN AGENTS
        # -------------------------------------------------

        technical = (
            self.technical
            .analyze(df)
        )


        pattern = (
            self.pattern
            .analyze(df)
        )


        risk = (
            self.risk
            .analyze(df)
        )


        news = (
            self.news
            .analyze(symbol)
        )


        # -------------------------------------------------
        # SCORES
        # -------------------------------------------------

        bullish = (

            safe_float(
                technical.get(
                    "bullish_score"
                )
            )

            +

            safe_float(
                pattern.get(
                    "bullish_score"
                )
            )

            +

            safe_float(
                news.get(
                    "bullish_score"
                )
            )

        )


        bearish = (

            safe_float(
                technical.get(
                    "bearish_score"
                )
            )

            +

            safe_float(
                pattern.get(
                    "bearish_score"
                )
            )

            +

            safe_float(
                news.get(
                    "bearish_score"
                )
            )

        )


        # -------------------------------------------------
        # DECISION
        # -------------------------------------------------

        difference = (
            bullish -
            bearish
        )


        if difference >= 3:

            decision = "BUY"


        elif difference <= -3:

            decision = "SELL"


        elif difference >= 1:

            decision = "WATCH_BUY"


        elif difference <= -1:

            decision = "WATCH_SELL"


        else:

            decision = "HOLD"


        # -------------------------------------------------
        # RESULT BEFORE AI
        # -------------------------------------------------

        result = {

            "symbol":
                symbol,

            "price":
                round(
                    price,
                    2
                ),

            "decision":
                decision,

            "bullish_score":
                round(
                    bullish,
                    2
                ),

            "bearish_score":
                round(
                    bearish,
                    2
                ),

            "technical":
                technical,

            "pattern":
                pattern,

            "risk":
                risk,

            "news":
                news,

            "ai":
                {},

            "generated_at":
                datetime.now().isoformat()

        }


        return clean_for_json(
            result
        )


    # =====================================================
    # TOP 5
    # =====================================================

    def top5(self):

        results = []


        print(
            "\n================================"
        )

        print(
            "STARTING TOP 50 ANALYSIS"
        )

        print(
            "================================"
        )


        # -------------------------------------------------
        # ANALYZE ALL 50
        # -------------------------------------------------

        for index, symbol in enumerate(
            UNIVERSE,
            start=1
        ):

            print(
                f"[{index}/"
                f"{len(UNIVERSE)}] "
                f"Analyzing {symbol}"
            )


            try:

                result = (
                    self.analyze(
                        symbol
                    )
                )


                if not result:

                    continue


                price = optional_float(
                    result.get(
                        "price"
                    )
                )


                if (
                    price is None
                    or price <= 0
                ):

                    print(
                        f"Skipping {symbol}: "
                        f"invalid price"
                    )

                    continue


                results.append(
                    result
                )


            except Exception as e:

                print(
                    f"Skipping {symbol}: "
                    f"{e}"
                )

                continue


        # -------------------------------------------------
        # RANKING
        # -------------------------------------------------

        def score(result):

            bullish = safe_float(
                result.get(
                    "bullish_score",
                    0
                )
            )


            bearish = safe_float(
                result.get(
                    "bearish_score",
                    0
                )
            )


            conviction = abs(
                bullish -
                bearish
            )


            strongest = max(
                bullish,
                bearish
            )


            # Higher conviction gets more weight

            return (
                strongest
                +
                conviction * 0.5
            )


        results.sort(
            key=score,
            reverse=True
        )


        # -------------------------------------------------
        # TOP 5
        # -------------------------------------------------

        top = results[:5]


        # -------------------------------------------------
        # AI ANALYSIS ONLY FOR TOP 5
        # -------------------------------------------------

        print(
            "\n================================"
        )

        print(
            "TOP 5 AI ANALYSIS"
        )

        print(
            "================================"
        )


        for result in top:

            try:

                print(
                    f"AI analyzing "
                    f"{result['symbol']}"
                )


                result["ai"] = (
                    self.ai.run(
                        result
                    )
                )


            except Exception as e:

                result["ai"] = {

                    "summary":
                        "AI unavailable",

                    "available":
                        False,

                    "error":
                        str(e)

                }


        # -------------------------------------------------
        # FINAL CLEAN
        # -------------------------------------------------

        top = clean_for_json(
            top
        )


        print(
            "\n================================"
        )

        print(
            f"ANALYSIS COMPLETE: "
            f"{len(results)} valid stocks"
        )

        print(
            "================================"
        )


        return top


# =========================================================
# OPTIONAL COMPATIBILITY CLASS
# =========================================================

class StockAnalysisAgents:

    """
    Compatibility wrapper for the previous
    version of the project.

    This keeps older code working while
    Orchestrator is now the main interface.
    """

    def __init__(
        self,
        market=None,
        technical_agent=None,
        pattern_agent=None,
        risk_agent=None,
        news_agent=None,
        llm=None,
        universe=None
    ):

        self.orchestrator = (
            Orchestrator()
        )

        self.market = (
            market
            or self.orchestrator.market
        )

        self.technical_agent = (
            technical_agent
            or self.orchestrator.technical
        )

        self.pattern_agent = (
            pattern_agent
            or self.orchestrator.pattern
        )

        self.risk_agent = (
            risk_agent
            or self.orchestrator.risk
        )

        self.news_agent = (
            news_agent
            or self.orchestrator.news
        )

        self.llm = (
            llm
            or self.orchestrator.ai
        )

        self.universe = (
            universe
            or UNIVERSE
        )


    def analyze(self, symbol):

        return self.orchestrator.analyze(
            symbol
        )


    def top5(self):

        return self.orchestrator.top5()