// jarvis.js - Adapted from Crucix by calesthio
// Integrates the Intelligence Terminal aesthetic into Nexus Quant

let D = null;
let globe = null;

const regionPOV = {
  world: { lat: 20, lng: 20, altitude: 2.5 },
  americas: { lat: 15, lng: -80, altitude: 1.6 },
  europe: { lat: 50, lng: 15, altitude: 1.2 },
  middleEast: { lat: 28, lng: 45, altitude: 1.4 },
  asiaPacific: { lat: 25, lng: 110, altitude: 1.6 },
  africa: { lat: 5, lng: 20, altitude: 1.5 }
};

export async function initJarvis() {
    const container = document.getElementById('jarvis-container');
    if (!container) return;

    console.log("[Jarvis] Initializing Intelligence Terminal...");

    // Load initial data
    try {
        const response = await fetch('/api/jarvis_data?cb=' + Date.now());
        if (!response.ok) throw new Error("HTTP " + response.status);
        
        D = await response.json();
        console.log("[Jarvis] Intelligence packet decrypted:", D);
        
        renderJarvis();
    } catch (e) {
        console.error("[Jarvis] Critical Sync Failure:", e);
        container.innerHTML = `
            <div style="display:flex; align-items:center; justify-content:center; height:100%; color:var(--jarvis-danger); font-family:'JetBrains Mono'">
                <div style="text-align:center">
                    <div style="font-size:24px; margin-bottom:10px">⚠️ SYNC ERROR</div>
                    <div>${e.message}</div>
                    <button onclick="location.reload()" style="margin-top:20px; background:none; border:1px solid var(--jarvis-danger); color:inherit; padding:5px 15px; cursor:pointer">RETRY LINK</button>
                </div>
            </div>
        `;
    }

    // Refresh every 30s
    setInterval(async () => {
        try {
            const response = await fetch('/api/jarvis_data');
            if (response.ok) {
                D = await response.json();
                updateJarvis();
            }
        } catch (e) {}
    }, 30000);
}

function renderJarvis() {
    const container = document.getElementById('jarvis-container');
    if (!container) return;

    container.innerHTML = `
        <div class="jarvis-terminal scanlines">
            <div class="topbar-mini" id="jarvis-topbar"></div>
            <div class="jarvis-grid">
                <div class="jarvis-col left">
                    <div id="jarvis-sensor-grid"></div>
                    <div id="jarvis-exchange-watch"></div>
                    <div id="jarvis-rates-watch"></div>
                </div>
                <div class="jarvis-col center">
                    <div class="globe-preview" id="jarvis-globe"></div>
                </div>
                <div class="jarvis-col right">
                    <div id="jarvis-osint-feed"></div>
                    <div id="jarvis-ideas"></div>
                </div>
            </div>
            <div class="breaking-ticker" id="jarvis-ticker">
                <div class="ticker-label">BREAKING</div>
                <div class="ticker-content" id="ticker-scroll"></div>
            </div>
        </div>
    `;

    try {
        renderTopbar();
        renderLeftRail();
        renderRightRail();
        initGlobe();
    } catch (err) {
        console.error("Render loop error:", err);
    }
}

function updateJarvis() {
    renderTopbar();
    renderLeftRail();
    renderRightRail();
    if (globe) plotMarkers();
}

function renderTopbar() {
    const bar = document.getElementById('jarvis-topbar');
    if (!bar) return;
    const ts = new Date(D.meta.timestamp);
    const t = ts.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    
    bar.innerHTML = `
        <div class="t-left">
            <span class="t-brand">GLOBAL EMPIRE MONITOR</span>
            <span class="t-chip blink-red">VOLATILITY: ${D.macro.vix}</span>
            <span class="t-chip" style="background:rgba(100,240,200,0.1); border-color:var(--jarvis-accent)">FED: ${D.macro.fed_rate}%</span>
        </div>
        <div class="t-right">
            <span class="t-pill">Gold: <span class="v">$${D.macro.gold.toFixed(2)}</span></span>
            <span class="t-pill">WTI: <span class="v">$${D.energy.wti.toFixed(2)}</span></span>
            <span class="t-pill">US CPI: <span class="v">${D.macro.inflation_us}%</span></span>
            <span class="t-pill">BTC: <span class="v">$${(D.macro.btc/1000).toFixed(1)}K</span></span>
            <span class="t-pill">Sync: <span class="v">${t}</span></span>
        </div>
    `;
}

function renderLeftRail() {
    const sensorGrid = document.getElementById('jarvis-sensor-grid');
    const exchangeWatch = document.getElementById('jarvis-exchange-watch');

    const totalBots = D.air.reduce((s, a) => s + a.total, 0);
    const layers = [
        { name: 'Active Bot Fleet', count: totalBots, dot: 'cyan', sub: 'Unified Operations' },
        { name: 'Live Liquidations', count: layerFormat(D.thermal[0].det), dot: 'red', sub: 'Market Stress' },
        { name: 'Signal Streams', count: D.tg.posts, dot: 'yellow', sub: 'Strategy listeners' },
        { name: 'Treasury Debt', count: D.treasury.totalDebt, dot: 'purple', sub: 'US National' }
    ];

    sensorGrid.innerHTML = `
        <div class="j-panel">
            <div class="j-head"><h3>Operational Status</h3></div>
            ${layers.map(l => `
                <div class="j-row">
                    <div class="j-row-left">
                        <div class="j-dot ${l.dot}"></div>
                        <div class="j-info"><div class="j-name">${l.name}</div><div class="j-sub">${l.sub}</div></div>
                    </div>
                    <div class="j-val">${l.count}</div>
                </div>
            `).join('')}
        </div>
    `;

    exchangeWatch.innerHTML = `
        <div class="j-panel mt-10">
            <div class="j-head"><h3>Global Exchange API</h3></div>
            ${D.nuke.map(n => `
                <div class="j-row-simple">
                    <span>${n.site}</span>
                    <span class="j-val ${n.anom ? 'text-red' : 'text-green'}">${n.anom ? 'ERR' : 'OK'}</span>
                </div>
            `).join('')}
        </div>
    `;

    const ratesWatch = document.getElementById('jarvis-rates-watch');
    if (ratesWatch) {
        ratesWatch.innerHTML = `
            <div class="j-panel mt-10">
                <div class="j-head"><h3>Central Bank Rates</h3></div>
                <div class="j-row-simple"><span>FED RATE</span><span class="v">${D.macro.fed_rate}%</span></div>
                <div class="j-row-simple"><span>ECB RATE</span><span class="v">${D.macro.ecb_rate}%</span></div>
                <div class="j-row-simple"><span>US INFLATION</span><span class="v">${D.macro.inflation_us}%</span></div>
                <div class="j-row-simple"><span>EU INFLATION</span><span class="v">${D.macro.inflation_eu}%</span></div>
            </div>
        `;
    }
}

function layerFormat(val) {
    return val > 1000 ? (val/1000).toFixed(1) + 'K' : val;
}

function renderRightRail() {
    const osintFeed = document.getElementById('jarvis-osint-feed');
    const ideas = document.getElementById('jarvis-ideas');

    osintFeed.innerHTML = `
        <div class="j-panel">
            <div class="j-head"><h3>Macro Intelligence</h3></div>
            <div class="j-macro-grid">
                <div class="j-macro-item"><span>S&P 500</span><span class="v">${D.macro.spx.toFixed(0)}</span></div>
                <div class="j-macro-item"><span>DXY</span><span class="v">${D.macro.dxy.toFixed(2)}</span></div>
                <div class="j-macro-item"><span>10Y Yield</span><span class="v">${D.macro.us10y}%</span></div>
                <div class="j-macro-item"><span>Brent</span><span class="v">$${D.energy.brent.toFixed(2)}</span></div>
                <div class="j-macro-item"><span>VIX</span><span class="v">${D.macro.vix}</span></div>
                <div class="j-macro-item"><span>Natural Gas</span><span class="v">$${D.energy.ng.toFixed(2)}</span></div>
            </div>
            <div class="j-head mt-20"><h3>Global News Cycle</h3></div>
            <div class="j-feed">
                ${D.news.map(n => `
                    <div class="j-feed-item ${n.type || 'info'}">
                        <div class="j-feed-meta">
                            <span class="source-tag">${n.source}</span> 
                            <span class="type-tag ${n.type || ''}">${n.type || 'NEWS'}</span>
                            <span class="region-tag">${n.region}</span>
                        </div>
                        <div class="j-feed-text">${n.title}</div>
                        <div class="j-feed-time">${n.date ? new Date(n.date).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) : ''}</div>
                    </div>
                `).join('')}
                ${D.tg.urgent.map(p => `
                    <div class="j-feed-item tg-item">
                        <div class="j-feed-meta"><span class="source-tag telegram">${p.channel}</span> <span class="urgent-tag">URGENT CALL</span></div>
                        <div class="j-feed-text">${p.text}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    const ticker = document.getElementById('ticker-scroll');
    if (ticker) {
        const allNews = D.news.map(n => `[${n.source}] ${n.title}`).join(' • ');
        ticker.innerHTML = `<span>${allNews} • ${allNews}</span>`;
    }

    if (ideas) {
        ideas.innerHTML = `
            <div class="j-panel mt-10">
                <div class="j-head"><h3>Strategic Hypotheses</h3></div>
                ${D.ideas.map(i => `
                    <div class="j-idea-card ${i.type || 'info'}">
                        <div class="j-idea-title">${i.title}</div>
                        <div class="j-idea-text">${i.text}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

function initGlobe() {
    const el = document.getElementById('jarvis-globe');
    if (!el) return;

    if (typeof Globe !== 'function') {
        console.error("Globe.gl not loaded!");
        el.innerHTML = '<div style="color:var(--jarvis-dim); height:100%; display:flex; align-items:center; justify-content:center; font-size:12px;">GLOBE MODULE OFFLINE</div>';
        return;
    }

    globe = Globe()
        (el)
        .width(el.clientWidth)
        .height(el.clientHeight || 400)
        .globeImageUrl('//unpkg.com/three-globe@2.33.0/example/img/earth-night.jpg')
        .backgroundColor('rgba(0,0,0,0)')
        .atmosphereColor('#64f0c8')
        .atmosphereAltitude(0.15)
        .pointRadius(d => d.size || 0.4)
        .pointColor(d => d.color)
        .pointAltitude(0.01)
        .arcColor(d => d.color)
        .arcDashLength(0.4)
        .arcDashGap(0.2)
        .arcDashAnimateTime(2000)
        .onPointHover(pt => el.style.cursor = pt ? 'pointer' : 'grab');

    globe.pointOfView(regionPOV.world, 0);
    globe.controls().autoRotate = true;
    globe.controls().autoRotateSpeed = 0.5;

    plotMarkers();

    window.addEventListener('resize', () => {
        globe.width(el.clientWidth).height(el.clientHeight || 400);
    });
}

function plotMarkers() {
    const points = [];
    const arcs = [];

    // Exchange Hubs
    const hubs = [
        { name: 'Binance (TOKYO)', lat: 35.6, lon: 139.6, color: '#f0b90b' },
        { name: 'OKX (HONG KONG)', lat: 22.3, lon: 114.1, color: '#ffffff' },
        { name: 'Coinbase (NYC)', lat: 40.7, lon: -74.0, color: '#0052ff' },
        { name: 'Kraken (LONDON)', lat: 51.5, lon: -0.1, color: '#5741d9' }
    ];

    hubs.forEach(h => {
        points.push({
            lat: h.lat, lng: h.lon, size: 0.8, color: h.color, head: h.name
        });
    });

    // Strategy Arcs (Mock signal flow between hubs)
    arcs.push({
        startLat: hubs[0].lat, startLng: hubs[0].lon,
        endLat: hubs[2].lat, endLng: hubs[2].lon,
        color: ['rgba(100,240,200,0.4)', 'rgba(68,204,255,0.1)']
    });

    // News/Event markers from the Global News Cycle
    if (D.news) {
        D.news.forEach(n => {
            if (n.lat && n.lon) {
                let color = '#ff5f63'; // Default red
                if (n.type === 'energy') color = '#ffb84c';
                if (n.type === 'crypto') color = '#64f0c8';
                if (n.type === 'geopolitical') color = '#ff00ff';

                points.push({
                    lat: n.lat, lng: n.lon, size: 0.5, color: color, head: `[${n.source}] ${n.title}`, type: n.type
                });
                // Link news event to the nearest or primary hub
                const hub = hubs[0]; 
                arcs.push({
                    startLat: n.lat, startLng: n.lon,
                    endLat: hub.lat, endLng: hub.lon,
                    color: [color, 'rgba(255,255,255,0.05)']
                });
            }
        });
    }

    globe.pointsData(points);
    globe.arcsData(arcs);
    globe.pointLabel(d => `<div style="padding:5px; background:rgba(0,0,0,0.8); border:1px solid #64f0c8; font-size:10px; color:#fff">${d.head}</div>`);
}
