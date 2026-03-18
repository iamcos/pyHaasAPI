import { state } from './state.js';

export function populateStrategySelector() {
    const stratSelect = document.getElementById('bt_strategy');
    if (!stratSelect) return;
    stratSelect.innerHTML = '';
    state.haasScripts.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.innerText = `${s.name} (Haas)`;
        stratSelect.appendChild(opt);
    });
}

export function populateAccountSelector() {
    const accSelect = document.getElementById('bt_account');
    if (!accSelect) return;
    accSelect.innerHTML = '';
    state.accounts.forEach(acc => {
        const opt = document.createElement('option');
        opt.value = acc.id;
        opt.innerText = `${acc.name} [${acc.exchange}]`;
        if (acc.is_simulated) opt.innerText += ' (Sim)';
        accSelect.appendChild(opt);
    });
}

export async function runBacktest(event) {
    const strategyId = document.getElementById('bt_strategy').value;
    const accountId  = document.getElementById('bt_account').value;
    const pair       = document.getElementById('bt_pair').value;
    const leverage   = document.getElementById('bt_leverage').value;

    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader" class="spin"></i> Creating &amp; Starting Lab...';
    if (window.lucide) window.lucide.createIcons();

    try {
        const resp = await fetch('/api/haas/labs/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ script_id: strategyId, account_id: accountId, market: pair, leverage }),
        });
        const result = await resp.json();
        if (resp.ok) {
            const badge = document.getElementById('bt-status');
            if (badge) { badge.innerText = 'Running'; badge.className = 'badge-status warning'; }
            alert(`Lab "${result.lab_name}" started! It will process on Haas Cloud in a few minutes.`);
            await refreshLabsPipeline();
        } else {
            alert('Lab failed: ' + result.error);
        }
    } catch (e) {
        console.error(e);
        alert('Execution Error: ' + e.message);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
        if (window.lucide) window.lucide.createIcons();
    }
}

// ─── Shared status helpers ────────────────────────────────────────────────────
const STATUS_MAP   = { 0: 'Idle', 1: 'Running', 2: 'Completed', 3: 'Failed', 4: 'Cancelled' };
const STATUS_CLASS = { 0: 'waiting', 1: 'warning', 2: 'success', 3: 'danger', 4: '' };

function resolveStatus(lab) {
    const num = typeof lab.status === 'number' ? lab.status : -1;
    return {
        text:  num >= 0 ? (STATUS_MAP[num]   || lab.status || 'Unknown') : (lab.status || 'Unknown'),
        cls:   num >= 0 ? (STATUS_CLASS[num] || '') : '',
    };
}

// ─── Live Pipeline Table ──────────────────────────────────────────────────────
export async function refreshLabsPipeline() {
    const tbody   = document.getElementById('labs-pipeline-list');
    const summary = document.getElementById('pipeline-summary');
    if (!tbody) return;

    try {
        const resp = await fetch('/api/labs');
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const labs = await resp.json();
        state.labs = labs;

        if (labs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--text-muted);">No labs found on this server.</td></tr>';
            if (summary) summary.textContent = '0 labs';
            return;
        }

        const running   = labs.filter(l => l.status === 1 || l.status === 'Running').length;
        const completed = labs.filter(l => l.status === 2 || l.status === 'Completed').length;
        if (summary) summary.textContent = `${labs.length} total · ${running} running · ${completed} completed`;

        tbody.innerHTML = '';
        labs.forEach(lab => {
            const { text: statusText, cls: badgeCls } = resolveStatus(lab);
            const total   = lab.scheduled || 0;
            const done    = lab.completed  || 0;
            const pct     = total > 0 ? Math.min(100, Math.round((done / total) * 100)) : 0;

            const progressBar = total > 0
                ? `<div style="display:flex;align-items:center;gap:8px;">
                     <div style="flex:1;background:rgba(255,255,255,0.08);border-radius:4px;height:6px;overflow:hidden;">
                       <div style="width:${pct}%;height:100%;background:var(--accent-primary);border-radius:4px;transition:width 0.5s;"></div>
                     </div>
                     <span style="font-size:0.75rem;color:var(--text-muted);white-space:nowrap;">${pct}%</span>
                   </div>`
                : '<span style="color:var(--text-muted);font-size:0.8rem;">N/A</span>';

            const marketShort = (lab.market || 'N/A')
                .replace('BINANCEFUTURES_', '')
                .replace('_PERPETUAL', '');

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="font-weight:600;color:#fff;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${lab.name}">${lab.name}</td>
                <td style="font-family:'JetBrains Mono';font-size:0.8rem;color:var(--accent-secondary);">${marketShort}</td>
                <td><span class="badge-status ${badgeCls}" style="font-size:0.75rem;padding:2px 8px;">${statusText}</span></td>
                <td style="text-align:center;">${done}</td>
                <td style="text-align:center;">${total}</td>
                <td style="min-width:130px;">${progressBar}</td>
                <td>
                    <button class="btn btn-ghost btn-sm" style="font-size:0.75rem;padding:2px 8px;"
                        onclick="window.viewLabAnalytics && window.viewLabAnalytics('${lab.id}', '${lab.name}')">
                        <i data-lucide="bar-chart-2" style="width:12px;height:12px;"></i> View
                    </button>
                </td>`;
            tbody.appendChild(tr);
        });

        if (window.lucide) window.lucide.createIcons();

    } catch (e) {
        console.error('Pipeline fetch failed', e);
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--danger);padding:1.5rem;">⚠ Could not connect to Haas: ${e.message}</td></tr>`;
        if (summary) summary.textContent = 'Disconnected';
    }
}

// Expose for the "Refresh Pipeline" button in HTML
window.refreshLabsPipeline = refreshLabsPipeline;

// ─── Update top metrics panel ─────────────────────────────────────────────────
export async function updateLabsArenaUI() {
    // Always refresh the pipeline table
    await refreshLabsPipeline();

    const badge = document.getElementById('bt-status');
    const tradesEl = document.getElementById('bt-trades-count');
    const roiEl    = document.getElementById('bt-roi-value');
    const winEl    = document.getElementById('bt-winrate');

    if (!state.labs || state.labs.length === 0) {
        if (badge) { badge.innerText = 'Idle'; badge.className = 'badge-status success'; }
        if (tradesEl) tradesEl.innerText = '--';
        if (roiEl)    roiEl.innerText    = '--%';
        if (winEl)    winEl.innerText    = '--%';
        return;
    }

    const latestLab = state.labs[0];
    const { text: statusText, cls: badgeCls } = resolveStatus(latestLab);

    if (badge) { badge.innerText = statusText; badge.className = `badge-status ${badgeCls}`; }

    // Fetch latest backtest results for the most recent lab
    try {
        const btResp = await fetch(`/api/labs/backtests?lab_id=${latestLab.id}`);
        if (btResp.ok) {
            const backtests = await btResp.json();
            if (backtests.length > 0) {
                const best = backtests[0];
                if (tradesEl) tradesEl.innerText = best.trades ?? '--';
                if (roiEl) {
                    const roi = parseFloat(best.roi) || 0;
                    roiEl.innerText = `${roi >= 0 ? '+' : ''}${roi.toFixed(2)}%`;
                    roiEl.style.color = roi >= 0 ? 'var(--success)' : 'var(--danger)';
                }
                if (winEl) winEl.innerText = `${best.winRate ?? '--'}%`;
                return;
            }
        }
    } catch (e) { console.error('Failed to fetch lab stats', e); }

    // Fallback if no backtests yet
    if (tradesEl) tradesEl.innerText = '--';
    if (roiEl)    roiEl.innerText    = '--%';
    if (winEl)    winEl.innerText    = '--%';
}
