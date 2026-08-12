const API = "http://127.0.0.1:8000";

const $ = (id) => document.getElementById(id);


/* =====================================================
   LOAD TOP 5
===================================================== */

async function loadTop5() {

    const container = $("top5");

    container.innerHTML = `
        <div class="loading">
            Analyzing Top 50 stocks...
        </div>
    `;

    try {

        const response = await fetch(`${API}/top5`);

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Failed to load Top 5"
            );
        }

        const results = data.results || [];

        let buyCount = 0;
        let sellCount = 0;

        results.forEach(stock => {

            if (
                stock.decision === "BUY" ||
                stock.decision === "WATCH_BUY"
            ) {
                buyCount++;
            }

            if (
                stock.decision === "SELL" ||
                stock.decision === "WATCH_SELL"
            ) {
                sellCount++;
            }

        });


        $("buyCount").textContent = buyCount;

        $("sellCount").textContent = sellCount;

        $("lastScan").textContent =
            new Date().toLocaleTimeString();


        if (results.length === 0) {

            container.innerHTML = `
                <div class="card">
                    No analysis results available.
                </div>
            `;

            return;
        }


        container.innerHTML = results
            .map((stock, index) =>
                createStockCard(
                    stock,
                    index + 1
                )
            )
            .join("");


    } catch (error) {

        console.error(error);

        container.innerHTML = `
            <div class="card">
                ❌ Error loading analysis:
                ${error.message}
            </div>
        `;

    }

}



/* =====================================================
   CREATE STOCK CARD
===================================================== */

function createStockCard(stock, rank) {

    const decision =
        stock.decision || "HOLD";


    let directionClass =
        "direction-hold";


    if (
        decision === "BUY" ||
        decision === "WATCH_BUY"
    ) {

        directionClass =
            decision === "BUY"
                ? "direction-buy"
                : "direction-watch";
    }


    if (
        decision === "SELL" ||
        decision === "WATCH_SELL"
    ) {

        directionClass =
            decision === "SELL"
                ? "direction-sell"
                : "direction-watch";
    }


    const bullish =
        stock.bullish_score ?? 0;


    const bearish =
        stock.bearish_score ?? 0;


    const rsi =
        stock.technical?.rsi ?? "-";


    const newsDirection =
        stock.news?.direction ?? "NEUTRAL";


    return `

        <div class="stock-card">

            <div class="stock-rank">
                #${rank}
            </div>


            <div class="stock-symbol">
                ${stock.symbol}
            </div>


            <div class="stock-price">
                ₹${stock.price ?? "-"}
            </div>


            <div class="score">
                ${Math.max(
                    bullish,
                    bearish
                )}
            </div>


            <div class="score-label">
                Strongest Signal Score
            </div>


            <div class="direction ${directionClass}">
                ${decision}
            </div>


            <div class="score-row">

                <span>
                    🟢 Bullish
                </span>

                <b>
                    ${bullish}
                </b>

            </div>


            <div class="score-row">

                <span>
                    🔴 Bearish
                </span>

                <b>
                    ${bearish}
                </b>

            </div>


            <div class="score-row">

                <span>
                    RSI
                </span>

                <b>
                    ${rsi}
                </b>

            </div>


            <div class="score-row">

                <span>
                    News
                </span>

                <b>
                    ${newsDirection}
                </b>

            </div>

        </div>

    `;
}



/* =====================================================
   ANALYZE SINGLE STOCK
===================================================== */

async function analyzeStock() {

    const symbol =
        $("symbol")
            .value
            .trim()
            .toUpperCase();


    if (!symbol) {

        $("analysis").innerHTML =
            "Please enter a stock symbol.";

        return;
    }


    $("analysis").innerHTML = `
        Analyzing ${symbol}...
    `;


    try {

        const response =
            await fetch(
                `${API}/analyze/${symbol}`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Analysis failed"
            );
        }


        const decision =
            data.decision || "HOLD";


        let decisionClass =
            "direction-watch";


        if (
            decision === "BUY" ||
            decision === "WATCH_BUY"
        ) {

            decisionClass =
                decision === "BUY"
                    ? "direction-buy"
                    : "direction-watch";
        }


        if (
            decision === "SELL" ||
            decision === "WATCH_SELL"
        ) {

            decisionClass =
                decision === "SELL"
                    ? "direction-sell"
                    : "direction-watch";
        }


        const strongestScore =
            Math.max(
                data.bullish_score ?? 0,
                data.bearish_score ?? 0
            );


        const news =
            data.news || {};


        const technical =
            data.technical || {};


        const risk =
            data.risk || {};


        const pattern =
            data.pattern || {};


        const ai =
            data.ai || {};


        $("analysis").innerHTML = `

            <div class="analysis-header">

                <div>

                    <h2>
                        ${data.symbol}
                    </h2>

                    <div>
                        ₹${data.price ?? "-"}
                    </div>

                </div>


                <div>

                    <div class="analysis-score">
                        ${strongestScore}
                    </div>

                    <div class="direction ${decisionClass}">
                        ${decision}
                    </div>

                </div>

            </div>


            <!-- SIGNAL SCORES -->

            <div class="analysis-section">

                <h3>
                    📊 Signal Scores
                </h3>

                <p>
                    🟢 Bullish:
                    <b>
                        ${data.bullish_score ?? 0}
                    </b>
                </p>

                <p>
                    🔴 Bearish:
                    <b>
                        ${data.bearish_score ?? 0}
                    </b>
                </p>

            </div>


            <!-- TECHNICAL -->

            <div class="analysis-section">

                <h3>
                    📈 Technical Analysis
                </h3>

                <p>
                    Direction:
                    <b>
                        ${technical.direction ?? "-"}
                    </b>
                </p>

                <p>
                    RSI:
                    ${technical.rsi ?? "-"}
                </p>

                <p>
                    EMA20:
                    ₹${technical.ema20 ?? "-"}
                </p>

                <p>
                    EMA50:
                    ₹${technical.ema50 ?? "-"}
                </p>

                <p>
                    5 Day Return:
                    ${technical.five_day_return ?? "-"}%
                </p>

            </div>


            <!-- PATTERN -->

            <div class="analysis-section">

                <h3>
                    📐 Pattern Analysis
                </h3>

                <p>
                    Direction:
                    <b>
                        ${pattern.direction ?? "-"}
                    </b>
                </p>

                <p>
                    20 Day Trend:
                    ${pattern.trend_20d_pct ?? "-"}%
                </p>

                <p>
                    Pattern Bullish Score:
                    ${pattern.bullish_score ?? "-"}
                </p>

                <p>
                    Pattern Bearish Score:
                    ${pattern.bearish_score ?? "-"}
                </p>

            </div>


            <!-- RISK -->

            <div class="analysis-section">

                <h3>
                    ⚠️ Risk
                </h3>

                <p>
                    Risk:
                    <b>
                        ${risk.risk ?? "-"}
                    </b>
                </p>

                <p>
                    ATR:
                    ₹${risk.atr ?? "-"}
                </p>

                <p>
                    ATR %:
                    ${risk.atr_pct ?? "-"}%
                </p>

                <p>
                    Suggested Stop Loss:
                    ${risk.stop_loss_pct ?? "-"}%
                </p>

                <p>
                    Suggested Target:
                    ${risk.target_pct ?? "-"}%
                </p>

            </div>


            <!-- NEWS -->

            <div class="analysis-section">

                <h3>
                    📰 News Analysis
                </h3>

                <p>
                    News Direction:
                    <b>
                        ${news.direction ?? "NEUTRAL"}
                    </b>
                </p>

                <p>
                    🟢 Bullish Headlines:
                    ${news.bullish_count ?? 0}
                </p>

                <p>
                    🔴 Bearish Headlines:
                    ${news.bearish_count ?? 0}
                </p>


                ${
                    news.headlines &&
                    news.headlines.length
                        ? `

                            <h4>
                                Recent Headlines
                            </h4>

                            <ul>

                                ${
                                    news.headlines
                                        .map(
                                            item =>
                                                `<li>
                                                    ${item.title}
                                                </li>`
                                        )
                                        .join("")
                                }

                            </ul>

                        `
                        : ""
                }

            </div>


            <!-- AI -->

            <div class="analysis-section">

                <h3>
                    🤖 AI Analyst
                </h3>

                <p>
                    ${
                        ai.summary ||
                        "AI analysis unavailable."
                    }
                </p>

            </div>

        `;


    } catch (error) {

        console.error(error);

        $("analysis").innerHTML = `
            ❌ Error:
            ${error.message}
        `;

    }

}



/* =====================================================
   PAPER TRADING
===================================================== */

async function refreshPortfolio() {

    const portfolio =
        $("portfolio");


    if (portfolio) {

        portfolio.textContent =
            "Refreshing portfolio prices...";

    }


    try {

        /*
         * IMPORTANT:
         *
         * The backend now fetches the latest
         * available market price for every
         * open position.
         *
         * Therefore clicking Refresh will
         * recalculate unrealized P&L.
         */

        const response =
            await fetch(
                `${API}/paper`
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to load portfolio"
            );
        }


        /* -----------------------------------------
           ACCOUNT SUMMARY
        ----------------------------------------- */

        if ($("cash")) {

            $("cash").textContent =
                `₹${Number(
                    data.cash || 0
                ).toLocaleString(
                    "en-IN",
                    {
                        maximumFractionDigits: 2
                    }
                )}`;
        }


        if ($("positionCount")) {

            $("positionCount").textContent =
                Object.keys(
                    data.positions || {}
                ).length;
        }


        if ($("tradeCount")) {

            $("tradeCount").textContent =
                (
                    data.trades || []
                ).length;
        }


        /* -----------------------------------------
           OPTIONAL PORTFOLIO VALUES
        ----------------------------------------- */

        if ($("invested")) {

            $("invested").textContent =
                `₹${Number(
                    data.invested || 0
                ).toLocaleString(
                    "en-IN"
                )}`;
        }


        if ($("currentValue")) {

            $("currentValue").textContent =
                `₹${Number(
                    data.current_value || 0
                ).toLocaleString(
                    "en-IN"
                )}`;
        }


        if ($("unrealizedPnl")) {

            $("unrealizedPnl").textContent =
                formatPnl(
                    data.unrealized_pnl
                );
        }


        if ($("realizedPnl")) {

            $("realizedPnl").textContent =
                formatPnl(
                    data.realized_pnl
                );
        }


        if ($("totalPnl")) {

            $("totalPnl").textContent =
                formatPnl(
                    data.total_pnl
                );
        }


        /* -----------------------------------------
           POSITIONS
        ----------------------------------------- */

        renderPositions(
            data.positions || {}
        );


        /* -----------------------------------------
           TRADE HISTORY
        ----------------------------------------- */

        renderTradeHistory(
            data.trades || []
        );


        if (portfolio) {

            portfolio.textContent =
                JSON.stringify(
                    data,
                    null,
                    2
                );
        }


    } catch (error) {

        console.error(error);


        if (portfolio) {

            portfolio.textContent =
                `❌ ${error.message}`;
        }

    }

}



/* =====================================================
   FORMAT P&L
===================================================== */

function formatPnl(value) {

    const pnl =
        Number(value || 0);


    const sign =
        pnl >= 0
            ? "+"
            : "";


    return `${sign}₹${pnl.toLocaleString(
        "en-IN",
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    )}`;

}



/* =====================================================
   RENDER OPEN POSITIONS
===================================================== */

function renderPositions(
    positions
) {

    const container =
        $("positions");


    if (!container) {
        return;
    }


    const symbols =
        Object.keys(positions);


    if (symbols.length === 0) {

        container.innerHTML =
            "No open positions.";

        return;
    }


    container.innerHTML =
        symbols.map(symbol => {

            const p =
                positions[symbol];


            const pnl =
                Number(
                    p.unrealized_pnl || 0
                );


            const pnlPercent =
                Number(
                    p.pnl_percent || 0
                );


            const pnlClass =
                pnl >= 0
                    ? "direction-buy"
                    : "direction-sell";


            const sign =
                pnl >= 0
                    ? "+"
                    : "";


            return `

                <div class="position">

                    <div>

                        <b>
                            ${symbol}
                        </b>

                        <br>

                        Quantity:
                        ${p.quantity}

                    </div>


                    <div>

                        Avg Buy
                        <br>

                        <b>
                            ₹${Number(
                                p.avg_price
                            ).toFixed(2)}
                        </b>

                    </div>


                    <div>

                        Latest
                        <br>

                        <b>
                            ₹${Number(
                                p.current_price
                            ).toFixed(2)}
                        </b>

                    </div>


                    <div>

                        Current Value
                        <br>

                        <b>
                            ₹${Number(
                                p.current_value
                            ).toLocaleString(
                                "en-IN"
                            )}
                        </b>

                    </div>


                    <div>

                        Unrealized P&L
                        <br>

                        <span
                            class="direction ${pnlClass}">

                            ${sign}₹${pnl.toFixed(2)}

                            (${sign}${pnlPercent.toFixed(2)}%)

                        </span>

                    </div>

                </div>

            `;

        }).join("");

}



/* =====================================================
   TRADE HISTORY
===================================================== */

function renderTradeHistory(
    trades
) {

    const container =
        $("tradeHistory");


    if (!container) {
        return;
    }


    if (!trades.length) {

        container.innerHTML =
            "No trades yet.";

        return;
    }


    container.innerHTML = `

        <div class="trade-row">

            <b>Symbol</b>

            <b>Side</b>

            <b>Qty</b>

            <b>Price</b>

            <b>P&L</b>

            <b>Time</b>

        </div>


        ${
            trades
                .slice()
                .reverse()
                .map(trade => {

                    const pnl =
                        Number(
                            trade.pnl || 0
                        );


                    const pnlClass =
                        pnl > 0
                            ? "direction-buy"
                            : pnl < 0
                                ? "direction-sell"
                                : "";


                    return `

                        <div class="trade-row">

                            <span>
                                ${trade.symbol}
                            </span>

                            <span>
                                ${trade.side}
                            </span>

                            <span>
                                ${trade.quantity}
                            </span>

                            <span>
                                ₹${Number(
                                    trade.price
                                ).toFixed(2)}
                            </span>

                            <span
                                class="${pnlClass}">

                                ${formatPnl(pnl)}

                            </span>

                            <span>

                                ${new Date(
                                    trade.timestamp
                                ).toLocaleString()}

                            </span>

                        </div>

                    `;

                })
                .join("")
        }

    `;

}



/* =====================================================
   EXECUTE PAPER TRADE
===================================================== */

async function executeTrade(
    side
) {

    const symbol =
        $("tradeSymbol")
            .value
            .trim()
            .toUpperCase();


    const price =
        Number(
            $("tradePrice").value
        );


    const quantity =
        Number(
            $("tradeQty").value
        );


    if (
        !symbol ||
        price <= 0 ||
        quantity <= 0
    ) {

        $("tradeResult").textContent =
            "❌ Please enter valid symbol, price and quantity.";

        return;
    }


    try {

        const response =
            await fetch(

                `${API}/paper/${side}/${symbol}?price=${price}&quantity=${quantity}`,

                {
                    method: "POST"
                }

            );


        const data =
            await response.json();


        if (data.error) {

            $("tradeResult").textContent =
                `❌ ${data.error}`;

            return;
        }


        $("tradeResult").textContent =
            `✅ ${side.toUpperCase()} executed successfully.`;


        /*
         * Immediately refresh the portfolio.
         *
         * This means after BUY:
         * current market price is fetched.
         *
         * After SELL:
         * realized P&L is updated.
         */

        await refreshPortfolio();


    } catch (error) {

        console.error(error);

        $("tradeResult").textContent =
            `❌ ${error.message}`;

    }

}



/* =====================================================
   OPTIONAL AUTO REFRESH
===================================================== */

/*
 * We intentionally do NOT refresh every few seconds.
 *
 * Your requirement is:
 *
 *     Click Refresh
 *          ↓
 *     Fetch latest available price
 *          ↓
 *     Calculate P&L
 *
 * Therefore the user controls when the
 * portfolio is revalued.
 *
 * Later we can add an automatic 8 PM
 * portfolio valuation using the same
 * market snapshot as the AI scanner.
 */


/* =====================================================
   INITIAL LOAD
===================================================== */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadTop5();

        refreshPortfolio();

    }
);