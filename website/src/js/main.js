import '../css/style.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// A real repository's public commit history; no simulated development activity.
const githubRepo = 'protikka1/safehaven-tay-app';
const updatesEl = document.querySelector('#github-updates');
const statusEl = document.querySelector('#github-status');

async function loadGitHubUpdates() {
  try {
    const response = await fetch(`https://api.github.com/repos/${githubRepo}/commits?per_page=4`, {
      headers: { Accept: 'application/vnd.github+json' }
    });
    if (!response.ok) throw new Error(`GitHub returned HTTP ${response.status}`);
    const commits = await response.json();
    if (!Array.isArray(commits) || !commits.length) {
      updatesEl.textContent = 'No public commits found.';
      statusEl.textContent = 'No public updates';
      return;
    }
    updatesEl.replaceChildren();
    for (const entry of commits) {
      const item = document.createElement('div');
      item.className = 'update-item';
      const link = document.createElement('a');
      link.href = entry.html_url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = (entry.commit?.message || 'Repository update').split('\n')[0];
      const detail = document.createElement('p');
      const author = entry.commit?.author?.name || 'Contributor';
      const date = entry.commit?.author?.date;
      const formatted = date && !Number.isNaN(Date.parse(date))
        ? new Intl.DateTimeFormat(undefined, {dateStyle:'medium'}).format(new Date(date)) : 'Date unavailable';
      detail.textContent = `${author} • ${formatted}`;
      item.append(link, detail);
      updatesEl.append(item);
    }
    statusEl.textContent = 'Public GitHub commits';
  } catch (error) {
    statusEl.textContent = 'Updates unavailable';
    updatesEl.textContent = 'Automatic updates could not load. The repository may be private, GitHub may be rate-limiting requests, or the network may be unavailable. View the repository directly instead.';
  }
}

const map = L.map('civic-map', { scrollWheelZoom: false }).setView([34.0448, -118.244], 14);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>'
}).addTo(map);
const civicStatus = document.querySelector('#civic-feed-status');
const civicCards = document.querySelector('#civic-feed-cards');
const permitDataset = 'https://data.lacity.org/d/gwh9-jnip';

async function loadCivicFeed() {
  try {
    const response = await fetch('./verified_watchdog.geojson', {cache: 'no-cache'});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const feed = await response.json();
    if (feed.type !== 'FeatureCollection' || !Array.isArray(feed.features)) {
      throw new Error('Invalid civic feed');
    }
    const checked = Date.parse(feed.ladbs_last_checked);
    const count = feed.features.length;
    civicStatus.textContent = Number.isFinite(checked)
      ? `${count} verified · DataLA checked ${new Date(checked).toLocaleString()}${Date.now() - checked > 24 * 60 * 60 * 1000 ? ' · Update overdue' : ''}`
      : `${count} verified · DataLA check pending`;

    if (!count) {
      civicCards.textContent = 'No verified records have been published yet.';
      return;
    }
    const layer = L.geoJSON(feed, {
      pointToLayer: (_, latlng) => L.circleMarker(latlng, {radius: 7, color: '#0b8175'}),
      onEachFeature: ({properties: record}, marker) => {
        const title = document.createElement('strong');
        title.textContent = record.project_name;
        marker.bindPopup(title.cloneNode(true));

        const card = document.createElement('article');
        card.className = 'content-card metric-card';
        const id = document.createElement('p');
        id.textContent = record.external_case_id;
        const details = document.createElement('p');
        details.textContent = record.feed_source === 'LADBS'
          ? [record.permit?.permit_type, record.permit?.status_desc, record.permit?.status_date?.slice(0, 10)].filter(Boolean).join(' · ')
          : `Watchdog finding: ${record.audit_status}`;
        card.append(title, id, details);
        if (record.feed_source === 'LADBS') {
          const source = document.createElement('a');
          source.href = permitDataset;
          source.textContent = 'LADBS source dataset';
          card.append(source);
        }
        civicCards.append(card);
      }
    }).addTo(map);
    if (layer.getBounds().isValid()) map.fitBounds(layer.getBounds(), {padding: [24, 24], maxZoom: 16});
  } catch (error) {
    civicStatus.textContent = 'Verified feed unavailable';
    civicCards.textContent = 'The public feed could not be loaded.';
  }
}

const nav = document.querySelector('#navLinks');
nav.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', () => {
    const toggler = document.querySelector('.navbar-toggler');
    if (window.innerWidth < 992 && nav.classList.contains('show')) toggler.click();
  });
});

document.querySelector('#current-year').textContent = new Date().getFullYear();
loadGitHubUpdates();
loadCivicFeed();
