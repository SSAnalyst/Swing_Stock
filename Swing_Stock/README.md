# Stock Analytics AI — Phase 3
Includes a 50-stock universe, multi-agent analysis, web/news agent, OpenRouter analyst, top-5 ranking, Analyze workflow and paper trading.

Copy `.env.example` to `.env`, add your keys, then:
`pip install -r requirements.txt`
`python -m uvicorn backend.app:app --reload`

Frontend:
`python -m http.server 5500 --directory frontend`

The frontend is deployable to Netlify. The Python backend must be hosted separately; Netlify alone cannot host this FastAPI process.
