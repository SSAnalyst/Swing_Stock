import yfinance as yf
import pandas as pd

class MarketData:
    def get_history(self,symbol,period="5y",interval="1d"):
        df=yf.download(symbol,period=period,interval=interval,auto_adjust=True,progress=False)
        if df.empty: raise ValueError(f"No data found for {symbol}")
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        df.reset_index(inplace=True)
        return df
