from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .analytics import AnalyticsAgent
from .agents import Orchestrator, UNIVERSE
from .paper import PaperBroker
from .scanner import ScannerEngine
from .database import Database

app = FastAPI(
    title="Stock Analytics AI",
    version="0.4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

db = Database()
orch = Orchestrator()
broker = PaperBroker()
scanner = ScannerEngine()
analytics = AnalyticsAgent()

@app.get("/analytics")
def analytics_summary():

    trades = broker.get_trades()

    return analytics.generate(
        trades
    )

@app.get("/")
def home():
    return {
        "status": "running",
        "version": "0.4.0"
    }


@app.get("/analyze/{symbol}")
def analyze(symbol: str):
    try:
        return orch.analyze(symbol)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@app.get("/top5")
def top5():
    return {
        "results": orch.top5()
    }


@app.get("/universe")
def universe():
    return {
        "count": len(UNIVERSE),
        "symbols": UNIVERSE
    }


@app.get("/scan/breakout")
def breakout():
    return {
        "results": scanner.breakout_scan()
    }


@app.get("/scan/momentum")
def momentum():
    return {
        "results": scanner.momentum_scan()
    }


@app.get("/scan/rsi")
def rsi():
    return {
        "results": scanner.rsi_scan()
    }


@app.get("/paper")
def paper():
    return broker.summary()


@app.post("/paper/buy/{symbol}")
def buy(
    symbol: str,
    price: float,
    quantity: int
):
    return broker.buy(
        symbol.upper(),
        price,
        quantity
    )


@app.post("/paper/sell/{symbol}")
def sell(
    symbol: str,
    price: float,
    quantity: int
):
    return broker.sell(
        symbol.upper(),
        price,
        quantity
    )
