const API = "http://127.0.0.1:8000";

// Better fetch with error logging and timeout
async function fetchAPI(endpoint, options = {}) {
    try {
        const url = `${API}${endpoint}`;
        const timeout = options.timeout || 60000; // 60 second default timeout
        console.log(`[API] Fetching: ${url} (timeout: ${timeout}ms)`);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                ...options.headers,
            },
        });
        clearTimeout(timeoutId);

        if (response.status === 204) {
            return null;
        }

        const text = await response.text();
        let data = null;

        if (text) {
            try {
                data = JSON.parse(text);
            } catch (e) {
                throw new Error(`Invalid JSON from ${endpoint}: ${text.slice(0, 120)}`);
            }
        }

        if (!response.ok) {
            const errorMsg = data?.detail || data?.message || `HTTP ${response.status}`;
            throw new Error(errorMsg);
        }

        console.log(`[API] Success: ${endpoint}`, data);
        return data;
    } catch (error) {
        console.error(`[API] Error for ${endpoint}:`, error.message);
        throw error;
    }
}

/* =====================================================
   INITIALIZATION
===================================================== */

document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    updateTime();
    setInterval(updateTime, 1000);
    loadTop5();
    loadBreakoutScan();
    loadMomentumScan();
    loadRsiScan();
    loadAnalytics();
    refreshPortfolio();
});

/* =====================================================
   TIME UPDATE
===================================================== */

function updateTime() {
    const now = new Date();
    document.getElementById('timeDisplay').textContent = now.toLocaleTimeString();
}

/* =====================================================
   NAVIGATION
===================================================== */

function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active from all links
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Hide all sections
            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            
            // Show selected section
            const sectionId = this.dataset.section + '-section';
            const section = document.getElementById(sectionId);
            if (section) {
                section.classList.add('active');
                
                // Load data for specific sections
                if (this.dataset.section === 'dashboard') {
                    loadTop5();
                } else if (this.dataset.section === 'trading') {
                    refreshPortfolio();
                } else if (this.dataset.section === 'analytics') {
                    loadAnalytics();
                }
            }
        });
    });
}

function autoRefresh() {
    const activeSection = document.querySelector('.content-section.active');
    if (activeSection.id.includes('dashboard')) {
        loadTop5();
    } else if (activeSection.id.includes('trading')) {
        refreshPortfolio();
    }
}

/* =====================================================
   TOP 5 DASHBOARD
===================================================== */

async function loadTop5() {
    const container = document.getElementById("top5");
    
    container.innerHTML = `
        <div class="loading-spinner">
            <i class="fas fa-spinner"></i>
            Analyzing Top 50 stocks...
        </div>
    `;

    try {
        const data = await fetchAPI("/top5?skip_ai=true", { timeout: 45000 });
        const results = data.results || [];

        let buyCount = 0;
        let sellCount = 0;

        results.forEach(stock => {
            if (stock.decision === "BUY" || stock.decision === "WATCH_BUY") {
                buyCount++;
            }
            if (stock.decision === "SELL" || stock.decision === "WATCH_SELL") {
                sellCount++;
            }
        });

        document.getElementById("buyCount").textContent = buyCount;
        document.getElementById("sellCount").textContent = sellCount;
        document.getElementById("lastScan").textContent = new Date().toLocaleTimeString();

        if (results.length === 0) {
            container.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--text-secondary);">No analysis results available.</div>`;
            return;
        }

        container.innerHTML = results
            .map((stock, index) => createStockCard(stock, index + 1))
            .join("");

    } catch (error) {
        console.error(error);
        const errorMsg = error.name === 'AbortError' ? 'Request timeout - backend is busy' : error.message;
        container.innerHTML = `
            <div style="padding: 20px; color: var(--secondary);">
                ❌ Error: ${errorMsg}
            </div>
        `;
    }
}

function createStockCard(stock, rank) {
    const decision = stock.decision || "HOLD";
    let directionClass = "direction-hold";

    if (decision === "BUY" || decision === "WATCH_BUY") {
        directionClass = decision === "BUY" ? "direction-buy" : "direction-watch";
    }
    if (decision === "SELL" || decision === "WATCH_SELL") {
        directionClass = decision === "SELL" ? "direction-sell" : "direction-watch";
    }

    const bullish = stock.bullish_score ?? 0;
    const bearish = stock.bearish_score ?? 0;
    const rsi = stock.technical?.rsi ?? "-";
    const newsDirection = stock.news?.direction ?? "NEUTRAL";

    return `
        <div class="stock-card">
            <div class="stock-header">
                <div>
                    <div class="stock-symbol">${stock.symbol}</div>
                    <div class="stock-price">₹${stock.price ?? "-"}</div>
                </div>
                <div class="stock-rank">#${rank}</div>
            </div>

            <div class="score-display">
                <div>
                    <div class="metric-label">Strongest Signal</div>
                    <div class="score-value">${Math.max(bullish, bearish)}</div>
                </div>
                <div class="direction-badge ${directionClass}">
                    ${decision}
                </div>
            </div>

            <div class="signal-info">
                <div class="signal-row">
                    <span>🟢 Bullish</span>
                    <strong>${bullish}</strong>
                </div>
                <div class="signal-row">
                    <span>🔴 Bearish</span>
                    <strong>${bearish}</strong>
                </div>
                <div class="signal-row">
                    <span>📊 RSI</span>
                    <strong>${rsi}</strong>
                </div>
                <div class="signal-row">
                    <span>📰 News</span>
                    <strong>${newsDirection}</strong>
                </div>
            </div>
        </div>
    `;
}

/* =====================================================
   MARKET SCANS
===================================================== */

async function loadBreakoutScan() {
    const container = document.getElementById("breakout-results");
    container.innerHTML = `<i class="fas fa-spinner"></i> Scanning...`;

    try {
        const data = await fetchAPI("/scan/breakout");
        const results = data.results || [];
        container.innerHTML = results.length > 0
            ? results.slice(0, 5).map(r => `<div>• ${r.symbol} - ₹${r.price}</div>`).join("")
            : "No breakout stocks found";

    } catch (error) {
        container.innerHTML = `<span style="color: var(--secondary);">❌ ${error.message}</span>`;
    }
}

async function loadMomentumScan() {
    const container = document.getElementById("momentum-results");
    container.innerHTML = `<i class="fas fa-spinner"></i> Scanning...`;

    try {
        const data = await fetchAPI("/scan/momentum");
        const results = data.results || [];
        container.innerHTML = results.length > 0
            ? results.slice(0, 5).map(r => `<div>• ${r.symbol} - ₹${r.price}</div>`).join("")
            : "No momentum stocks found";

    } catch (error) {
        container.innerHTML = `<span style="color: var(--secondary);">❌ ${error.message}</span>`;
    }
}

async function loadRsiScan() {
    const container = document.getElementById("rsi-results");
    container.innerHTML = `<i class="fas fa-spinner"></i> Scanning...`;

    try {
        const data = await fetchAPI("/scan/rsi");
        const results = data.results || [];
        container.innerHTML = results.length > 0
            ? results.slice(0, 5).map(r => `<div>• ${r.symbol} - RSI: ${r.rsi?.toFixed(2) ?? 'N/A'}</div>`).join("")
            : "No RSI opportunities found";

    } catch (error) {
        container.innerHTML = `<span style="color: var(--secondary);">❌ ${error.message}</span>`;
    }
}

/* =====================================================
   ANALYTICS
===================================================== */

async function loadAnalytics() {
    const container = document.getElementById("analytics-content");
    container.innerHTML = `<i class="fas fa-spinner"></i> Loading analytics...`;

    try {
        const data = await fetchAPI("/analytics");

        let analyticsHtml = `<strong>Portfolio Analytics</strong><br>`;
        analyticsHtml += `Win Rate: ${(data.win_rate || 0).toFixed(2)}%<br>`;
        analyticsHtml += `Total Trades: ${data.total_trades || 0}<br>`;
        analyticsHtml += `Average Return: ${(data.avg_return || 0).toFixed(2)}%<br>`;
        analyticsHtml += `Best Trade: ${(data.best_trade || 0).toFixed(2)}%<br>`;
        analyticsHtml += `Worst Trade: ${(data.worst_trade || 0).toFixed(2)}%<br>`;

        container.innerHTML = analyticsHtml;

    } catch (error) {
        container.innerHTML = `<span style="color: var(--secondary);">❌ ${error.message}</span>`;
    }
}

/* =====================================================
   STOCK ANALYZER
===================================================== */

async function analyzeStock() {
    const symbol = document.getElementById("analyzeSymbol").value.trim().toUpperCase();
    
    if (!symbol) {
        document.getElementById("analyzer-results").innerHTML = 
            `<span style="color: var(--warning);">Please enter a stock symbol</span>`;
        return;
    }

    const container = document.getElementById("analyzer-results");
    container.innerHTML = `
        <div class="loading-spinner">
            <i class="fas fa-spinner"></i>
            Analyzing ${symbol}...
        </div>
    `;

    try {
        const data = await fetchAPI(`/analyze/${symbol}`);

        if (!data || !data.symbol) {
            throw new Error("No data returned for this symbol. Try an Indian listed ticker such as TCS, INFY, RELIANCE.");
        }

        const decision = data.decision || "HOLD";
        let decisionClass = "direction-hold";

        if (decision === "BUY" || decision === "WATCH_BUY") {
            decisionClass = decision === "BUY" ? "direction-buy" : "direction-watch";
        }
        if (decision === "SELL" || decision === "WATCH_SELL") {
            decisionClass = decision === "SELL" ? "direction-sell" : "direction-watch";
        }

        const strongestScore = Math.max(data.bullish_score ?? 0, data.bearish_score ?? 0);
        const news = data.news || {};
        const technical = data.technical || {};
        const risk = data.risk || {};
        const pattern = data.pattern || {};
        const ai = data.ai || {};

        let html = `
            <div style="margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid var(--border-color);">
                <h2 style="color: var(--primary); margin-bottom: 10px;">${data.symbol}</h2>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 20px;">₹${data.price ?? "-"}</div>
                    <div style="text-align: right;">
                        <div style="font-size: 28px; font-weight: 700; color: var(--primary);">${strongestScore}</div>
                        <div class="direction-badge ${decisionClass}">${decision}</div>
                    </div>
                </div>
            </div>

            <div class="analysis-grid">
                <div class="analysis-section">
                    <h4><i class="fas fa-signal"></i> Signal Scores</h4>
                    <div class="analysis-item">
                        <span class="analysis-label">🟢 Bullish</span>
                        <span class="analysis-value">${data.bullish_score ?? 0}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">🔴 Bearish</span>
                        <span class="analysis-value">${data.bearish_score ?? 0}</span>
                    </div>
                </div>

                <div class="analysis-section">
                    <h4><i class="fas fa-chart-line"></i> Technical Analysis</h4>
                    <div class="analysis-item">
                        <span class="analysis-label">Direction</span>
                        <span class="analysis-value">${technical.direction ?? "-"}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">RSI</span>
                        <span class="analysis-value">${technical.rsi ?? "-"}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">EMA20</span>
                        <span class="analysis-value">₹${technical.ema20 ?? "-"}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">EMA50</span>
                        <span class="analysis-value">₹${technical.ema50 ?? "-"}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">5D Return</span>
                        <span class="analysis-value">${technical.five_day_return ?? "-"}%</span>
                    </div>
                </div>

                <div class="analysis-section">
                    <h4><i class="fas fa-shapes"></i> Pattern Analysis</h4>
                    <div class="analysis-item">
                        <span class="analysis-label">Direction</span>
                        <span class="analysis-value">${pattern.direction ?? "-"}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">20D Trend</span>
                        <span class="analysis-value">${pattern.trend_20d_pct ?? "-"}%</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">Bullish Score</span>
                        <span class="analysis-value">${pattern.bullish_score ?? "-"}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">Bearish Score</span>
                        <span class="analysis-value">${pattern.bearish_score ?? "-"}</span>
                    </div>
                </div>

                <div class="analysis-section">
                    <h4><i class="fas fa-exclamation-triangle"></i> Risk Metrics</h4>
                    <div class="analysis-item">
                        <span class="analysis-label">Risk Level</span>
                        <span class="analysis-value">${risk.risk ?? "-"}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">ATR</span>
                        <span class="analysis-value">₹${risk.atr ?? "-"}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">Stop Loss</span>
                        <span class="analysis-value">${risk.stop_loss_pct ?? "-"}%</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">Target</span>
                        <span class="analysis-value">${risk.target_pct ?? "-"}%</span>
                    </div>
                </div>

                <div class="analysis-section">
                    <h4><i class="fas fa-newspaper"></i> News Analysis</h4>
                    <div class="analysis-item">
                        <span class="analysis-label">Direction</span>
                        <span class="analysis-value">${news.direction ?? "NEUTRAL"}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">🟢 Bullish</span>
                        <span class="analysis-value">${news.bullish_count ?? 0}</span>
                    </div>
                    <div class="analysis-item">
                        <span class="analysis-label">🔴 Bearish</span>
                        <span class="analysis-value">${news.bearish_count ?? 0}</span>
                    </div>
                </div>

                <div class="analysis-section">
                    <h4><i class="fas fa-brain"></i> AI Analysis</h4>
                    <p style="font-size: 12px; line-height: 1.5; margin: 0;">
                        ${ai.summary || "AI analysis unavailable."}
                    </p>
                </div>
            </div>
        `;

        container.innerHTML = html;

    } catch (error) {
        console.error(error);
        container.innerHTML = `
            <div style="color: var(--secondary); padding: 20px; text-align: center;">
                ❌ Error: ${error.message}
            </div>
        `;
    }
}

/* =====================================================
   PAPER TRADING
===================================================== */

async function refreshPortfolio() {
    try {
        const data = await fetchAPI("/paper");

        // Update stats
        if (document.getElementById("cash")) {
            document.getElementById("cash").textContent = 
                `₹${Number(data.cash || 0).toLocaleString("en-IN", {maximumFractionDigits: 2})}`;
        }
        if (document.getElementById("positionCount")) {
            document.getElementById("positionCount").textContent = Object.keys(data.positions || {}).length;
        }
        if (document.getElementById("tradeCount")) {
            document.getElementById("tradeCount").textContent = (data.trades || []).length;
        }
        if (document.getElementById("totalPnl")) {
            document.getElementById("totalPnl").textContent = formatPnl(data.total_pnl);
        }

        // Render positions
        renderPositions(data.positions || {});

        // Render trade history
        renderTradeHistory(data.trades || []);

    } catch (error) {
        console.error(error);
        alert("Error refreshing portfolio: " + error.message);
    }
}

function formatPnl(value) {
    const pnl = Number(value || 0);
    const sign = pnl >= 0 ? "+" : "";
    return `${sign}₹${pnl.toLocaleString("en-IN", {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

function renderPositions(positions) {
    const container = document.getElementById("positions");
    const symbols = Object.keys(positions);

    if (symbols.length === 0) {
        container.innerHTML = `<div style="text-align: center; color: var(--text-secondary); padding: 20px;">No open positions</div>`;
        return;
    }

    container.innerHTML = symbols.map(symbol => {
        const p = positions[symbol];
        const pnl = Number(p.unrealized_pnl || 0);
        const pnlPercent = Number(p.pnl_percent || 0);
        const pnlClass = pnl >= 0 ? "pnl-positive" : "pnl-negative";
        const sign = pnl >= 0 ? "+" : "";

        return `
            <div class="position-item">
                <div class="position-info">
                    <div class="position-symbol">${symbol}</div>
                    <div class="position-details">
                        <span>Qty: ${p.quantity}</span>
                        <span>Avg: ₹${Number(p.avg_price).toFixed(2)}</span>
                        <span>Current: ₹${Number(p.current_price).toFixed(2)}</span>
                    </div>
                </div>
                <div class="position-pnl">
                    <div class="pnl-amount ${pnlClass}">
                        ₹${Number(p.current_value).toLocaleString("en-IN")}
                    </div>
                    <div class="pnl-percent ${pnlClass}">
                        ${sign}₹${pnl.toFixed(2)} (${sign}${pnlPercent.toFixed(2)}%)
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

function renderTradeHistory(trades) {
    const container = document.getElementById("tradeHistory");

    if (!trades.length) {
        container.innerHTML = `<div style="text-align: center; color: var(--text-secondary); padding: 20px;">No trades yet</div>`;
        return;
    }

    container.innerHTML = trades.map(trade => {
        const tradeClass = trade.type === "BUY" ? "trade-buy" : "trade-sell";
        return `
            <div class="trade-item">
                <span class="trade-type ${tradeClass}">${trade.type}</span>
                <span>${trade.symbol} @ ₹${Number(trade.price).toFixed(2)} x ${trade.quantity}</span>
                <span style="color: var(--text-secondary); font-size: 12px;">${new Date(trade.timestamp).toLocaleString()}</span>
            </div>
        `;
    }).join("");
}

async function executeTrade(tradeType) {
    const symbol = document.getElementById("tradeSymbol").value.trim().toUpperCase();
    const price = parseFloat(document.getElementById("tradePrice").value);
    const quantity = parseInt(document.getElementById("tradeQty").value);

    if (!symbol || !price || !quantity) {
        showTradeResult("Please fill all fields", false);
        return;
    }

    const resultContainer = document.getElementById("tradeResult");
    resultContainer.textContent = "Executing trade...";

    try {
        const endpoint = tradeType === 'buy' ? `/paper/buy/${symbol}` : `/paper/sell/${symbol}`;
        const data = await fetchAPI(endpoint + `?price=${price}&quantity=${quantity}`, {
            method: 'POST'
        });

        showTradeResult(`✓ ${tradeType.toUpperCase()} order placed: ${symbol}`, true);
        
        // Reset form
        document.getElementById("tradeSymbol").value = "TCS";
        document.getElementById("tradePrice").value = "";
        document.getElementById("tradeQty").value = "1";

        // Refresh portfolio
        setTimeout(refreshPortfolio, 1000);

    } catch (error) {
        showTradeResult(`✗ Error: ${error.message}`, false);
    }
}

function showTradeResult(message, isSuccess) {
    const container = document.getElementById("tradeResult");
    container.textContent = message;
    container.className = isSuccess ? "trade-result success" : "trade-result error";
}
