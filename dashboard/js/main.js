import { initCharts, populateActivityFeed, populateBotList } from './dashboard.js';
import { initServerSelector, updateStatus, refreshData } from './data.js';
import { refreshForgeScripts, selectForgeScript, runForgeRepair } from './forge.js';
import { runBacktest as runLab, refreshLabsPipeline } from './backtest.js';
import { populateCachedBacktests, openAdvancedMetricsModal } from './analytics.js';
import { initJarvis } from './jarvis.js';
import { state } from './state.js';

window.runBacktest = runLab;
window.selectForgeScript = selectForgeScript;
window.refreshForgeScripts = refreshForgeScripts;
window.refreshLabsPipeline = refreshLabsPipeline;

// Opens Deep Analytics modal from the pipeline View button
window.viewLabAnalytics = async (labId, labName) => {
    // Navigate to Analytics tab so the modal is visible
    const analyticsNav = document.querySelector('[data-tab="analytics"]');
    if (analyticsNav) analyticsNav.click();
    // Open for the latest backtest of this lab (use lab_id, blank bt_id triggers best-effort)
    await openAdvancedMetricsModal(labId, '');
};

function initTheme() {
    const style = document.createElement('style');
    style.innerHTML = `
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from {transform:rotate(0deg);} to {transform:rotate(360deg);} }
    `;
    document.head.appendChild(style);
}

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabId).classList.add('active');
            if (tabId === 'dashboard' || tabId === 'analytics') { window.dispatchEvent(new Event('resize')); }
            if (tabId === 'labs') { refreshLabsPipeline(); }
        });
    });
}

function initEngineToggles() {
    const pills = document.querySelectorAll('.engine-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            state.engine = pill.getAttribute('data-engine');
            populateBotList();
            populateCachedBacktests();
        });
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    if (window.lucide) window.lucide.createIcons();
    initTheme();
    initCharts();
    initNavigation();
    initEngineToggles();
    initServerSelector();
    initJarvis();

    await updateStatus();
    await refreshData();
    refreshLabsPipeline();

    populateActivityFeed();
    
    // Auto-refresh data every 15 seconds
    setInterval(async () => {
        await refreshData();
    }, 15000);

    if (document.getElementById('script-forge')) {
        refreshForgeScripts();
        document.getElementById('btn-forge-run')?.addEventListener('click', runForgeRepair);
    }
    
    document.getElementById('vault-server-filter')?.addEventListener('change', () => {
        populateCachedBacktests();
    });
});
