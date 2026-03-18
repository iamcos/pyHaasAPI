import { state } from './state.js';
import { updateMainChart } from './dashboard.js';

export async function refreshCacheStats() {
    try {
        const resp = await fetch('/api/cache/stats');
        if (resp.ok) {
            const stats = await resp.json();
            const recordElm = document.querySelector('#analytics h2');
            if (recordElm) {
                recordElm.innerHTML = `${stats.total_records.toLocaleString()} <i data-lucide="database" style="color:var(--accent-secondary); width:20px; height:20px"></i>`;
                if (window.lucide) window.lucide.createIcons();
            }
        }
    } catch (e) { console.error("Cache stats failed", e); }
}

export function populateCachedBacktests() {
    const tbody = document.getElementById('cached-backtests-list');
    if (!tbody) return;
    tbody.innerHTML = '';

    let visibleBacktests = state.engine === 'all'
        ? state.cachedBacktests
        : state.cachedBacktests.filter(b => b.engine === state.engine);

    const serverFilter = document.getElementById('vault-server-filter');
    if (serverFilter && serverFilter.value !== 'all') {
        visibleBacktests = visibleBacktests.filter(b => b.server === serverFilter.value);
    }

    if (visibleBacktests.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center">No records found. Sync with Haas or run a Freq backtest.</td></tr>';
        return;
    }

    visibleBacktests.forEach(bt => {
        const badgeClass = bt.engine === 'haas' ? 'haas' : 'freq';
        const tr = document.createElement('tr');
        const roiColor = parseFloat(bt.roi) > 0 ? 'var(--success)' : (parseFloat(bt.roi) < 0 ? 'var(--danger)' : '');
        
        tr.style.cursor = 'pointer';
        tr.onclick = () => {
            updateMainChart(bt.lab_id, bt.id);
            // Show new modal
            openAdvancedMetricsModal(bt.lab_id, bt.id);
        };

        const name = bt.name || `Lab_${bt.lab_id ? bt.lab_id.substring(0,6) : 'Unknown'}`;
        const pair = bt.pair || 'BTC/USDT';
        const trades = bt.trades || 0;
        const roi = bt.roi || '0.00';
        const dd = bt.dd || '0.0';

        const server = bt.server || 'Unknown';
        
        tr.innerHTML = `
            <td><span class="badge ${badgeClass}">${bt.engine.toUpperCase()}</span></td>
            <td style="font-weight:600; color:#fff">${name} <span style="opacity:0.6; font-size:0.8rem">(${bt.backtest_count} bts)</span></td>
            <td style="font-family:'JetBrains Mono'; font-size:0.85rem">${pair}</td>
            <td style="font-family:'Outfit'; font-size:0.85rem; color:var(--accent-secondary); font-weight: 500;">${server}</td>
            <td>${trades}</td>
            <td style="color:${bt.winRate > 60 ? 'var(--success)' : 'inherit'}">${bt.winRate || 0}%</td>
            <td style="color:${roiColor}; font-weight:600">${parseFloat(roi) >= 0 ? '+' + roi : roi}%</td>
            <td style="color:var(--danger)">${dd}%</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderMetricBlock(label, value, colorClass = '', subtitle = '') {
    return `<div class="metric-box">
        <span style="font-size: 0.8rem; color: var(--text-muted)">${label}</span>
        <h4 class="${colorClass}" style="margin-top: 5px">${value}</h4>
        ${subtitle ? `<span style="font-size: 0.7rem; color: var(--text-muted)">${subtitle}</span>` : ''}
    </div>`;
}

export async function openAdvancedMetricsModal(lab_id, bt_id) {
    const modal = document.getElementById('advanced-metrics-modal');
    if (!modal) return;
    const content = document.getElementById('advanced-metrics-content');
    content.innerHTML = '<div style="text-align:center; padding: 2rem"><i data-lucide="loader" class="spin"></i> Loading deep analytics...</div>';
    if (window.lucide) window.lucide.createIcons();
    modal.classList.add('show');

    try {
        const resp = await fetch(`/api/backtest/analysis?lab_id=${lab_id}&backtest_id=${bt_id}`);
        if (!resp.ok) throw new Error("Failed to fetch full metrics");
        const m = await resp.json();

        // Build HTML
        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1rem; margin-bottom: 1rem;">
                <div>
                    <h2 style="font-size: 1.5rem; margin-bottom:0.25rem;">Analysis Report</h2>
                    <span style="font-family: 'JetBrains Mono'; font-size: 0.85rem; color: var(--accent-secondary)">${~~m.total_trades} Trades | ROI: ${m.roi_pct.toFixed(2)}%</span>
                </div>
                <button class="btn btn-ghost" onclick="document.getElementById('advanced-metrics-modal').classList.remove('show')"><i data-lucide="x"></i></button>
            </div>
        `;

        // Create groups
        const groups = [
            {
                title: 'Core Profitability',
                items: [
                    renderMetricBlock('Net Profit', `$${m.net_profit.toFixed(2)}`, m.net_profit > 0 ? 'text-success' : 'text-danger'),
                    renderMetricBlock('Profit Factor', m.profit_factor.toFixed(2)),
                    renderMetricBlock('Win Rate', `${m.win_rate_pct.toFixed(1)}%`),
                    renderMetricBlock('Expectancy', `$${m.expectancy.toFixed(2)}`),
                ]
            },
            {
                title: 'Downside Risk & Drawdown',
                items: [
                    renderMetricBlock('Max Drawdown', `${Math.abs(m.max_drawdown_pct).toFixed(2)}%`, 'text-danger', `$${Math.abs(m.max_drawdown).toFixed(2)}`),
                    renderMetricBlock('Avg Drawdown', `${Math.abs(m.avg_drawdown_pct).toFixed(2)}%`),
                    renderMetricBlock('Drawdown Duration', `${(m.drawdown_duration_avg_seconds/3600).toFixed(1)} hrs avg`),
                    renderMetricBlock('Pain Index', m.pain_index.toFixed(2)),
                ]
            },
            {
                title: 'Risk-Adjusted Performance',
                items: [
                    renderMetricBlock('Sharpe Ratio', m.sharpe.toFixed(2)),
                    renderMetricBlock('Sortino Ratio', m.sortino.toFixed(2)),
                    renderMetricBlock('Calmar Ratio', m.calmar_ratio.toFixed(2)),
                    renderMetricBlock('Recovery Factor', m.recovery_factor.toFixed(2)),
                ]
            },
            {
                title: 'Trade Quality & Streaks',
                items: [
                    renderMetricBlock('Consecutive Wins', m.max_consecutive_wins),
                    renderMetricBlock('Consecutive Losses', m.max_consecutive_losses),
                    renderMetricBlock('Win/Loss Ratio', m.win_loss_ratio.toFixed(2)),
                    renderMetricBlock('Edge Ratio', m.edge_ratio.toFixed(2)),
                ]
            },
            {
                title: 'Advanced Risk',
                items: [
                    renderMetricBlock('Value at Risk (95%)', `$${m.var_95.toFixed(2)}`),
                    renderMetricBlock('Cond. VaR (95%)', `$${m.cvar_95.toFixed(2)}`),
                    renderMetricBlock('Skewness', m.skewness.toFixed(2)),
                    renderMetricBlock('Kurtosis', m.kurtosis.toFixed(2)),
                ]
            }
        ];

        groups.forEach(g => {
            html += `<h3 style="margin: 1.5rem 0 0.75rem 0; font-size: 1.1rem; border-left: 3px solid var(--accent-primary); padding-left: 10px;">${g.title}</h3>
            <div class="bt-metrics-grid" style="display:grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;">
                ${g.items.join('')}
            </div>`;
        });

        content.innerHTML = html;
        if (window.lucide) window.lucide.createIcons();

    } catch (e) {
        content.innerHTML = `<div style="color:var(--danger)">Error: ${e.message}</div>`;
    }
}
