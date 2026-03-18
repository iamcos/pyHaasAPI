import { state } from './state.js';
import { updateMainChart, populateBotList, updateMetricsUI } from './dashboard.js';
import { populateCachedBacktests, refreshCacheStats } from './analytics.js';
import { populateStrategySelector, populateAccountSelector, updateLabsArenaUI } from './backtest.js';

export async function updateStatus() {
    try {
        const resp = await fetch('/api/status');
        if (resp.ok) {
            const data = await resp.json();
            state.currentServer = data.current_server;
            document.getElementById('haas-server-select').value = state.currentServer;
            document.getElementById('global-status-text').innerText = `Haas: ${state.currentServer}`;
            document.getElementById('global-status-dot').style.background = 'var(--success)';
        }
    } catch (e) { console.error("Status check failed", e); }
}

export async function initServerSelector() {
    const select = document.getElementById('haas-server-select');
    select.addEventListener('change', async (e) => {
        const newServer = e.target.value;
        document.getElementById('global-status-text').innerText = `Switching to ${newServer}...`;
        document.getElementById('global-status-dot').style.background = 'var(--warning)';
        
        try {
            const resp = await fetch('/api/switch-server', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ server: newServer })
            });
            if (resp.ok) {
                await updateStatus();
                await refreshData();
                populateCachedBacktests();
            } else {
                alert("Failed to switch server. Check SSH tunnels.");
                await updateStatus();
            }
        } catch (e) { console.error("Switch failed", e); }
    });
    
    try {
        const resp = await fetch('/api/freq/strategies');
        if (resp.ok) {
            state.freqStrategies = await resp.json();
            const stratSelect = document.getElementById('bt_strategy');
            if (stratSelect) {
                state.freqStrategies.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.innerText = `${s} (Freq)`;
                    stratSelect.appendChild(opt);
                });
            }
        }
    } catch (e) { console.error("Freq strategies fetch failed", e); }
}

export async function refreshData() {
    try {
        const labsResp = await fetch('/api/labs');
        if (labsResp.ok) {
            state.labs = await labsResp.json();
            if (state.labs.length > 0) updateMainChart(state.labs[0].id);
            updateLabsArenaUI();
        }

        const scriptsResp = await fetch('/api/haas/scripts');
        if (scriptsResp.ok) {
            state.haasScripts = await scriptsResp.json();
            populateStrategySelector();
        }

        const accResp = await fetch('/api/haas/accounts');
        if (accResp.ok) {
            state.accounts = await accResp.json();
            populateAccountSelector();
        }

        const btResponse = await fetch('/api/backtests');
        if (btResponse.ok) {
            state.cachedBacktests = await btResponse.json();
            populateCachedBacktests();
        }

        const botResponse = await fetch('/api/bots');
        if (botResponse.ok) {
            state.bots = await botResponse.json();
            populateBotList();
        }

        const metricsResponse = await fetch('/api/metrics');
        if (metricsResponse.ok) {
            state.metrics = await metricsResponse.json();
            updateMetricsUI();
        }
        
        refreshCacheStats();
    } catch (e) { console.error("Failed to fetch dashboard data:", e); }
}
