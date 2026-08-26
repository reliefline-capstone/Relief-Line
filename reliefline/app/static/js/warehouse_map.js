document.addEventListener('DOMContentLoaded', function () {
    var mapEl = document.getElementById('warehouse-map');
    if (!mapEl) return;

    var points = window.RELIEFLINE_WAREHOUSE_POINTS || [];

    var HEALTH_COLORS = {
        Healthy: '#27ae60',
        Moderate: '#f1c40f',
        Low: '#e74c3c',
    };

    var map = L.map(mapEl, {
        zoomControl: true,
        scrollWheelZoom: false,
    }).setView([15.98, 120.45], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 15,
    }).addTo(map);

    var markers = [];
    points.forEach(function (w) {
        var color = HEALTH_COLORS[w.health] || '#8a94a6';
        var marker = L.circleMarker([w.lat, w.lng], {
            radius: 12,
            color: '#fff',
            weight: 2,
            fillColor: color,
            fillOpacity: 0.9,
        }).addTo(map);

        marker.bindPopup(
            '<strong>' + w.name + '</strong><br>' +
            w.area_covered + '<br>' +
            w.food_pack_qty.toLocaleString() + ' / ' + w.capacity.toLocaleString() + ' packs (' + w.pct + '%)<br>' +
            '<span style="color:' + color + '; font-weight:700;">' + w.health + '</span>'
        );
        markers.push(marker);
    });

    if (markers.length) {
        var group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.3));
        if (markers.length === 1) map.setZoom(11);
    }
});
