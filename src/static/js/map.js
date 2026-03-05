(function () {
  'use strict';

  var map          = null;
  var clusterGroup = null;
  var markers      = {};   // listing id -> L.Marker
  var cardEls      = {};   // listing id -> .listing-col element
  var isMapMode    = false;

  function esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  var markerIcon = null;

  function getMarkerIcon() {
    if (!markerIcon) {
      markerIcon = L.divIcon({
        className: '',
        html: '<div class="map-marker"></div>',
        iconSize:    [26, 26],
        iconAnchor:  [13, 13],
        popupAnchor: [0, -16],
      });
    }
    return markerIcon;
  }

  function initMap() {
    if (map) return;

    map = L.map('map').setView([1.3521, 103.8198], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map);

    clusterGroup = L.markerClusterGroup({ maxClusterRadius: 40 });

    var cols   = document.querySelectorAll('.listing-col[data-listing-id]');
    var bounds = [];

    cols.forEach(function (col) {
      var id  = col.dataset.listingId;
      var lat = parseFloat(col.dataset.lat);
      var lng = parseFloat(col.dataset.lng);

      if (!id || isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) return;

      cardEls[id] = col;

      var popup =
        '<div class="map-popup">' +
          '<strong class="map-popup-title">' + esc(col.dataset.title) + '</strong>' +
          '<div class="map-popup-price">' + esc(col.dataset.cuisine) + ' &mdash; S$' + esc(col.dataset.price) + ' / person</div>' +
          '<a href="' + esc(col.dataset.url) + '" class="map-popup-link">View Details &rarr;</a>' +
        '</div>';

      var marker = L.marker([lat, lng], { icon: getMarkerIcon() })
        .bindPopup(popup, { maxWidth: 220 });

      marker.on('click', function () { scrollToCard(id); });

      markers[id] = marker;
      clusterGroup.addLayer(marker);
      bounds.push([lat, lng]);
    });

    clusterGroup.addTo(map);

    if (bounds.length === 1) {
      map.setView(bounds[0], 15);
    } else if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }

  function clearHighlights() {
    Object.values(cardEls).forEach(function (c) {
      c.classList.remove('card-highlighted');
    });
  }

  function activateCard(id) {
    clearHighlights();
    if (cardEls[id]) cardEls[id].classList.add('card-highlighted');
    if (markers[id] && clusterGroup) {
      clusterGroup.zoomToShowLayer(markers[id], function () {
        markers[id].openPopup();
      });
    }
  }

  function scrollToCard(id) {
    clearHighlights();
    if (cardEls[id]) {
      cardEls[id].classList.add('card-highlighted');
      cardEls[id].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  // ── Card click handler (event delegation on #cards-col) ──────────
  var cardsCol = document.getElementById('cards-col');
  if (cardsCol) {
    cardsCol.addEventListener('click', function (e) {
      if (!isMapMode) return;
      if (e.target.closest('.card-footer a, .card-footer button')) return;
      var col = e.target.closest('.listing-col');
      if (!col) return;
      e.preventDefault();
      activateCard(col.dataset.listingId);
    });
  }

  // ── Toggle buttons ────────────────────────────────────────────────
  var btnList  = document.getElementById('btn-list-view');
  var btnMap   = document.getElementById('btn-map-view');
  var wrapper  = document.getElementById('results-wrapper');
  var mapPanel = document.getElementById('map-panel');

  if (!btnList || !btnMap || !wrapper || !mapPanel) return;

  function setListView() {
    isMapMode = false;
    wrapper.classList.remove('map-mode');
    mapPanel.classList.add('d-none');
    btnList.classList.add('btn-secondary');
    btnList.classList.remove('btn-outline-secondary');
    btnMap.classList.remove('btn-secondary');
    btnMap.classList.add('btn-outline-secondary');
    clearHighlights();
  }

  function setMapView() {
    isMapMode = true;
    wrapper.classList.add('map-mode');
    mapPanel.classList.remove('d-none');
    btnMap.classList.add('btn-secondary');
    btnMap.classList.remove('btn-outline-secondary');
    btnList.classList.remove('btn-secondary');
    btnList.classList.add('btn-outline-secondary');
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        initMap();
        if (map) map.invalidateSize();
      });
    });
  }

  btnList.addEventListener('click', setListView);
  btnMap.addEventListener('click', setMapView);

  window.addEventListener('resize', function () {
    if (isMapMode && map) map.invalidateSize();
  });
}());
