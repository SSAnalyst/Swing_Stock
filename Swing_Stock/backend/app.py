from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .agents import Orchestrator, UNIVERSE
from .paper import PaperBroker

app=FastAPI(title="Stock Analytics AI",version="0.3.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
orch=Orchestrator(); broker=PaperBroker()

@app.get("/")
def home(): return {"status":"running","version":"0.3.0"}

@app.get("/analyze/{symbol}")
def analyze(symbol):
    try: return orch.analyze(symbol)
    except Exception as e: raise HTTPException(400,str(e))

@app.get("/top5")
def top5(): return {"results":orch.top5()}

@app.get("/universe")
def universe(): return {"count":len(UNIVERSE),"symbols":UNIVERSE}

@app.get("/paper")
def paper(): return broker.summary()

@app.post("/paper/buy/{symbol}")
def buy(symbol,price:float,quantity:int): return broker.buy(symbol.upper(),price,quantity)

@app.post("/paper/sell/{symbol}")
def sell(symbol,price:float,quantity:int): return broker.sell(symbol.upper(),price,quantity)
