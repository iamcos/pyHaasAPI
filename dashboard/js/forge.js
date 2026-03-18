export let selectedForgeScriptId = null;

export async function refreshForgeScripts() {
    const tbody = document.getElementById('forge-script-list');
    if (!tbody) return;
    
    tbody.innerHTML = '<tr><td colspan="3" style="text-align:center"><i data-lucide="loader" class="spin"></i> Scanning srv...</td></tr>';
    if (window.lucide) window.lucide.createIcons();
    
    try {
        const resp = await fetch('/api/haas/scripts');
        if (!resp.ok) throw new Error("Fetch failed");
        const scripts = await resp.json();
        
        tbody.innerHTML = '';
        scripts.forEach(s => {
            const tr = document.createElement('tr');
            const statusClass = s.isValid ? 'text-success' : 'text-danger';
            const statusIcon = s.isValid ? 'check-circle' : 'alert-circle';
            
            tr.innerHTML = `
                <td style="font-weight:500">${s.name}</td>
                <td class="${statusClass}"><i data-lucide="${statusIcon}" style="width:14px; margin-right:4px"></i> ${s.isValid ? 'Valid' : 'Invalid'}</td>
                <td>
                    <button class="btn btn-ghost btn-sm" onclick="selectForgeScript('${s.id}', '${s.name.replace(/'/g, "\\'")}')">
                        <i data-lucide="target"></i> Select
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        if (window.lucide) window.lucide.createIcons();
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--danger)">Failed to load scripts.</td></tr>';
    }
}

export function selectForgeScript(id, name) {
    selectedForgeScriptId = id;
    document.getElementById('forge-summary').innerText = `Target: ${name}`;
    document.getElementById('btn-forge-run').disabled = false;
    
    const console = document.getElementById('forge-console');
    console.innerHTML = `<div class="term-line" style="color:var(--accent-primary)">> Selected script ${id}</div>`;
    console.innerHTML += `<div class="term-line">> Ready for autonomous repair.</div>`;
}

export async function runForgeRepair() {
    if (!selectedForgeScriptId) return;
    
    const console = document.getElementById('forge-console');
    const status = document.getElementById('forge-status');
    const btn = document.getElementById('btn-forge-run');
    
    status.innerText = 'Analyzing';
    status.className = 'badge-status warning';
    btn.disabled = true;
    
    console.innerHTML += `<div class="term-line" style="color:var(--warning)">[Autonomous] Starting lifecycle for ${selectedForgeScriptId}...</div>`;
    console.innerHTML += `<div class="term-line">[Autonomous] Discovering local dependencies...</div>`;
    console.scrollTop = console.scrollHeight;

    try {
        const resp = await fetch('/api/haas/scripts/lifecycle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ script_id: selectedForgeScriptId })
        });
        
        const result = await resp.json();
        if (result.success) {
            status.innerText = 'Tradable';
            status.className = 'badge-status success';
            console.innerHTML += `<div class="term-line" style="color:var(--success)">[Autonomous] Compilation Successful!</div>`;
            console.innerHTML += `<div class="term-line" style="color:var(--success)">[Autonomous] All dependencies integrated.</div>`;
        } else {
            status.innerText = 'Failed';
            status.className = 'badge-status danger';
            console.innerHTML += `<div class="term-line" style="color:var(--danger)">[Autonomous] Repair failed.</div>`;
            if (result.logs && result.logs.length > 0) {
                result.logs.forEach(log => {
                    console.innerHTML += `<div class="term-line" style="opacity:0.6; font-size:0.8rem">  ${log}</div>`;
                });
            }
        }
    } catch (e) {
        console.error(e);
        console.innerHTML += `<div class="term-line" style="color:var(--danger)">[System] Connection error during repair.</div>`;
    } finally {
        btn.disabled = false;
        console.scrollTop = console.scrollHeight;
        refreshForgeScripts();
    }
}
