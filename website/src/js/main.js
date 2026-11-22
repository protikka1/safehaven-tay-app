import '../css/style.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import L from 'leaflet';

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

// Reference map only. These coordinates are an approximate neighborhood center,
// NOT verified project boundaries, parcel boundaries, or monitored locations.
const map = L.map('civic-map', { scrollWheelZoom: false }).setView([34.0448, -118.244], 14);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>'
}).addTo(map);
L.circleMarker([34.0448, -118.244], {
  radius: 10, color: '#0b8175', fillColor: '#13b69f', fillOpacity: 0.28, weight: 2
}).addTo(map).bindPopup('Approximate Skid Row reference area. No live monitoring is connected.');

const nav = document.querySelector('#navLinks');
nav.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', () => {
    const toggler = document.querySelector('.navbar-toggler');
    if (window.innerWidth < 992 && nav.classList.contains('show')) toggler.click();
  });
});

document.querySelector('#current-year').textContent = new Date().getFullYear();
loadGitHubUpdates();
