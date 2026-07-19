/* ================================================================
   CIFRE PhD Tracker — Frontend Logic
   ================================================================ */

const API = {
    offers: '/api/offers',
    updateStatus: (id) => `/api/offers/${id}/status`,
    refresh: '/api/refresh',
    status: '/api/status',
};

const SOURCE_LABELS = {
    doctorat_gouv: 'Doctorat.gouv',
    safran: 'Safran',
    airbus: 'Airbus',
    renault: 'Renault',
    cea: 'CEA',
    edf: 'EDF',
    orange: 'Orange',
    thales: 'Thales',
    inria: 'INRIA',
    hellowork: 'HelloWork',
    linkedin: 'LinkedIn',
};

let allOffers = [];
let refreshPollInterval = null;

// ------------------------------------------------------------------
// Initialisation
// ------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    fetchOffers();
});

// ------------------------------------------------------------------
// Data fetching
// ------------------------------------------------------------------

async function fetchOffers() {
    try {
        const params = new URLSearchParams();
        const status = document.getElementById('filter-status').value;
        const source = document.getElementById('filter-source').value;
        const search = document.getElementById('filter-search').value.trim();

        if (status) params.set('status', status);
        if (source) params.set('source', source);
        if (search) params.set('search', search);

        const resp = await fetch(`${API.offers}?${params}`);
        const data = await resp.json();

        allOffers = data.offers || [];
        updateStats(data);
        renderOffers(allOffers);
        updateScrapeInfo(data.last_scrape);
    } catch (err) {
        console.error('Failed to fetch offers:', err);
        showToast('Failed to load offers', 'error');
    }
}

function applyFilters() {
    fetchOffers();
}

// ------------------------------------------------------------------
// Rendering
// ------------------------------------------------------------------

function renderOffers(offers) {
    const grid = document.getElementById('offers-grid');
    const empty = document.getElementById('empty-state');
    const resultsCount = document.getElementById('results-count');

    resultsCount.textContent = `${offers.length} offer${offers.length !== 1 ? 's' : ''}`;

    if (offers.length === 0) {
        grid.innerHTML = '';
        empty.classList.remove('hidden');
        return;
    }

    empty.classList.add('hidden');
    grid.innerHTML = offers.map((offer, i) => renderCard(offer, i)).join('');
}

function renderCard(offer, index) {
    const sourceLabel = SOURCE_LABELS[offer.source] || offer.source;
    const isNew = offer.status === 'new';
    const isApplied = offer.status === 'applied';
    const isNotInterested = offer.status === 'not_interested';
    const desc = escapeHtml(offer.description || '');
    const title = escapeHtml(offer.title || 'Untitled');
    const company = escapeHtml(offer.company || 'Unknown');
    const link = offer.link || '#';
    const dateStr = offer.date_found || '';

    // Status badge
    let statusBadge = '';
    if (isNew) {
        statusBadge = '<span class="new-badge">✦ New</span>';
    } else if (isApplied) {
        statusBadge = '<span class="applied-badge">✓ Applied</span>';
    }

    // Actions depend on current status
    let actions = '';
    if (isNotInterested) {
        actions = `
            <button class="btn-action btn-undo" onclick="updateOfferStatus('${offer.id}', 'new')">
                ↩ Restore
            </button>
        `;
    } else if (isApplied) {
        actions = `
            <button class="btn-action btn-undo" onclick="updateOfferStatus('${offer.id}', 'new')">
                ↩ Undo
            </button>
            <button class="btn-action btn-not-interested" onclick="updateOfferStatus('${offer.id}', 'not_interested')">
                ✕ Not interested
            </button>
        `;
    } else {
        actions = `
            <button class="btn-action btn-not-interested" onclick="updateOfferStatus('${offer.id}', 'not_interested')">
                ✕ Not interested
            </button>
            <button class="btn-action btn-applied" onclick="updateOfferStatus('${offer.id}', 'applied')">
                ✓ Applied
            </button>
        `;
    }

    return `
        <div class="offer-card" data-source="${offer.source}" data-id="${offer.id}"
             style="animation-delay: ${index * 0.04}s">
            <div class="card-header">
                <span class="source-badge">${sourceLabel}</span>
                ${statusBadge}
            </div>
            <div class="card-title">
                <a href="${link}" target="_blank" rel="noopener">${title}</a>
            </div>
            <div class="card-company">${company}</div>
            ${desc ? `<div class="card-description">${desc}</div>` : ''}
            <div class="card-date">Found: ${dateStr}</div>
            <div class="card-actions">
                ${actions}
            </div>
        </div>
    `;
}

// ------------------------------------------------------------------
// Status updates
// ------------------------------------------------------------------

async function updateOfferStatus(offerId, newStatus) {
    // Animate the card out
    const card = document.querySelector(`.offer-card[data-id="${offerId}"]`);
    if (card) {
        card.classList.add('removing');
    }

    try {
        const resp = await fetch(API.updateStatus(offerId), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus }),
        });

        if (!resp.ok) throw new Error('Update failed');

        const statusLabels = {
            applied: 'Marked as applied ✓',
            not_interested: 'Marked as not interested',
            new: 'Restored to new',
        };
        showToast(statusLabels[newStatus] || 'Status updated', 'success');

        // Re-fetch after animation
        setTimeout(() => fetchOffers(), 300);
    } catch (err) {
        console.error('Status update failed:', err);
        showToast('Failed to update status', 'error');
        if (card) card.classList.remove('removing');
    }
}

// ------------------------------------------------------------------
// Refresh / Scraping
// ------------------------------------------------------------------

async function triggerRefresh() {
    const btn = document.getElementById('btn-refresh');
    const overlay = document.getElementById('refresh-overlay');

    btn.classList.add('loading');
    overlay.classList.remove('hidden');

    try {
        const resp = await fetch(API.refresh, { method: 'POST' });
        const data = await resp.json();

        if (resp.status === 409) {
            showToast('A scrape is already running', 'error');
            overlay.classList.add('hidden');
            btn.classList.remove('loading');
            return;
        }

        // Poll for completion
        pollScrapeStatus();
    } catch (err) {
        console.error('Refresh failed:', err);
        showToast('Failed to start scraping', 'error');
        overlay.classList.add('hidden');
        btn.classList.remove('loading');
    }
}

function pollScrapeStatus() {
    if (refreshPollInterval) clearInterval(refreshPollInterval);

    refreshPollInterval = setInterval(async () => {
        try {
            const resp = await fetch(API.status);
            const data = await resp.json();

            if (!data.running) {
                clearInterval(refreshPollInterval);
                refreshPollInterval = null;

                const overlay = document.getElementById('refresh-overlay');
                const btn = document.getElementById('btn-refresh');
                overlay.classList.add('hidden');
                btn.classList.remove('loading');

                if (data.result) {
                    if (data.result.error) {
                        showToast(`Scraping error: ${data.result.error}`, 'error');
                    } else {
                        const msg = `Scraping complete: ${data.result.new || 0} new offers found`;
                        showToast(msg, 'success');
                    }
                }

                fetchOffers();
            }
        } catch (err) {
            console.error('Poll failed:', err);
        }
    }, 3000);
}

// ------------------------------------------------------------------
// Stats & Info
// ------------------------------------------------------------------

function updateStats(data) {
    const offers = data.offers || [];
    const newCount = offers.filter(o => o.status === 'new').length;
    const appliedCount = offers.filter(o => o.status === 'applied').length;

    // For total, we need all offers count — fetch without filters
    document.getElementById('stat-new').textContent = newCount;
    document.getElementById('stat-applied').textContent = appliedCount;
    document.getElementById('stat-total').textContent = data.total || offers.length;
}

function updateScrapeInfo(lastScrape) {
    const el = document.getElementById('scrape-info');
    if (lastScrape) {
        const dt = new Date(lastScrape);
        const formatted = dt.toLocaleString('en-GB', {
            day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
        });
        el.textContent = `Last scraped: ${formatted}`;
    } else {
        el.textContent = 'No scrape performed yet — click Refresh to start';
    }
}

// ------------------------------------------------------------------
// Toast notifications
// ------------------------------------------------------------------

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;

    // Auto-hide after 4s
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 4000);
}

// ------------------------------------------------------------------
// Utilities
// ------------------------------------------------------------------

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
