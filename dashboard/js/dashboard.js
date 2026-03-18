import { state } from './state.js';

export let mainChart = null;

export function initCharts() {
    const options = {
        series: [{ name: 'Equity Curve', data: [] }],
        chart: { type: 'area', height: 350, fontFamily: 'Outfit', background: 'transparent', toolbar: { show: false }, animations: { enabled: true, easing: 'easeinout', speed: 800 } },
        colors: ['#8b5cf6'],
        fill: { type: 'gradient', gradient: { opacityFrom: 0.4, opacityTo: 0.05 } },
        stroke: { curve: 'smooth', width: 2 },
        xaxis: { type: 'datetime', labels: { style: { colors: '#94a3b8' } } },
        yaxis: { labels: { style: { colors: '#94a3b8' }, formatter: (v) => '$' + v.toFixed(2) } },
        grid: { borderColor: 'rgba(255,255,255,0.05)', strokeDashArray: 4 },
        theme: { mode: 'dark' },
        noData: { text: "Loading Real Equity Data...", style: { color: '#94a3b8', fontSize: '14px' } }
    };
    const elm = document.querySelector("#equity-chart");
    if (elm) {
        mainChart = new ApexCharts(elm, options);
        mainChart.render();
    }
}

export async function updateMainChart(lab_id, backtest_id = null) {
    if (!mainChart) return;
    try {
        let chartData = null;
        let title = `Lab: ${lab_id.substring(0,6)}...`;
        if (backtest_id) {
            const resp = await fetch(`/api/backtest/analysis?lab_id=${lab_id}&backtest_id=${backtest_id}`);
            if (resp.ok) {
                const analysis = await resp.json();
                chartData = { labels: analysis.equity_curve.map((_, i) => i), equity: analysis.equity_curve };
                title = `BT: ${backtest_id.substring(0,8)}`;
            }
        } else {
            const btResp = await fetch(`/api/labs/backtests?lab_id=${lab_id}`);
            if (!btResp.ok) return;
            const backtests = await btResp.json();
            if (backtests.length === 0) return;
            const bestBt = backtests[0];
            const chartResp = await fetch(`/api/haas/charts?lab_id=${lab_id}&backtest_id=${bestBt.id}`);
            if (chartResp.ok) chartData = await chartResp.json();
        }
        
        if (chartData && chartData.equity && chartData.equity.length > 0) {
            const seriesData = chartData.labels && chartData.labels.length === chartData.equity.length
                ? chartData.labels.map((label, i) => ({ x: typeof label === 'string' ? new Date(label).getTime() : label, y: chartData.equity[i] }))
                : chartData.equity.map((val, i) => ({ x: i, y: val }));
            
            const isDateTime = chartData.labels && chartData.labels.length > 0 && typeof chartData.labels[0] === 'string';
            mainChart.updateOptions({ xaxis: { type: isDateTime ? 'datetime' : 'numeric' } });
            mainChart.updateSeries([{ name: title, data: seriesData }]);
        }
    } catch (e) { console.error("Failed to update chart", e); }
}

export function populateBotList() {
    const tbody = document.getElementById('bot-list');
    if (!tbody) return;
    const visibleBots = state.engine === 'all' ? state.bots : (state.engine === 'haas' ? state.bots : []);
    if (visibleBots.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center">No active bots found on this server.</td></tr>';
        return;
    }
    tbody.innerHTML = '';
    visibleBots.forEach(bot => {
        const tr = document.createElement('tr');
        const roiColor = bot.roi > 0 ? 'var(--success)' : (bot.roi < 0 ? 'var(--danger)' : '');
        tr.innerHTML = `
            <td><div class="dot" style="background:${bot.status === 'ACTIVE' ? 'var(--success)' : 'var(--danger)'}; animation:none; box-shadow:none; width:10px; height:10px;"></div></td>
            <td style="font-weight:600; color:#fff">${bot.name}</td>
            <td><span class="badge haas">HAAS</span></td>
            <td style="font-family:'JetBrains Mono'; font-size:0.8rem; color:var(--text-muted)">${bot.id.substring(0,8)}...</td>
            <td style="font-family:'JetBrains Mono'; font-size:0.85rem">${bot.market}</td>
            <td style="color:${roiColor}; font-weight:600">${bot.roi > 0 ? '+' : ''}${bot.roi}%</td>
            <td>${bot.trades} trades</td>
            <td>
                <button class="btn btn-ghost btn-sm"><i data-lucide="eye"></i></button>
                <button class="btn btn-ghost btn-sm" style="color:var(--danger)"><i data-lucide="square"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    if (window.lucide) window.lucide.createIcons();
}

export function updateMetricsUI() {
    document.getElementById('metric-bots').innerText = state.metrics.bot_count;
    document.getElementById('metric-roi').innerText = state.metrics.global_pnl;
    if (document.getElementById('metric-vault')) {
        document.getElementById('metric-vault').innerText = state.metrics.vault_count;
    }
    
    if (document.getElementById('metric-winrate')) {
        document.getElementById('metric-winrate').innerText = state.metrics.win_rate;
    }
    
    if (document.getElementById('metric-haas-winrate')) {
        document.getElementById('metric-haas-winrate').innerText = `H: ${state.metrics.win_rate}`;
    }
    
    if (document.getElementById('metric-drawdown')) {
        document.getElementById('metric-drawdown').innerText = state.metrics.max_drawdown;
    }
    
    if (document.getElementById('metric-pnl-trend')) {
        const trend = parseFloat(state.metrics.total_roi) >= 0 ? 'positive' : 'negative';
        const trendText = parseFloat(state.metrics.total_roi) >= 0 ? 'Growth Streak' : 'Recovery Phase';
        document.getElementById('metric-pnl-trend').className = `stat-trend ${trend}`;
        document.getElementById('metric-pnl-trend').innerText = trendText;
    }
}

export function populateActivityFeed() {
    const feed = document.getElementById('activity-feed');
    if (!feed) return;
    feed.innerHTML = '<div style="padding:20px; color:var(--text-muted)">Nexus listening for events...</div>';
}
