/**
 * recherche-overlay.js — Moteur de recherche Une IA par jour
 *
 * Intercepte la loupe du thème Kenta et ouvre un overlay full-screen
 * avec recherche texte + filtres multi-catégories sur la base CSV.
 *
 * Dépendances : PapaParse (chargé via functions.php)
 * Données     : base-uneiaparjour.csv (GitHub raw)
 */

(function () {
  'use strict';

  // ── Config ────────────────────────────────────────────────
  const CSV_URL  = 'https://raw.githubusercontent.com/uneIAparjour/base/main/base-uneiaparjour.csv';
  const PAGE_SZ  = 48;

  // Sélecteurs possibles pour la loupe Kenta (ordre de priorité)
  const SEARCH_BTN_SELECTORS = [
    '.kenta-search-button',
    'a:has(.fa-magnifying-glass)',
    'button:has(.fa-magnifying-glass)',
    '.kenta-action-search',
    '.kenta-header-search',
    '[data-element="search"]',
    '.header-search-toggle',
    '.search-toggle',
    'button[aria-label*="search" i]',
    'button[aria-label*="recherche" i]',
  ];

  // ── État ──────────────────────────────────────────────────
  let allData    = [];
  let filtered   = [];
  let activeTags = new Set();
  let logic      = 'and';  // 'or' | 'and'
  let query      = '';
  let page       = 0;
  let loaded     = false;
  let loading    = false;

  // ── Init ──────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    buildOverlay();
    hookSearchButton();
  });

  // ── Trouver et intercepter la loupe Kenta ─────────────────
  function hookSearchButton() {
    // Écoute au niveau document en phase de capture :
    // s'exécute AVANT le système kenta-toggleable, quel que soit l'ordre de chargement.
    document.addEventListener('click', function (e) {
      var target = e.target.closest('.kenta-search-button');
      if (!target) return;

      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();

      // Fermer la modal Kenta si elle s'ouvre quand même en parallèle
      setTimeout(function () {
        var kentaModal = document.getElementById('kenta-search-modal');
        if (kentaModal) {
          kentaModal.style.display = 'none';
          kentaModal.setAttribute('aria-hidden', 'true');
        }
      }, 0);

      openOverlay();
    }, true); // true = phase de capture
  }

  // ── Construire l'overlay (une seule fois) ─────────────────
  function buildOverlay() {
    const el = document.createElement('div');
    el.id = 'ro-overlay';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.setAttribute('aria-label', 'Recherche dans la base des outils IA');

    el.innerHTML = `
      <div id="ro-header">
        <div class="ro-header-inner">
          <div class="ro-top-bar">
            <span class="ro-site-name">Une IA par jour</span>
            <button id="ro-close" aria-label="Fermer la recherche">Fermer ✕</button>
          </div>
          <div class="ro-search-wrap">
            <span class="ro-search-icon" aria-hidden="true">🔍</span>
            <input type="search" id="ro-search"
              placeholder="Rechercher un outil, une description…"
              autocomplete="off" spellcheck="false"
              aria-label="Recherche textuelle">
            <button id="ro-clear" aria-label="Effacer la recherche">✕</button>
          </div>
          <div class="ro-tags-row">
            <span class="ro-tags-label" aria-hidden="true">Catégories</span>
            <div class="ro-tags-list" id="ro-tags" role="group" aria-label="Filtrer par catégorie"></div>
          </div>
        </div>
      </div>

      <div id="ro-status">
        <div class="ro-status-inner">
          <div class="ro-count" id="ro-count"></div>
          <div class="ro-logic" id="ro-logic" aria-label="Logique de filtrage">
            <span class="ro-logic-label">Logique :</span>
            <button class="ro-logic-btn" id="ro-btn-or">OU</button>
            <button class="ro-logic-btn ro-active" id="ro-btn-and">ET</button>
          </div>
        </div>
      </div>

      <div id="ro-body">
        <div class="ro-state" id="ro-state">
          <div class="ro-loader"></div>
          <strong>Chargement de la base…</strong>
          Récupération depuis GitHub
        </div>
        <div class="ro-grid-wrap">
          <div id="ro-grid" role="list" aria-label="Résultats de recherche"></div>
          <div id="ro-more-wrap">
            <button id="ro-more">Afficher plus de résultats</button>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(el);
    bindEvents();
  }

  // ── Événements ────────────────────────────────────────────
  function bindEvents() {
    // Fermeture
    document.getElementById('ro-close').addEventListener('click', closeOverlay);
    document.getElementById('ro-overlay').addEventListener('click', function (e) {
      if (e.target === this) closeOverlay();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeOverlay();
    });

    // Recherche texte
    const inp = document.getElementById('ro-search');
    const clr = document.getElementById('ro-clear');

    inp.addEventListener('input', function () {
      query = this.value.trim().toLowerCase();
      clr.classList.toggle('ro-visible', query.length > 0);
      applyFilters();
    });

    clr.addEventListener('click', function () {
      inp.value = '';
      query = '';
      this.classList.remove('ro-visible');
      inp.focus();
      applyFilters();
    });

    // Logique OU/ET
    document.getElementById('ro-btn-or').addEventListener('click', function () { setLogic('or'); });
    document.getElementById('ro-btn-and').addEventListener('click', function () { setLogic('and'); });

    // Load more
    document.getElementById('ro-more').addEventListener('click', function () {
      page++;
      renderCards(false);
    });

    // Intercepter le formulaire de recherche WordPress (sidebar)
    document.addEventListener('submit', function (e) {
      var form = e.target.closest('.widget_search form, .wp-block-search form');
      if (!form) return;
      e.preventDefault();
      var input = form.querySelector('input[type="search"], input[type="text"]');
      var val = input ? input.value.trim() : '';
      openOverlay();
      setTimeout(function () {
        var ro = document.getElementById('ro-search');
        if (ro && val) {
          ro.value = val;
          ro.dispatchEvent(new Event('input'));
        }
      }, 100);
    }, true);
  }

  // ── Ouvrir / fermer ───────────────────────────────────────
  function openOverlay() {
    const overlay = document.getElementById('ro-overlay');
    overlay.classList.add('ro-open');
    document.body.style.overflow = 'hidden';

    // Focus sur le champ de recherche
    setTimeout(function () {
      document.getElementById('ro-search').focus();
    }, 50);

    // Charger les données au premier ouverture seulement
    if (!loaded && !loading) loadData();
  }

  function closeOverlay() {
    document.getElementById('ro-overlay').classList.remove('ro-open');
    document.body.style.overflow = '';
  }

  // ── Chargement CSV ────────────────────────────────────────
  function loadData() {
    loading = true;

    fetch(CSV_URL)
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.text();
      })
      .then(function (text) {
        Papa.parse(text, {
          header: true,
          skipEmptyLines: true,
          complete: function (results) {
            allData = results.data
              .map(parseRow)
              .filter(function (r) { return r.titre; });

            loaded  = true;
            loading = false;
            buildTags();
            applyFilters();
            document.getElementById('ro-state').style.display = 'none';
          },
          error: function (err) { showError(err.message); }
        });
      })
      .catch(function (err) {
        showError('Impossible de charger la base : ' + err.message);
      });
  }

  // ── Parsing d'une ligne CSV ───────────────────────────────
  // Colonnes : Titre | Description | URL article | Cat1→6 | Date
  function parseRow(row) {
    var vals = Object.keys(row).map(function (k) { return (row[k] || '').trim(); });
    return {
      titre : vals[0] || '',
      desc  : vals[1] || '',
      url   : vals[2] || '',
      cats  : [vals[3], vals[4], vals[5], vals[6], vals[7], vals[8]].filter(Boolean),
      date  : vals[9] || ''
    };
  }

  // ── Construction des tags de catégories ───────────────────
  function buildTags() {
    var counts = {};
    allData.forEach(function (r) {
      r.cats.forEach(function (c) { counts[c] = (counts[c] || 0) + 1; });
    });

    var sorted = Object.keys(counts).sort(function (a, b) {
      return a.localeCompare(b, 'fr');
    });

    var container = document.getElementById('ro-tags');
    container.innerHTML = '';

    sorted.forEach(function (cat) {
      var btn = document.createElement('button');
      btn.className   = 'ro-tag';
      btn.textContent = cat;
      btn.dataset.cat = cat;
      btn.addEventListener('click', function () { toggleTag(cat); });
      container.appendChild(btn);
    });

    // Bouton "Tout effacer"
    var reset = document.createElement('button');
    reset.className   = 'ro-tag-reset';
    reset.id          = 'ro-tag-reset';
    reset.textContent = 'Tout effacer';
    reset.addEventListener('click', clearTags);
    container.appendChild(reset);
  }

  // ── Gestion des tags ──────────────────────────────────────
  function toggleTag(cat) {
    if (activeTags.has(cat)) activeTags.delete(cat);
    else activeTags.add(cat);

    document.querySelectorAll('.ro-tag').forEach(function (btn) {
      btn.classList.toggle('ro-active', activeTags.has(btn.dataset.cat));
    });

    var resetBtn = document.getElementById('ro-tag-reset');
    if (resetBtn) resetBtn.classList.toggle('ro-visible', activeTags.size > 0);

    var logicEl = document.getElementById('ro-logic');
    logicEl.classList.toggle('ro-visible', activeTags.size >= 2);

    applyFilters();
  }

  function clearTags() {
    activeTags.clear();
    document.querySelectorAll('.ro-tag').forEach(function (b) {
      b.classList.remove('ro-active');
    });
    var r = document.getElementById('ro-tag-reset');
    if (r) r.classList.remove('ro-visible');
    document.getElementById('ro-logic').classList.remove('ro-visible');
    applyFilters();
  }

  function setLogic(l) {
    logic = l;
    document.getElementById('ro-btn-or').classList.toggle('ro-active', l === 'or');
    document.getElementById('ro-btn-and').classList.toggle('ro-active', l === 'and');
    applyFilters();
  }

  // ── Normalisation : accents + pluriel simple ──────────────
  function normalize(str) {
    return str
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')  // supprime les diacritiques
      .replace(/\b(\w{3,})s\b/g, '$1'); // retire le s final (pluriel simple)
  }

  // ── Filtrage ──────────────────────────────────────────────
  function applyFilters() {
    var q    = normalize(query);
    var tags = activeTags;

    filtered = allData.filter(function (r) {
    // Filtre texte — chaque mot doit être présent (logique ET)
      if (q) {
        var hay = normalize(r.titre + ' ' + r.desc);
        var words = q.split(/\s+/).filter(Boolean);
        if (!words.every(function (w) { return hay.indexOf(w) !== -1; })) return false;
      }
      // Filtre catégories
      if (tags.size > 0) {
        var rCats = r.cats;
        if (logic === 'or') {
          var found = false;
          tags.forEach(function (t) { if (rCats.indexOf(t) !== -1) found = true; });
          if (!found) return false;
        } else {
          var allFound = true;
          tags.forEach(function (t) { if (rCats.indexOf(t) === -1) allFound = false; });
          if (!allFound) return false;
        }
      }
      return true;
    });

    page = 0;
    renderStatus();
    renderCards(true);
  }

  // ── Statut ────────────────────────────────────────────────
  function renderStatus() {
    var el    = document.getElementById('ro-count');
    var total = allData.length;
    var n     = filtered.length;
    if (!total) { el.innerHTML = ''; return; }
    if (n === total) {
      el.innerHTML = '<span>' + total + '</span> outils';
    } else {
      el.innerHTML = '<span>' + n + '</span> résultat' + (n > 1 ? 's' : '') + ' sur ' + total + ' outils';
    }
  }

  // ── Rendu des cartes ──────────────────────────────────────
  function renderCards(reset) {
    var grid     = document.getElementById('ro-grid');
    var stateEl  = document.getElementById('ro-state');
    var moreWrap = document.getElementById('ro-more-wrap');

    if (reset) {
      grid.innerHTML = '';
      stateEl.style.display = 'none';
      if (reset) document.getElementById('ro-body').scrollTop = 0;
    }

    if (filtered.length === 0) {
      stateEl.innerHTML =
        '<div class="ro-icon">🔍</div>' +
        '<strong>Aucun résultat</strong>' +
        'Essayez d\'autres termes ou retirez des filtres.';
      stateEl.style.display = 'block';
      moreWrap.style.display = 'none';
      return;
    }

    var start    = page * PAGE_SZ;
    var end      = start + PAGE_SZ;
    var slice    = filtered.slice(start, end);
    var fragment = document.createDocumentFragment();

    slice.forEach(function (r, i) {
      var card = document.createElement('div');
      card.className = 'ro-card';
      card.setAttribute('role', 'listitem');
      card.style.animationDelay = (i % PAGE_SZ * 12) + 'ms';

      var tagsHtml = r.cats.map(function (c) {
        var matched = activeTags.has(c) ? ' ro-matched' : '';
        return '<button class="ro-card-tag' + matched + '" data-cat="' + esc(c) + '">' + esc(c) + '</button>';
      }).join('');

      var linkHtml = r.url
        ? '<a class="ro-card-link" href="' + esc(r.url) + '" target="_blank" rel="noopener">Voir</a>'
        : '';

      card.innerHTML =
        '<div class="ro-card-head">' +
          '<div class="ro-card-title">' + hi(r.titre) + '</div>' +
          '<div class="ro-card-date">'  + esc(r.date)  + '</div>' +
        '</div>' +
        '<div class="ro-card-desc">'  + hi(r.desc)  + '</div>' +
        '<div class="ro-card-foot">' +
          '<div class="ro-card-tags">' + tagsHtml + '</div>' +
          linkHtml +
        '</div>';

      // Clic sur un tag dans la carte → active le filtre
      card.querySelectorAll('.ro-card-tag').forEach(function (tagEl) {
        tagEl.addEventListener('click', function () { toggleTag(this.dataset.cat); });
      });

      fragment.appendChild(card);
    });

    grid.appendChild(fragment);

    // Load more
    var hasMore = end < filtered.length;
    moreWrap.style.display = hasMore ? 'block' : 'none';
    if (hasMore) {
      var remaining = filtered.length - end;
      document.getElementById('ro-more').textContent =
        'Afficher ' + Math.min(PAGE_SZ, remaining) + ' résultats de plus (' + remaining + ' restants)';
    }
  }

  // ── Utilitaires ───────────────────────────────────────────
  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function hi(text) {
    if (!query) return esc(text);
    var escaped = esc(text);
    var re = new RegExp(escReg(esc(query)), 'gi');
    return escaped.replace(re, function (m) { return '<mark>' + m + '</mark>'; });
  }

  function escReg(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function showError(msg) {
    var body    = document.getElementById('ro-body');
    var stateEl = document.getElementById('ro-state');
    stateEl.style.display = 'none';
    var err = document.createElement('div');
    err.className   = 'ro-error';
    err.textContent = '⚠ ' + msg;
    body.insertBefore(err, body.firstChild);
    loading = false;
  }

})();
